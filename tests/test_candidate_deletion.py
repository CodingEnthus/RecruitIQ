import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
import asyncio
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal, init_db, engine, Base
from app.models.domain import Candidate, Resume, CandidateSkill
from app.services.vector_store import VectorStoreService

@pytest.mark.asyncio
async def test_vector_store_deletion():
    vector_store = VectorStoreService()
    cand_id = "test_del_cand_123"
    
    # 1. Upsert dummy vectors
    chunks = [
        {"section": "Summary", "text": "Experienced Python Backend Developer.", "candidate_name": "Test Candidate"}
    ]
    embeddings = [[0.1] * 1024]
    vector_store.upsert_chunks(cand_id, chunks, embeddings)
    
    # 2. Search to confirm presence
    results = vector_store.search_similar([0.1] * 1024, candidate_ids=[cand_id])
    assert len(results) >= 1
    
    # 3. Delete candidate vectors
    vector_store.delete_candidate_vectors(cand_id)
    
    # 4. Search again to confirm deletion
    results_after = vector_store.search_similar([0.1] * 1024, candidate_ids=[cand_id])
    assert len(results_after) == 0

@pytest.mark.asyncio
async def test_database_candidate_deletion():
    await init_db()
    async with AsyncSessionLocal() as session:

        # Create candidate
        cand = Candidate(
            name="Test Delete DB",
            email="delete_me@example.com",
            raw_resume_text="Experienced Backend Developer with Python skills."
        )
        session.add(cand)
        await session.flush()

        # Add child skill and resume
        skill = CandidateSkill(candidate_id=cand.id, raw_skill="Python", normalized_skill="Python")
        res = Resume(candidate_id=cand.id, filename="delete_me.pdf", file_type="pdf", sections_json={"Summary": "Experienced Backend Developer"})
        session.add(skill)
        session.add(res)
        await session.commit()

        cand_id = cand.id

        # Verify candidate exists
        db_cand = await session.get(Candidate, cand_id)
        assert db_cand is not None

        # Delete candidate
        await session.delete(db_cand)
        await session.commit()

        # Verify candidate and relations are deleted
        deleted_cand = await session.get(Candidate, cand_id)
        assert deleted_cand is None

        skills_res = await session.execute(select(CandidateSkill).where(CandidateSkill.candidate_id == cand_id))
        assert len(skills_res.scalars().all()) == 0
