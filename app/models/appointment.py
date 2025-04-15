"""
Appointment database model definition for ORM
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
import pytz

from app.db.database import Base

eastern = pytz.timezone('America/New_York')

class AppointmentStatus(str, enum.Enum):
    """Enumeration of possible appointment statuses"""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
    NO_SHOW = "NO_SHOW"

class Appointment(Base):
    """Appointment model for scheduling"""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(
        Enum(AppointmentStatus),
        nullable=False,
        default=AppointmentStatus.PENDING,
        index=True
    )
    
    # Foreign keys
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")
    reminders = relationship("Reminder", back_populates="appointment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Appointment {self.id} for client {self.client_id} on {self.datetime}>" 