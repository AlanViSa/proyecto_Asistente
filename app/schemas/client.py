"""
Client schema definitions for API data validation and serialization
"""
from pydantic import BaseModel, EmailStr, constr, validator
from typing import Optional
from datetime import datetime
import re

class ClientBase(BaseModel):
    """Base client schema with common attributes"""
    email: EmailStr
    full_name: constr(min_length=2, max_length=100)
    phone: constr(regex=r'^\+1-\d{3}-\d{3}-\d{4}$')

    @validator('phone')
    def validate_us_phone(cls, v):
        """Validate phone number is in USA format (+1-XXX-XXX-XXXX)"""
        if not re.match(r'^\+1-\d{3}-\d{3}-\d{4}$', v):
            raise ValueError('Phone number must be in format: +1-XXX-XXX-XXXX')
        return v

class ClientCreate(ClientBase):
    """Schema for client creation with password field"""
    password: constr(min_length=8, max_length=100)

class ClientUpdate(BaseModel):
    """Schema for client update with optional fields"""
    email: Optional[EmailStr] = None
    full_name: Optional[constr(min_length=2, max_length=100)] = None
    phone: Optional[constr(regex=r'^\+1-\d{3}-\d{3}-\d{4}$')] = None
    password: Optional[constr(min_length=8, max_length=100)] = None

class ClientInDB(ClientBase):
    """Schema for client in database with additional fields"""
    id: int
    hashed_password: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class ClientResponse(ClientBase):
    """Schema for client response without sensitive data"""
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True 