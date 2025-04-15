"""
Schemas for validating notification preferences data.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from zoneinfo import ZoneInfo, available_timezones


class PreferenciasNotificacionBase(BaseModel):
    """Base schema for notification preferences."""

    email_enabled: bool = Field(True, description="Whether email notifications are enabled.")
    sms_enabled: bool = Field(False, description="Whether SMS notifications are enabled.")
    whatsapp_enabled: bool = Field(False, description="Whether WhatsApp notifications are enabled.")
    reminder_24h: bool = Field(True, description="Whether the 24-hour reminder is enabled.")
    reminder_2h: bool = Field(True, description="Whether the 2-hour reminder is enabled.")
    timezone: str = Field(
        "US/Eastern", description="Client's timezone for notifications."
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validates that the timezone is valid."""
        if v not in available_timezones():
            raise ValueError("Invalid timezone.")
        return v

    @field_validator("email_enabled", "sms_enabled", "whatsapp_enabled")
    @classmethod
    def validate_at_least_one_channel(cls, v: bool, values: dict) -> bool:
        """Validates that at least one notification channel is enabled."""
        if not v and not any(
            values.data.get(canal, False)
            for canal in ["email_enabled", "sms_enabled", "whatsapp_enabled"]
            if canal in values.data
        ):
            raise ValueError("At least one notification channel must be enabled.")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email_enabled": True,
                "sms_enabled": False,
                "whatsapp_enabled": False,
                "reminder_24h": True,
                "reminder_2h": True,
                "timezone": "US/Eastern",
            }
        }
    }


class PreferenciasNotificacionCreate(PreferenciasNotificacionBase):
    """Schema for creating notification preferences."""

    client_id: int = Field(..., description="Client ID.")


class PreferenciasNotificacionUpdate(PreferenciasNotificacionBase):
    """Schema for updating notification preferences."""

    email_enabled: Optional[bool] = Field(None, description="Whether email notifications are enabled.")
    sms_enabled: Optional[bool] = Field(None, description="Whether SMS notifications are enabled.")
    whatsapp_enabled: Optional[bool] = Field(None, description="Whether WhatsApp notifications are enabled.")
    reminder_24h: Optional[bool] = Field(None, description="Whether the 24-hour reminder is enabled.")
    reminder_2h: Optional[bool] = Field(None, description="Whether the 2-hour reminder is enabled.")
    timezone: Optional[str] = Field(None, description="Client's timezone for notifications.")


class PreferenciasNotificacion(PreferenciasNotificacionBase):
    """Schema for notification preferences response."""

    id: int
    client_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }