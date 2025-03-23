"""
Modelo para registrar los recordatorios enviados
"""
from datetime import datetime
from sqlalchemy import Integer, DateTime, String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class RecordatorioEnviado(Base):
    """Modelo para registrar los recordatorios enviados"""
    __tablename__ = "recordatorios_enviados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cita_id: Mapped[int] = mapped_column(Integer, ForeignKey("citas.id", ondelete="CASCADE"), index=True)
    tipo_recordatorio: Mapped[str] = mapped_column(String(20), nullable=False)  # "24h" o "2h"
    canal: Mapped[str] = mapped_column(String(20), nullable=False)  # "email", "sms", "whatsapp"
    exitoso: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now()
    )

    # Relaciones
    cita = relationship("Cita", back_populates="recordatorios_enviados") 