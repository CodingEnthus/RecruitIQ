from pydantic import BaseModel, Field
from typing import List, Optional

class Citation(BaseModel):
    candidate_id: str
    candidate_name: str
    section: str
    excerpt: str

class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str
    citations: Optional[List[Citation]] = None

class ChatRequest(BaseModel):
    job_id: Optional[str] = None
    query: str
    history: List[ChatMessage] = Field(default_factory=list)

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    retrieved_chunks_count: int = 0
