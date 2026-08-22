import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    raw_text = Column(Text, nullable=False)
    domain = Column(String(100), nullable=True)
    structured_profile = Column(JSON, nullable=False)  # JobProfile dict
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    screening_results = relationship("ScreeningResult", back_populates="job", cascade="all, delete-orphan")

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    summary = Column(Text, nullable=True)
    raw_resume_text = Column(Text, nullable=False)
    has_prompt_injection = Column(Boolean, default=False)
    injection_warning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="candidate", cascade="all, delete-orphan")
    education = relationship("Education", back_populates="candidate", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="candidate", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="candidate", cascade="all, delete-orphan")
    screening_results = relationship("ScreeningResult", back_populates="candidate", cascade="all, delete-orphan")

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, txt
    sections_json = Column(JSON, nullable=False)     # Parsed sections
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="resumes")

class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id"), nullable=False)
    raw_skill = Column(String(100), nullable=False)
    normalized_skill = Column(String(100), nullable=False)
    category = Column(String(100), nullable=True)

    candidate = relationship("Candidate", back_populates="skills")

class Experience(Base):
    __tablename__ = "experiences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id"), nullable=False)
    company = Column(String(255), nullable=True)
    role = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    duration_months = Column(Integer, default=0)
    responsibilities = Column(JSON, default=list)
    technologies = Column(JSON, default=list)
    achievements = Column(JSON, default=list)

    candidate = relationship("Candidate", back_populates="experiences")

class Education(Base):
    __tablename__ = "education"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id"), nullable=False)
    degree = Column(String(255), nullable=True)
    field = Column(String(255), nullable=True)
    institution = Column(String(255), nullable=True)
    graduation_year = Column(String(50), nullable=True)
    gpa = Column(String(50), nullable=True)

    candidate = relationship("Candidate", back_populates="education")

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    technologies = Column(JSON, default=list)
    achievements = Column(JSON, default=list)

    candidate = relationship("Candidate", back_populates="projects")

class Certification(Base):
    __tablename__ = "certifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id"), nullable=False)
    name = Column(String(255), nullable=False)
    issuer = Column(String(255), nullable=True)
    year = Column(String(50), nullable=True)

    candidate = relationship("Candidate", back_populates="certifications")

class ScreeningResult(Base):
    __tablename__ = "screening_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    candidate_id = Column(String(36), ForeignKey("candidates.id"), nullable=False)
    final_score = Column(Float, nullable=False)
    confidence = Column(String(50), nullable=False)  # HIGH, MEDIUM, LOW
    evidence_coverage = Column(Float, nullable=False)
    anonymized = Column(Boolean, default=False)
    explanation_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="screening_results")
    candidate = relationship("Candidate", back_populates="screening_results")
    score_breakdown = relationship("ScoreBreakdown", back_populates="screening_result", uselist=False, cascade="all, delete-orphan")
    evidence_items = relationship("EvidenceItem", back_populates="screening_result", cascade="all, delete-orphan")

class ScoreBreakdown(Base):
    __tablename__ = "score_breakdowns"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    screening_result_id = Column(String(36), ForeignKey("screening_results.id"), nullable=False)
    skill_score = Column(Float, nullable=False)
    semantic_score = Column(Float, nullable=False)
    experience_score = Column(Float, nullable=False)
    education_score = Column(Float, nullable=False)
    project_score = Column(Float, nullable=False)
    evidence_score = Column(Float, nullable=False)

    screening_result = relationship("ScreeningResult", back_populates="score_breakdown")

class EvidenceItem(Base):
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    screening_result_id = Column(String(36), ForeignKey("screening_results.id"), nullable=False)
    requirement = Column(String(255), nullable=False)
    evidence_text = Column(Text, nullable=False)
    section = Column(String(100), nullable=False)
    match_status = Column(String(50), nullable=False)  # matched, partial, missing

    screening_result = relationship("ScreeningResult", back_populates="evidence_items")

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    candidates_count = Column(Integer, nullable=False)
    avg_score = Column(Float, nullable=False)
    run_timestamp = Column(DateTime, default=datetime.utcnow)
