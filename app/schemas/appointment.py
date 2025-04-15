"""
Appointment schema definitions for API data validation and serialization
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum


class AppointmentStatus(str, Enum):
    """Enumeration of possible appointment statuses"""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED" 
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class AppointmentBase(BaseModel):
    """Base appointment schema with common attributes"""
    datetime: datetime
    duration_minutes: int = Field(..., gt=0, le=480)  # Max 8 hours
    service_id: int
    notes: Optional[str] = None

    @validator('datetime')
    def validate_datetime(cls, v):
        """Validate appointment is in the future"""
        if v < datetime.now():
            raise ValueError("Appointment datetime must be in the future")
        return v


class AppointmentCreate(AppointmentBase):
    """Schema for appointment creation"""
    pass


class AppointmentUpdate(BaseModel):
    """Schema for appointment update with optional fields"""
    datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, gt=0, le=480)
    service_id: Optional[int] = None
    notes: Optional[str] = None


class AppointmentInDB(AppointmentBase):
    """Schema for appointment in database with additional fields"""
    id: int
    client_id: int
    status: AppointmentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class AppointmentList(BaseModel):
    """Schema for listing appointments (reduced version)"""
    id: int
    datetime: datetime
    duration_minutes: int
    status: AppointmentStatus
    service_id: int

    class Config:
        orm_mode = True


class Appointment(AppointmentBase):
    """Schema for complete appointment response"""
    id: int
    client_id: int
    status: AppointmentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True 