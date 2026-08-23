from collections import Counter, defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Dict, Any, List, Set

from app.core.database import get_db
from app.models.domain import Candidate, CandidateSkill, ScreeningResult, EvidenceItem, Job

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("")
async def get_recruiter_analytics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    # 1. Total Candidates Count
    cand_res = await db.execute(select(Candidate))
    candidates = cand_res.scalars().all()
    total_candidates = len(candidates)

    # 2. Skill Frequencies across Candidates
    skills_res = await db.execute(select(CandidateSkill))
    skills_db = skills_res.scalars().all()
    
    # Map candidate_id -> set of normalized skills to avoid candidate-level skill duplication
    cand_skills_map: Dict[str, Set[str]] = defaultdict(set)
    for s in skills_db:
        if s.normalized_skill:
            cand_skills_map[s.candidate_id].add(s.normalized_skill)
    
    skill_counts = Counter()
    for s_set in cand_skills_map.values():
        for sk in s_set:
            skill_counts[sk] += 1

    top_candidate_skills = [{"skill": s, "count": c} for s, c in skill_counts.most_common(8)]

    # 3. Screening Results & Latest Screening per Candidate Deduplication
    screen_res = await db.execute(
        select(ScreeningResult)
        .options(selectinload(ScreeningResult.evidence_items))
        .order_by(ScreeningResult.created_at.desc())
    )
    all_screenings = screen_res.scalars().all()
    total_screenings = len(all_screenings)

    # Group by candidate_id to select the LATEST screening result for each candidate
    latest_screenings_map: Dict[str, ScreeningResult] = {}
    for s in all_screenings:
        if s.candidate_id not in latest_screenings_map:
            latest_screenings_map[s.candidate_id] = s

    latest_screenings = list(latest_screenings_map.values())

    # 4. Metrics calculated strictly on the latest screening per candidate
    avg_score = 0.0
    strong_matches = 0
    score_distribution = {"90-100%": 0, "75-89%": 0, "60-74%": 0, "Below 60%": 0}
    missing_cand_map: Dict[str, Set[str]] = defaultdict(set)

    if latest_screenings:
        total_scores = sum(s.final_score for s in latest_screenings)
        avg_score = round(total_scores / float(len(latest_screenings)), 1)

        for s in latest_screenings:
            # Strong matches: final_score >= 85.0
            if s.final_score >= 85.0:
                strong_matches += 1

            # Distribution buckets (85 belongs to 75-89% bucket)
            if s.final_score >= 90.0:
                score_distribution["90-100%"] += 1
            elif s.final_score >= 75.0:
                score_distribution["75-89%"] += 1
            elif s.final_score >= 60.0:
                score_distribution["60-74%"] += 1
            else:
                score_distribution["Below 60%"] += 1

            # Track unique candidate IDs missing each requirement
            if s.evidence_items:
                for ev in s.evidence_items:
                    if ev.match_status == "missing" or ev.evidence_text == "No supporting evidence found for this requirement.":
                        missing_cand_map[ev.requirement].add(s.candidate_id)

    # Missing Skills Aggregation (count = unique candidate IDs missing the skill)
    missing_list = [
        {"skill": req, "count": len(cands)}
        for req, cands in missing_cand_map.items()
        if len(cands) > 0
    ]
    missing_list.sort(key=lambda x: x["count"], reverse=True)
    most_missing_skills = missing_list[:6]

    # 5. Dynamic Demand vs Supply Calculation
    jobs_res = await db.execute(select(Job).order_by(Job.created_at.desc()))
    active_jobs = jobs_res.scalars().all()

    demand_vs_supply = []
    if active_jobs:
        latest_job = active_jobs[0]
        jd_profile = latest_job.structured_profile or {}
        req_skills = jd_profile.get("required_skills", [])
        pref_skills = jd_profile.get("preferred_skills", [])
        all_jd_skills = list(dict.fromkeys(req_skills + pref_skills))

        for sk in all_jd_skills[:6]:
            demand_pct = 100.0 if sk in req_skills else 60.0
            supply_count = sum(1 for c_id, s_set in cand_skills_map.items() if sk in s_set)
            supply_pct = round((supply_count / float(total_candidates)) * 100.0, 1) if total_candidates > 0 else 0.0
            demand_vs_supply.append({
                "skill": sk,
                "demand": int(demand_pct),
                "supply": int(supply_pct)
            })

    return {
        "total_candidates": total_candidates,
        "total_screenings": total_screenings,
        "average_match_score": avg_score,
        "strong_matches": strong_matches,
        "score_distribution": [
            {"range": k, "count": v} for k, v in score_distribution.items()
        ],
        "most_common_candidate_skills": top_candidate_skills,
        "most_missing_skills": most_missing_skills,
        "skill_demand_vs_supply": demand_vs_supply
    }

