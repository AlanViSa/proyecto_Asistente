"""
NotificationPreference schema definitions for API data validation and serialization
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    """Types of notification methods supported"""
    SMS = "sms"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    NONE = "none"

class NotificationPreferenceBase(BaseModel):
    """Base notification preference schema with common attributes"""
    appointment_reminder: NotificationType = Field(
        default=NotificationType.SMS,
        description="Method for appointment reminders"
    )
    appointment_confirmation: NotificationType = Field(
        default=NotificationType.SMS,
        description="Method for appointment confirmations"
    )
    promotional: NotificationType = Field(
        default=NotificationType.NONE,
        description="Method for promotional messages"
    )
    reminder_hours_before: int = Field(
        default=24,
        description="Hours before appointment to send reminder",
        ge=1,
        le=72
    )
    notifications_enabled: bool = Field(
        default=True,
        description="Whether notifications are enabled for this user"
    )

class NotificationPreferenceCreate(NotificationPreferenceBase):
    """Schema for notification preference creation"""
    client_id: int = Field(..., description="ID of the client these preferences belong to")

class NotificationPreferenceUpdate(BaseModel):
    """Schema for notification preference update with optional fields"""
    appointment_reminder: Optional[NotificationType] = None
    appointment_confirmation: Optional[NotificationType] = None
    promotional: Optional[NotificationType] = None
    reminder_hours_before: Optional[int] = Field(
        None,
        description="Hours before appointment to send reminder",
        ge=1,
        le=72
    )
    notifications_enabled: Optional[bool] = None

class NotificationPreferenceInDB(NotificationPreferenceBase):
    """Schema for notification preference in database with additional fields"""
    id: int
    client_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class NotificationPreference(NotificationPreferenceInDB):
    """Schema for notification preference response"""
    pass 