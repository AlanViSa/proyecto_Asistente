"""
Esquemas Pydantic para el modelo Cita
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.cita import EstadoCita
from app.schemas.cliente import ClienteList

class CitaBase(BaseModel):
    """Schema base para citas"""
    model_config = ConfigDict(from_attributes=True)

class CitaCreate(CitaBase):
    """Schema para crear citas"""
    fecha_hora: datetime = Field(..., description="Fecha y hora de la cita")
    servicio: str = Field(..., min_length=2, max_length=100, description="Servicio solicitado")
    duracion_minutos: int = Field(60, ge=15, le=240, description="Duración en minutos")
    notas: Optional[str] = Field(None, max_length=500, description="Notas adicionales")

class CitaUpdate(CitaBase):
    """Schema para actualizar citas"""
    fecha_hora: Optional[datetime] = None
    servicio: Optional[str] = Field(None, min_length=2, max_length=100)
    duracion_minutos: Optional[int] = Field(None, ge=15, le=240)
    notas: Optional[str] = Field(None, max_length=500)

class CitaList(CitaBase):
    """Schema para listar citas (versión reducida)"""
    id: int = Field(..., description="ID único de la cita")
    fecha_hora: datetime = Field(..., description="Fecha y hora de la cita")
    servicio: str = Field(..., description="Servicio solicitado")
    estado: EstadoCita = Field(..., description="Estado actual de la cita")
    cliente: ClienteList = Field(..., description="Cliente que reservó la cita")

class Cita(CitaBase):
    """Schema para respuesta de cita"""
    id: int = Field(..., description="ID único de la cita")
    fecha_hora: datetime
    servicio: str
    duracion_minutos: int
    estado: EstadoCita
    notas: Optional[str] = None
    cliente_id: int = Field(..., description="ID del cliente")
    cliente: ClienteList
    created_at: datetime
    updated_at: datetime

class CitaInDB(Cita):
    """Schema para cita en base de datos"""
    pass  # Mismo que Cita, pero lo mantenemos por consistencia 