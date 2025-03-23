"""
Endpoints para la gestión de citas

Este módulo proporciona endpoints para:
- Listar citas del cliente
- Obtener detalles de una cita específica
- Crear nuevas citas
- Actualizar citas existentes
- Eliminar citas
- Confirmar citas pendientes
- Cancelar citas
- Filtrar citas por fecha
"""
from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_cliente
from app.services.cita import CitaService
from app.models.cliente import Cliente
from app.models.cita import EstadoCita
from app.schemas.cita import (
    Cita,
    CitaCreate,
    CitaUpdate,
    CitaList
)

router = APIRouter()

@router.get(
    "/",
    response_model=List[CitaList],
    summary="Listar Citas",
    description="""
    Obtiene la lista de citas del cliente actual.
    
    ## Parámetros
    * `skip`: Número de registros a saltar (paginación)
    * `limit`: Número máximo de registros a devolver (máx. 100)
    * `estado`: Filtrar por estado de la cita (PENDIENTE, CONFIRMADA, COMPLETADA, CANCELADA)
    
    ## Respuesta
    * Lista de citas con información básica
    
    ## Errores
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Lista de citas obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": [{
                        "id": 1,
                        "fecha_hora": "2024-03-20T10:00:00",
                        "duracion_minutos": 30,
                        "estado": "PENDIENTE",
                        "servicio_id": 1
                    }]
                }
            }
        }
    }
)
async def get_citas(
    *,
    db: AsyncSession = Depends(get_db),
    current_cliente: Cliente = Depends(get_current_cliente),
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    estado: EstadoCita = None
) -> Any:
    """
    Obtiene la lista de citas del cliente actual.
    Se puede filtrar por estado y usar paginación.
    """
    citas = await CitaService.get_by_cliente(
        db=db,
        cliente_id=current_cliente.id,
        skip=skip,
        limit=limit,
        estado=estado
    )
    return citas

@router.get(
    "/{cita_id}",
    response_model=Cita,
    summary="Obtener Detalles de Cita",
    description="""
    Obtiene los detalles completos de una cita específica.
    
    ## Parámetros
    * `cita_id`: ID de la cita a consultar
    
    ## Respuesta
    * Detalles completos de la cita
    
    ## Errores
    * 404: Cita no encontrada
    * 403: No tienes permiso para ver esta cita
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Detalles de la cita obtenidos exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "fecha_hora": "2024-03-20T10:00:00",
                        "duracion_minutos": 30,
                        "estado": "PENDIENTE",
                        "servicio_id": 1,
                        "cliente_id": 1,
                        "notas": "Primera consulta"
                    }
                }
            }
        },
        404: {
            "description": "Cita no encontrada",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cita no encontrada"
                    }
                }
            }
        }
    }
)
async def get_cita(
    *,
    db: AsyncSession = Depends(get_db),
    cita_id: int,
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Obtiene una cita específica por su ID.
    Solo se puede acceder a las citas propias.
    """
    cita = await CitaService.get_by_id(db=db, cita_id=cita_id)
    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cita no encontrada"
        )
    if cita.cliente_id != current_cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esta cita"
        )
    return cita

@router.post(
    "/",
    response_model=Cita,
    summary="Crear Nueva Cita",
    description="""
    Crea una nueva cita para el cliente actual.
    
    ## Parámetros
    * `fecha_hora`: Fecha y hora de la cita
    * `duracion_minutos`: Duración en minutos
    * `servicio_id`: ID del servicio a realizar
    * `notas`: Notas adicionales (opcional)
    
    ## Respuesta
    * Detalles de la cita creada
    
    ## Errores
    * 400: Horario no disponible
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Cita creada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "fecha_hora": "2024-03-20T10:00:00",
                        "duracion_minutos": 30,
                        "estado": "PENDIENTE",
                        "servicio_id": 1,
                        "cliente_id": 1,
                        "notas": "Primera consulta"
                    }
                }
            }
        },
        400: {
            "description": "Horario no disponible",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "El horario seleccionado no está disponible"
                    }
                }
            }
        }
    }
)
async def create_cita(
    *,
    db: AsyncSession = Depends(get_db),
    cita_in: CitaCreate,
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Crea una nueva cita para el cliente actual.
    """
    # Verificar disponibilidad del horario
    is_available = await CitaService.check_availability(
        db=db,
        fecha_hora=cita_in.fecha_hora,
        duracion_minutos=cita_in.duracion_minutos
    )
    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El horario seleccionado no está disponible"
        )
    
    cita = await CitaService.create(
        db=db,
        cita_in=cita_in,
        cliente_id=current_cliente.id
    )
    return cita

@router.put(
    "/{cita_id}",
    response_model=Cita,
    summary="Actualizar Cita",
    description="""
    Actualiza una cita existente.
    
    ## Parámetros
    * `cita_id`: ID de la cita a actualizar
    * `fecha_hora`: Nueva fecha y hora (opcional)
    * `duracion_minutos`: Nueva duración en minutos (opcional)
    * `servicio_id`: Nuevo ID de servicio (opcional)
    * `notas`: Nuevas notas (opcional)
    
    ## Respuesta
    * Detalles actualizados de la cita
    
    ## Errores
    * 404: Cita no encontrada
    * 403: No tienes permiso para modificar esta cita
    * 400: Cita completada o cancelada
    * 400: Horario no disponible
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Cita actualizada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "fecha_hora": "2024-03-20T11:00:00",
                        "duracion_minutos": 45,
                        "estado": "PENDIENTE",
                        "servicio_id": 2,
                        "cliente_id": 1,
                        "notas": "Actualización de notas"
                    }
                }
            }
        }
    }
)
async def update_cita(
    *,
    db: AsyncSession = Depends(get_db),
    cita_id: int,
    cita_in: CitaUpdate,
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Actualiza una cita existente.
    Solo se pueden actualizar citas propias que no estén completadas o canceladas.
    """
    cita = await CitaService.get_by_id(db=db, cita_id=cita_id)
    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cita no encontrada"
        )
    if cita.cliente_id != current_cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar esta cita"
        )
    if cita.estado in [EstadoCita.COMPLETADA, EstadoCita.CANCELADA]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede modificar una cita {cita.estado.lower()}"
        )
    
    # Si se está actualizando la fecha/hora o duración, verificar disponibilidad
    if cita_in.fecha_hora or cita_in.duracion_minutos:
        is_available = await CitaService.check_availability(
            db=db,
            fecha_hora=cita_in.fecha_hora or cita.fecha_hora,
            duracion_minutos=cita_in.duracion_minutos or cita.duracion_minutos,
            exclude_cita_id=cita_id
        )
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El horario seleccionado no está disponible"
            )
    
    cita = await CitaService.update(
        db=db,
        cita=cita,
        cita_in=cita_in
    )
    return cita

@router.delete(
    "/{cita_id}",
    response_model=Cita,
    summary="Eliminar Cita",
    description="""
    Elimina una cita existente.
    
    ## Parámetros
    * `cita_id`: ID de la cita a eliminar
    
    ## Respuesta
    * Detalles de la cita eliminada
    
    ## Errores
    * 404: Cita no encontrada
    * 403: No tienes permiso para eliminar esta cita
    * 400: Cita completada
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Cita eliminada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "fecha_hora": "2024-03-20T10:00:00",
                        "duracion_minutos": 30,
                        "estado": "CANCELADA",
                        "servicio_id": 1,
                        "cliente_id": 1,
                        "notas": "Cita eliminada"
                    }
                }
            }
        }
    }
)
async def delete_cita(
    *,
    db: AsyncSession = Depends(get_db),
    cita_id: int,
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Elimina una cita.
    Solo se pueden eliminar citas propias que no estén completadas.
    """
    cita = await CitaService.get_by_id(db=db, cita_id=cita_id)
    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cita no encontrada"
        )
    if cita.cliente_id != current_cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar esta cita"
        )
    if cita.estado == EstadoCita.COMPLETADA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar una cita completada"
        )
    
    await CitaService.delete(db=db, cita=cita)
    return cita

@router.patch(
    "/{cita_id}/confirmar",
    response_model=Cita,
    summary="Confirmar Cita",
    description="""
    Confirma una cita pendiente.
    
    ## Parámetros
    * `cita_id`: ID de la cita a confirmar
    
    ## Respuesta
    * Detalles de la cita confirmada
    
    ## Errores
    * 404: Cita no encontrada
    * 403: No tienes permiso para confirmar esta cita
    * 400: Cita no está pendiente
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Cita confirmada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "fecha_hora": "2024-03-20T10:00:00",
                        "duracion_minutos": 30,
                        "estado": "CONFIRMADA",
                        "servicio_id": 1,
                        "cliente_id": 1,
                        "notas": "Cita confirmada"
                    }
                }
            }
        }
    }
)
async def confirmar_cita(
    *,
    db: AsyncSession = Depends(get_db),
    cita_id: int,
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Confirma una cita pendiente.
    Solo se pueden confirmar citas propias que estén pendientes.
    """
    cita = await CitaService.get_by_id(db=db, cita_id=cita_id)
    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cita no encontrada"
        )
    if cita.cliente_id != current_cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para confirmar esta cita"
        )
    if cita.estado != EstadoCita.PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede confirmar una cita {cita.estado.lower()}"
        )
    
    cita = await CitaService.confirm(db=db, cita=cita)
    return cita

@router.patch(
    "/{cita_id}/cancelar",
    response_model=Cita,
    summary="Cancelar Cita",
    description="""
    Cancela una cita existente.
    
    ## Parámetros
    * `cita_id`: ID de la cita a cancelar
    
    ## Respuesta
    * Detalles de la cita cancelada
    
    ## Errores
    * 404: Cita no encontrada
    * 403: No tienes permiso para cancelar esta cita
    * 400: Cita completada o ya cancelada
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Cita cancelada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "fecha_hora": "2024-03-20T10:00:00",
                        "duracion_minutos": 30,
                        "estado": "CANCELADA",
                        "servicio_id": 1,
                        "cliente_id": 1,
                        "notas": "Cita cancelada"
                    }
                }
            }
        }
    }
)
async def cancelar_cita(
    *,
    db: AsyncSession = Depends(get_db),
    cita_id: int,
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Cancela una cita.
    Solo se pueden cancelar citas propias que no estén completadas o ya canceladas.
    """
    cita = await CitaService.get_by_id(db=db, cita_id=cita_id)
    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cita no encontrada"
        )
    if cita.cliente_id != current_cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para cancelar esta cita"
        )
    if cita.estado in [EstadoCita.COMPLETADA, EstadoCita.CANCELADA]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede cancelar una cita {cita.estado.lower()}"
        )
    
    cita = await CitaService.cancel(db=db, cita=cita)
    return cita

@router.get(
    "/fecha/{fecha}",
    response_model=List[CitaList],
    summary="Listar Citas por Fecha",
    description="""
    Obtiene todas las citas para una fecha específica.
    
    ## Parámetros
    * `fecha`: Fecha a consultar (formato: YYYY-MM-DD)
    
    ## Respuesta
    * Lista de citas para la fecha especificada
    
    ## Errores
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Lista de citas obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": [{
                        "id": 1,
                        "fecha_hora": "2024-03-20T10:00:00",
                        "duracion_minutos": 30,
                        "estado": "PENDIENTE",
                        "servicio_id": 1
                    }]
                }
            }
        }
    }
)
async def get_citas_by_fecha(
    *,
    db: AsyncSession = Depends(get_db),
    fecha: datetime,
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Obtiene todas las citas para una fecha específica.
    Solo devuelve las citas del cliente actual.
    """
    citas = await CitaService.get_by_fecha(
        db=db,
        fecha=fecha,
        cliente_id=current_cliente.id
    )
    return citas 