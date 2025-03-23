"""
Modelo para las preferencias de notificación de los clientes
"""
from datetime import datetime
from sqlalchemy import Integer, DateTime, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class PreferenciasNotificacion(Base):
    """Modelo para las preferencias de notificación de los clientes"""
    __tablename__ = "preferencias_notificacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), unique=True)
    
    # Canales habilitados
    email_habilitado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sms_habilitado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    whatsapp_habilitado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Tipos de recordatorio habilitados
    recordatorio_24h: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recordatorio_2h: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Zona horaria del cliente
    zona_horaria: Mapped[str] = mapped_column(String(50), nullable=False, default="America/Mexico_City")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now()
    )

    # Relaciones
    cliente = relationship("Cliente", back_populates="preferencias_notificacion") 