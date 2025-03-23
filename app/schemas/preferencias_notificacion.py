"""
Esquemas para la validación de datos de preferencias de notificación
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from zoneinfo import ZoneInfo, available_timezones

class PreferenciasNotificacionBase(BaseModel):
    """Esquema base para preferencias de notificación"""
    email_habilitado: bool = Field(True, description="Si las notificaciones por email están habilitadas")
    sms_habilitado: bool = Field(False, description="Si las notificaciones por SMS están habilitadas")
    whatsapp_habilitado: bool = Field(False, description="Si las notificaciones por WhatsApp están habilitadas")
    recordatorio_24h: bool = Field(True, description="Si el recordatorio de 24 horas está habilitado")
    recordatorio_2h: bool = Field(True, description="Si el recordatorio de 2 horas está habilitado")
    zona_horaria: str = Field(
        "America/Mexico_City",
        description="Zona horaria del cliente para las notificaciones"
    )

    @field_validator("zona_horaria")
    @classmethod
    def validar_zona_horaria(cls, v: str) -> str:
        """Valida que la zona horaria sea válida"""
        if v not in available_timezones():
            raise ValueError("Zona horaria no válida")
        return v

    @field_validator("email_habilitado", "sms_habilitado", "whatsapp_habilitado")
    @classmethod
    def validar_al_menos_un_canal(cls, v: bool, values: dict) -> bool:
        """Valida que al menos un canal de notificación esté habilitado"""
        if not v and not any(
            values.data.get(canal, False)
            for canal in ["email_habilitado", "sms_habilitado", "whatsapp_habilitado"]
            if canal in values.data
        ):
            raise ValueError("Al menos un canal de notificación debe estar habilitado")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email_habilitado": True,
                "sms_habilitado": False,
                "whatsapp_habilitado": False,
                "recordatorio_24h": True,
                "recordatorio_2h": True,
                "zona_horaria": "America/Mexico_City"
            }
        }
    }

class PreferenciasNotificacionCreate(PreferenciasNotificacionBase):
    """Esquema para crear preferencias de notificación"""
    cliente_id: int = Field(..., description="ID del cliente")

class PreferenciasNotificacionUpdate(PreferenciasNotificacionBase):
    """Esquema para actualizar preferencias de notificación"""
    email_habilitado: Optional[bool] = Field(None, description="Si las notificaciones por email están habilitadas")
    sms_habilitado: Optional[bool] = Field(None, description="Si las notificaciones por SMS están habilitadas")
    whatsapp_habilitado: Optional[bool] = Field(None, description="Si las notificaciones por WhatsApp están habilitadas")
    recordatorio_24h: Optional[bool] = Field(None, description="Si el recordatorio de 24 horas está habilitado")
    recordatorio_2h: Optional[bool] = Field(None, description="Si el recordatorio de 2 horas está habilitado")
    zona_horaria: Optional[str] = Field(None, description="Zona horaria del cliente para las notificaciones")

class PreferenciasNotificacion(PreferenciasNotificacionBase):
    """Esquema para respuesta de preferencias de notificación"""
    id: int
    cliente_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    } 