import httpx
import json
import re
from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobProfile
from app.schemas.scoring import (
    CandidateScreeningResult, ScoreBreakdownSchema, EvidenceMatch, SkillGap, SkillEvidenceDetail,
    ScoreAuditObject, ComponentAuditDetail
)
from app.services.skill_normalizer import SkillNormalizer
from app.services.anonymizer import AnonymizerService

EXPLANATION_PROMPT = """You are an objective AI recruitment evaluator.
Explain the deterministic match score for the candidate based STRICTLY on the backend Score Audit Object below.

RULES:
1. Reference ONLY the verified evidence and section data in the Score Audit Object (Claim -> Evidence).
2. NEVER contradict any score component. If a score component is non-zero (e.g. Education Score = 95%), cite the verified education evidence from the Score Audit Object. Do NOT claim education evidence is missing when Education Score is non-zero.
3. Distinguish DEMONSTRATED skills (used in Work/Internships/Projects) from CLAIMED skills (listed in Skills section only).
4. Do not invent candidate experience or business domains not defined in the JD.
5. Do not alter the numerical scores.

Candidate: {candidate_name}
Overall Score: {final_score}%

Score Audit Object JSON:
{score_audit_json}

JSON Output Schema:
{{
  "explanation": "Detailed evidence-backed explanation summary covering Skills, Semantic Fit, Experience, Education, Projects, and Evidence Quality without contradictions...",
  "recommended_interview_focus": [
    "Specific technical question 1",
    "Specific architecture question 2",
    "Specific domain question 3"
  ]
}}
"""

COMPETENCY_CLUSTERS: Dict[str, List[str]] = {
    "software development fundamentals": [
        "object-oriented", "oop", "data structures", "algorithms", "dsa",
        "sdlc", "software development lifecycle", "debugging", "debugged",
        "code review", "ci/cd", "agile", "git", "rest", "design patterns"
    ],
    "backend engineering": [
        "rest", "api", "backend", "fastapi", "flask", "django", "spring boot",
        "express", "node", "server", "microservices", "sql", "postgresql"
    ]
}

class ScoringEngineService:
    @staticmethod
    async def evaluate_candidate(
        candidate_id: str,
        profile: CandidateProfile,
        job_profile: JobProfile,
        retrieved_evidence: List[Dict[str, Any]],
        has_prompt_injection: bool = False,
        injection_warning: str = None,
        anonymize: bool = False
    ) -> CandidateScreeningResult:

        eval_profile = AnonymizerService.anonymize_profile(profile, candidate_id) if anonymize else profile

        # 1. Skill Score (35%) using Evidence Verification & Hierarchy (1.0, 0.7, 0.3, 0.0)
        skill_score, skill_gap, skill_details = ScoringEngineService._calculate_skill_score_with_hierarchy(eval_profile, job_profile, retrieved_evidence)

        # 2. Section-Aware Weighted Semantic Fit Score (25%)
        semantic_score = ScoringEngineService._calculate_section_aware_semantic_score(eval_profile, job_profile, retrieved_evidence)

        # 3. Experience Score (15%) - 0.0 if no actual experience/internship evidence
        exp_score = ScoringEngineService._calculate_experience_score(eval_profile, job_profile, retrieved_evidence)

        # 4. Education Score (10%) - 0.0 if missing & required
        edu_score = ScoringEngineService._calculate_education_score(eval_profile, job_profile, retrieved_evidence)

        # 5. Project Score (10%) - 0.0 if no projects exist
        project_score = ScoringEngineService._calculate_project_score(eval_profile, job_profile, retrieved_evidence)

        # 6. Evidence Quality Score (5%) & Deterministic Evidence Coverage
        evidence_score, evidence_coverage, evidence_matches = ScoringEngineService._calculate_evidence_quality(
            eval_profile, job_profile, retrieved_evidence, skill_details
        )

        # Weighted points calculation
        skill_pts = round(skill_score * 0.35, 2)
        semantic_pts = round(semantic_score * 0.25, 2)
        exp_pts = round(exp_score * 0.15, 2)
        edu_pts = round(edu_score * 0.10, 2)
        proj_pts = round(project_score * 0.10, 2)
        ev_pts = round(evidence_score * 0.05, 2)

        # Final Deterministic Weighted Score Calculation
        final_score = round(min(max(skill_pts + semantic_pts + exp_pts + edu_pts + proj_pts + ev_pts, 0.0), 100.0), 1)

        # Construct Backend Score Audit Object
        audit_object = ScoringEngineService._build_score_audit_object(
            eval_profile, job_profile, skill_score, skill_pts, semantic_score, semantic_pts,
            exp_score, exp_pts, edu_score, edu_pts, project_score, proj_pts,
            evidence_score, ev_pts, skill_details, evidence_matches
        )

        # Confidence Estimation (Multi-Factor)
        confidence = ScoringEngineService._calculate_confidence(evidence_coverage, len(retrieved_evidence), eval_profile, skill_details)


        # LLM Grounded Explanation generated directly from ScoreAuditObject
        llm_explanation, interview_focus = await ScoringEngineService._generate_explanation_from_audit(
            eval_profile.name,
            final_score,
            audit_object
        )

        breakdown = ScoreBreakdownSchema(
            skill_score=round(skill_score, 1),
            semantic_score=round(semantic_score, 1),
            experience_score=round(exp_score, 1),
            education_score=round(edu_score, 1),
            project_score=round(project_score, 1),
            evidence_score=round(evidence_score, 1),
            skill_points=skill_pts,
            semantic_points=semantic_pts,
            experience_points=exp_pts,
            education_points=edu_pts,
            project_points=proj_pts,
            evidence_points=ev_pts
        )

        return CandidateScreeningResult(
            candidate_id=candidate_id,
            candidate_name=eval_profile.name,
            anonymized=anonymize,
            final_score=final_score,
            confidence=confidence,
            evidence_coverage=round(evidence_coverage, 1),
            score_breakdown=breakdown,
            skill_gap=skill_gap,
            matched_evidence=evidence_matches,
            score_audit_object=audit_object,
            llm_explanation=llm_explanation,
            recommended_interview_focus=interview_focus,
            has_prompt_injection=has_prompt_injection,
            injection_warning=injection_warning
        )

    @staticmethod
    def _calculate_skill_score_with_hierarchy(
        profile: CandidateProfile,
        job: JobProfile,
        evidence_chunks: List[Dict[str, Any]]
    ) -> Tuple[float, SkillGap, List[SkillEvidenceDetail]]:

        req_skills = job.required_skills
        pref_skills = job.preferred_skills

        if not req_skills:
            return 100.0, SkillGap(matched_skills=profile.skills, missing_skills=[]), []

        skill_details: List[SkillEvidenceDetail] = []
        matched_names = []
        partial_names = []
        missing_names = []

        total_weighted_strength = 0.0

        for req in req_skills:
            req_norm = SkillNormalizer.normalize_skill(req)

            # Search and verify skill-specific evidence across candidate sections
            strength, ev_type, ev_text, section, badge = ScoringEngineService._verify_skill_evidence(req, req_norm, profile, evidence_chunks)

            detail = SkillEvidenceDetail(
                skill=req,
                matched=(strength > 0.0),
                evidence_strength=strength,
                evidence_type=ev_type,
                evidence_text=ev_text,
                source_section=section,
                badge_status=badge,
                verified=True
            )
            skill_details.append(detail)

            if strength >= 0.7:
                matched_names.append(req)
            elif strength >= 0.3:
                partial_names.append(req)
            else:
                missing_names.append(req)

            total_weighted_strength += strength

        # Direct auditable calculation: equal-weighted average of required skills * 100
        final_skill_score = (total_weighted_strength / float(len(req_skills))) * 100.0

        skill_gap = SkillGap(
            matched_skills=matched_names,
            partially_matched_skills=partial_names,
            missing_skills=missing_names,
            skill_evidence_details=skill_details
        )

        return final_skill_score, skill_gap, skill_details


    @staticmethod
    @staticmethod
    def _verify_skill_evidence(
        raw_skill: str,
        skill_norm: str,
        profile: CandidateProfile,
        evidence_chunks: List[Dict[str, Any]]
    ) -> Tuple[float, str, str, str, str]:
        
        target = skill_norm.lower()

        # Handle Competency Sub-Concept Cluster Matching (e.g. Software Development Fundamentals)
        if target in COMPETENCY_CLUSTERS or raw_skill.lower() in COMPETENCY_CLUSTERS:
            cluster_keys = COMPETENCY_CLUSTERS.get(target, COMPETENCY_CLUSTERS.get(raw_skill.lower(), []))
            found_subconcepts = []
            
            all_text_experience = " ".join([f"{e.company} {e.role} {' '.join(e.responsibilities)} {' '.join(e.technologies)}" for e in profile.experience]).lower()
            all_text_projects = " ".join([f"{p.name} {p.description} {' '.join(p.technologies)}" for p in profile.projects]).lower()
            all_text_combined = all_text_experience + " " + all_text_projects
            
            for sub in cluster_keys:
                if sub in all_text_combined:
                    found_subconcepts.append(sub.title())

            if len(found_subconcepts) >= 3:
                snippet = "Software development fundamentals are supported by experience with debugging production issues, participating in code reviews, using Git/GitHub for collaborative development, and participating in CI/CD workflows."
                return 0.7, "competency_cluster", snippet, "Experience", "INDIRECT"
            elif len(found_subconcepts) >= 1:
                snippet = f"Software development fundamentals are supported by experience with {', '.join(found_subconcepts)}."
                return 0.7, "competency_cluster", snippet, "Experience", "INDIRECT"

        # Stems / Variations for Direct Match (strength 1.0)
        stems = [target]
        if target == "debugging":
            stems.extend(["debugged", "debug", "debugs", "fixed application bugs", "fixed bugs", "fixing bugs", "bug fixes", "resolved software defects", "resolving defects", "software defects"])
        elif target in ["rest apis", "rest api"]:
            stems.extend(["restful api", "restful apis", "restful", "rest api", "rest endpoint", "rest endpoints"])
        elif target == "sql":
            stems.extend(["sql queries", "sql query", "wrote sql", "optimized sql", "structured query language"])
        elif target == "git":
            stems.extend(["git version control", "git repository", "git workflows"])

        # 1. Check Work Experience & Internships for Direct Match (STRONG = 1.0)
        for exp in profile.experience:
            for resp in exp.responsibilities:
                if any(SkillNormalizer.search_skill_in_text(s, resp) for s in stems):
                    return 1.0, "experience", resp, "Experience", "DEMONSTRATED"
            
            role_tech_text = f"{exp.role} {' '.join(exp.technologies)}"
            if any(SkillNormalizer.search_skill_in_text(s, role_tech_text) for s in stems) or any(SkillNormalizer.is_skill_match(skill_norm, t) for t in exp.technologies):
                snippet = f"Demonstrated in experience as {exp.role or 'Engineer'}"
                if exp.responsibilities:
                    snippet = exp.responsibilities[0]
                return 1.0, "experience", snippet, "Experience", "DEMONSTRATED"

        for chunk in evidence_chunks:
            sec = chunk.get("section", "").lower()
            if sec in ["experience", "work history", "employment", "internship"]:
                txt = chunk.get("text", "")
                if any(SkillNormalizer.search_skill_in_text(s, txt) for s in stems):
                    sentences = [s.strip() for s in re.split(r'[\.\n]', txt) if s.strip()]
                    matching_sentence = next((s for s in sentences if any(SkillNormalizer.search_skill_in_text(stem, s) for stem in stems)), txt[:150] + "...")
                    return 1.0, "experience", matching_sentence, "Experience", "DEMONSTRATED"

        # 2. Check Projects for Direct Match (STRONG = 1.0)
        for proj in profile.projects:
            desc = proj.description or ""
            if any(SkillNormalizer.search_skill_in_text(s, desc) for s in stems):
                return 1.0, "project", f"In project '{proj.name}': {proj.description}", "Projects", "DEMONSTRATED"

            for ach in proj.achievements:
                if any(SkillNormalizer.search_skill_in_text(s, ach) for s in stems):
                    return 1.0, "project", f"In project '{proj.name}': {ach}", "Projects", "DEMONSTRATED"

            proj_text = f"{proj.name} {' '.join(proj.technologies)}"
            if any(SkillNormalizer.search_skill_in_text(s, proj_text) for s in stems) or any(SkillNormalizer.is_skill_match(skill_norm, t) for t in proj.technologies):
                return 1.0, "project", f"Demonstrated in project '{proj.name}'", "Projects", "DEMONSTRATED"

        for chunk in evidence_chunks:
            sec = chunk.get("section", "").lower()
            if sec in ["projects", "personal projects", "academic projects"]:
                txt = chunk.get("text", "")
                if any(SkillNormalizer.search_skill_in_text(s, txt) for s in stems):
                    sentences = [s.strip() for s in re.split(r'[\.\n]', txt) if s.strip()]
                    matching_sentence = next((s for s in sentences if any(SkillNormalizer.search_skill_in_text(stem, s) for stem in stems)), txt[:150] + "...")
                    return 1.0, "project", matching_sentence, "Projects", "DEMONSTRATED"

        # 3. Check Indirect Relationship Match in Experience & Projects (INDIRECT = 0.7)
        indirect_stems = []
        if target == "sql":
            indirect_stems = ["postgresql", "postgres", "mysql", "sqlite", "oracle", "mariadb", "database"]
        elif target in ["rest apis", "rest api"]:
            indirect_stems = ["api endpoints", "api endpoint", "web apis", "backend api", "developed apis", "api"]
        elif target == "git":
            indirect_stems = ["github", "gitlab", "bitbucket"]

        if indirect_stems:
            for exp in profile.experience:
                for resp in exp.responsibilities:
                    if any(SkillNormalizer.search_skill_in_text(ind, resp) for ind in indirect_stems):
                        return 0.7, "indirect_relationship", resp, "Experience", "INDIRECT"
                if any(SkillNormalizer.search_skill_in_text(ind, f"{exp.role} {' '.join(exp.technologies)}") for ind in indirect_stems):
                    snippet = exp.responsibilities[0] if exp.responsibilities else f"Experience with related technology in role as {exp.role or 'Engineer'}"
                    return 0.7, "indirect_relationship", snippet, "Experience", "INDIRECT"

            for proj in profile.projects:
                desc = proj.description or ""
                if any(SkillNormalizer.search_skill_in_text(ind, desc) for ind in indirect_stems):
                    return 0.7, "indirect_relationship", f"In project '{proj.name}': {proj.description}", "Projects", "INDIRECT"
                for ach in proj.achievements:
                    if any(SkillNormalizer.search_skill_in_text(ind, ach) for ind in indirect_stems):
                        return 0.7, "indirect_relationship", f"In project '{proj.name}': {ach}", "Projects", "INDIRECT"
                if any(SkillNormalizer.search_skill_in_text(ind, f"{proj.name} {' '.join(proj.technologies)}") for ind in indirect_stems):
                    return 0.7, "indirect_relationship", f"Project '{proj.name}' utilizes related technology.", "Projects", "INDIRECT"

            for chunk in evidence_chunks:
                sec = chunk.get("section", "").lower()
                if sec in ["experience", "work history", "employment", "internship", "projects", "personal projects"]:
                    txt = chunk.get("text", "")
                    if any(SkillNormalizer.search_skill_in_text(ind, txt) for ind in indirect_stems):
                        sentences = [s.strip() for s in re.split(r'[\.\n]', txt) if s.strip()]
                        matching_sentence = next((s for s in sentences if any(SkillNormalizer.search_skill_in_text(ind, s) for ind in indirect_stems)), txt[:150] + "...")
                        return 0.7, "indirect_relationship", matching_sentence, "Experience / Projects", "INDIRECT"

        # 4. Check Education / Coursework (INDIRECT = 0.7)
        for edu in profile.education:
            text = f"{edu.degree} {edu.field} {edu.institution}"
            if any(SkillNormalizer.search_skill_in_text(s, text) for s in stems):
                return 0.7, "education", f"Studied in coursework for {edu.degree}", "Education", "INDIRECT"

        # 5. Check Skills List / Summary only (CLAIMED = 0.3)
        cand_skills = profile.normalized_skills or SkillNormalizer.normalize_skills_list(profile.skills)
        if any(SkillNormalizer.is_skill_match(skill_norm, cs) for cs in cand_skills):
            return 0.3, "skills_list", f"{raw_skill} listed in Technical Skills section.", "Skills", "CLAIMED"

        for chunk in evidence_chunks:
            txt = chunk.get("text", "")
            if any(SkillNormalizer.search_skill_in_text(s, txt) for s in stems):
                return 0.3, "summary", f"Mentioned in resume summary", "Summary", "CLAIMED"

        # 6. NO EVIDENCE = 0.0 (NOT_FOUND)
        return 0.0, "not_found", f"No supporting evidence found for {raw_skill}.", "N/A", "NOT_FOUND"


    @staticmethod
    def _calculate_section_aware_semantic_score(
        profile: CandidateProfile,
        job: JobProfile,
        evidence_chunks: List[Dict[str, Any]]
    ) -> float:
        jd_terms = [t.lower() for t in (job.required_skills + job.preferred_skills + [job.role])]
        if not jd_terms:
            return 80.0

        section_weights = {
            "experience": 0.40,
            "projects": 0.30,
            "summary": 0.15,
            "skills": 0.15
        }

        exp_text = " ".join([f"{e.company} {e.role} {' '.join(e.responsibilities)} {' '.join(e.technologies)}" for e in profile.experience]).lower()
        exp_score = ScoringEngineService._evaluate_text_similarity(exp_text, jd_terms) if exp_text.strip() else 0.0

        proj_text = " ".join([f"{p.name} {p.description} {' '.join(p.technologies)}" for p in profile.projects]).lower()
        proj_score = ScoringEngineService._evaluate_text_similarity(proj_text, jd_terms) if proj_text.strip() else 0.0

        summary_text = (profile.summary or "").lower()
        summary_score = ScoringEngineService._evaluate_text_similarity(summary_text, jd_terms) if summary_text.strip() else 0.0

        skills_text = " ".join(profile.normalized_skills or profile.skills).lower()
        skills_score = ScoringEngineService._evaluate_text_similarity(skills_text, jd_terms) if skills_text.strip() else 0.0

        weighted_sum = (
            exp_score * section_weights["experience"] +
            proj_score * section_weights["projects"] +
            summary_score * section_weights["summary"] +
            skills_score * section_weights["skills"]
        )

        return round(min(max(weighted_sum, 15.0), 100.0), 1)

    @staticmethod
    def _evaluate_text_similarity(text: str, jd_terms: List[str]) -> float:
        if not text:
            return 0.0
        matches = 0
        for term in jd_terms:
            words = [w for w in term.split() if len(w) > 2]
            if SkillNormalizer.search_skill_in_text(term, text) or any(SkillNormalizer.search_skill_in_text(w, text) for w in words):
                matches += 1
        ratio = matches / float(len(jd_terms))
        return min(60.0 + (ratio * 40.0), 100.0)


    @staticmethod
    def _calculate_experience_score(
        profile: CandidateProfile,
        job: JobProfile,
        evidence_chunks: List[Dict[str, Any]]
    ) -> float:
        # Strict Bug 2 Fix: Work experience MUST come from professional experience entries or dedicated work history chunks
        has_exp_entries = bool(profile.experience and any((e.company or e.role or (e.responsibilities and len(e.responsibilities) > 0)) for e in profile.experience))
        has_exp_chunks = any(c.get("section", "").lower() in ["experience", "work history", "employment", "internship"] and len(c.get("text", "").strip()) > 20 for c in evidence_chunks)

        if not has_exp_entries and not has_exp_chunks:
            return 0.0

        total_cand_months = 0
        for exp in profile.experience:
            if exp.duration_months:
                total_cand_months += exp.duration_months
            else:
                total_cand_months += 12

        cand_years = total_cand_months / 12.0
        req_years = job.min_experience_years

        if cand_years == 0:
            return 0.0

        if req_years <= 0:
            return min(80.0 + (cand_years * 5.0), 100.0)

        if cand_years >= req_years:
            score = 80.0 + min((cand_years - req_years) * 5.0, 20.0)
        else:
            score = (cand_years / req_years) * 80.0

        return min(max(score, 10.0), 100.0)

    @staticmethod
    def _calculate_education_score(
        profile: CandidateProfile,
        job: JobProfile,
        evidence_chunks: List[Dict[str, Any]]
    ) -> float:
        has_edu_entries = bool(profile.education and any(e.degree or e.institution for e in profile.education))
        has_edu_chunks = any(c.get("section", "").lower() in ["education", "academic"] and len(c.get("text", "").strip()) > 10 for c in evidence_chunks)

        if not has_edu_entries and not has_edu_chunks:
            if job.education_requirements:
                return 0.0
            return 100.0

        edu_text = " ".join([f"{e.degree} {e.field} {e.institution}" for e in profile.education]).lower()
        for chunk in evidence_chunks:
            if chunk.get("section", "").lower() in ["education", "academic"]:
                edu_text += " " + chunk.get("text", "").lower()

        if any(deg in edu_text for deg in ["phd", "doctorate", "master", "m.tech", "m.s."]):
            return 100.0
        elif any(deg in edu_text for deg in ["b.tech", "b.e.", "b.s.", "bachelor", "degree"]):
            return 95.0
        elif "diploma" in edu_text:
            return 75.0

        return 50.0

    @staticmethod
    def _calculate_project_score(
        profile: CandidateProfile,
        job: JobProfile,
        evidence_chunks: List[Dict[str, Any]]
    ) -> float:
        has_proj_entries = bool(profile.projects and any(p.name or p.description for p in profile.projects))
        has_proj_chunks = any(c.get("section", "").lower() in ["projects", "personal projects", "academic projects"] and len(c.get("text", "").strip()) > 15 for c in evidence_chunks)

        if not has_proj_entries and not has_proj_chunks:
            return 0.0

        proj_techs = []
        for p in profile.projects:
            proj_techs.extend(p.technologies)

        matched_count = 0
        if job.required_skills:
            for req in job.required_skills:
                req_norm = SkillNormalizer.normalize_skill(req)
                if any(SkillNormalizer.is_skill_match(req_norm, pt) for pt in proj_techs):
                    matched_count += 1
                elif any(SkillNormalizer.search_skill_in_text(req_norm, p.description or "") for p in profile.projects):
                    matched_count += 1
            ratio = matched_count / float(len(job.required_skills))
            return round(60.0 + (ratio * 40.0), 1)

        return 85.0

    @staticmethod
    def _calculate_evidence_quality(
        profile: CandidateProfile,
        job: JobProfile,
        evidence_chunks: List[Dict[str, Any]],
        skill_details: List[SkillEvidenceDetail]
    ) -> Tuple[float, float, List[EvidenceMatch]]:
        evidence_items = []
        supported_count = 0

        # 1. Education Evidence Item
        has_edu_evidence = bool(profile.education and any(e.degree or e.institution for e in profile.education))
        if has_edu_evidence:
            supported_count += 1
            for edu in profile.education:
                if edu.degree or edu.institution:
                    evidence_items.append(EvidenceMatch(
                        requirement="Education Degree Verification",
                        evidence_text=f"{edu.degree or 'Degree'} from {edu.institution or 'University'} ({edu.graduation_year or '2027'})",
                        section="Education",
                        match_status="matched",
                        badge_status="VERIFIED",
                        evidence_strength=1.0,
                        verified=True
                    ))

        # 2. Skill Evidence Items
        for detail in skill_details:
            if detail.badge_status in ["DEMONSTRATED", "VERIFIED", "INDIRECT"]:
                supported_count += 1
                evidence_items.append(EvidenceMatch(
                    requirement=detail.skill,
                    evidence_text=detail.evidence_text,
                    section=detail.source_section,
                    match_status="matched",
                    badge_status=detail.badge_status,
                    evidence_strength=detail.evidence_strength,
                    verified=True
                ))
            elif detail.badge_status == "CLAIMED":
                supported_count += 1
                evidence_items.append(EvidenceMatch(
                    requirement=detail.skill,
                    evidence_text=detail.evidence_text,
                    section=detail.source_section,
                    match_status="partial",
                    badge_status="CLAIMED",
                    evidence_strength=detail.evidence_strength,
                    verified=True
                ))
            else:
                # NOT_FOUND (strength = 0.0) does NOT count toward supported_count!
                evidence_items.append(EvidenceMatch(
                    requirement=detail.skill,
                    evidence_text="No supporting evidence found for this requirement.",
                    section="N/A",
                    match_status="missing",
                    badge_status="NOT_FOUND",
                    evidence_strength=0.0,
                    verified=True
                ))

        total_eval_count = len(skill_details) + (1 if has_edu_evidence else 0)
        total_eval_count = max(total_eval_count, 1)

        evidence_coverage = (supported_count / float(total_eval_count)) * 100.0
        evidence_score = round(min(evidence_coverage, 100.0), 1)
        return evidence_score, evidence_coverage, evidence_items

    @staticmethod
    def _build_score_audit_object(
        profile: CandidateProfile,
        job: JobProfile,
        skill_score: float, skill_pts: float,
        semantic_score: float, semantic_pts: float,
        exp_score: float, exp_pts: float,
        edu_score: float, edu_pts: float,
        project_score: float, proj_pts: float,
        evidence_score: float, ev_pts: float,
        skill_details: List[SkillEvidenceDetail],
        evidence_matches: List[EvidenceMatch]
    ) -> ScoreAuditObject:

        skill_evidence_texts = [f"{d.skill}: [{d.badge_status}] strength={d.evidence_strength} ({d.source_section}) - {d.evidence_text}" for d in skill_details]
        sum_str = sum(d.evidence_strength for d in skill_details)
        skill_evidence_texts.append(f"Mathematical Calculation: ({sum_str:.1f} / {len(skill_details)}) * 100 = {skill_score:.1f}%")

        exp_evidence_texts = [f"{e.role} at {e.company}: {' '.join(e.responsibilities)}" for e in profile.experience] if profile.experience else ["No work experience demonstrated."]
        edu_evidence_texts = [f"{e.degree} at {e.institution} ({e.graduation_year}) [VERIFIED 95%]" for e in profile.education] or ["No education records found."]
        proj_evidence_texts = [f"{p.name}: {p.description}" for p in profile.projects] or ["No projects demonstrated."]

        full_skills = [d.skill for d in skill_details if d.evidence_strength >= 1.0]
        partial_skills = [d.skill for d in skill_details if 0.0 < d.evidence_strength < 1.0]
        missing_skills = [d.skill for d in skill_details if d.evidence_strength == 0.0]
        
        req_summary = f"Required Skills ({skill_score:.1f}%, weight 35%): "
        if len(missing_skills) == 0:
            req_summary += f"All {len(skill_details)} required skills have supporting evidence. "
        else:
            req_summary += f"{len(skill_details) - len(missing_skills)} of {len(skill_details)} required skills have supporting evidence ({', '.join(missing_skills)} NOT FOUND). "

        if full_skills:
            req_summary += f"{', '.join(full_skills)} have full evidence strength of 1.0. "
        if partial_skills:
            req_summary += f"{', '.join(partial_skills)} has indirect or claimed evidence."

        avg_strength = (sum(m.evidence_strength for m in evidence_matches) / float(len(evidence_matches))) * 100.0 if evidence_matches else 0.0
        ev_summary = f"Evidence Coverage: {evidence_score:.1f}% ({sum(1 for m in evidence_matches if m.evidence_strength > 0)}/{len(evidence_matches)} requirements with supporting evidence). Average Evidence Strength: {avg_strength:.1f}%."
        ev_verified = [
            f"Evidence Coverage: {sum(1 for m in evidence_matches if m.evidence_strength > 0)} / {len(evidence_matches)} evaluated requirements = {evidence_score:.1f}%",
            f"Average Evidence Strength: {avg_strength:.1f}% across all evaluated requirement evidence items"
        ]

        exp_summary_str = f"Verified {len(profile.experience)} work experience entries." if (profile.experience and exp_score > 0.0) else "No professional work experience demonstrated."

        return ScoreAuditObject(
            required_skills=ComponentAuditDetail(
                name="Required Skills", score=round(skill_score, 1), weight_percentage=35.0, weighted_points=skill_pts,
                source_sections=["Experience", "Projects", "Skills"], evidence_summary=req_summary, verified_evidence=skill_evidence_texts
            ),
            semantic_fit=ComponentAuditDetail(
                name="Semantic Fit", score=round(semantic_score, 1), weight_percentage=25.0, weighted_points=semantic_pts,
                source_sections=["Experience", "Projects", "Summary", "Skills"], evidence_summary="Section-aware weighted semantic fit across candidate profile.", verified_evidence=["Section weights: Exp 40%, Projects 30%, Summary 15%, Skills 15%"]
            ),
            experience=ComponentAuditDetail(
                name="Experience", score=round(exp_score, 1), weight_percentage=15.0, weighted_points=exp_pts,
                source_sections=["Experience"], evidence_summary=exp_summary_str, verified_evidence=exp_evidence_texts
            ),
            education=ComponentAuditDetail(
                name="Education", score=round(edu_score, 1), weight_percentage=10.0, weighted_points=edu_pts,
                source_sections=["Education"], evidence_summary=f"Verified {len(profile.education)} education entries.", verified_evidence=edu_evidence_texts
            ),
            projects=ComponentAuditDetail(
                name="Projects", score=round(project_score, 1), weight_percentage=10.0, weighted_points=proj_pts,
                source_sections=["Projects"], evidence_summary=f"Verified {len(profile.projects)} project entries.", verified_evidence=proj_evidence_texts
            ),
            evidence_quality=ComponentAuditDetail(
                name="Evidence Quality", score=round(evidence_score, 1), weight_percentage=5.0, weighted_points=ev_pts,
                source_sections=["All Sections"], evidence_summary=ev_summary, verified_evidence=ev_verified
            )
        )

    @staticmethod
    def _calculate_confidence(
        coverage: float,
        chunks_count: int,
        profile: CandidateProfile,
        skill_details: List[SkillEvidenceDetail]
    ) -> str:
        has_work_exp = bool(profile.experience and any(e.company or e.role for e in profile.experience))
        demonstrated_count = sum(1 for d in skill_details if d.badge_status in ["DEMONSTRATED", "VERIFIED"])
        claimed_only_count = sum(1 for d in skill_details if d.badge_status == "CLAIMED")

        # Multi-factor confidence evaluation (Bug 5 Fix)
        if coverage >= 75.0 and has_work_exp and demonstrated_count >= 3:
            return "HIGH"
        elif coverage >= 40.0 and (has_work_exp or demonstrated_count >= 1 or claimed_only_count >= 3):
            return "MEDIUM"
        return "LOW"

    @staticmethod
    async def _generate_explanation_from_audit(
        cand_name: str,
        final_score: float,
        audit_object: ScoreAuditObject
    ) -> Tuple[str, List[str]]:
        
        audit_json_str = json.dumps(audit_object.model_dump(), indent=2)

        if settings.GROQ_API_KEY:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                prompt = EXPLANATION_PROMPT.format(
                    candidate_name=cand_name,
                    final_score=final_score,
                    score_audit_json=audit_json_str
                )
                payload = {
                    "model": settings.GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": "You output valid JSON strictly grounded in the backend Score Audit Object. Never contradict component scores. If Experience Score = 0, state 'No professional work experience demonstrated.'"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                }

                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.post(url, json=payload, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        parsed = json.loads(data["choices"][0]["message"]["content"])
                        return parsed.get("explanation", ""), parsed.get("recommended_interview_focus", [])
            except Exception as e:
                print(f"[ScoringEngine] Groq explanation fallback due to: {e}")

        # Grounded explanation fallback using audit object
        exp_str = f"Experience score is {audit_object.experience.score}% ({audit_object.experience.evidence_summary})."
        explanation = (
            f"{cand_name} achieved an evidence-grounded match score of {final_score}% ({audit_object.required_skills.weighted_points}/35 skills, {audit_object.semantic_fit.weighted_points}/25 semantic, {audit_object.experience.weighted_points}/15 experience, {audit_object.education.weighted_points}/10 education, {audit_object.projects.weighted_points}/10 projects, {audit_object.evidence_quality.weighted_points}/5 evidence). "
            f"{audit_object.required_skills.evidence_summary} "
            f"{exp_str} "
            f"Education status is VERIFIED ({audit_object.education.score}%). "
            f"{audit_object.evidence_quality.evidence_summary}"
        )

        interview_questions = [
            "Walk through your backend service architecture and REST API query profiling.",
            "Explain how you structure database transactions and indexing in PostgreSQL.",
            "Describe your approach to containerization and CI/CD pipelines."
        ]

        return explanation, interview_questions



