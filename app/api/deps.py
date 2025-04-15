"""
API dependencies
"""
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from app.core.config import settings
from app.core.security import oauth2_scheme
from app.db.database import get_async_db
from app.models.client import Client
from app.services.client_service import ClientService
from app.services.auth import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Re-export get_async_db as get_db for compatibility
get_db = get_async_db

async def get_current_client(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Client:
    """
    Dependency to get current client based on JWT token.
    Validates the token and returns the authenticated client.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = AuthService.decode_token(token)
        if token_data is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
        
    client = await ClientService.get_by_email(db, token_data.sub)
    if client is None:
        raise credentials_exception
    if not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive client"
        )
    return client

async def get_current_active_client(
    current_client: Client = Depends(get_current_client),
) -> Client:
    """
    Dependency to get the current client and verify they are active.
    """
    if not current_client.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive client"
        )
    return current_client

async def get_current_admin(
    current_client: Client = Depends(get_current_client),
) -> Client:
    """
    Dependency to get the current client and verify they are an admin.
    """
    if not current_client.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_client 