"""
Services package exposing standardized English-named services
"""

# Import all service classes with their English names
from app.services.client_service import ClientService
from app.services.appointment_service import AppointmentService
from app.services.reminder_service import ReminderService
from app.services.service_service import ServiceService
from app.services.auth import AuthService
from app.services.notification_service import NotificationService
from app.services.blocked_schedule_service import BlockedScheduleService
from app.services.notification_preference_service import NotificationPreferenceService
from app.services.health_service import HealthService

# Import for backward compatibility - deprecated
from app.services.client_service import ClientService as ClienteService
from app.services.appointment_service import AppointmentService as CitaService
from app.services.reminder_service import ReminderService as RecordatorioService
from app.services.blocked_schedule_service import BlockedScheduleService as HorarioBloqueadoService
from app.services.notification_preference_service import NotificationPreferenceService as PreferenciasNotificacionService

__all__ = [
    "ClientService",
    "AppointmentService",
    "ReminderService",
    "ServiceService",
    "AuthService",
    "NotificationService",
    "BlockedScheduleService",
    "NotificationPreferenceService",
    "HealthService",
    # Deprecated - for backward compatibility
    "ClienteService",
    "CitaService",
    "RecordatorioService",
    "HorarioBloqueadoService",
    "PreferenciasNotificacionService",
] 