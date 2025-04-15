"""
BlockedSchedule database model definition for ORM
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from datetime import datetime
import pytz

from app.db.database import Base

eastern = pytz.timezone('America/New_York')

class BlockedSchedule(Base):
    """Model for blocked time slots that are unavailable for appointments"""
    __tablename__ = "blocked_schedules"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<BlockedSchedule {self.id}: {self.start_time} - {self.end_time}>" 