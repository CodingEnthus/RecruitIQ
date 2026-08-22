import re
from typing import List, Dict
from rapidfuzz import process, fuzz

CANONICAL_SKILL_MAP: Dict[str, str] = {
    # Web & Frontend
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "react js": "React",
    "next": "Next.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "vuejs": "Vue.js",
    "angular": "Angular",
    "angularjs": "Angular",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "html": "HTML5",
    "html5": "HTML5",
    "css": "CSS3",
    "css3": "CSS3",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",

    # Backend & APIs
    "java": "Java",
    "python": "Python",
    "python3": "Python",
    "fastapi": "FastAPI",
    "fast api": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "express": "Express.js",
    "express.js": "Express.js",
    "rest": "REST APIs",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "restful api": "REST APIs",
    "restful apis": "REST APIs",
    "graphql": "GraphQL",
    "grpc": "gRPC",

    # Database & Systems
    "c": "C",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "psql": "PostgreSQL",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "qdrant": "Qdrant",
    "vector database": "Vector DB",
    "vector db": "Vector DB",

    # AI / ML & Data Science
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "artificial intelligence": "AI",
    "ai": "AI",
    "nlp": "Natural Language Processing",
    "natural language processing": "Natural Language Processing",
    "rag": "RAG",
    "retrieval augmented generation": "RAG",
    "llm": "LLMs",
    "llms": "LLMs",
    "large language models": "LLMs",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "spacy": "spaCy",
    "huggingface": "Hugging Face",

    # DevOps & Infrastructure
    "docker": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "aws": "Amazon Web Services (AWS)",
    "amazon web services": "Amazon Web Services (AWS)",
    "gcp": "Google Cloud Platform (GCP)",
    "google cloud": "Google Cloud Platform (GCP)",
    "azure": "Microsoft Azure",
    "ci/cd": "CI/CD",
    "github actions": "GitHub Actions",
    "git": "Git",
    "github": "GitHub",
    "linux": "Linux",
    "bash": "Bash"
}

class SkillNormalizer:
    @staticmethod
    def normalize_skill(raw_skill: str) -> str:
        clean = raw_skill.strip().lower()
        if not clean:
            return ""

        # Direct canonical lookup
        if clean in CANONICAL_SKILL_MAP:
            return CANONICAL_SKILL_MAP[clean]

        # Stripped symbols lookup
        clean_alphanumeric = re.sub(r'[^a-z0-9]', '', clean)
        for map_key, canonical in CANONICAL_SKILL_MAP.items():
            key_alphanumeric = re.sub(r'[^a-z0-9]', '', map_key)
            if clean_alphanumeric == key_alphanumeric:
                return canonical

        # Fuzzy match fallback against canonical dictionary
        all_canonical_list = list(set(CANONICAL_SKILL_MAP.values()))
        best_match = process.extractOne(raw_skill, all_canonical_list, scorer=fuzz.token_sort_ratio)
        if best_match and best_match[1] >= 88:
            return best_match[0]

        # Capitalize nicely if unmatched
        return raw_skill.strip().title()

    @classmethod
    def normalize_skills_list(cls, skills: List[str]) -> List[str]:
        normalized = []
        seen = set()
        for skill in skills:
            norm = cls.normalize_skill(skill)
            if norm and norm.lower() not in seen:
                seen.add(norm.lower())
                normalized.append(norm)
        return normalized

    @classmethod
    def is_skill_match(cls, skill1: str, skill2: str) -> bool:
        norm1 = cls.normalize_skill(skill1)
        norm2 = cls.normalize_skill(skill2)
        n1 = norm1.lower()
        n2 = norm2.lower()

        # Strict entity rejection pairs
        distinct_pairs = {
            ("java", "javascript"),
            ("javascript", "java"),
            ("c", "c++"),
            ("c++", "c"),
            ("c", "c#"),
            ("c#", "c"),
            ("react", "react native"),
            ("react native", "react"),
            ("git", "github"),
            ("github", "git")
        }
        if (n1, n2) in distinct_pairs:
            return False

        if n1 == n2:
            return True

        # Short skills (length <= 4) require exact canonical match
        if len(n1) <= 4 or len(n2) <= 4:
            return False

        ratio = fuzz.token_sort_ratio(n1, n2)
        return ratio >= 85

    @classmethod
    def search_skill_in_text(cls, raw_skill: str, text: str) -> bool:
        if not raw_skill or not text:
            return False

        target = cls.normalize_skill(raw_skill).lower()

        if target == "java":
            # Must match exact word 'java', but NEVER 'javascript'
            pattern = r'\bjava\b'
            return bool(re.search(pattern, text, re.IGNORECASE))
        elif target == "c":
            # Must match 'c' but NOT 'c++' or 'c#'
            pattern = r'\bc\b(?!\+|\#)'
            return bool(re.search(pattern, text, re.IGNORECASE))
        elif target in ["git", "sql", "python", "rest apis", "fastapi"]:
            pattern = r'\b' + re.escape(target) + r'\b'
            return bool(re.search(pattern, text, re.IGNORECASE))

        # Default word boundary regex search
        pattern = r'\b' + re.escape(target) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))

