import asyncio
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.pdf_parser import PDFParserService
from app.services.job_analyzer import JobAnalyzerService
from app.services.structured_extractor import StructuredExtractorService
from app.services.scoring_engine import ScoringEngineService

ARJUN_RESUME = """Arjun Kumar
Email: arjun.kumar@example.com

EDUCATION
B.Tech in Computer Science and Engineering
2027

EXPERIENCE
Software Engineering Intern | Tech Solutions
June 2025 - May 2026
- Developed RESTful backend APIs using Python and FastAPI.
- Worked with PostgreSQL databases and optimized SQL queries.
- Used Docker for containerization and Git for version control.
- Debugged production issues and optimized SQL queries.

PROJECTS
E-Commerce Backend
- Developed a RESTful backend using FastAPI and PostgreSQL.
- Implemented product, order and authentication APIs.
- Containerized the application using Docker.

Student Management System
- Built a Java Spring Boot backend.
- Designed REST APIs and MySQL database integration.
- Implemented CRUD operations and validation.

SKILLS
Python, Java, FastAPI, Docker, Git, SQL, PostgreSQL, Debugging, Object-Oriented Programming, Data Structures & Algorithms, Software Development Lifecycle, Code Review, CI/CD, Agile
"""

RAHUL_RESUME = """Rahul Sharma
Email: rahul.sharma@example.com

SUMMARY
Passionate developer interested in software engineering roles.

SKILLS
Python, Java, FastAPI, Docker, AWS, Git, SQL, PostgreSQL, Spring Boot, Debugging, Software Development Fundamentals
"""

JOB_DESCRIPTION = """Job Title: Backend Developer

Required Skills:
- Python
- Java
- REST APIs
- Git
- SQL
- Debugging
- Software Development Fundamentals

Education Requirements:
- B.Tech or equivalent in Computer Science

Experience Requirements:
- 1+ years of backend engineering or internship experience.
"""

async def run_arjun_vs_rahul_validation():
    print("==================================================")
    print("    RECRUITIQ VALIDATION TEST: ARJUN VS RAHUL     ")
    print("==================================================\n")

    job_profile = await JobAnalyzerService.analyze_job_description(JOB_DESCRIPTION, "Backend Developer")

    # 1. Ingest Arjun
    arjun_raw, arjun_secs = PDFParserService.extract_text_from_bytes(ARJUN_RESUME.encode("utf-8"), "arjun_resume.txt")
    arjun_profile = await StructuredExtractorService.extract_candidate_profile(arjun_raw, arjun_secs)
    arjun_chunks = [
        {"candidate_id": "arjun", "candidate_name": "Arjun Kumar", "section": k, "text": v}
        for k, v in arjun_secs.items() if v
    ]
    arjun_result = await ScoringEngineService.evaluate_candidate("arjun", arjun_profile, job_profile, arjun_chunks)

    # 2. Ingest Rahul
    rahul_raw, rahul_secs = PDFParserService.extract_text_from_bytes(RAHUL_RESUME.encode("utf-8"), "rahul_resume.txt")
    rahul_profile = await StructuredExtractorService.extract_candidate_profile(rahul_raw, rahul_secs)
    rahul_chunks = [
        {"candidate_id": "rahul", "candidate_name": "Rahul Sharma", "section": k, "text": v}
        for k, v in rahul_secs.items() if v
    ]
    rahul_result = await ScoringEngineService.evaluate_candidate("rahul", rahul_profile, job_profile, rahul_chunks)

    safe_explanation = arjun_result.llm_explanation.encode('ascii', 'ignore').decode('ascii')

    print(f"--- CANDIDATE 1: ARJUN KUMAR (Demonstrated Evidence) ---")
    print(f"  Final Match Score:      {arjun_result.final_score}% (Confidence: {arjun_result.confidence})")
    print(f"  Required Skills Score:  {arjun_result.score_breakdown.skill_score}% ({arjun_result.score_breakdown.skill_points}/35 pts)")
    print(f"  Semantic Fit Score:     {arjun_result.score_breakdown.semantic_score}% ({arjun_result.score_breakdown.semantic_points}/25 pts)")
    print(f"  Experience Score:       {arjun_result.score_breakdown.experience_score}% ({arjun_result.score_breakdown.experience_points}/15 pts)")
    print(f"  Education Score:        {arjun_result.score_breakdown.education_score}% ({arjun_result.score_breakdown.education_points}/10 pts)")
    print(f"  Project Score:          {arjun_result.score_breakdown.project_score}% ({arjun_result.score_breakdown.project_points}/10 pts)")
    print(f"  Evidence Coverage:      {arjun_result.evidence_coverage}%")
    print(f"  Extracted Education:    {[f'{e.degree}' for e in arjun_profile.education]}")
    print(f"  Extracted Projects:     {[f'{p.name}' for p in arjun_profile.projects]}")
    print(f"  Grounded Explanation:   \"{safe_explanation}\"")
    print(f"\n  Score Audit Object Summary:")
    if arjun_result.score_audit_object:
        print(f"    - Education Audit:    {arjun_result.score_audit_object.education.score}% | Evidence: {arjun_result.score_audit_object.education.verified_evidence}")
        print(f"    - Projects Audit:     {arjun_result.score_audit_object.projects.score}% | Evidence: {arjun_result.score_audit_object.projects.verified_evidence}")

    print(f"\n--- CANDIDATE 2: RAHUL SHARMA (Keyword Stuffer / Claimed Only) ---")
    print(f"  Final Match Score:      {rahul_result.final_score}% (Confidence: {rahul_result.confidence})")
    print(f"  Required Skills Score:  {rahul_result.score_breakdown.skill_score}% ({rahul_result.score_breakdown.skill_points}/35 pts)")
    print(f"  Semantic Fit Score:     {rahul_result.score_breakdown.semantic_score}% ({rahul_result.score_breakdown.semantic_points}/25 pts)")
    print(f"  Experience Score:       {rahul_result.score_breakdown.experience_score}% ({rahul_result.score_breakdown.experience_points}/15 pts)")
    print(f"  Education Score:        {rahul_result.score_breakdown.education_score}% ({rahul_result.score_breakdown.education_points}/10 pts)")
    print(f"  Project Score:          {rahul_result.score_breakdown.project_score}% ({rahul_result.score_breakdown.project_points}/10 pts)")
    print(f"  Evidence Coverage:      {rahul_result.evidence_coverage}%")

    print("\n==================================================")
    print("               VERIFICATION CHECKS                ")
    print("==================================================")

    # Verification checks
    check_edu_audit = arjun_result.score_audit_object is not None and arjun_result.score_audit_object.education.score >= 90.0 and len(arjun_result.score_audit_object.education.verified_evidence) > 0
    check_semantic_high = arjun_result.score_breakdown.semantic_score >= 70.0
    check_no_contradiction = "cannot be verified" not in safe_explanation.lower() and "missing" not in safe_explanation.lower()[:100]
    check_arjun_rank = arjun_result.final_score > (rahul_result.final_score + 30.0)

    print(f"1. Education Audit Object Verified (B.Tech):        [{'PASS' if check_edu_audit else 'FAIL'}] ({arjun_result.score_breakdown.education_score}%)")
    print(f"2. Section-Aware Semantic Fit Score (>= 70%):      [{'PASS' if check_semantic_high else 'FAIL'}] ({arjun_result.score_breakdown.semantic_score}%)")
    print(f"3. Explanation Free of Education Contradictions:   [{'PASS' if check_no_contradiction else 'FAIL'}]")
    print(f"4. Arjun ranks clearly above Rahul (+30% score gap):   [{'PASS' if check_arjun_rank else 'FAIL'}] ({arjun_result.final_score}% vs {rahul_result.final_score}%)")
    print("==================================================\n")

    assert check_edu_audit and check_semantic_high and check_no_contradiction and check_arjun_rank, "Validation failed!"

if __name__ == "__main__":
    asyncio.run(run_arjun_vs_rahul_validation())
