"""
BlockedSchedule schema definitions for API data validation and serialization
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class BlockedScheduleBase(BaseModel):
    """Base blocked schedule schema with common attributes"""
    start_time: datetime = Field(..., description="Start time of the blocked period")
    end_time: datetime = Field(..., description="End time of the blocked period")
    reason: Optional[str] = Field(None, description="Reason for blocking the schedule")

    @validator('end_time')
    def end_time_after_start_time(cls, v, values):
        """Validate end time is after start time"""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

class BlockedScheduleCreate(BlockedScheduleBase):
    """Schema for blocked schedule creation"""
    pass

class BlockedScheduleUpdate(BaseModel):
    """Schema for blocked schedule update with optional fields"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    reason: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('end_time')
    def end_time_after_start_time(cls, v, values):
        """Validate end time is after start time if both are provided"""
        if v and 'start_time' in values and values['start_time'] and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

class BlockedScheduleInDB(BlockedScheduleBase):
    """Schema for blocked schedule in database with additional fields"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class BlockedSchedule(BlockedScheduleInDB):
    """Schema for blocked schedule response"""
    pass 