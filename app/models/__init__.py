"""
Models package exposing all data models
"""

from app.models.client import Client
from app.models.appointment import Appointment, AppointmentStatus
from app.models.service import Service
from app.models.reminder import Reminder
from app.models.blocked_schedule import BlockedSchedule
from app.models.notification_preference import NotificationPreference
from app.models.sent_reminder import SentReminder
from app.models.health import HealthCheck

# Compatibility aliases
Cliente = Client
Cita = Appointment
EstadoCita = AppointmentStatus
Servicio = Service
Recordatorio = Reminder
HorarioBloqueado = BlockedSchedule
PreferenciaNotificacion = NotificationPreference
RecordatorioEnviado = SentReminder

__all__ = [
    # English names
    "Client",
    "Appointment",
    "AppointmentStatus",
    "Service",
    "Reminder",
    "BlockedSchedule",
    "NotificationPreference",
    "SentReminder",
    "HealthCheck",
    # Spanish names - for backward compatibility
    "Cliente",
    "Cita",
    "EstadoCita",
    "Servicio",
    "Recordatorio",
    "HorarioBloqueado",
    "PreferenciaNotificacion",
    "RecordatorioEnviado"
] 