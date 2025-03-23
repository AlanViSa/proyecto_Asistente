from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, text, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Cliente(Base):
    """Modelo para la tabla de clientes"""
    __tablename__ = "clientes"
    __table_args__ = {"comment": "Tabla que almacena la información de los clientes"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    preferencias: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ultima_visita: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
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
    citas: Mapped[List["Cita"]] = relationship(
        "Cita",
        back_populates="cliente",
        cascade="all, delete-orphan"
    )
    preferencias_notificacion: Mapped["PreferenciasNotificacion"] = relationship(
        "PreferenciasNotificacion",
        back_populates="cliente",
        uselist=False,
        cascade="all, delete-orphan"
    ) 