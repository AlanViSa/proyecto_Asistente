"""
Reminder database model definition for ORM
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz

from app.db.database import Base

eastern = pytz.timezone('America/New_York')

class Reminder(Base):
    """Reminder model for appointment notifications"""
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)
    sent = Column(Boolean, default=False, nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    appointment = relationship("Appointment", back_populates="reminders")
    
    def __repr__(self):
        return f"<Reminder {self.id} for appointment {self.appointment_id}>" 