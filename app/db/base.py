"""
Database base module

Import all models here for Alembic to discover them
"""

from app.db.database import Base

# Import all models here for Alembic to discover them
from app.models.client import Client
from app.models.user import User
from app.models.appointment import Appointment
from app.models.service import Service
from app.models.reminder import Reminder
from app.models.notification_preference import NotificationPreference
from app.models.blocked_schedule import BlockedSchedule
from app.models.health import Health 