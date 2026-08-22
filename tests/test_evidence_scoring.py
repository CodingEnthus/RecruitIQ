import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
import asyncio
from app.schemas.candidate import CandidateProfile, ExperienceSchema, EducationSchema, ProjectSchema
from app.schemas.job import JobProfile
from app.services.scoring_engine import ScoringEngineService

@pytest.mark.asyncio
async def test_strong_candidate_high_score():
    # Test A: Strong candidate with work experience, projects, and education
    profile = CandidateProfile(
        name="Test Strong Candidate",
        skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        normalized_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        experience=[ExperienceSchema(
            company="TechCorp",
            role="Backend Engineer Intern",
            responsibilities=["Developed REST APIs using Python and FastAPI.", "Optimized PostgreSQL database queries."],
            technologies=["Python", "FastAPI", "PostgreSQL"],
            duration_months=12
        )],
        projects=[ProjectSchema(
            name="E-Commerce Backend",
            description="Containerized the application using Docker and PostgreSQL.",
            technologies=["Docker", "PostgreSQL"]
        )],
        education=[EducationSchema(
            degree="B.Tech in Computer Science and Engineering",
            institution="Tech University"
        )]
    )

    job = JobProfile(
        role="Backend Engineer",
        required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        min_experience_years=1.0,
        education_requirements=["Bachelor's degree in Computer Science"]
    )

    evidence_chunks = [
        {"section": "Experience", "text": "Developed REST APIs using Python and FastAPI. Optimized PostgreSQL database queries.", "reranker_score": 0.85},
        {"section": "Projects", "text": "Containerized the application using Docker and PostgreSQL.", "reranker_score": 0.85}
    ]

    result = await ScoringEngineService.evaluate_candidate("cand_strong", profile, job, evidence_chunks)

    assert result.final_score >= 75.0
    assert result.score_breakdown.skill_score >= 80.0
    assert result.score_breakdown.experience_score > 0.0
    assert result.score_breakdown.education_score > 0.0
    assert result.score_breakdown.project_score > 0.0

@pytest.mark.asyncio
async def test_keyword_stuffer_lower_score():
    # Test B: Keyword stuffer listing skills without work experience or projects
    profile = CandidateProfile(
        name="Test Keyword Stuffer",
        skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        normalized_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        experience=[],
        projects=[],
        education=[]
    )

    job = JobProfile(
        role="Backend Engineer",
        required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        min_experience_years=1.0,
        education_requirements=["Bachelor's degree in Computer Science"]
    )

    result = await ScoringEngineService.evaluate_candidate("cand_stuffer", profile, job, [])

    # Weak evidence (0.3) for skills list only, 0 experience, 0 education, 0 projects
    assert result.score_breakdown.skill_score <= 35.0
    assert result.score_breakdown.experience_score == 0.0
    assert result.score_breakdown.education_score == 0.0
    assert result.score_breakdown.project_score == 0.0
    assert result.final_score < 40.0

@pytest.mark.asyncio
async def test_missing_experience_zero_score():
    # Test D: Missing experience
    profile = CandidateProfile(
        name="No Experience Candidate",
        skills=["Python"],
        normalized_skills=["Python"],
        experience=[],
        projects=[],
        education=[]
    )
    job = JobProfile(role="Engineer", required_skills=["Python"], min_experience_years=2.0)

    result = await ScoringEngineService.evaluate_candidate("cand_no_exp", profile, job, [])
    assert result.score_breakdown.experience_score == 0.0

@pytest.mark.asyncio
async def test_missing_education_zero_score():
    # Test C: Missing education when required by JD
    profile = CandidateProfile(
        name="No Education Candidate",
        skills=["Python"],
        normalized_skills=["Python"],
        experience=[],
        projects=[],
        education=[]
    )
    job = JobProfile(role="Engineer", required_skills=["Python"], education_requirements=["B.Tech Degree"])

    result = await ScoringEngineService.evaluate_candidate("cand_no_edu", profile, job, [])
    assert result.score_breakdown.education_score == 0.0

@pytest.mark.asyncio
async def test_required_skills_exact_calculation():
    # Verify exact equal-weighted calculation when strengths are [1, 1, 1, 1, 1, 1, 0.7]
    profile = CandidateProfile(
        name="Arjun Audit Test",
        skills=["Python", "Java", "Git", "SQL", "Debugging", "Software Development Fundamentals"],
        normalized_skills=["Python", "Java", "Git", "SQL", "Debugging", "Software Development Fundamentals"],
        experience=[ExperienceSchema(
            company="Tech Solutions",
            role="Software Engineering Intern",
            responsibilities=[
                "Developed RESTful backend APIs using Python and FastAPI.",
                "Worked with PostgreSQL databases and optimized SQL queries.",
                "Used Docker for containerization and Git for version control.",
                "Debugged production issues and participated in code reviews and CI/CD."
            ],
            technologies=["Python", "FastAPI", "Git", "SQL", "PostgreSQL"],
            duration_months=12
        )],
        projects=[ProjectSchema(
            name="Student Management System",
            description="Built a Java Spring Boot backend. Designed REST APIs.",
            technologies=["Java", "REST APIs"]
        )],
        education=[EducationSchema(
            degree="B.Tech in Computer Science and Engineering",
            institution="University",
            graduation_year="2027"
        )]
    )

    job = JobProfile(
        role="Backend Developer",
        required_skills=["Python", "Java", "REST APIs", "Git", "SQL", "Debugging", "Software Development Fundamentals"],
        min_experience_years=1.0,
        education_requirements=["B.Tech in Computer Science"]
    )

    result = await ScoringEngineService.evaluate_candidate("cand_arjun_exact", profile, job, [])

    # Skill strengths: Python=1.0, Java=1.0, REST APIs=1.0, Git=1.0, SQL=1.0, Debugging=1.0, SDF=0.7 -> Sum = 6.7
    # Required skills score = (6.7 / 7) * 100 = 95.7142857% -> 95.7%
    assert round(result.score_breakdown.skill_score, 1) == 95.7
    assert result.score_breakdown.skill_points == 33.5
    assert result.evidence_coverage == 100.0

# -------------------------------------------------------------------------
# ADVERSARIAL REGRESSION TESTS (1 TO 10)
# -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reg_1_java_req_javascript_resume_not_found():
    # Test 1: Java requirement + JavaScript resume -> Java NOT_FOUND
    profile = CandidateProfile(
        name="JS Only Candidate",
        skills=["JavaScript", "HTML5", "CSS3"],
        normalized_skills=["JavaScript", "HTML5", "CSS3"],
        projects=[ProjectSchema(name="Portfolio Website", description="Built using HTML, CSS and JavaScript.", technologies=["JavaScript"])]
    )
    job = JobProfile(role="Backend Developer", required_skills=["Java"])
    result = await ScoringEngineService.evaluate_candidate("c_js", profile, job, [])
    java_detail = next(d for d in result.skill_gap.skill_evidence_details if d.skill == "Java")
    assert java_detail.badge_status == "NOT_FOUND"
    assert java_detail.evidence_strength == 0.0

@pytest.mark.asyncio
async def test_reg_2_java_req_java_resume_valid_match():
    # Test 2: Java requirement + Java resume -> Java valid match
    profile = CandidateProfile(
        name="Java Dev Candidate",
        skills=["Java", "Spring Boot"],
        normalized_skills=["Java", "Spring Boot"],
        projects=[ProjectSchema(name="Java Service", description="Built high scale backend using Java and Spring Boot.", technologies=["Java"])]
    )
    job = JobProfile(role="Backend Developer", required_skills=["Java"])
    result = await ScoringEngineService.evaluate_candidate("c_java", profile, job, [])
    java_detail = next(d for d in result.skill_gap.skill_evidence_details if d.skill == "Java")
    assert java_detail.badge_status in ["DEMONSTRATED", "VERIFIED"]
    assert java_detail.evidence_strength == 1.0

@pytest.mark.asyncio
async def test_reg_3_git_req_github_only_indirect():
    # Test 3: Git requirement + GitHub only -> INDIRECT or CLAIMED, not DEMONSTRATED
    profile = CandidateProfile(
        name="GitHub User Candidate",
        skills=["Python"],
        projects=[ProjectSchema(name="Project A", description="Hosted code on GitHub for collaboration.", technologies=["Python"])]
    )
    job = JobProfile(role="Developer", required_skills=["Git"])
    result = await ScoringEngineService.evaluate_candidate("c_gh", profile, job, [])
    git_detail = next(d for d in result.skill_gap.skill_evidence_details if d.skill == "Git")
    assert git_detail.badge_status in ["INDIRECT", "CLAIMED"]
    assert git_detail.badge_status != "DEMONSTRATED"

@pytest.mark.asyncio
async def test_reg_4_no_experience_section_zero_score():
    # Test 4: No experience section -> Experience = 0
    profile = CandidateProfile(name="No Exp", skills=["Python"], experience=[], projects=[ProjectSchema(name="P", description="Desc")])
    job = JobProfile(role="Dev", required_skills=["Python"], min_experience_years=1.0)
    result = await ScoringEngineService.evaluate_candidate("c_no_exp", profile, job, [])
    assert result.score_breakdown.experience_score == 0.0
    assert result.score_breakdown.experience_points == 0.0

@pytest.mark.asyncio
async def test_reg_5_projects_only_experience_remains_zero():
    # Test 5: Projects only -> Experience remains 0
    profile = CandidateProfile(
        name="Projects Only",
        skills=["Python", "FastAPI"],
        experience=[],
        projects=[
            ProjectSchema(name="Project 1", description="FastAPI Backend"),
            ProjectSchema(name="Project 2", description="Python Scripting")
        ]
    )
    job = JobProfile(role="Dev", required_skills=["Python"], min_experience_years=2.0)
    result = await ScoringEngineService.evaluate_candidate("c_proj_only", profile, job, [])
    assert result.score_breakdown.experience_score == 0.0
    assert result.score_breakdown.project_score > 0.0

@pytest.mark.asyncio
async def test_reg_6_skill_listed_only_in_skills_claimed():
    # Test 6: Skill listed only in Skills -> CLAIMED
    profile = CandidateProfile(name="Skills Only", skills=["Docker"], normalized_skills=["Docker"], experience=[], projects=[])
    job = JobProfile(role="DevOps", required_skills=["Docker"])
    result = await ScoringEngineService.evaluate_candidate("c_skills_only", profile, job, [])
    docker_detail = next(d for d in result.skill_gap.skill_evidence_details if d.skill == "Docker")
    assert docker_detail.badge_status == "CLAIMED"
    assert docker_detail.evidence_strength == 0.3

@pytest.mark.asyncio
async def test_reg_7_no_evidence_not_found():
    # Test 7: No evidence -> NOT_FOUND
    profile = CandidateProfile(name="Empty", skills=["Python"], experience=[], projects=[])
    job = JobProfile(role="Dev", required_skills=["Kubernetes"])
    result = await ScoringEngineService.evaluate_candidate("c_empty", profile, job, [])
    k8s_detail = next(d for d in result.skill_gap.skill_evidence_details if d.skill == "Kubernetes")
    assert k8s_detail.badge_status == "NOT_FOUND"
    assert k8s_detail.evidence_strength == 0.0

@pytest.mark.asyncio
async def test_reg_8_indirect_evidence_status_indirect():
    # Test 8: Indirect evidence -> INDIRECT, not NOT_FOUND
    profile = CandidateProfile(
        name="Subconcept Candidate",
        skills=["Python"],
        projects=[ProjectSchema(name="P", description="Participated in code reviews and CI/CD pipelines.")]
    )
    job = JobProfile(role="Dev", required_skills=["Software Development Fundamentals"])
    result = await ScoringEngineService.evaluate_candidate("c_sdf", profile, job, [])
    sdf_detail = next(d for d in result.skill_gap.skill_evidence_details if d.skill == "Software Development Fundamentals")
    assert sdf_detail.badge_status == "INDIRECT"
    assert sdf_detail.evidence_strength == 0.7

@pytest.mark.asyncio
async def test_reg_9_invalid_evidence_cannot_increase_coverage():
    # Test 9: Invalid evidence cannot increase coverage
    profile = CandidateProfile(name="Fake Java", skills=["JavaScript"], projects=[ProjectSchema(name="JS App", description="JS app")])
    job = JobProfile(role="Java Dev", required_skills=["Java"])
    result = await ScoringEngineService.evaluate_candidate("c_fake_cov", profile, job, [])
    assert result.evidence_coverage == 0.0

@pytest.mark.asyncio
async def test_reg_10_audit_narrative_matches_component_scores():
    # Test 10: Audit narrative must exactly match component scores
    profile = CandidateProfile(name="Audit Check", skills=["Python"], experience=[], projects=[])
    job = JobProfile(role="Dev", required_skills=["Python"])
    result = await ScoringEngineService.evaluate_candidate("c_audit_narrative", profile, job, [])
    b = result.score_breakdown
    expected_pts = round(b.skill_points + b.semantic_points + b.experience_points + b.education_points + b.project_points + b.evidence_points, 1)
    assert result.final_score == expected_pts

@pytest.mark.asyncio
async def test_test2_relationship_aware_evidence_classification():
    # Test 2 Scenario from prompt:
    profile = CandidateProfile(
        name="Test 2 Candidate",
        skills=["Python", "PostgreSQL", "GitHub", "JavaScript", "React", "Docker"],
        normalized_skills=["Python", "PostgreSQL", "GitHub", "JavaScript", "React", "Docker"],
        experience=[
            ExperienceSchema(
                company="Tech Solutions",
                role="Software Engineer",
                responsibilities=[
                    "Built React applications using JavaScript.",
                    "Used PostgreSQL for application data storage.",
                    "Used GitHub for version control.",
                    "Fixed application bugs and improved performance."
                ],
                technologies=["React", "JavaScript", "PostgreSQL", "GitHub"],
                duration_months=12
            )
        ],
        projects=[
            ProjectSchema(
                name="Web App",
                description="Built React and Node.js application. Integrated PostgreSQL database. Developed API endpoints for application data.",
                technologies=["React", "Node.js", "PostgreSQL"]
            )
        ]
    )

    job = JobProfile(
        role="Backend Engineer",
        required_skills=["Java", "SQL", "Git", "REST APIs", "Python", "Debugging", "Software Development Fundamentals"]
    )

    result = await ScoringEngineService.evaluate_candidate("c_test2", profile, job, [])

    details = {d.skill: d for d in result.skill_gap.skill_evidence_details}

    # 1. Java -> NOT_FOUND (strength 0.0)
    assert details["Java"].badge_status == "NOT_FOUND"
    assert details["Java"].evidence_strength == 0.0

    # 2. SQL -> INDIRECT (strength 0.7), quoting PostgreSQL text
    assert details["SQL"].badge_status == "INDIRECT"
    assert details["SQL"].evidence_strength == 0.7
    assert "PostgreSQL" in details["SQL"].evidence_text

    # 3. Git -> INDIRECT (strength 0.7), quoting GitHub text
    assert details["Git"].badge_status == "INDIRECT"
    assert details["Git"].evidence_strength == 0.7
    assert "GitHub" in details["Git"].evidence_text

    # 4. REST APIs -> INDIRECT (strength 0.7), quoting API endpoints text
    assert details["REST APIs"].badge_status == "INDIRECT"
    assert details["REST APIs"].evidence_strength == 0.7
    assert "API endpoints" in details["REST APIs"].evidence_text

    # 5. Debugging -> DEMONSTRATED (strength 1.0), quoting Fixed application bugs
    assert details["Debugging"].badge_status == "DEMONSTRATED"
    assert details["Debugging"].evidence_strength == 1.0
    assert "Fixed application bugs" in details["Debugging"].evidence_text

    # 6. Python -> CLAIMED (strength 0.3)
    assert details["Python"].badge_status == "CLAIMED"
    assert details["Python"].evidence_strength == 0.3

    # 7. Software Development Fundamentals -> INDIRECT (strength 0.7)
    assert details["Software Development Fundamentals"].badge_status == "INDIRECT"
    assert details["Software Development Fundamentals"].evidence_strength == 0.7



