"""
Configuration settings for Pollinexus.

This module contains all application configuration settings using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database settings
    database_url: str = "duckdb:///pollinexus.db"
    
    # Celery settings
    celery_broker_url: str = "memory://"
    celery_result_backend: str = "memory://"
    
    # API settings
    api_secret_key: str = "your-secret-key-here"
    debug: bool = False
    
    # File upload settings
    upload_dir: str = "uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create global settings instance
settings = Settings() 