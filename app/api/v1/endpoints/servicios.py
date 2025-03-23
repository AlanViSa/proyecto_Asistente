"""
Endpoints para la gestión de servicios

Este módulo proporciona endpoints para:
- Listar todos los servicios disponibles
- Obtener detalles de un servicio específico
- Crear nuevos servicios (solo administradores)
- Actualizar servicios existentes (solo administradores)
- Eliminar servicios (solo administradores)
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_admin
from app.services.servicio import ServicioService
from app.models.admin import Admin
from app.schemas.servicio import (
    Servicio,
    ServicioCreate,
    ServicioUpdate,
    ServicioList
)

router = APIRouter()

@router.get(
    "/",
    response_model=List[ServicioList],
    summary="Listar Servicios",
    description="""
    Obtiene la lista de todos los servicios disponibles.
    
    ## Respuesta
    * Lista de servicios con información básica
    
    ## Errores
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Lista de servicios obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": [{
                        "id": 1,
                        "nombre": "Corte de Cabello",
                        "descripcion": "Corte de cabello básico",
                        "duracion_minutos": 30,
                        "precio": 25.00,
                        "activo": true
                    }]
                }
            }
        }
    }
)
async def get_servicios(
    *,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Obtiene la lista de todos los servicios disponibles.
    """
    servicios = await ServicioService.get_all(db=db)
    return servicios

@router.get(
    "/{servicio_id}",
    response_model=Servicio,
    summary="Obtener Detalles de Servicio",
    description="""
    Obtiene los detalles completos de un servicio específico.
    
    ## Parámetros
    * `servicio_id`: ID del servicio a consultar
    
    ## Respuesta
    * Detalles completos del servicio
    
    ## Errores
    * 404: Servicio no encontrado
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Detalles del servicio obtenidos exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "nombre": "Corte de Cabello",
                        "descripcion": "Corte de cabello básico",
                        "duracion_minutos": 30,
                        "precio": 25.00,
                        "activo": true,
                        "categoria": "Corte",
                        "requisitos": "Sin requisitos especiales"
                    }
                }
            }
        },
        404: {
            "description": "Servicio no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Servicio no encontrado"
                    }
                }
            }
        }
    }
)
async def get_servicio(
    *,
    db: AsyncSession = Depends(get_db),
    servicio_id: int
) -> Any:
    """
    Obtiene un servicio específico por su ID.
    """
    servicio = await ServicioService.get_by_id(db=db, servicio_id=servicio_id)
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado"
        )
    return servicio

@router.post(
    "/",
    response_model=Servicio,
    summary="Crear Nuevo Servicio",
    description="""
    Crea un nuevo servicio en el sistema.
    Solo disponible para administradores.
    
    ## Parámetros
    * `nombre`: Nombre del servicio
    * `descripcion`: Descripción detallada
    * `duracion_minutos`: Duración en minutos
    * `precio`: Precio del servicio
    * `categoria`: Categoría del servicio
    * `requisitos`: Requisitos especiales (opcional)
    
    ## Respuesta
    * Detalles del servicio creado
    
    ## Errores
    * 401: No autenticado
    * 403: No tienes permisos de administrador
    * 400: Datos inválidos
    """,
    responses={
        200: {
            "description": "Servicio creado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "nombre": "Corte de Cabello",
                        "descripcion": "Corte de cabello básico",
                        "duracion_minutos": 30,
                        "precio": 25.00,
                        "activo": true,
                        "categoria": "Corte",
                        "requisitos": "Sin requisitos especiales"
                    }
                }
            }
        }
    }
)
async def create_servicio(
    *,
    db: AsyncSession = Depends(get_db),
    servicio_in: ServicioCreate,
    current_admin: Admin = Depends(get_current_admin)
) -> Any:
    """
    Crea un nuevo servicio.
    Solo disponible para administradores.
    """
    servicio = await ServicioService.create(db=db, servicio_in=servicio_in)
    return servicio

@router.put(
    "/{servicio_id}",
    response_model=Servicio,
    summary="Actualizar Servicio",
    description="""
    Actualiza un servicio existente.
    Solo disponible para administradores.
    
    ## Parámetros
    * `servicio_id`: ID del servicio a actualizar
    * `nombre`: Nuevo nombre (opcional)
    * `descripcion`: Nueva descripción (opcional)
    * `duracion_minutos`: Nueva duración (opcional)
    * `precio`: Nuevo precio (opcional)
    * `categoria`: Nueva categoría (opcional)
    * `requisitos`: Nuevos requisitos (opcional)
    * `activo`: Estado de activación (opcional)
    
    ## Respuesta
    * Detalles actualizados del servicio
    
    ## Errores
    * 404: Servicio no encontrado
    * 401: No autenticado
    * 403: No tienes permisos de administrador
    * 400: Datos inválidos
    """,
    responses={
        200: {
            "description": "Servicio actualizado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "nombre": "Corte de Cabello Premium",
                        "descripcion": "Corte de cabello básico con acabado premium",
                        "duracion_minutos": 45,
                        "precio": 35.00,
                        "activo": true,
                        "categoria": "Corte",
                        "requisitos": "Sin requisitos especiales"
                    }
                }
            }
        }
    }
)
async def update_servicio(
    *,
    db: AsyncSession = Depends(get_db),
    servicio_id: int,
    servicio_in: ServicioUpdate,
    current_admin: Admin = Depends(get_current_admin)
) -> Any:
    """
    Actualiza un servicio existente.
    Solo disponible para administradores.
    """
    servicio = await ServicioService.get_by_id(db=db, servicio_id=servicio_id)
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado"
        )
    
    servicio = await ServicioService.update(
        db=db,
        servicio=servicio,
        servicio_in=servicio_in
    )
    return servicio

@router.delete(
    "/{servicio_id}",
    response_model=Servicio,
    summary="Eliminar Servicio",
    description="""
    Elimina un servicio existente.
    Solo disponible para administradores.
    
    ## Parámetros
    * `servicio_id`: ID del servicio a eliminar
    
    ## Respuesta
    * Detalles del servicio eliminado
    
    ## Errores
    * 404: Servicio no encontrado
    * 401: No autenticado
    * 403: No tienes permisos de administrador
    * 400: No se puede eliminar un servicio con citas asociadas
    """,
    responses={
        200: {
            "description": "Servicio eliminado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "nombre": "Corte de Cabello",
                        "descripcion": "Corte de cabello básico",
                        "duracion_minutos": 30,
                        "precio": 25.00,
                        "activo": false,
                        "categoria": "Corte",
                        "requisitos": "Sin requisitos especiales"
                    }
                }
            }
        }
    }
)
async def delete_servicio(
    *,
    db: AsyncSession = Depends(get_db),
    servicio_id: int,
    current_admin: Admin = Depends(get_current_admin)
) -> Any:
    """
    Elimina un servicio existente.
    Solo disponible para administradores.
    """
    servicio = await ServicioService.get_by_id(db=db, servicio_id=servicio_id)
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado"
        )
    
    # Verificar si hay citas asociadas
    if await ServicioService.has_citas(db=db, servicio_id=servicio_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar un servicio con citas asociadas"
        )
    
    await ServicioService.delete(db=db, servicio=servicio)
    return servicio 