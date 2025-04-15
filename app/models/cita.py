from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declared_attr
from app.db.base import Base
import enum

class EstadoCita(str, enum.Enum):
    """Enumeration of possible states for an appointment"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELED = "canceled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class Cita(Base):
    """Model for the appointments table"""
    __tablename__ = "appointments"
    __table_args__ = {"comment": "Table that stores client appointments"}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    service: Mapped[str] = mapped_column(String(100))
    duration_minutes: Mapped[int] = mapped_column(default=60)
    status: Mapped[EstadoCita] = mapped_column(
        SQLEnum(EstadoCita),
        default=EstadoCita.PENDING
    )
    notas: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    client: Mapped["Cliente"] = relationship("Cliente", back_populates="appointments")