"""
Schemas for blocked time validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class BlockedTimeBase(BaseModel):
    """Base schema for blocked time slots."""
    start_time: datetime = Field(..., description="Start date and time of the blocking.")
    end_time: datetime = Field(..., description="End date and time of the blocking.")
    reason: str = Field(..., max_length=100, description="Reason for the blocking.")
    description: Optional[str] = Field(None, description="Detailed description of the blocking.")

    @field_validator("end_time")
    @classmethod
    def end_time_must_be_after_start_time(cls, v: datetime, values: dict) -> datetime:
        """Validates that the end time is after the start time."""
        if "start_time" in values.data and v <= values.data["start_time"]:
            raise ValueError("The end time must be after the start time.")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "start_time": "2024-03-20T09:00:00Z",
                "end_time": "2024-03-20T18:00:00Z",
                "reason": "Maintenance",
                "description": "Scheduled maintenance of the premises"
            }
        }
    }

class BlockedTimeCreate(BlockedTimeBase):
    """Schema for creating a blocked time slot."""
    pass

class BlockedTimeUpdate(BlockedTimeBase):
    """Schema for updating a blocked time slot."""
    start_time: Optional[datetime] = Field(None, description="Start date and time of the blocking.")
    end_time: Optional[datetime] = Field(None, description="End date and time of the blocking.")
    reason: Optional[str] = Field(None, max_length=100, description="Reason for the blocking.")

class BlockedTime(BlockedTimeBase):
    """Schema for blocked time slot response."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
}