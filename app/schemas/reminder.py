"""
Reminder schema definitions for API data validation and serialization
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, timedelta


class ReminderBase(BaseModel):
    """Base reminder schema with common attributes"""
    appointment_id: int
    scheduled_time: datetime
    message: Optional[str] = None

    @validator('scheduled_time')
    def validate_scheduled_time(cls, v):
        """Validate scheduled time is in the future"""
        if v < datetime.now():
            raise ValueError("Scheduled time must be in the future")
        return v


class ReminderCreate(ReminderBase):
    """Schema for reminder creation"""
    pass


class ReminderUpdate(BaseModel):
    """Schema for reminder update with optional fields"""
    scheduled_time: Optional[datetime] = None
    message: Optional[str] = None
    sent: Optional[bool] = None

    @validator('scheduled_time')
    def validate_scheduled_time(cls, v):
        """Validate scheduled time is in the future"""
        if v is not None and v < datetime.now():
            raise ValueError("Scheduled time must be in the future")
        return v


class ReminderInDB(ReminderBase):
    """Schema for reminder in database with additional fields"""
    id: int
    sent: bool
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class Reminder(ReminderInDB):
    """Schema for reminder response"""
    pass 