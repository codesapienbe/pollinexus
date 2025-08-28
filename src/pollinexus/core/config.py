"""
Configuration settings for Pollinexus.

This module contains all application configuration settings using Pydantic Settings
with comprehensive enterprise-grade configuration management.
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
from pathlib import Path
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables with enterprise defaults."""
    
    # Application Info
    app_name: str = "Pollinexus API"
    version: str = "0.1.0"
    description: str = "Data-Driven Pollinator Conservation API for Environmental Agencies"
    environment: str = "development"  # development, staging, production
    
    # Database settings
    database_url: str = "sqlite:///pollinexus.db"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600
    
    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/0"  # Use Redis for local development
    celery_result_backend: str = "redis://localhost:6379/0"  # Use Redis for results
    celery_task_time_limit: int = 1800  # 30 minutes
    celery_task_soft_time_limit: int = 1500  # 25 minutes
    celery_worker_max_tasks_per_child: int = 1000
    celery_worker_prefetch_multiplier: int = 4
    
    # API Security settings
    api_secret_key: str = secrets.token_urlsafe(32)
    jwt_secret_key: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # CORS settings
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    rate_limit_burst: int = 200
    
    # File upload settings
    upload_dir: str = "uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_extensions: List[str] = [".csv", ".xlsx", ".xls", ".json"]
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    log_file: str = "application.log"
    log_rotation: str = "midnight"
    log_retention: int = 30  # days
    
    # Monitoring settings
    enable_metrics: bool = True
    metrics_endpoint: bool = True
    health_check_timeout: int = 30  # seconds
    
    # Cache settings
    cache_backend: str = "memory"  # memory, redis
    cache_default_timeout: int = 300  # seconds
    cache_max_entries: int = 1000
    
    # Email settings (for notifications)
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    
    # WhatsApp settings (for notifications)
    whatsapp_api_url: Optional[str] = None
    whatsapp_api_token: Optional[str] = None
    
    # Security settings
    password_min_length: int = 8
    password_require_special: bool = True
    password_require_numbers: bool = True
    password_require_uppercase: bool = True
    session_timeout: int = 86400  # 24 hours in seconds
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes in seconds
    
    # Development security settings
    disable_security_for_local: bool = True  # Disable security features for local development by default
    
    # Production settings
    debug: bool = False
    reload: bool = False
    workers: int = 1
    
    # SSL/TLS settings
    ssl_keyfile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    use_ssl: bool = False
    
    # Trusted hosts
    trusted_hosts: List[str] = ["localhost", "127.0.0.1", "host.docker.internal"]
    
    # Performance settings
    request_timeout: int = 30
    keep_alive_timeout: int = 5
    max_connections: int = 1000
    max_connection_size: int = 16384
    
    # Shutdown settings
    shutdown_graceful_timeout: int = 30  # seconds
    shutdown_force_timeout: int = 5  # seconds
    shutdown_enable_signal_handling: bool = True
    shutdown_log_level: str = "WARNING"
    
    # Data processing limits
    max_dataset_rows: int = 1000000
    max_processing_time: int = 3600  # 1 hour
    max_memory_usage_mb: int = 4096  # 4GB
    
    # Feature flags
    enable_user_registration: bool = True
    enable_anonymous_access: bool = False
    enable_data_export: bool = True
    enable_visualization_download: bool = True
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging mode."""
        return self.environment.lower() == "staging"
    
    def get_upload_path(self) -> Path:
        """Get the upload directory path."""
        upload_path = Path(self.upload_dir)
        upload_path.mkdir(exist_ok=True)
        return upload_path
    
    def get_log_file_path(self) -> Path:
        """Get the log file path."""
        return Path(self.log_file)
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of warnings/errors."""
        warnings = []
        
        # Production checks
        if self.is_production:
            if self.debug:
                warnings.append("Debug mode should be disabled in production")
            
            if self.api_secret_key == "your-secret-key-here":
                warnings.append("Default API secret key detected - use environment variable")
            
            if not self.use_ssl:
                warnings.append("SSL should be enabled in production")
            
            if "localhost" in self.cors_origins:
                warnings.append("Localhost origins should be removed in production")
        
        # Security checks
        if len(self.api_secret_key) < 32:
            warnings.append("API secret key should be at least 32 characters")
        
        # Database checks
        if self.database_url.startswith("sqlite:") and self.is_production:
            warnings.append("SQLite should not be used in production")
        
        return warnings

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_prefix = "POLLINEXUS_"


# Create global settings instance
settings = Settings()

# Validate configuration on startup
config_warnings = settings.validate_configuration()
if config_warnings:
    import logging
    logger = logging.getLogger(__name__)
    for warning in config_warnings:
        logger.warning(f"Configuration warning: {warning}") 