"""
User database model definition for ORM
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import List, TYPE_CHECKING

from app.db.database import Base

class User(Base):
    """User model for admin and staff accounts"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)  # Format: +1-XXX-XXX-XXXX
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=True)  # Users are admins by default
    is_superuser = Column(Boolean, default=False)  # For system-level access
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User {self.email}>" 