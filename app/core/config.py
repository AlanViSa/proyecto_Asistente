"""
Application configuration settings using Pydantic

This module defines all configuration settings used throughout the application,
loaded from environment variables or .env files.
"""
from datetime import time
from functools import lru_cache
from typing import List, Optional, Union
from pydantic import (
    Field,
    EmailStr,
    SecretStr,
    validator,
    AnyHttpUrl,
    PostgresDsn
)
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import secrets

class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    """
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Salon Assistant"
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    
    # Authentication
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT: int = 60  # Requests per minute
    
    # Business Hours
    HORARIO_APERTURA: str = "09:00"
    HORARIO_CIERRE: str = "19:00"
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: Optional[str] = None
    
    # OpenAI API
    OPENAI_API_KEY: Optional[str] = None
    
    # Logging
    LOGGING_LEVEL: str = "INFO"
    
    # Monitoring
    PROMETHEUS_MULTIPROC_DIR: Optional[str] = None
    GRAFANA_URL: Optional[str] = None
    SENTRY_DSN: Optional[str] = None
    
    # SSL Configuration
    SSL_CERTIFICATE: Optional[str] = None
    SSL_KEY: Optional[str] = None
    
    # Application
    BUSINESS_NAME: str = Field(default="Salon Assistant")
    TIMEZONE: str = Field(default="America/New_York")
    DEBUG: bool = Field(default=True)
    ENVIRONMENT: str = Field(default="development")
    
    # Database
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = Field(default="./logs/app.log")
    
    # Monitoring
    PROMETHEUS_METRICS_PATH: str = "/metrics"
    GRAFANA_PORT: int = 3000

    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        allowed = ["development", "testing", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @validator("HORARIO_APERTURA", "HORARIO_CIERRE")
    def validate_business_hours(cls, v):
        try:
            hour, minute = map(int, v.split(":"))
            time(hour, minute)
        except ValueError:
            raise ValueError("Business hours must be in format HH:MM")
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.upper()

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

@lru_cache()
def get_settings() -> Settings:
    """Returns a cached instance of the settings"""
    return Settings()

# Global settings instance
settings = get_settings() 