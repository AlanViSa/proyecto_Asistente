"""
BlockedSchedule database model definition for ORM
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime

from app.db.database import Base

class BlockedSchedule(Base):
    """Model for blocked time slots in the schedule"""
    __tablename__ = "blocked_schedule"

    id = Column(Integer, primary_key=True, index=True)
    reason = Column(String, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String, nullable=True)  # JSON string with recurrence details
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<BlockedSchedule {self.start_date} to {self.end_date}>" 