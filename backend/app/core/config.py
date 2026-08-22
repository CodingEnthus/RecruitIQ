import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "RecruitIQ"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    ENV: str = "development"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./recruitiq.db"
    
    # Qdrant
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "recruitiq_candidate_evidence"
    
    # Groq API
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    
    # AI Models
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    
    # Feature Flags
    ENABLE_PROMPT_INJECTION_DEFENSE: bool = True
    DEFAULT_ANONYMOUS_MODE: bool = False

    @property
    def GROQ_API_KEY(self) -> str:
        # Dynamically read GROQ_API_KEY from environment or .env file
        key = os.getenv("GROQ_API_KEY", "")
        if not key:
            # Try reading directly from .env file if env var not set in process
            env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("GROQ_API_KEY="):
                            key = line.split("=", 1)[1].strip()
                            break
        return key

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
