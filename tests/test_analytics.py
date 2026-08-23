import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.domain import Candidate, Job, ScreeningResult, EvidenceItem, CandidateSkill
from app.api.v1.analytics import get_recruiter_analytics


@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    await engine.dispose()

@pytest.mark.asyncio
async def test_case_a_three_candidates_scores_and_strong_matches(async_db: AsyncSession):
    # CASE A: 3 candidates with scores 88.9, 71.1, 60.6
    job = Job(id="job_1", title="Backend Engineer", raw_text="Job", structured_profile={"required_skills": ["Python"]})
    async_db.add(job)

    c1 = Candidate(id="cand_1", name="Arjun", raw_resume_text="Resume 1")
    c2 = Candidate(id="cand_2", name="Neha", raw_resume_text="Resume 2")
    c3 = Candidate(id="cand_3", name="Rahul", raw_resume_text="Resume 3")
    async_db.add_all([c1, c2, c3])
    await async_db.commit()

    sr1 = ScreeningResult(id="sr_1", job_id="job_1", candidate_id="cand_1", final_score=88.9, confidence="HIGH", evidence_coverage=100.0, explanation_json={})
    sr2 = ScreeningResult(id="sr_2", job_id="job_1", candidate_id="cand_2", final_score=71.1, confidence="HIGH", evidence_coverage=80.0, explanation_json={})
    sr3 = ScreeningResult(id="sr_3", job_id="job_1", candidate_id="cand_3", final_score=60.6, confidence="MEDIUM", evidence_coverage=70.0, explanation_json={})
    async_db.add_all([sr1, sr2, sr3])
    await async_db.commit()

    analytics = await get_recruiter_analytics(async_db)

    assert analytics["total_candidates"] == 3
    assert analytics["strong_matches"] == 1  # Only 88.9 >= 85.0
    assert abs(analytics["average_match_score"] - 73.5) <= 0.1  # (88.9 + 71.1 + 60.6) / 3 = 73.53 -> 73.5

@pytest.mark.asyncio
async def test_case_b_missing_skills_unique_candidate_count(async_db: AsyncSession):
    # CASE B: 3 candidates all missing Software Development Fundamentals (with multiple evidence items per cand)
    job = Job(id="job_1", title="Backend Engineer", raw_text="Job", structured_profile={"required_skills": ["Software Development Fundamentals"]})
    async_db.add(job)

    c1 = Candidate(id="cand_1", name="Candidate 1", raw_resume_text="Resume 1")
    c2 = Candidate(id="cand_2", name="Candidate 2", raw_resume_text="Resume 2")
    c3 = Candidate(id="cand_3", name="Candidate 3", raw_resume_text="Resume 3")
    async_db.add_all([c1, c2, c3])
    await async_db.commit()

    sr1 = ScreeningResult(id="sr_1", job_id="job_1", candidate_id="cand_1", final_score=70.0, confidence="HIGH", evidence_coverage=50.0, explanation_json={})
    sr2 = ScreeningResult(id="sr_2", job_id="job_1", candidate_id="cand_2", final_score=70.0, confidence="HIGH", evidence_coverage=50.0, explanation_json={})
    sr3 = ScreeningResult(id="sr_3", job_id="job_1", candidate_id="cand_3", final_score=70.0, confidence="HIGH", evidence_coverage=50.0, explanation_json={})
    async_db.add_all([sr1, sr2, sr3])
    await async_db.commit()

    # Add 4 evidence items total (cand_1 has 2 items for same requirement)
    ev1 = EvidenceItem(screening_result_id="sr_1", requirement="Software Development Fundamentals", evidence_text="No evidence", section="N/A", match_status="missing")
    ev2 = EvidenceItem(screening_result_id="sr_1", requirement="Software Development Fundamentals", evidence_text="No evidence 2", section="N/A", match_status="missing")
    ev3 = EvidenceItem(screening_result_id="sr_2", requirement="Software Development Fundamentals", evidence_text="No evidence", section="N/A", match_status="missing")
    ev4 = EvidenceItem(screening_result_id="sr_3", requirement="Software Development Fundamentals", evidence_text="No evidence", section="N/A", match_status="missing")
    async_db.add_all([ev1, ev2, ev3, ev4])
    await async_db.commit()

    analytics = await get_recruiter_analytics(async_db)

    # Must equal 3 unique candidate IDs missing the skill, NOT 4 raw evidence items
    sdf_missing = next(item for item in analytics["most_missing_skills"] if item["skill"] == "Software Development Fundamentals")
    assert sdf_missing["count"] == 3

@pytest.mark.asyncio
async def test_case_c_duplicate_screening_results_uses_latest(async_db: AsyncSession):
    # CASE C: Same candidate has 2 screening results (old: 50.0, new: 90.0)
    job = Job(id="job_1", title="Dev", raw_text="Job", structured_profile={})
    cand = Candidate(id="cand_1", name="Arjun", raw_resume_text="Resume")
    async_db.add_all([job, cand])
    await async_db.commit()

    old_time = datetime.utcnow() - timedelta(days=1)
    new_time = datetime.utcnow()

    sr_old = ScreeningResult(id="sr_old", job_id="job_1", candidate_id="cand_1", final_score=50.0, confidence="LOW", evidence_coverage=50.0, explanation_json={}, created_at=old_time)
    sr_new = ScreeningResult(id="sr_new", job_id="job_1", candidate_id="cand_1", final_score=90.0, confidence="HIGH", evidence_coverage=100.0, explanation_json={}, created_at=new_time)
    async_db.add_all([sr_old, sr_new])
    await async_db.commit()

    analytics = await get_recruiter_analytics(async_db)

    # Candidate should be counted once using latest screening result (90.0)
    assert analytics["total_candidates"] == 1
    assert analytics["average_match_score"] == 90.0
    assert analytics["strong_matches"] == 1

@pytest.mark.asyncio
async def test_case_d_no_candidates_returns_zero_defaults(async_db: AsyncSession):
    # CASE D: No candidates in DB
    analytics = await get_recruiter_analytics(async_db)

    assert analytics["total_candidates"] == 0
    assert analytics["average_match_score"] == 0.0
    assert analytics["strong_matches"] == 0
    assert analytics["most_missing_skills"] == []
    assert analytics["most_common_candidate_skills"] == []
