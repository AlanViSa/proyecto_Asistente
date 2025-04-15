"""
Main API router that includes all endpoint routers
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    clients, 
    appointments, 
    services, 
    auth, 
    notification_preferences,
    reminders,
    blocked_schedule
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(clients.router, prefix="/clients", tags=["Clients"])
api_router.include_router(services.router, prefix="/services", tags=["Services"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
api_router.include_router(notification_preferences.router, prefix="/notification-preferences", tags=["Notification Preferences"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["Reminders"])
api_router.include_router(blocked_schedule.router, prefix="/blocked-schedules", tags=["Blocked Schedules"]) 