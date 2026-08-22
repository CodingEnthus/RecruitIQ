import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.core.database import get_db
from app.models.domain import Job
from app.schemas.job import JobCreateRequest, JobResponse, JobProfile
from app.services.job_analyzer import JobAnalyzerService

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/analyze", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_and_analyze_job(
    request: JobCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    structured_profile = await JobAnalyzerService.analyze_job_description(request.raw_text, request.title)
    
    new_job = Job(
        title=request.title,
        raw_text=request.raw_text,
        domain=request.domain or structured_profile.domain,
        structured_profile=structured_profile.model_dump()
    )
    
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)
    
    return JobResponse(
        id=new_job.id,
        title=new_job.title,
        domain=new_job.domain,
        raw_text=new_job.raw_text,
        structured_profile=JobProfile(**new_job.structured_profile),
        created_at=new_job.created_at.isoformat()
    )

@router.get("", response_model=List[JobResponse])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).order_by(Job.created_at.desc()))
    jobs = result.scalars().all()
    
    responses = []
    for j in jobs:
        responses.append(JobResponse(
            id=j.id,
            title=j.title,
            domain=j.domain,
            raw_text=j.raw_text,
            structured_profile=JobProfile(**j.structured_profile),
            created_at=j.created_at.isoformat()
        ))
    return responses

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    j = result.scalar_one_or_none()
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return JobResponse(
        id=j.id,
        title=j.title,
        domain=j.domain,
        raw_text=j.raw_text,
        structured_profile=JobProfile(**j.structured_profile),
        created_at=j.created_at.isoformat()
    )
