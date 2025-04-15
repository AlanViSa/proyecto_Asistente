"""
Schemas package initialization
Import all schemas here for easy access throughout the application
"""

from app.schemas.client import (
    ClientBase,
    ClientCreate,
    ClientUpdate,
    ClientInDB,
    ClientResponse
)

from app.schemas.appointment import (
    AppointmentStatus,
    AppointmentBase,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentInDB,
    AppointmentList,
    Appointment
)

from app.schemas.service import (
    ServiceBase,
    ServiceCreate,
    ServiceUpdate,
    ServiceInDB,
    Service
)

from app.schemas.reminder import (
    ReminderBase,
    ReminderCreate,
    ReminderUpdate,
    ReminderInDB,
    Reminder
)

# Exportar los esquemas
__all__ = [
    # Cliente schemas
    "ClientBase",
    "ClientCreate",
    "ClientUpdate",
    "ClientInDB",
    "ClientResponse",
    # Cita schemas
    "AppointmentStatus",
    "AppointmentBase",
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentInDB",
    "AppointmentList",
    "Appointment",
    # Token schemas
    "ServiceBase",
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceInDB",
    "Service",
    "ReminderBase",
    "ReminderCreate",
    "ReminderUpdate",
    "ReminderInDB",
    "Reminder"
] 