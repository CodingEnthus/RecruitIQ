import httpx
import json
from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.schemas.rag import ChatMessage, ChatResponse, Citation
from app.services.hybrid_search import HybridSearchService
from app.services.reranker import RerankerEngine

RECRUITER_RAG_PROMPT = """You are RecruitIQ RAG Assistant, an expert AI recruitment intelligence co-pilot.
Answer the recruiter's query based STRICTLY on the retrieved candidate evidence provided below.

RULES:
1. Base your answer ONLY on the provided retrieved context.
2. Provide direct, objective comparisons and evidence citations referencing candidate names and sections.
3. If information is missing or not present in the candidate database, explicitly state: "Information not found in the candidate database."
4. Never invent experience, skills, or candidate facts.

User Query:
{query}

Retrieved Candidate Evidence Context:
{context}

Format your output into a JSON object matching this schema:
{{
  "answer": "Clear, grounded answer with candidate citations...",
  "citations": [
    {{
      "candidate_id": "id",
      "candidate_name": "Candidate Name",
      "section": "experience",
      "excerpt": "Specific evidence excerpt"
    }}
  ]
}}
"""

class RAGAssistantService:
    def __init__(self, hybrid_search: HybridSearchService, reranker: RerankerEngine):
        self.hybrid_search = hybrid_search
        self.reranker = reranker

    async def answer_recruiter_query(
        self,
        query: str,
        all_candidate_chunks: List[Dict[str, Any]],
        history: List[ChatMessage] = None
    ) -> ChatResponse:
        
        if not all_candidate_chunks:
            return ChatResponse(
                answer="No candidate resumes have been uploaded yet. Please upload candidate resumes to enable RAG assistance.",
                citations=[],
                retrieved_chunks_count=0
            )

        # 1. Hybrid retrieval (Dense + Sparse BM25 + RRF)
        retrieved = self.hybrid_search.hybrid_retrieve(query, all_candidate_chunks, top_k=15)

        # 2. Transformer reranking
        reranked_chunks = self.reranker.rerank(query, retrieved, top_n=6)

        # Build context string and citations
        context_parts = []
        citations_list = []

        for chunk in reranked_chunks:
            c_name = chunk.get("candidate_name", "Candidate")
            c_id = chunk.get("candidate_id", "")
            sec = chunk.get("section", "resume")
            text = chunk.get("text", "")
            
            context_parts.append(f"Candidate: {c_name} (ID: {c_id})\nSection: {sec}\nContent: {text}\n---")
            citations_list.append(Citation(
                candidate_id=c_id,
                candidate_name=c_name,
                section=sec,
                excerpt=text[:160] + "..." if len(text) > 160 else text
            ))

        context_str = "\n\n".join(context_parts)

        # 3. LLM synthesis with evidence grounding
        if settings.GROQ_API_KEY:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                prompt = RECRUITER_RAG_PROMPT.format(query=query, context=context_str)
                payload = {
                    "model": settings.GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": "You output valid JSON grounded strictly in the provided evidence."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                }

                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.post(url, json=payload, headers=headers)
                    if res.status_code == 200:
                        parsed = json.loads(res.json()["choices"][0]["message"]["content"])
                        return ChatResponse(
                            answer=parsed.get("answer", ""),
                            citations=citations_list,
                            retrieved_chunks_count=len(reranked_chunks)
                        )
            except Exception as e:
                print(f"[RAGAssistant] Groq RAG fallback due to: {e}")

        # Deterministic Grounded RAG Fallback
        summary_answer = f"Based on the retrieved evidence across candidate resumes for your query '{query}':\n\n"
        for chunk in reranked_chunks[:4]:
            summary_answer += f"• **{chunk.get('candidate_name')}** ({chunk.get('section')}): \"{chunk.get('text')[:180]}...\"\n\n"

        return ChatResponse(
            answer=summary_answer,
            citations=citations_list,
            retrieved_chunks_count=len(reranked_chunks)
        )
