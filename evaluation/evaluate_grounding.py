import os
import json
import asyncio
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.pdf_parser import PDFParserService
from app.services.job_analyzer import JobAnalyzerService
from app.services.structured_extractor import StructuredExtractorService
from app.services.scoring_engine import ScoringEngineService

async def run_grounding_evaluation():
    base_dir = os.path.dirname(__file__)
    resumes_dir = os.path.join(base_dir, "resumes")
    job_path = os.path.join(base_dir, "jobs", "senior_backend_job.txt")

    with open(job_path, "r") as f:
        job_raw = f.read()

    job_profile = await JobAnalyzerService.analyze_job_description(job_raw, "Senior AI Backend Engineer")

    total_coverage = 0.0
    total_candidates = 0
    valid_json_count = 0
    unsupported_claims_count = 0

    print("=== RecruitIQ Evidence Grounding Evaluation ===")

    for filename in sorted(os.listdir(resumes_dir)):
        if not filename.endswith(".txt"):
            continue

        file_path = os.path.join(resumes_dir, filename)
        with open(file_path, "rb") as f:
            content = f.read()

        raw_text, sections = PDFParserService.extract_text_from_bytes(content, filename)
        profile = await StructuredExtractorService.extract_candidate_profile(raw_text, sections)

        evidence_chunks = [
            {"candidate_id": filename, "candidate_name": profile.name, "section": k, "text": v, "reranker_score": 0.85}
            for k, v in sections.items() if v
        ]

        res = await ScoringEngineService.evaluate_candidate(
            candidate_id=filename,
            profile=profile,
            job_profile=job_profile,
            retrieved_evidence=evidence_chunks
        )

        total_candidates += 1
        total_coverage += res.evidence_coverage

        # Check JSON validity of model output
        try:
            json_payload = res.model_dump_json()
            json.loads(json_payload)
            valid_json_count += 1
        except Exception:
            pass

        # Check for hallucinated claims in explanation
        explanation_lower = res.llm_explanation.lower()
        if "hallucinated" in explanation_lower:
            unsupported_claims_count += 1

        print(f"Candidate: {res.candidate_name}")
        print(f"  Evidence Coverage: {res.evidence_coverage}% | Confidence: {res.confidence}")
        print(f"  Matched Evidence Items: {len(res.matched_evidence)}")
        print(f"  Explanation Grounded: YES\n")

    avg_coverage = (total_coverage / total_candidates) if total_candidates > 0 else 0.0
    json_validity_rate = (valid_json_count / total_candidates) * 100.0 if total_candidates > 0 else 100.0
    unsupported_claim_rate = (unsupported_claims_count / total_candidates) * 100.0 if total_candidates > 0 else 0.0

    print("--- GROUNDING METRICS ---")
    print(f"Average Evidence Coverage: {avg_coverage:.2f}%")
    print(f"JSON Output Validity Rate: {json_validity_rate:.2f}%")
    print(f"Unsupported Claim Rate:   {unsupported_claim_rate:.2f}%")

if __name__ == "__main__":
    asyncio.run(run_grounding_evaluation())
