"""
Client database model definition for ORM
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import List, TYPE_CHECKING
from datetime import datetime
import pytz
from app.db.database import Base

eastern = pytz.timezone('America/New_York')

# Import relationships if needed
if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.notification_preference import NotificationPreference

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

    # Relationships
    appointments = relationship(
        "Appointment",
        back_populates="client",
        cascade="all, delete-orphan"
    )
    notification_preferences = relationship(
        "NotificationPreference",
        back_populates="client",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Client {self.email}>" 