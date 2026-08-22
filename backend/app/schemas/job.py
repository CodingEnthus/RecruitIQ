from pydantic import BaseModel, Field
from typing import List, Optional

class JobProfile(BaseModel):
    role: str = ""
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    experience_requirements: List[str] = Field(default_factory=list)
    min_experience_years: float = 0.0
    education_requirements: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    domain: Optional[str] = "General Tech"
    keywords: List[str] = Field(default_factory=list)

class JobCreateRequest(BaseModel):
    title: str
    raw_text: str
    domain: Optional[str] = None

class JobResponse(BaseModel):
    id: str
    title: str
    domain: Optional[str] = ""
    raw_text: str
    structured_profile: JobProfile
    created_at: str
