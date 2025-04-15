"""
Model for customer notification preferences.
"""
from datetime import datetime
from sqlalchemy import Integer, DateTime, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class NotificationPreferences(Base):
    """Model for customer notification preferences."""
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), unique=True)
    
    # Enabled channels
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Enabled reminder types
    reminder_24h: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reminder_2h: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Customer timezone
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="US/Eastern")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
    )

    # Relationships
    customer = relationship("Customer", back_populates="notification_preferences")