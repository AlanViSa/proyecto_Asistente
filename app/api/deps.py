"""
Dependencias para la API
"""
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from app.core.config import settings
from app.db.database import get_async_db
from app.services.auth import AuthService
from app.services.cliente import ClienteService
from app.models.cliente import Cliente

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Reexportar get_async_db como get_db para mantener compatibilidad
get_db = get_async_db

async def get_current_cliente(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Cliente:
    """
    Dependencia para obtener el cliente actual basado en el token JWT.
    Valida el token y retorna el cliente autenticado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = AuthService.decode_token(token)
        if token_data is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
        
    cliente = await ClienteService.get_by_email(db, token_data.sub)
    if cliente is None:
        raise credentials_exception
    if not cliente.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cliente inactivo"
        )
    return cliente

async def get_current_active_cliente(
    current_cliente: Cliente = Depends(get_current_cliente),
) -> Cliente:
    """
    Dependencia para obtener el cliente actual y verificar que esté activo.
    """
    if not current_cliente.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cliente inactivo"
        )
    return current_cliente 