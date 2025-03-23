"""
Router principal para la API v1
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    usuarios,
    roles,
    servicios,
    citas,
    notificaciones,
    preferencias_notificacion,
    recordatorios,
    clientes,
    health
)

api_router = APIRouter()

# Incluir los routers de los endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["usuarios"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(servicios.router, prefix="/servicios", tags=["servicios"])
api_router.include_router(citas.router, prefix="/citas", tags=["citas"])
api_router.include_router(notificaciones.router, prefix="/notificaciones", tags=["notificaciones"])
api_router.include_router(
    preferencias_notificacion.router,
    prefix="/preferencias-notificacion",
    tags=["preferencias-notificacion"]
)
api_router.include_router(recordatorios.router, prefix="/recordatorios", tags=["recordatorios"])
api_router.include_router(clientes.router, prefix="/clientes", tags=["clientes"])
api_router.include_router(health.router, tags=["health"]) 