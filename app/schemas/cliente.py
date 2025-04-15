"""
Pydantic schemas for the Client model
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr

class ClienteBase(BaseModel):
    """Base schema for clients"""
    model_config = ConfigDict(from_attributes=True)

class ClienteCreate(ClienteBase):
    """Schema for creating clients"""
    name: str = Field(..., min_length=2, max_length=100, description="Client name")
    phone: str = Field(..., min_length=10, max_length=15, description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    preferences: Optional[str] = Field(None, description="Client preferences in JSON format")

class ClienteUpdate(ClienteBase):
    """Schema for updating clients"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    email: Optional[EmailStr] = None
    preferences: Optional[str] = None
    active: Optional[bool] = None

class ClienteList(ClienteBase):
    """Schema for listing clients (reduced version)"""
    id: int = Field(..., description="Unique client ID")
    name: str = Field(..., description="Client name")
    phone: str = Field(..., description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    active: bool = Field(True, description="Client status")

class Cliente(ClienteBase):
    """Schema for client response"""
    id: int = Field(..., description="Unique client ID")
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    email: Optional[EmailStr] = None
    preferences: Optional[str] = None
    active: bool = True
    last_visit: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class ClienteInDB(Cliente):
    """Schema for client in database (includes sensitive fields)"""
    hashed_password: Optional[str] = Field(None, description="Password hash")