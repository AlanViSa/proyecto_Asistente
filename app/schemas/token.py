from typing import Optional
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    """Schema para token de acceso"""
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    """Schema para el payload del token JWT"""
    sub: Optional[int] = None
    exp: Optional[int] = None

class TokenData(BaseModel):
    """Schema para datos del token"""
    email: Optional[EmailStr] = None 