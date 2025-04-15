"""
Model to register sent reminders
"""
from datetime import datetime
from sqlalchemy import Integer, DateTime, String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class SentReminder(Base):
    """Model to register sent reminders"""
    __tablename__ = "sent_reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    appointment_id: Mapped[int] = mapped_column(Integer, ForeignKey("appointments.id", ondelete="CASCADE"), index=True)
    reminder_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "24h" or "2h"
    channel: Mapped[str] = mapped_column(String(20), nullable=False)  # "email", "sms", "whatsapp"
    successful: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now()
    )
    sent_date: Mapped[datetime]

    # Relationships
    appointment = relationship("Appointment", back_populates="sent_reminders")