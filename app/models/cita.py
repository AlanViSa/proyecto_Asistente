from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declared_attr
from app.db.base import Base
import enum

class EstadoCita(str, enum.Enum):
    """Enumeración de estados posibles para una cita"""
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    COMPLETADA = "completada"
    NO_ASISTIO = "no_asistio"

class Cita(Base):
    """Modelo para la tabla de citas"""
    __tablename__ = "citas"
    __table_args__ = {"comment": "Tabla que almacena las citas de los clientes"}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    servicio: Mapped[str] = mapped_column(String(100))
    duracion_minutos: Mapped[int] = mapped_column(default=60)
    estado: Mapped[EstadoCita] = mapped_column(
        SQLEnum(EstadoCita),
        default=EstadoCita.PENDIENTE
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
    
    # Relaciones
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="citas") 