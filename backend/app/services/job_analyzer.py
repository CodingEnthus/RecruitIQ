import json
import re
import httpx
from typing import Dict, Any
from app.core.config import settings
from app.schemas.job import JobProfile
from app.services.skill_normalizer import SkillNormalizer

JOB_ANALYSIS_PROMPT = """You are an expert technical recruitment analyst.
Analyze the following Job Description and extract a structured JobProfile JSON matching the exact schema.

Separate Must-Have required skills from Nice-To-Have preferred skills.

JSON Schema format:
{{
  "role": "Backend Engineer",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "preferred_skills": ["Docker", "AWS", "Kubernetes"],
  "experience_requirements": ["2+ years of backend development"],
  "min_experience_years": 2.0,
  "education_requirements": ["Bachelor's degree in Computer Science or equivalent"],
  "responsibilities": ["Develop REST APIs", "Optimize SQL queries"],
  "domain": "AI / Backend Engineering",
  "keywords": ["Python", "FastAPI", "PostgreSQL", "REST", "SQL"]
}}

Job Description:
{job_text}
"""

class JobAnalyzerService:
    @staticmethod
    async def analyze_job_description(raw_text: str, title: str = "") -> JobProfile:
        if settings.GROQ_API_KEY:
            try:
                profile = await JobAnalyzerService._analyze_with_groq(raw_text)
                if profile:
                    if not profile.role and title:
                        profile.role = title
                    return profile
            except Exception as e:
                print(f"[JobAnalyzer] Groq API fallback due to: {e}")

        return JobAnalyzerService._heuristic_job_analysis(raw_text, title)

    @staticmethod
    async def _analyze_with_groq(text: str) -> JobProfile:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        prompt = JOB_ANALYSIS_PROMPT.format(job_text=text[:5000])
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You output only valid JSON matching the exact schema."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload, headers=headers)
            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                parsed_json = json.loads(content)
                
                # Normalize skills
                parsed_json["required_skills"] = SkillNormalizer.normalize_skills_list(parsed_json.get("required_skills", []))
                parsed_json["preferred_skills"] = SkillNormalizer.normalize_skills_list(parsed_json.get("preferred_skills", []))
                
                return JobProfile(**parsed_json)
        return None

    @staticmethod
    def _heuristic_job_analysis(text: str, title: str) -> JobProfile:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        role_name = title or (lines[0] if lines else "Software Engineer")

        tech_catalog = [
            "Python", "FastAPI", "PostgreSQL", "React", "Next.js", "Docker", "AWS", "Kubernetes",
            "Machine Learning", "LLM", "RAG", "SQL", "JavaScript", "TypeScript", "REST API",
            "Node.js", "PyTorch", "scikit-learn", "Git", "CI/CD"
        ]

        found_tech = []
        for tech in tech_catalog:
            if re.search(r'\b' + re.escape(tech) + r'\b', text, re.IGNORECASE):
                found_tech.append(tech)

        norm_tech = SkillNormalizer.normalize_skills_list(found_tech)
        req_skills = norm_tech[:4] if len(norm_tech) >= 4 else norm_tech
        pref_skills = norm_tech[4:] if len(norm_tech) > 4 else []

        # Min experience extraction regex
        exp_match = re.search(r'(\d+)\+?\s*years?', text, re.IGNORECASE)
        min_years = float(exp_match.group(1)) if exp_match else 2.0

        return JobProfile(
            role=role_name,
            required_skills=req_skills,
            preferred_skills=pref_skills,
            experience_requirements=[f"{int(min_years)}+ years of relevant technical experience"],
            min_experience_years=min_years,
            education_requirements=["Bachelor's degree in Computer Science, Software Engineering, or related field"],
            responsibilities=lines[1:5] if len(lines) > 5 else ["Design, develop, and maintain high performance applications"],
            domain="Software Engineering / AI",
            keywords=norm_tech
        )
