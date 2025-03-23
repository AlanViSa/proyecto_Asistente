"""
Endpoints para la autenticación de clientes

Este módulo proporciona endpoints para:
- Inicio de sesión de clientes
- Registro de nuevos clientes
- Verificación de tokens JWT
"""
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_cliente
from app.core.config import settings
from app.services.auth import AuthService
from app.services.cliente import ClienteService
from app.schemas.cliente import ClienteCreate, Cliente
from app.schemas.token import Token

router = APIRouter()

@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar Sesión",
    description="""
    Endpoint para autenticar un cliente y obtener un token JWT.
    
    ## Parámetros
    * `username`: Email del cliente
    * `password`: Contraseña del cliente
    
    ## Respuesta
    * `access_token`: Token JWT para autenticación
    * `token_type`: Tipo de token (siempre "bearer")
    
    ## Errores
    * 401: Credenciales incorrectas
    * 400: Cliente inactivo
    """,
    responses={
        200: {
            "description": "Login exitoso",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "Credenciales incorrectas",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email o contraseña incorrectos"
                    }
                }
            }
        },
        400: {
            "description": "Cliente inactivo",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cliente inactivo"
                    }
                }
            }
        }
    }
)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Endpoint para autenticar un cliente y obtener un token JWT
    """
    cliente = await AuthService.authenticate_cliente(
        db, form_data.username, form_data.password
    )
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not cliente.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cliente inactivo"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": cliente.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post(
    "/registro",
    response_model=Cliente,
    summary="Registrar Cliente",
    description="""
    Endpoint para registrar un nuevo cliente en el sistema.
    
    ## Parámetros
    * `email`: Email del cliente (único)
    * `password`: Contraseña del cliente
    * `nombre`: Nombre completo del cliente
    * `telefono`: Teléfono del cliente (único)
    * `fecha_nacimiento`: Fecha de nacimiento (opcional)
    
    ## Respuesta
    * Datos del cliente registrado
    
    ## Errores
    * 400: Email o teléfono ya registrado
    * 422: Datos inválidos
    """,
    responses={
        200: {
            "description": "Cliente registrado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "cliente@example.com",
                        "nombre": "Juan Pérez",
                        "telefono": "+1234567890",
                        "fecha_nacimiento": "1990-01-01",
                        "activo": true
                    }
                }
            }
        },
        400: {
            "description": "Email o teléfono ya registrado",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Ya existe un cliente registrado con este email"
                    }
                }
            }
        }
    }
)
async def registro(
    *,
    db: AsyncSession = Depends(get_db),
    cliente_in: ClienteCreate
) -> Any:
    """
    Endpoint para registrar un nuevo cliente
    """
    # Verificar si ya existe un cliente con ese email
    cliente = await ClienteService.get_by_email(db, email=cliente_in.email)
    if cliente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un cliente registrado con este email"
        )
    
    # Verificar si ya existe un cliente con ese teléfono
    cliente = await ClienteService.get_by_telefono(db, telefono=cliente_in.telefono)
    if cliente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un cliente registrado con este teléfono"
        )
    
    cliente = await ClienteService.create(db, cliente_in)
    return cliente

@router.post(
    "/test-token",
    response_model=Cliente,
    summary="Probar Token",
    description="""
    Endpoint para verificar la validez de un token JWT.
    
    ## Headers
    * `Authorization`: Bearer token JWT
    
    ## Respuesta
    * Datos del cliente autenticado
    
    ## Errores
    * 401: Token inválido o expirado
    """,
    responses={
        200: {
            "description": "Token válido",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "cliente@example.com",
                        "nombre": "Juan Pérez",
                        "telefono": "+1234567890",
                        "fecha_nacimiento": "1990-01-01",
                        "activo": true
                    }
                }
            }
        },
        401: {
            "description": "Token inválido o expirado",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Could not validate credentials"
                    }
                }
            }
        }
    }
)
async def test_token(
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Endpoint para probar el token JWT
    """
    return current_cliente 