"""
Modelo para el estado de salud de la aplicación
"""
from pydantic import BaseModel

class HealthStatus(BaseModel):
    status: str
    database: str
    version: str 