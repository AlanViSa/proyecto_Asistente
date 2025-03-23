"""
Esquemas Pydantic para el modelo Cliente
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr

class ClienteBase(BaseModel):
    """Schema base para clientes"""
    model_config = ConfigDict(from_attributes=True)

class ClienteCreate(ClienteBase):
    """Schema para crear clientes"""
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del cliente")
    telefono: str = Field(..., min_length=10, max_length=15, description="Número de teléfono")
    email: Optional[EmailStr] = Field(None, description="Correo electrónico")
    preferencias: Optional[str] = Field(None, description="Preferencias del cliente en formato JSON")

class ClienteUpdate(ClienteBase):
    """Schema para actualizar clientes"""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, min_length=10, max_length=15)
    email: Optional[EmailStr] = None
    preferencias: Optional[str] = None
    activo: Optional[bool] = None

class ClienteList(ClienteBase):
    """Schema para listar clientes (versión reducida)"""
    id: int = Field(..., description="ID único del cliente")
    nombre: str = Field(..., description="Nombre del cliente")
    telefono: str = Field(..., description="Número de teléfono")
    email: Optional[EmailStr] = Field(None, description="Correo electrónico")
    activo: bool = Field(True, description="Estado del cliente")

class Cliente(ClienteBase):
    """Schema para respuesta de cliente"""
    id: int = Field(..., description="ID único del cliente")
    nombre: str = Field(..., min_length=2, max_length=100)
    telefono: str = Field(..., min_length=10, max_length=15)
    email: Optional[EmailStr] = None
    preferencias: Optional[str] = None
    activo: bool = True
    ultima_visita: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class ClienteInDB(Cliente):
    """Schema para cliente en base de datos (incluye campos sensibles)"""
    hashed_password: Optional[str] = Field(None, description="Hash de la contraseña") 