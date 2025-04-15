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

class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # API
    API_V1_STR: str = Field(default="/api/v1")
    PROJECT_NAME: str = Field(default="Asistente Virtual de Citas")
    SERVER_HOST: AnyHttpUrl = Field(default="http://localhost:8000")
    
    # OpenAI
    OPENAI_API_KEY: str = Field(...)
    
    # Database
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./app.db")
    
    # Twilio
    TWILIO_ACCOUNT_SID: str = Field(...)
    TWILIO_AUTH_TOKEN: str = Field(...)
    TWILIO_PHONE_NUMBER: str = Field(...)
    TWILIO_WHATSAPP_NUMBER: str = Field(...)
    
    # Application
    APP_NAME: str = Field(default="Asistente Virtual Salón")
    BUSINESS_NAME: str = Field(default="Beauty Salon")
    BUSINESS_HOURS_START: str = Field(default="09:00")
    BUSINESS_HOURS_END: str = Field(default="17:00")
    TIMEZONE: str = Field(default="UTC")
    DEBUG: bool = Field(default=True)
    ENVIRONMENT: str = Field(default="development")
    
    # JWT
    SECRET_KEY: str = Field(...)
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(default=["http://localhost:3000"])
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="./logs/app.log")
    
    # Localization
    LOCALE: str = Field(default="es_CO")

    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        allowed = ["development", "testing", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @validator("BUSINESS_HOURS_START", "BUSINESS_HOURS_END")
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

    @validator("ALLOWED_ORIGINS", pre=True)
    def validate_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

@lru_cache()
def get_settings() -> Settings:
    """Retorna una instancia cacheada de la configuración"""
    return Settings()

# Instancia global de configuración
settings = get_settings() 