"""
Main API router that includes all endpoint routers
"""
from fastapi import APIRouter

from app.api.v1.endpoints import clients, appointments, services, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(clients.router, tags=["Clients"])
api_router.include_router(services.router, tags=["Services"])
api_router.include_router(appointments.router, tags=["Appointments"]) 