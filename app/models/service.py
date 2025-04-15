"""
Service database model definition for ORM
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base

class Service(Base):
    """Service model for salon services offered"""
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    appointments = relationship("Appointment", back_populates="service")
    
    def __repr__(self):
        return f"<Service {self.name}>" 