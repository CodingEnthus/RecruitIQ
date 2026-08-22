from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.core.database import get_db
from app.models.domain import (
    Job, Candidate, Resume, CandidateSkill, Experience, Education, Project, ScreeningResult, ScoreBreakdown, EvidenceItem, AnalysisRun
)
from app.schemas.candidate import CandidateProfile, ExperienceSchema, EducationSchema, ProjectSchema
from app.schemas.job import JobProfile
from app.schemas.scoring import (
    ScreeningRequest, ScreeningRunResponse, CandidateScreeningResult,
    CandidateComparisonRequest, CandidateComparisonResponse
)
from app.services.vector_store import VectorStoreService
from app.services.hybrid_search import HybridSearchService
from app.services.reranker import RerankerEngine
from app.services.scoring_engine import ScoringEngineService

router = APIRouter(tags=["Screening & Comparison"])
vector_store = VectorStoreService()
hybrid_search = HybridSearchService(vector_store)
reranker = RerankerEngine()

@router.post("/screen", response_model=ScreeningRunResponse)
async def screen_candidates(
    request: ScreeningRequest,
    db: AsyncSession = Depends(get_db)
):
    # Fetch job
    job_res = await db.execute(select(Job).where(Job.id == request.job_id))
    job_db = job_res.scalar_one_or_none()
    if not job_db:
        raise HTTPException(status_code=404, detail="Job description not found")

    job_profile = JobProfile(**job_db.structured_profile)

    # Fetch candidates
    query = select(Candidate)
    if request.candidate_ids:
        query = query.where(Candidate.id.in_(request.candidate_ids))
    
    cand_res = await db.execute(query)
    candidates = cand_res.scalars().all()

    if not candidates:
        raise HTTPException(status_code=400, detail="No candidates available to screen")

    rankings: List[CandidateScreeningResult] = []

    for c in candidates:
        # Load profile
        skills_res = await db.execute(select(CandidateSkill).where(CandidateSkill.candidate_id == c.id))
        skills_list = [s.normalized_skill for s in skills_res.scalars().all()]

        exp_res = await db.execute(select(Experience).where(Experience.candidate_id == c.id))
        exp_list = [ExperienceSchema(
            company=e.company, role=e.role, start_date=e.start_date, end_date=e.end_date,
            duration_months=e.duration_months, responsibilities=e.responsibilities or [],
            technologies=e.technologies or []
        ) for e in exp_res.scalars().all()]

        edu_res = await db.execute(select(Education).where(Education.candidate_id == c.id))
        edu_list = [EducationSchema(
            degree=e.degree, field=e.field, institution=e.institution, graduation_year=e.graduation_year
        ) for e in edu_res.scalars().all()]

        proj_res = await db.execute(select(Project).where(Project.candidate_id == c.id))
        proj_list = [ProjectSchema(
            name=p.name, description=p.description, technologies=p.technologies or []
        ) for p in proj_res.scalars().all()]

        profile = CandidateProfile(
            name=c.name,
            email=c.email,
            phone=c.phone,
            summary=c.summary,
            skills=skills_list,
            normalized_skills=skills_list,
            experience=exp_list,
            education=edu_list,
            projects=proj_list
        )

        # Retrieve evidence chunks across ALL candidate sections
        res_res = await db.execute(select(Resume).where(Resume.candidate_id == c.id))
        resume_db = res_res.scalar_one_or_none()
        sections = resume_db.sections_json if resume_db else {}

        cand_chunks = []
        if sections:
            for sec_name, sec_text in sections.items():
                if sec_text:
                    cand_chunks.append({
                        "candidate_id": c.id,
                        "candidate_name": c.name,
                        "section": sec_name,
                        "text": f"Section: {sec_name}\nCandidate: {c.name}\n{sec_text}"
                    })
        
        # If no sections dict stored, construct synthetic section chunks from structured profile
        if not cand_chunks:
            if profile.summary:
                cand_chunks.append({"candidate_id": c.id, "candidate_name": c.name, "section": "Summary", "text": profile.summary})
            if profile.skills:
                cand_chunks.append({"candidate_id": c.id, "candidate_name": c.name, "section": "Skills", "text": "Skills: " + ", ".join(profile.skills)})
            if profile.experience:
                exp_text = "\n".join([f"Role: {e.role} at {e.company}. Responsibilities: {' '.join(e.responsibilities)}. Tech: {','.join(e.technologies)}" for e in profile.experience])
                cand_chunks.append({"candidate_id": c.id, "candidate_name": c.name, "section": "Experience", "text": exp_text})
            if profile.education:
                edu_text = "\n".join([f"Degree: {e.degree} Field: {e.field} Institution: {e.institution} Year: {e.graduation_year}" for e in profile.education])
                cand_chunks.append({"candidate_id": c.id, "candidate_name": c.name, "section": "Education", "text": edu_text})
            if profile.projects:
                proj_text = "\n".join([f"Project: {p.name}. Description: {p.description}. Tech: {','.join(p.technologies)}" for p in profile.projects])
                cand_chunks.append({"candidate_id": c.id, "candidate_name": c.name, "section": "Projects", "text": proj_text})

        query_str = f"{job_profile.role} {' '.join(job_profile.required_skills)}"
        retrieved = hybrid_search.hybrid_retrieve(query_str, cand_chunks, top_k=15)
        reranked_evidence = reranker.rerank(query_str, retrieved, top_n=10)

        # Merge all chunks into evidence list so NO section is excluded from scoring evaluation
        all_candidate_evidence = cand_chunks + [c for c in reranked_evidence if c not in cand_chunks]

        # Evaluate candidate using deterministic scoring engine
        result = await ScoringEngineService.evaluate_candidate(
            candidate_id=c.id,
            profile=profile,
            job_profile=job_profile,
            retrieved_evidence=all_candidate_evidence,
            has_prompt_injection=c.has_prompt_injection,
            injection_warning=c.injection_warning,
            anonymize=request.anonymize
        )

        rankings.append(result)

        # Save result to DB
        db_screening = ScreeningResult(
            job_id=job_db.id,
            candidate_id=c.id,
            final_score=result.final_score,
            confidence=result.confidence,
            evidence_coverage=result.evidence_coverage,
            anonymized=request.anonymize,
            explanation_json={
                "llm_explanation": result.llm_explanation,
                "interview_focus": result.recommended_interview_focus
            }
        )
        db.add(db_screening)
        await db.flush()

        db.add(ScoreBreakdown(
            screening_result_id=db_screening.id,
            skill_score=result.score_breakdown.skill_score,
            semantic_score=result.score_breakdown.semantic_score,
            experience_score=result.score_breakdown.experience_score,
            education_score=result.score_breakdown.education_score,
            project_score=result.score_breakdown.project_score,
            evidence_score=result.score_breakdown.evidence_score
        ))

        for ev in result.matched_evidence:
            db.add(EvidenceItem(
                screening_result_id=db_screening.id,
                requirement=ev.requirement,
                evidence_text=ev.evidence_text,
                section=ev.section,
                match_status=ev.match_status
            ))

    # Sort candidates by deterministic final score descending
    rankings.sort(key=lambda r: r.final_score, reverse=True)

    # Save Analysis Run record
    avg_score = sum(r.final_score for r in rankings) / float(len(rankings))
    db.add(AnalysisRun(
        job_id=job_db.id,
        candidates_count=len(rankings),
        avg_score=round(avg_score, 1)
    ))
    await db.commit()

    return ScreeningRunResponse(
        job_id=job_db.id,
        total_screened=len(rankings),
        rankings=rankings
    )

@router.post("/candidates/compare", response_model=CandidateComparisonResponse)
async def compare_candidates(
    request: CandidateComparisonRequest,
    db: AsyncSession = Depends(get_db)
):
    # Perform screening on both candidates
    screen_res = await screen_candidates(
        ScreeningRequest(
            job_id=request.job_id,
            candidate_ids=[request.candidate_id_a, request.candidate_id_b]
        ),
        db=db
    )

    if len(screen_res.rankings) < 2:
        raise HTTPException(status_code=400, detail="Could not retrieve screening results for both candidates.")

    cand_map = {r.candidate_id: r for r in screen_res.rankings}
    cand_a = cand_map.get(request.candidate_id_a)
    cand_b = cand_map.get(request.candidate_id_b)

    if not cand_a or not cand_b:
        raise HTTPException(status_code=404, detail="One or both candidates could not be found.")

    # Determine winner based on deterministic score
    winner = cand_a if cand_a.final_score >= cand_b.final_score else cand_b
    loser = cand_b if winner == cand_a else cand_a

    differentiators = []
    if winner.score_breakdown.skill_score > loser.score_breakdown.skill_score:
        diff = round(winner.score_breakdown.skill_score - loser.score_breakdown.skill_score, 1)
        differentiators.append(f"Higher required skill match (+{diff}% higher skill score)")
    if winner.score_breakdown.experience_score > loser.score_breakdown.experience_score:
        diff = round(winner.score_breakdown.experience_score - loser.score_breakdown.experience_score, 1)
        differentiators.append(f"Greater verified experience depth (+{diff}% experience score)")
    if winner.score_breakdown.project_score > loser.score_breakdown.project_score:
        diff = round(winner.score_breakdown.project_score - loser.score_breakdown.project_score, 1)
        differentiators.append(f"Stronger demonstrated project evidence (+{diff}% project score)")
    if winner.evidence_coverage > loser.evidence_coverage:
        differentiators.append(f"Superior evidence coverage ({winner.evidence_coverage}% vs {loser.evidence_coverage}%)")

    summary = (
        f"{winner.candidate_name} ranks higher primarily due to demonstrated technical alignment with job requirements. "
        f"{winner.candidate_name} achieved an overall match score of {winner.final_score}% vs {loser.final_score}% for {loser.candidate_name}. "
        f"Grounding evidence confirms verified skills in {', '.join(winner.skill_gap.matched_skills[:3])}."
    )

    job_res = await db.execute(select(Job).where(Job.id == request.job_id))
    job_db = job_res.scalar_one_or_none()

    return CandidateComparisonResponse(
        job_title=job_db.title if job_db else "Job Role",
        candidate_a=cand_a,
        candidate_b=cand_b,
        winner_id=winner.candidate_id,
        comparison_summary=summary,
        key_differentiators=differentiators
    )
