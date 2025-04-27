import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/webhook_service")
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Webhook settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5  # seconds
    LOG_RETENTION_DAYS: int = 30
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Cache settings
    CACHE_TTL: int = os.getenv("CACHE_TTL") # Cache time-to-live in seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings() 