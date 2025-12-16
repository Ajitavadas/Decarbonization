# app/config.py
"""
Application configuration settings
Using Pydantic Settings for environment variable management
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    APP_NAME: str = "Decarbonization Platform API"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    
    # Gemini AI Configuration
    GEMINI_API_KEY: str = "Gemini API Key"
    AI_MIN_CONFIDENCE_THRESHOLD: float = 0.80 # 80% confidence threshold for AI responses
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours per AC-1.1
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://decarb_user:decarb_password@localhost:5432/decarb_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000", "http://localhost","http://127.0.0.1:3000"]
    
    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
