"""
Modelo para el estado de salud de la aplicación
"""
from pydantic import BaseModel

class HealthStatus(BaseModel):
    status: str
    database: str
    version: str 

"""
Health check model for database connectivity testing
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db.database import Base

class Health(Base):
    """Health check model for testing database connectivity"""
    __tablename__ = "health"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, nullable=False, default="ok")
    checked_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Health check at {self.checked_at}>" 