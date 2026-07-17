"""
Application configuration management using Pydantic Settings
"""

from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Decarbonization Platform"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Climatiq API
    CLIMATIQ_API_KEY: str = Field(..., description="Climatiq API authentication key")
    CLIMATIQ_BASE_URL: str = "https://api.climatiq.io"
    CLIMATIQ_PREVIEW_URL: str = "https://preview.api.climatiq.io"
    CLIMATIQ_DATA_VERSION: str = "29.29"  # Use specific version 29.29

    # AI API
    MISTRAL_API_KEY: str = Field(..., description="Mistral AI API key")
    GEMINI_API_KEY: str = Field(default="", description="Gemini AI API key for Auditor Agent")
    GROQ_API_KEY: str = Field(default="", description="Groq AI API key for Auditor Agent")
    AI_MIN_CONFIDENCE_THRESHOLD: float = 0.7  # Minimum confidence for auto-approval

    # Vertex AI (Gemini via Google Cloud, authenticated with ADC)
    # Uses Application Default Credentials (gcloud auth application-default login)
    # instead of an API key, billed to the configured GCP project.
    USE_VERTEX_AI: bool = Field(default=True, description="Route Gemini calls through Vertex AI with ADC")
    VERTEX_PROJECT_ID: str = Field(default="", description="GCP project ID with Vertex AI credits")
    VERTEX_LOCATION: str = Field(default="global", description="Vertex AI location/region")
    VERTEX_MODEL: str = Field(default="gemini-2.5-flash", description="Vertex AI Gemini model")
    
    # Database
    DATABASE_URL: str = Field(..., description="Database connection string (PostgreSQL or SQLite)")

    # Redis (optional - cache disabled if not available)
    REDIS_URL: str = Field(default="", description="Redis connection string")
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    
    # Security
    SECRET_KEY: str = Field(..., min_length=32, description="JWT secret key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000,http://frontend:3000"
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000
    
    # Batch Processing
    BATCH_CHUNK_SIZE: int = 100  # Climatiq limit
    BATCH_TIMEOUT_SECONDS: int = 300
    
    # Cache TTL (seconds)
    EMISSION_FACTOR_CACHE_TTL: int = 86400  # 24 hours
    
    # Copilot LLM Settings
    COPILOT_MODEL: str = "llama-3.1-8b-instant"  # Can switch to llama-3.3-70b-versatile
    COPILOT_MAX_QUERIES_PER_HOUR: int = 50  # Per organization
    COPILOT_RATE_LIMIT_WINDOW_SECONDS: int = 3600  # 1 hour
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


# Global settings instance
settings = Settings()
