"""
Client database model definition for ORM
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from datetime import datetime
import pytz
from app.db.database import Base

eastern = pytz.timezone('America/New_York')

class Client(Base):
    """Client model for user accounts"""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)  # Format: +1-XXX-XXX-XXXX
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    preferences = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

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