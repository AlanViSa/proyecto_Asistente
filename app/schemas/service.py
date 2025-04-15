"""
Service schema definitions for API data validation and serialization
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class ServiceBase(BaseModel):
    """Base service schema with common attributes"""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    duration_minutes: int = Field(..., gt=0, le=480)  # Max 8 hours

    @validator('price')
    def validate_price(cls, v):
        """Validate price is positive and properly formatted"""
        if v <= 0:
            raise ValueError("Price must be greater than zero")
        return round(v, 2)  # Round to 2 decimal places for currency


class ServiceCreate(ServiceBase):
    """Schema for service creation"""
    pass


class ServiceUpdate(BaseModel):
    """Schema for service update with optional fields"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    duration_minutes: Optional[int] = Field(None, gt=0, le=480)
    is_active: Optional[bool] = None

    @validator('price')
    def validate_price(cls, v):
        """Validate price is positive and properly formatted"""
        if v is not None and v <= 0:
            raise ValueError("Price must be greater than zero")
        return round(v, 2) if v is not None else v


class ServiceInDB(ServiceBase):
    """Schema for service in database with additional fields"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class Service(ServiceInDB):
    """Schema for service response"""
    pass 