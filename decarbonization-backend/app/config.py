# app/config.py
"""
Application configuration settings
Using Pydantic Settings for environment variable management
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    APP_NAME: str = "Decarbonization Platform API"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours per AC-1.1
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://decarb_user:decarb_password@localhost:5432/decarb_db"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]
    
    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Gemini Configuration
    GEMINI_API_KEY: str = "test-api-key-default"
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # DSPy Configuration
    DSPY_LM_MODEL: str = "gemini-2.0-flash"
    DSPY_TEMPERATURE: float = 0.3
    DSPY_MAX_TOKENS: int = 150
    
    # Classifition Configuration
    MIN_MAX_TOKENS: int = 150

    # if < 80%
    CLASSIFICATION_THRESHOLD: float = 0.80 # Flag
    BATCH_CLASSIFICATION_SIZE: int = 50 # Process in batches

    # Features Flags
    ENABLE_DSPY_AGENTS: bool = True
    ENABLE_CONFIDENCE_FLAGGING: bool = True
    ENABLE_AUDIT_LOGGING: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
