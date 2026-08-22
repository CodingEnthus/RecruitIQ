import os
import json
import math
import asyncio
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.pdf_parser import PDFParserService
from app.services.job_analyzer import JobAnalyzerService
from app.services.structured_extractor import StructuredExtractorService
from app.services.injection_guard import InjectionGuardService
from app.services.scoring_engine import ScoringEngineService

async def run_ranking_evaluation():
    base_dir = os.path.dirname(__file__)
    resumes_dir = os.path.join(base_dir, "resumes")
    job_path = os.path.join(base_dir, "jobs", "senior_backend_job.txt")
    expected_path = os.path.join(base_dir, "expected_results.json")

    with open(expected_path, "r") as f:
        expected = json.load(f)

    with open(job_path, "r") as f:
        job_raw = f.read()

    job_profile = await JobAnalyzerService.analyze_job_description(job_raw, "Senior AI Backend Engineer")

    evaluated_candidates = []

    for filename in sorted(os.listdir(resumes_dir)):
        if not filename.endswith(".txt"):
            continue

        file_path = os.path.join(resumes_dir, filename)
        with open(file_path, "rb") as f:
            content = f.read()

        raw_text, sections = PDFParserService.extract_text_from_bytes(content, filename)
        has_inj, inj_warn = InjectionGuardService.scan_for_injection(raw_text)
        profile = await StructuredExtractorService.extract_candidate_profile(raw_text, sections)

        evidence_chunks = [
            {"candidate_id": filename, "candidate_name": profile.name, "section": k, "text": v, "reranker_score": 0.85}
            for k, v in sections.items() if v
        ]

        res = await ScoringEngineService.evaluate_candidate(
            candidate_id=filename,
            profile=profile,
            job_profile=job_profile,
            retrieved_evidence=evidence_chunks,
            has_prompt_injection=has_inj,
            injection_warning=inj_warn
        )
        evaluated_candidates.append(res)

    # Sort candidates descending by deterministic score
    evaluated_candidates.sort(key=lambda x: x.final_score, reverse=True)

    predicted_ranking = [c.candidate_name for c in evaluated_candidates]
    expected_order = expected.get("expected_rank_order", [])
    expected_top5 = set(expected.get("expected_top_5", []))

    # Calculate Precision@5 & Recall@5
    pred_top5 = set(predicted_ranking[:5])
    relevant_in_top5 = len(pred_top5.intersection(expected_top5))

    precision_at_5 = relevant_in_top5 / 5.0
    recall_at_5 = relevant_in_top5 / float(len(expected_top5)) if expected_top5 else 1.0

    # Calculate MRR (Mean Reciprocal Rank of Top Candidate)
    mrr = 0.0
    top_expected = expected_order[0] if expected_order else ""
    for rank, cand_name in enumerate(predicted_ranking, 1):
        if cand_name == top_expected:
            mrr = 1.0 / rank
            break

    # Calculate NDCG@5
    dcg = 0.0
    idcg = 0.0

    rel_map = {name: (len(expected_order) - idx) for idx, name in enumerate(expected_order)}

    for i, name in enumerate(predicted_ranking[:5], 1):
        rel = rel_map.get(name, 0)
        dcg += (2**rel - 1) / math.log2(i + 1)

    for i, name in enumerate(expected_order[:5], 1):
        rel = rel_map.get(name, 0)
        idcg += (2**rel - 1) / math.log2(i + 1)

    ndcg_at_5 = (dcg / idcg) if idcg > 0 else 0.0

    print("=== RecruitIQ Candidate Ranking Evaluation ===")
    print("Predicted Ranking:")
    for rank, c in enumerate(evaluated_candidates, 1):
        inj_str = " [PROMPT INJECTION DETECTED]" if c.has_prompt_injection else ""
        print(f"  #{rank} {c.candidate_name}: Score = {c.final_score}% (Confidence: {c.confidence}){inj_str}")

    print("\n--- RANKING METRICS ---")
    print(f"Precision@5: {precision_at_5:.4f}")
    print(f"Recall@5:    {recall_at_5:.4f}")
    print(f"MRR:         {mrr:.4f}")
    print(f"NDCG@5:      {ndcg_at_5:.4f}")

if __name__ == "__main__":
    asyncio.run(run_ranking_evaluation())
