"""
Endpoints para la gestión de notificaciones

Este módulo proporciona endpoints para:
- Listar notificaciones del cliente
- Obtener detalles de una notificación específica
- Marcar notificaciones como leídas
- Eliminar notificaciones
- Enviar notificaciones (solo administradores)
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_cliente, get_current_admin
from app.services.notificacion import NotificacionService
from app.models.cliente import Cliente
from app.models.admin import Admin
from app.schemas.notificacion import (
    Notificacion,
    NotificacionCreate,
    NotificacionList
)

router = APIRouter()

@router.get(
    "/",
    response_model=List[NotificacionList],
    summary="Listar Notificaciones",
    description="""
    Obtiene la lista de notificaciones del cliente actual.
    
    ## Respuesta
    * Lista de notificaciones con información básica
    
    ## Errores
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Lista de notificaciones obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": [{
                        "id": 1,
                        "titulo": "Recordatorio de Cita",
                        "mensaje": "Tienes una cita programada para mañana",
                        "tipo": "RECORDATORIO",
                        "leida": false,
                        "fecha_creacion": "2024-03-19T10:00:00"
                    }]
                }
            }
        }
    }
)
async def get_notificaciones(
    *,
    db: AsyncSession = Depends(get_db),
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Obtiene la lista de notificaciones del cliente actual.
    """
    notificaciones = await NotificacionService.get_by_cliente(
        db=db,
        cliente_id=current_cliente.id
    )
    return notificaciones

@router.get(
    "/{notificacion_id}",
    response_model=Notificacion,
    summary="Obtener Detalles de Notificación",
    description="""
    Obtiene los detalles completos de una notificación específica.
    
    ## Parámetros
    * `notificacion_id`: ID de la notificación a consultar
    
    ## Respuesta
    * Detalles completos de la notificación
    
    ## Errores
    * 404: Notificación no encontrada
    * 403: No tienes permiso para ver esta notificación
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Detalles de la notificación obtenidos exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "titulo": "Recordatorio de Cita",
                        "mensaje": "Tienes una cita programada para mañana a las 10:00",
                        "tipo": "RECORDATORIO",
                        "leida": false,
                        "fecha_creacion": "2024-03-19T10:00:00",
                        "cliente_id": 1,
                        "cita_id": 1
                    }
                }
            }
        },
        404: {
            "description": "Notificación no encontrada",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Notificación no encontrada"
                    }
                }
            }
        }
    }
)
async def get_notificacion(
    *,
    db: AsyncSession = Depends(get_db),
    notificacion_id: int,
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Obtiene una notificación específica por su ID.
    Solo se puede acceder a las notificaciones propias.
    """
    notificacion = await NotificacionService.get_by_id(
        db=db,
        notificacion_id=notificacion_id
    )
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    if notificacion.cliente_id != current_cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esta notificación"
        )
    return notificacion

@router.patch(
    "/{notificacion_id}/leer",
    response_model=Notificacion,
    summary="Marcar Notificación como Leída",
    description="""
    Marca una notificación como leída.
    
    ## Parámetros
    * `notificacion_id`: ID de la notificación a marcar
    
    ## Respuesta
    * Detalles de la notificación actualizada
    
    ## Errores
    * 404: Notificación no encontrada
    * 403: No tienes permiso para modificar esta notificación
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Notificación marcada como leída exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "titulo": "Recordatorio de Cita",
                        "mensaje": "Tienes una cita programada para mañana",
                        "tipo": "RECORDATORIO",
                        "leida": true,
                        "fecha_creacion": "2024-03-19T10:00:00",
                        "fecha_lectura": "2024-03-19T11:00:00"
                    }
                }
            }
        }
    }
)
async def marcar_leida(
    *,
    db: AsyncSession = Depends(get_db),
    notificacion_id: int,
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Marca una notificación como leída.
    Solo se pueden marcar notificaciones propias.
    """
    notificacion = await NotificacionService.get_by_id(
        db=db,
        notificacion_id=notificacion_id
    )
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    if notificacion.cliente_id != current_cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar esta notificación"
        )
    
    notificacion = await NotificacionService.marcar_leida(
        db=db,
        notificacion=notificacion
    )
    return notificacion

@router.delete(
    "/{notificacion_id}",
    response_model=Notificacion,
    summary="Eliminar Notificación",
    description="""
    Elimina una notificación existente.
    
    ## Parámetros
    * `notificacion_id`: ID de la notificación a eliminar
    
    ## Respuesta
    * Detalles de la notificación eliminada
    
    ## Errores
    * 404: Notificación no encontrada
    * 403: No tienes permiso para eliminar esta notificación
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Notificación eliminada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "titulo": "Recordatorio de Cita",
                        "mensaje": "Tienes una cita programada para mañana",
                        "tipo": "RECORDATORIO",
                        "leida": true,
                        "fecha_creacion": "2024-03-19T10:00:00",
                        "fecha_lectura": "2024-03-19T11:00:00"
                    }
                }
            }
        }
    }
)
async def delete_notificacion(
    *,
    db: AsyncSession = Depends(get_db),
    notificacion_id: int,
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Elimina una notificación existente.
    Solo se pueden eliminar notificaciones propias.
    """
    notificacion = await NotificacionService.get_by_id(
        db=db,
        notificacion_id=notificacion_id
    )
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    if notificacion.cliente_id != current_cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar esta notificación"
        )
    
    await NotificacionService.delete(db=db, notificacion=notificacion)
    return notificacion

@router.post(
    "/enviar",
    response_model=Notificacion,
    summary="Enviar Notificación",
    description="""
    Envía una nueva notificación a un cliente.
    Solo disponible para administradores.
    
    ## Parámetros
    * `cliente_id`: ID del cliente destinatario
    * `titulo`: Título de la notificación
    * `mensaje`: Contenido de la notificación
    * `tipo`: Tipo de notificación (RECORDATORIO, SISTEMA, PROMOCION)
    * `cita_id`: ID de la cita asociada (opcional)
    
    ## Respuesta
    * Detalles de la notificación enviada
    
    ## Errores
    * 404: Cliente no encontrado
    * 401: No autenticado
    * 403: No tienes permisos de administrador
    * 400: Datos inválidos
    """,
    responses={
        200: {
            "description": "Notificación enviada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "titulo": "Recordatorio de Cita",
                        "mensaje": "Tienes una cita programada para mañana",
                        "tipo": "RECORDATORIO",
                        "leida": false,
                        "fecha_creacion": "2024-03-19T10:00:00",
                        "cliente_id": 1,
                        "cita_id": 1
                    }
                }
            }
        }
    }
)
async def enviar_notificacion(
    *,
    db: AsyncSession = Depends(get_db),
    notificacion_in: NotificacionCreate,
    current_admin: Admin = Depends(get_current_admin)
) -> Any:
    """
    Envía una nueva notificación a un cliente.
    Solo disponible para administradores.
    """
    notificacion = await NotificacionService.create(
        db=db,
        notificacion_in=notificacion_in
    )
    return notificacion 