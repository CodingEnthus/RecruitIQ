from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any

class ExperienceSchema(BaseModel):
    company: Optional[str] = ""
    role: Optional[str] = ""
    start_date: Optional[str] = ""
    end_date: Optional[str] = ""
    duration: Optional[str] = ""
    duration_months: Optional[int] = 0
    responsibilities: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)

class EducationSchema(BaseModel):
    degree: Optional[str] = ""
    field: Optional[str] = ""
    institution: Optional[str] = ""
    graduation_year: Optional[str] = ""
    CGPA_or_percentage: Optional[str] = ""

class ProjectSchema(BaseModel):
    name: str = ""
    description: Optional[str] = ""
    technologies: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)

class CertificationSchema(BaseModel):
    name: str = ""
    issuer: Optional[str] = ""
    year: Optional[str] = ""

class CandidateProfile(BaseModel):
    name: str = "Unknown Candidate"
    email: Optional[str] = ""
    phone: Optional[str] = ""
    summary: Optional[str] = ""
    skills: List[str] = Field(default_factory=list)
    normalized_skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceSchema] = Field(default_factory=list)
    education: List[EducationSchema] = Field(default_factory=list)
    projects: List[ProjectSchema] = Field(default_factory=list)
    certifications: List[CertificationSchema] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)

class ResumeExtractionResponse(BaseModel):
    candidate_id: str
    candidate: CandidateProfile
    has_prompt_injection: bool = False
    injection_warning: Optional[str] = None
    raw_text: str
    sections: Dict[str, str] = Field(default_factory=dict)

class CandidateResponse(BaseModel):
    id: str
    name: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    summary: Optional[str] = ""
    skills: List[str] = Field(default_factory=list)
    normalized_skills: List[str] = Field(default_factory=list)
    has_prompt_injection: bool = False
    injection_warning: Optional[str] = None
    created_at: str
    experience: List[ExperienceSchema] = Field(default_factory=list)
    education: List[EducationSchema] = Field(default_factory=list)
    projects: List[ProjectSchema] = Field(default_factory=list)
    certifications: List[CertificationSchema] = Field(default_factory=list)
