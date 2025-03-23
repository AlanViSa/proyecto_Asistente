"""
Esquemas para la validación de datos de horarios bloqueados
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class HorarioBloqueadoBase(BaseModel):
    """Esquema base para horarios bloqueados"""
    fecha_inicio: datetime = Field(..., description="Fecha y hora de inicio del bloqueo")
    fecha_fin: datetime = Field(..., description="Fecha y hora de fin del bloqueo")
    motivo: str = Field(..., max_length=100, description="Motivo del bloqueo")
    descripcion: Optional[str] = Field(None, description="Descripción detallada del bloqueo")

    @field_validator("fecha_fin")
    @classmethod
    def fecha_fin_mayor_inicio(cls, v: datetime, values: dict) -> datetime:
        """Valida que la fecha de fin sea posterior a la de inicio"""
        if "fecha_inicio" in values.data and v <= values.data["fecha_inicio"]:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "fecha_inicio": "2024-03-20T09:00:00Z",
                "fecha_fin": "2024-03-20T18:00:00Z",
                "motivo": "Mantenimiento",
                "descripcion": "Mantenimiento programado del local"
            }
        }
    }

class HorarioBloqueadoCreate(HorarioBloqueadoBase):
    """Esquema para crear un horario bloqueado"""
    pass

class HorarioBloqueadoUpdate(HorarioBloqueadoBase):
    """Esquema para actualizar un horario bloqueado"""
    fecha_inicio: Optional[datetime] = Field(None, description="Fecha y hora de inicio del bloqueo")
    fecha_fin: Optional[datetime] = Field(None, description="Fecha y hora de fin del bloqueo")
    motivo: Optional[str] = Field(None, max_length=100, description="Motivo del bloqueo")

class HorarioBloqueado(HorarioBloqueadoBase):
    """Esquema para respuesta de horario bloqueado"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    } 