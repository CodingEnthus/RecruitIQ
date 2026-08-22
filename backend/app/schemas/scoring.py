from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class SkillEvidenceDetail(BaseModel):
    skill: str
    matched: bool
    evidence_strength: float = Field(..., description="1.0 Strong, 0.7 Medium, 0.3 Weak, 0.0 None")
    evidence_type: str = Field(..., description="experience, project, education, skills_list, not_found")
    evidence_text: str
    source_section: str = Field(..., description="Experience, Projects, Education, Skills, Summary, N/A")
    badge_status: str = Field(..., description="DEMONSTRATED, CLAIMED, NOT_FOUND")
    verified: bool = True

class ComponentAuditDetail(BaseModel):
    name: str
    score: float
    weight_percentage: float
    weighted_points: float
    source_sections: List[str] = Field(default_factory=list)
    evidence_summary: str = ""
    verified_evidence: List[str] = Field(default_factory=list)

class ScoreAuditObject(BaseModel):
    required_skills: ComponentAuditDetail
    semantic_fit: ComponentAuditDetail
    experience: ComponentAuditDetail
    education: ComponentAuditDetail
    projects: ComponentAuditDetail
    evidence_quality: ComponentAuditDetail

class ScoreBreakdownSchema(BaseModel):
    skill_score: float = Field(..., description="Weight: 35%")
    semantic_score: float = Field(..., description="Weight: 25%")
    experience_score: float = Field(..., description="Weight: 15%")
    education_score: float = Field(..., description="Weight: 10%")
    project_score: float = Field(..., description="Weight: 10%")
    evidence_score: float = Field(..., description="Weight: 5%")
    
    # Weighted point contributions
    skill_points: float = 0.0
    semantic_points: float = 0.0
    experience_points: float = 0.0
    education_points: float = 0.0
    project_points: float = 0.0
    evidence_points: float = 0.0

class EvidenceMatch(BaseModel):
    requirement: str
    evidence_text: str
    section: str
    match_status: str  # "matched", "partial", "missing"
    badge_status: Optional[str] = "DEMONSTRATED"
    evidence_strength: Optional[float] = 1.0
    verified: bool = True

class SkillGap(BaseModel):
    matched_skills: List[str] = Field(default_factory=list)
    partially_matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    skill_evidence_details: List[SkillEvidenceDetail] = Field(default_factory=list)

class CandidateScreeningResult(BaseModel):
    candidate_id: str
    candidate_name: str
    anonymized: bool = False
    final_score: float
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    evidence_coverage: float  # Percentage e.g. 94.0
    score_breakdown: ScoreBreakdownSchema
    skill_gap: SkillGap
    matched_evidence: List[EvidenceMatch] = Field(default_factory=list)
    score_audit_object: Optional[ScoreAuditObject] = None
    llm_explanation: str
    recommended_interview_focus: List[str] = Field(default_factory=list)
    has_prompt_injection: bool = False
    injection_warning: Optional[str] = None

class ScreeningRequest(BaseModel):
    job_id: str
    candidate_ids: Optional[List[str]] = None
    anonymize: bool = False

class ScreeningRunResponse(BaseModel):
    job_id: str
    total_screened: int
    rankings: List[CandidateScreeningResult]

class CandidateComparisonRequest(BaseModel):
    candidate_id_a: str
    candidate_id_b: str
    job_id: str

class CandidateComparisonResponse(BaseModel):
    job_title: str
    candidate_a: CandidateScreeningResult
    candidate_b: CandidateScreeningResult
    winner_id: str
    comparison_summary: str
    key_differentiators: List[str]
