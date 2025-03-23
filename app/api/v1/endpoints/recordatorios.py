"""
Endpoints para la gestión de recordatorios de citas

Este módulo proporciona endpoints para:
- Listar recordatorios del cliente
- Obtener detalles de un recordatorio específico
- Crear nuevos recordatorios
- Actualizar recordatorios existentes
- Eliminar recordatorios
- Marcar recordatorios como enviados
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_cliente, get_current_admin
from app.services.recordatorio import RecordatorioService
from app.models.cliente import Cliente
from app.models.admin import Admin
from app.schemas.recordatorio import (
    Recordatorio,
    RecordatorioCreate,
    RecordatorioUpdate,
    RecordatorioList
)

router = APIRouter()

@router.get(
    "/",
    response_model=List[RecordatorioList],
    summary="Listar Recordatorios",
    description="""
    Obtiene la lista de recordatorios del cliente actual.
    
    ## Respuesta
    * Lista de recordatorios con información básica
    
    ## Errores
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Lista de recordatorios obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": [{
                        "id": 1,
                        "cita_id": 1,
                        "tipo": "EMAIL",
                        "estado": "PENDIENTE",
                        "fecha_envio_programada": "2024-03-19T09:00:00"
                    }]
                }
            }
        }
    }
)
async def get_recordatorios(
    *,
    db: AsyncSession = Depends(get_db),
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Obtiene la lista de recordatorios del cliente actual.
    """
    recordatorios = await RecordatorioService.get_by_cliente(
        db=db,
        cliente_id=current_cliente.id
    )
    return recordatorios

@router.get(
    "/{recordatorio_id}",
    response_model=Recordatorio,
    summary="Obtener Detalles de Recordatorio",
    description="""
    Obtiene los detalles completos de un recordatorio específico.
    
    ## Parámetros
    * `recordatorio_id`: ID del recordatorio a consultar
    
    ## Respuesta
    * Detalles completos del recordatorio
    
    ## Errores
    * 404: Recordatorio no encontrado
    * 403: No tienes permiso para ver este recordatorio
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Detalles del recordatorio obtenidos exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "cita_id": 1,
                        "cliente_id": 1,
                        "tipo": "EMAIL",
                        "estado": "PENDIENTE",
                        "fecha_envio_programada": "2024-03-19T09:00:00",
                        "fecha_envio": None,
                        "contenido": "Recordatorio de su cita para mañana",
                        "destinatario": "cliente@example.com"
                    }
                }
            }
        },
        404: {
            "description": "Recordatorio no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Recordatorio no encontrado"
                    }
                }
            }
        }
    }
)
async def get_recordatorio(
    *,
    db: AsyncSession = Depends(get_db),
    recordatorio_id: int,
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Obtiene un recordatorio específico por su ID.
    Solo se puede acceder a los recordatorios propios.
    """
    recordatorio = await RecordatorioService.get_by_id(
        db=db,
        recordatorio_id=recordatorio_id
    )
    if not recordatorio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )
    if recordatorio.cliente_id != current_cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este recordatorio"
        )
    return recordatorio

@router.post(
    "/",
    response_model=Recordatorio,
    summary="Crear Nuevo Recordatorio",
    description="""
    Crea un nuevo recordatorio para una cita.
    Solo disponible para administradores.
    
    ## Parámetros
    * `cita_id`: ID de la cita asociada
    * `tipo`: Tipo de recordatorio (EMAIL, SMS, PUSH)
    * `fecha_envio_programada`: Fecha y hora programada para el envío
    * `contenido`: Contenido del recordatorio
    * `destinatario`: Email o teléfono del destinatario
    
    ## Respuesta
    * Detalles del recordatorio creado
    
    ## Errores
    * 401: No autenticado
    * 403: No tienes permisos de administrador
    * 400: Datos inválidos
    * 404: Cita no encontrada
    """,
    responses={
        200: {
            "description": "Recordatorio creado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "cita_id": 1,
                        "cliente_id": 1,
                        "tipo": "EMAIL",
                        "estado": "PENDIENTE",
                        "fecha_envio_programada": "2024-03-19T09:00:00",
                        "fecha_envio": None,
                        "contenido": "Recordatorio de su cita para mañana",
                        "destinatario": "cliente@example.com"
                    }
                }
            }
        }
    }
)
async def create_recordatorio(
    *,
    db: AsyncSession = Depends(get_db),
    recordatorio_in: RecordatorioCreate,
    current_admin: Admin = Depends(get_current_admin)
) -> Any:
    """
    Crea un nuevo recordatorio.
    Solo disponible para administradores.
    """
    recordatorio = await RecordatorioService.create(
        db=db,
        recordatorio_in=recordatorio_in
    )
    return recordatorio

@router.put(
    "/{recordatorio_id}",
    response_model=Recordatorio,
    summary="Actualizar Recordatorio",
    description="""
    Actualiza un recordatorio existente.
    Solo disponible para administradores.
    
    ## Parámetros
    * `recordatorio_id`: ID del recordatorio a actualizar
    * `tipo`: Nuevo tipo de recordatorio (opcional)
    * `fecha_envio_programada`: Nueva fecha y hora programada (opcional)
    * `contenido`: Nuevo contenido (opcional)
    * `destinatario`: Nuevo destinatario (opcional)
    
    ## Respuesta
    * Detalles actualizados del recordatorio
    
    ## Errores
    * 404: Recordatorio no encontrado
    * 401: No autenticado
    * 403: No tienes permisos de administrador
    * 400: Datos inválidos
    """,
    responses={
        200: {
            "description": "Recordatorio actualizado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "cita_id": 1,
                        "cliente_id": 1,
                        "tipo": "SMS",
                        "estado": "PENDIENTE",
                        "fecha_envio_programada": "2024-03-19T10:00:00",
                        "fecha_envio": None,
                        "contenido": "Recordatorio actualizado de su cita",
                        "destinatario": "+1234567890"
                    }
                }
            }
        }
    }
)
async def update_recordatorio(
    *,
    db: AsyncSession = Depends(get_db),
    recordatorio_id: int,
    recordatorio_in: RecordatorioUpdate,
    current_admin: Admin = Depends(get_current_admin)
) -> Any:
    """
    Actualiza un recordatorio existente.
    Solo disponible para administradores.
    """
    recordatorio = await RecordatorioService.get_by_id(
        db=db,
        recordatorio_id=recordatorio_id
    )
    if not recordatorio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )
    
    recordatorio = await RecordatorioService.update(
        db=db,
        recordatorio=recordatorio,
        recordatorio_in=recordatorio_in
    )
    return recordatorio

@router.delete(
    "/{recordatorio_id}",
    response_model=Recordatorio,
    summary="Eliminar Recordatorio",
    description="""
    Elimina un recordatorio existente.
    Solo disponible para administradores.
    
    ## Parámetros
    * `recordatorio_id`: ID del recordatorio a eliminar
    
    ## Respuesta
    * Detalles del recordatorio eliminado
    
    ## Errores
    * 404: Recordatorio no encontrado
    * 401: No autenticado
    * 403: No tienes permisos de administrador
    """,
    responses={
        200: {
            "description": "Recordatorio eliminado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "cita_id": 1,
                        "cliente_id": 1,
                        "tipo": "EMAIL",
                        "estado": "CANCELADO",
                        "fecha_envio_programada": "2024-03-19T09:00:00",
                        "fecha_envio": None,
                        "contenido": "Recordatorio de su cita para mañana",
                        "destinatario": "cliente@example.com"
                    }
                }
            }
        }
    }
)
async def delete_recordatorio(
    *,
    db: AsyncSession = Depends(get_db),
    recordatorio_id: int,
    current_admin: Admin = Depends(get_current_admin)
) -> Any:
    """
    Elimina un recordatorio existente.
    Solo disponible para administradores.
    """
    recordatorio = await RecordatorioService.get_by_id(
        db=db,
        recordatorio_id=recordatorio_id
    )
    if not recordatorio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )
    
    await RecordatorioService.delete(db=db, recordatorio=recordatorio)
    return recordatorio

@router.patch(
    "/{recordatorio_id}/marcar-enviado",
    response_model=Recordatorio,
    summary="Marcar Recordatorio como Enviado",
    description="""
    Marca un recordatorio como enviado.
    Solo disponible para administradores.
    
    ## Parámetros
    * `recordatorio_id`: ID del recordatorio a marcar
    
    ## Respuesta
    * Detalles del recordatorio actualizado
    
    ## Errores
    * 404: Recordatorio no encontrado
    * 401: No autenticado
    * 403: No tienes permisos de administrador
    * 400: Recordatorio ya enviado
    """,
    responses={
        200: {
            "description": "Recordatorio marcado como enviado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "cita_id": 1,
                        "cliente_id": 1,
                        "tipo": "EMAIL",
                        "estado": "ENVIADO",
                        "fecha_envio_programada": "2024-03-19T09:00:00",
                        "fecha_envio": "2024-03-19T09:00:00",
                        "contenido": "Recordatorio de su cita para mañana",
                        "destinatario": "cliente@example.com"
                    }
                }
            }
        }
    }
)
async def marcar_enviado(
    *,
    db: AsyncSession = Depends(get_db),
    recordatorio_id: int,
    current_admin: Admin = Depends(get_current_admin)
) -> Any:
    """
    Marca un recordatorio como enviado.
    Solo disponible para administradores.
    """
    recordatorio = await RecordatorioService.get_by_id(
        db=db,
        recordatorio_id=recordatorio_id
    )
    if not recordatorio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recordatorio no encontrado"
        )
    if recordatorio.estado == "ENVIADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El recordatorio ya fue enviado"
        )
    
    recordatorio = await RecordatorioService.marcar_enviado(
        db=db,
        recordatorio=recordatorio
    )
    return recordatorio 