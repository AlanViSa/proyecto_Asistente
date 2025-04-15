"""
Models package initialization
Import all models here for SQLAlchemy to detect them
"""

from typing import List, Optional

from app.models.cliente import Cliente
from app.models.cita import Cita, EstadoCita
from app.models.client import Client
from app.models.appointment import Appointment, AppointmentStatus
from app.models.service import Service
from app.models.reminder import Reminder

# Exportar los modelos
__all__ = [
    "Cliente",
    "Cita",
    "EstadoCita",
    "Client",
    "Appointment",
    "AppointmentStatus",
    "Service",
    "Reminder"
] 