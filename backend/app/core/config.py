import os
from typing import List, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "MCUVerse AI"
    API_V1_STR: str = "/api/v1"
    
    # Security & JWT
    SECRET_KEY: str = "SUPER_SECRET_JARVIS_CODE_DO_NOT_SHARE_IN_PRODUCTION_12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = "sqlite:///./mcuverse.db"
    
    # Caching
    CACHE_PROVIDER: str = "memory"  # memory, sqlite, redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Embeddings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "embeddings/faiss_index"
    
    # LLM Configuration
    LLM_PROVIDER: str = "retrieval_only"  # gemini, openai, anthropic, groq, ollama, retrieval_only
    PREFERRED_MODEL: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    OLLAMA_API_URL: str = "http://localhost:11434"
    
    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
