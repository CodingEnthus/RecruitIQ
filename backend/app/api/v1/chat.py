from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any

from app.core.database import get_db
from app.models.domain import Candidate, Resume
from app.schemas.rag import ChatRequest, ChatResponse
from app.services.vector_store import VectorStoreService
from app.services.hybrid_search import HybridSearchService
from app.services.reranker import RerankerEngine
from app.services.rag_assistant import RAGAssistantService

router = APIRouter(prefix="/chat", tags=["Recruiter RAG Chat"])
vector_store = VectorStoreService()
hybrid_search = HybridSearchService(vector_store)
reranker = RerankerEngine()
rag_assistant = RAGAssistantService(hybrid_search, reranker)

@router.post("", response_model=ChatResponse)
async def recruiter_rag_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    # Fetch all candidate chunks
    cands_res = await db.execute(select(Candidate))
    candidates = cands_res.scalars().all()

    all_chunks: List[Dict[str, Any]] = []

    for c in candidates:
        res_res = await db.execute(select(Resume).where(Resume.candidate_id == c.id))
        resume_db = res_res.scalar_one_or_none()
        sections = resume_db.sections_json if resume_db else {}

        for sec_name, sec_text in sections.items():
            if sec_text:
                all_chunks.append({
                    "candidate_id": c.id,
                    "candidate_name": c.name,
                    "section": sec_name,
                    "text": sec_text
                })

    response = await rag_assistant.answer_recruiter_query(
        query=request.query,
        all_candidate_chunks=all_chunks,
        history=request.history
    )

    return response
