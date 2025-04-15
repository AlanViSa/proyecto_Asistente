"""
NotificationPreference database model definition for ORM
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base

class NotificationType(str, enum.Enum):
    """Types of notification methods supported"""
    SMS = "sms"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    NONE = "none"

class NotificationPreference(Base):
    """Model for user notification preferences"""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, unique=True, index=True)
    
    # Notification types
    appointment_reminder = Column(Enum(NotificationType), default=NotificationType.SMS, nullable=False)
    appointment_confirmation = Column(Enum(NotificationType), default=NotificationType.SMS, nullable=False)
    promotional = Column(Enum(NotificationType), default=NotificationType.NONE, nullable=False)
    
    # Timing preferences (hours before appointment)
    reminder_hours_before = Column(Integer, default=24, nullable=False)
    
    # Enable/disable flags
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="notification_preferences")
    
    def __repr__(self):
        return f"<NotificationPreference for client_id: {self.client_id}>" 