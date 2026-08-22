import hashlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.core.database import get_db
from app.models.domain import (
    Candidate, Resume, CandidateSkill, Experience, Education, Project, Certification
)
from app.schemas.candidate import CandidateResponse, ResumeExtractionResponse, CandidateProfile, ExperienceSchema, EducationSchema, ProjectSchema
from app.services.pdf_parser import PDFParserService
from app.services.injection_guard import InjectionGuardService
from app.services.structured_extractor import StructuredExtractorService
from app.services.vector_store import VectorStoreService
from app.services.hybrid_search import HybridSearchService

router = APIRouter(prefix="/candidates", tags=["Candidates"])
vector_store = VectorStoreService()
hybrid_search = HybridSearchService(vector_store)

@router.post("/upload", response_model=ResumeExtractionResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT resumes are supported.")

    file_bytes = await file.read()
    raw_text, sections = PDFParserService.extract_text_from_bytes(file_bytes, file.filename)

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Unable to extract text from uploaded resume.")

    # Deduplication Check by SHA-256 fingerprint or exact candidate email
    text_fingerprint = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    
    # 1. Check if candidate with identical raw resume text already exists
    existing_cand_res = await db.execute(select(Candidate).where(Candidate.raw_resume_text == raw_text))
    existing_candidate = existing_cand_res.scalar_one_or_none()

    if existing_candidate:
        # Candidate already exists - load existing profile and return without creating duplicate!
        res_res = await db.execute(select(Resume).where(Resume.candidate_id == existing_candidate.id))
        resume_db = res_res.scalar_one_or_none()
        
        # Load profile
        skills_res = await db.execute(select(CandidateSkill).where(CandidateSkill.candidate_id == existing_candidate.id))
        skills_list = [s.normalized_skill for s in skills_res.scalars().all()]

        exp_res = await db.execute(select(Experience).where(Experience.candidate_id == existing_candidate.id))
        exp_list = [ExperienceSchema(
            company=e.company, role=e.role, start_date=e.start_date, end_date=e.end_date,
            duration_months=e.duration_months, responsibilities=e.responsibilities or [],
            technologies=e.technologies or []
        ) for e in exp_res.scalars().all()]

        edu_res = await db.execute(select(Education).where(Education.candidate_id == existing_candidate.id))
        edu_list = [EducationSchema(
            degree=e.degree, field=e.field, institution=e.institution, graduation_year=e.graduation_year
        ) for e in edu_res.scalars().all()]

        proj_res = await db.execute(select(Project).where(Project.candidate_id == existing_candidate.id))
        proj_list = [ProjectSchema(
            name=p.name, description=p.description, technologies=p.technologies or []
        ) for p in proj_res.scalars().all()]

        profile = CandidateProfile(
            name=existing_candidate.name,
            email=existing_candidate.email,
            phone=existing_candidate.phone,
            summary=existing_candidate.summary,
            skills=skills_list,
            normalized_skills=skills_list,
            experience=exp_list,
            education=edu_list,
            projects=proj_list
        )

        return ResumeExtractionResponse(
            candidate_id=existing_candidate.id,
            candidate=profile,
            has_prompt_injection=existing_candidate.has_prompt_injection,
            injection_warning=existing_candidate.injection_warning,
            raw_text=raw_text,
            sections=resume_db.sections_json if resume_db else sections
        )

    # 2. Prompt Injection Defense Scan
    has_injection, injection_warning = InjectionGuardService.scan_for_injection(raw_text)

    # 3. Structured Extraction
    profile = await StructuredExtractorService.extract_candidate_profile(raw_text, sections)

    # Check if candidate email already exists
    if profile.email:
        email_cand_res = await db.execute(select(Candidate).where(Candidate.email == profile.email))
        email_candidate = email_cand_res.scalar_one_or_none()
        if email_candidate:
            return ResumeExtractionResponse(
                candidate_id=email_candidate.id,
                candidate=profile,
                has_prompt_injection=email_candidate.has_prompt_injection,
                injection_warning=email_candidate.injection_warning,
                raw_text=raw_text,
                sections=sections
            )

    # 4. Store New Candidate in Database
    db_candidate = Candidate(
        name=profile.name,
        email=profile.email,
        phone=profile.phone,
        summary=profile.summary,
        raw_resume_text=raw_text,
        has_prompt_injection=has_injection,
        injection_warning=injection_warning
    )
    db.add(db_candidate)
    await db.flush()

    # Store Skills
    for skill in profile.normalized_skills:
        db.add(CandidateSkill(
            candidate_id=db_candidate.id,
            raw_skill=skill,
            normalized_skill=skill,
            category="Technical"
        ))

    # Store Experience
    for exp in profile.experience:
        db.add(Experience(
            candidate_id=db_candidate.id,
            company=exp.company,
            role=exp.role,
            start_date=exp.start_date,
            end_date=exp.end_date,
            duration_months=exp.duration_months or 12,
            responsibilities=exp.responsibilities,
            technologies=exp.technologies,
            achievements=exp.achievements
        ))

    # Store Education
    for edu in profile.education:
        db.add(Education(
            candidate_id=db_candidate.id,
            degree=edu.degree,
            field=edu.field,
            institution=edu.institution,
            graduation_year=edu.graduation_year,
            gpa=edu.CGPA_or_percentage
        ))

    # Store Projects
    for proj in profile.projects:
        db.add(Project(
            candidate_id=db_candidate.id,
            name=proj.name,
            description=proj.description,
            technologies=proj.technologies,
            achievements=proj.achievements
        ))

    # Store Resume Metadata
    db_resume = Resume(
        candidate_id=db_candidate.id,
        filename=file.filename,
        file_type="pdf" if file.filename.lower().endswith(".pdf") else "txt",
        sections_json=sections
    )
    db.add(db_resume)
    await db.commit()

    # 5. Chunk & Store Vector Embeddings in Qdrant
    chunks = []
    for sec_name, sec_text in sections.items():
        if sec_text.strip():
            chunks.append({
                "candidate_name": profile.name,
                "section": sec_name,
                "text": f"Section: {sec_name}\nCandidate: {profile.name}\n{sec_text}",
                "technologies": profile.normalized_skills
            })

    if chunks:
        texts = [c["text"] for c in chunks]
        embeddings = hybrid_search.generate_embeddings(texts)
        vector_store.upsert_chunks(db_candidate.id, chunks, embeddings)

    return ResumeExtractionResponse(
        candidate_id=db_candidate.id,
        candidate=profile,
        has_prompt_injection=has_injection,
        injection_warning=injection_warning,
        raw_text=raw_text,
        sections=sections
    )

@router.get("", response_model=List[CandidateResponse])
async def list_candidates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Candidate).order_by(Candidate.created_at.desc()))
    candidates = result.scalars().all()
    
    response = []
    seen_ids = set()
    for c in candidates:
        if c.id in seen_ids:
            continue
        seen_ids.add(c.id)

        skills_res = await db.execute(select(CandidateSkill).where(CandidateSkill.candidate_id == c.id))
        skills_list = [s.normalized_skill for s in skills_res.scalars().all()]
        
        response.append(CandidateResponse(
            id=c.id,
            name=c.name,
            email=c.email,
            phone=c.phone,
            summary=c.summary,
            skills=skills_list,
            normalized_skills=skills_list,
            has_prompt_injection=c.has_prompt_injection,
            injection_warning=c.injection_warning,
            created_at=c.created_at.isoformat()
        ))
    return response

@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")

    skills_res = await db.execute(select(CandidateSkill).where(CandidateSkill.candidate_id == c.id))
    skills_list = [s.normalized_skill for s in skills_res.scalars().all()]

    return CandidateResponse(
        id=c.id,
        name=c.name,
        email=c.email,
        phone=c.phone,
        summary=c.summary,
        skills=skills_list,
        normalized_skills=skills_list,
        has_prompt_injection=c.has_prompt_injection,
        injection_warning=c.injection_warning,
        created_at=c.created_at.isoformat()
    )

@router.delete("/{candidate_id}", status_code=status.HTTP_200_OK)
async def delete_candidate(candidate_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # 1. Purge vector embeddings from Qdrant
    vector_store.delete_candidate_vectors(candidate_id)

    # 2. Delete candidate from DB (ORM cascades to child tables)
    await db.delete(candidate)
    await db.commit()

    return {"message": "Candidate deleted successfully", "id": candidate_id}

@router.delete("", status_code=status.HTTP_200_OK)
async def delete_all_candidates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Candidate))
    candidates = result.scalars().all()

    # 1. Purge all vector embeddings from Qdrant
    vector_store.delete_all_vectors()

    # 2. Delete candidates from DB
    for c in candidates:
        await db.delete(c)
    await db.commit()

    return {"message": "All candidates deleted successfully", "count": len(candidates)}

