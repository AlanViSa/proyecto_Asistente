"""
SentReminder database model definition for ORM
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base

class ReminderStatus(str, enum.Enum):
    """Status of sent reminders"""
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"

class SentReminder(Base):
    """Model for tracking sent reminders"""
    __tablename__ = "sent_reminders"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(Enum(ReminderStatus), default=ReminderStatus.SENT, nullable=False)
    status_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional metadata
    channel = Column(String(50), nullable=False)  # sms, email, whatsapp
    recipient = Column(String(100), nullable=False)  # phone number or email
    external_id = Column(String(100), nullable=True)  # ID from external service (e.g., Twilio)
    
    # Relationships
    appointment = relationship("Appointment", back_populates="sent_reminders")
    
    def __repr__(self):
        return f"<SentReminder {self.id} for appointment {self.appointment_id}>" 