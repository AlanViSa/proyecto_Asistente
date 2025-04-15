"""
Pydantic schemas for the Appointment model
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlmodel import SQLModel, Field as SQLField, Relationship

if TYPE_CHECKING:
    from app.models.cliente import Cliente  # Import only during type checking

class AppointmentBase(SQLModel):
    """Base schema for appointments"""
    date_time: datetime = SQLField(index=True)
    service: str = SQLField(max_length=100, index=True)
    duration_minutes: int = SQLField(default=60, ge=15, le=240)
    notes: Optional[str] = SQLField(max_length=500, nullable=True, default=None)

class Appointment(AppointmentBase, table=True):
    """Appointment model for the database"""
    id: Optional[int] = SQLField(default=None, primary_key=True)
    status: str = SQLField(default="scheduled")  # Use string for status
    client_id: int = SQLField(foreign_key="cliente.id")
    client: "Cliente" = Relationship(back_populates="appointments")  # Use forward reference
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)

    @field_validator("status")
    def validate_status(cls, value):
        valid_statuses = ["scheduled", "confirmed", "cancelled", "completed", "no-show"]
        if value not in valid_statuses:
            raise ValueError(f"Invalid appointment status: {value}. Valid statuses are: {valid_statuses}")
        return value

class AppointmentCreate(AppointmentBase):
    """Schema for creating appointments"""
    client_id: int
    status: str = "scheduled"  # Default status
    
class AppointmentUpdate(AppointmentBase):
    """Schema for updating appointments"""
    date_time: Optional[datetime] = None
    service: Optional[str] = None
    duration_minutes: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None