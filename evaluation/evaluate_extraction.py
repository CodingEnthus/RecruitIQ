import os
import json
import asyncio
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.pdf_parser import PDFParserService
from app.services.structured_extractor import StructuredExtractorService

async def run_extraction_evaluation():
    base_dir = os.path.dirname(__file__)
    resumes_dir = os.path.join(base_dir, "resumes")
    expected_path = os.path.join(base_dir, "expected_results.json")

    with open(expected_path, "r") as f:
        expected_data = json.load(f)

    expected_skills_map = expected_data.get("expected_skills", {})
    
    total_tp = 0
    total_fp = 0
    total_fn = 0

    print("=== RecruitIQ Structured Extraction Evaluation ===")

    for filename in sorted(os.listdir(resumes_dir)):
        if not filename.endswith(".txt"):
            continue

        file_path = os.path.join(resumes_dir, filename)
        with open(file_path, "rb") as f:
            content = f.read()

        raw_text, sections = PDFParserService.extract_text_from_bytes(content, filename)
        profile = await StructuredExtractorService.extract_candidate_profile(raw_text, sections)

        cand_name = profile.name
        extracted_skills = set(s.lower() for s in profile.normalized_skills)
        target_skills = set(s.lower() for s in expected_skills_map.get(cand_name, []))

        if not target_skills:
            continue

        tp = len(extracted_skills.intersection(target_skills))
        fp = len(extracted_skills - target_skills)
        fn = len(target_skills - extracted_skills)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        precision = tp / float(tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / float(tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        print(f"Candidate: {cand_name}")
        print(f"  Extracted Skills ({len(extracted_skills)}): {list(profile.normalized_skills)}")
        print(f"  Precision: {precision:.2f} | Recall: {recall:.2f} | F1: {f1:.2f}\n")

    overall_precision = total_tp / float(total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    overall_recall = total_tp / float(total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0.0

    print("--- OVERALL EXTRACTION METRICS ---")
    print(f"Overall Precision: {overall_precision:.4f}")
    print(f"Overall Recall:    {overall_recall:.4f}")
    print(f"Overall F1 Score:  {overall_f1:.4f}")

if __name__ == "__main__":
    asyncio.run(run_extraction_evaluation())
