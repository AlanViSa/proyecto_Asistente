"""
Schemas for authentication tokens.
"""
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """
    Schema for the token response sent to the client after login.
    """
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    Schema for the JWT token payload.
    """
    sub: Optional[str] = None
    exp: int = 0


class TokenRequest(BaseModel):
    """
    Schema for the token request received from the client during login.
    """
    username: str  # Actually the email in our case
    password: str 