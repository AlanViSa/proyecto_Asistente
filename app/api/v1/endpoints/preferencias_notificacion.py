"""
Endpoints para gestionar las preferencias de notificación de los clientes

Este módulo proporciona endpoints para:
- Obtener preferencias de notificación de un cliente
- Crear nuevas preferencias de notificación
- Actualizar preferencias existentes
- Eliminar preferencias
- Crear preferencias por defecto
- Listar clientes sin preferencias configuradas
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.services.preferencias_notificacion import PreferenciasNotificacionService
from app.schemas.preferencias_notificacion import (
    PreferenciasNotificacion,
    PreferenciasNotificacionCreate,
    PreferenciasNotificacionUpdate
)

router = APIRouter()

@router.get(
    "/{cliente_id}",
    response_model=PreferenciasNotificacion,
    summary="Obtener Preferencias de Notificación",
    description="""
    Obtiene las preferencias de notificación de un cliente específico.
    
    ## Parámetros
    * `cliente_id`: ID del cliente a consultar
    
    ## Respuesta
    * Preferencias de notificación del cliente
    
    ## Errores
    * 404: No se encontraron preferencias para este cliente
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Preferencias obtenidas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "cliente_id": 1,
                        "notificaciones_email": true,
                        "notificaciones_sms": true,
                        "notificaciones_push": false,
                        "recordatorios_citas": true,
                        "promociones": false,
                        "horario_notificaciones": {
                            "inicio": "09:00",
                            "fin": "21:00"
                        }
                    }
                }
            }
        },
        404: {
            "description": "Preferencias no encontradas",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No se encontraron preferencias para este cliente"
                    }
                }
            }
        }
    }
)
async def get_preferencias(
    cliente_id: int,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Obtiene las preferencias de notificación de un cliente
    """
    preferencias = await PreferenciasNotificacionService.get_by_cliente(db, cliente_id)
    if not preferencias:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron preferencias para este cliente"
        )
    return preferencias

@router.post(
    "",
    response_model=PreferenciasNotificacion,
    summary="Crear Preferencias de Notificación",
    description="""
    Crea nuevas preferencias de notificación para un cliente.
    
    ## Parámetros
    * `cliente_id`: ID del cliente
    * `notificaciones_email`: Habilitar notificaciones por email
    * `notificaciones_sms`: Habilitar notificaciones por SMS
    * `notificaciones_push`: Habilitar notificaciones push
    * `recordatorios_citas`: Habilitar recordatorios de citas
    * `promociones`: Habilitar notificaciones de promociones
    * `horario_notificaciones`: Horario permitido para notificaciones
    
    ## Respuesta
    * Preferencias creadas
    
    ## Errores
    * 400: Ya existen preferencias para este cliente
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Preferencias creadas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "cliente_id": 1,
                        "notificaciones_email": true,
                        "notificaciones_sms": true,
                        "notificaciones_push": false,
                        "recordatorios_citas": true,
                        "promociones": false,
                        "horario_notificaciones": {
                            "inicio": "09:00",
                            "fin": "21:00"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Preferencias ya existentes",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Ya existen preferencias para este cliente"
                    }
                }
            }
        }
    }
)
async def create_preferencias(
    preferencias_in: PreferenciasNotificacionCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Crea nuevas preferencias de notificación para un cliente
    """
    # Verificar si ya existen preferencias para este cliente
    preferencias_existentes = await PreferenciasNotificacionService.get_by_cliente(
        db, preferencias_in.cliente_id
    )
    if preferencias_existentes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existen preferencias para este cliente"
        )
    
    return await PreferenciasNotificacionService.create(db, preferencias_in)

@router.put(
    "/{cliente_id}",
    response_model=PreferenciasNotificacion,
    summary="Actualizar Preferencias de Notificación",
    description="""
    Actualiza las preferencias de notificación de un cliente.
    
    ## Parámetros
    * `cliente_id`: ID del cliente
    * `notificaciones_email`: Habilitar/deshabilitar notificaciones por email
    * `notificaciones_sms`: Habilitar/deshabilitar notificaciones por SMS
    * `notificaciones_push`: Habilitar/deshabilitar notificaciones push
    * `recordatorios_citas`: Habilitar/deshabilitar recordatorios de citas
    * `promociones`: Habilitar/deshabilitar notificaciones de promociones
    * `horario_notificaciones`: Actualizar horario permitido
    
    ## Respuesta
    * Preferencias actualizadas
    
    ## Errores
    * 404: No se encontraron preferencias para este cliente
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Preferencias actualizadas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "cliente_id": 1,
                        "notificaciones_email": true,
                        "notificaciones_sms": false,
                        "notificaciones_push": true,
                        "recordatorios_citas": true,
                        "promociones": false,
                        "horario_notificaciones": {
                            "inicio": "10:00",
                            "fin": "20:00"
                        }
                    }
                }
            }
        }
    }
)
async def update_preferencias(
    cliente_id: int,
    preferencias_in: PreferenciasNotificacionUpdate,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Actualiza las preferencias de notificación de un cliente
    """
    preferencias = await PreferenciasNotificacionService.get_by_cliente(db, cliente_id)
    if not preferencias:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron preferencias para este cliente"
        )
    
    return await PreferenciasNotificacionService.update(db, preferencias, preferencias_in)

@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar Preferencias de Notificación",
    description="""
    Elimina las preferencias de notificación de un cliente.
    
    ## Parámetros
    * `cliente_id`: ID del cliente
    
    ## Respuesta
    * 204: Preferencias eliminadas exitosamente
    
    ## Errores
    * 404: No se encontraron preferencias para este cliente
    * 401: No autenticado
    """,
    responses={
        204: {
            "description": "Preferencias eliminadas exitosamente"
        },
        404: {
            "description": "Preferencias no encontradas",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No se encontraron preferencias para este cliente"
                    }
                }
            }
        }
    }
)
async def delete_preferencias(
    cliente_id: int,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Elimina las preferencias de notificación de un cliente
    """
    preferencias = await PreferenciasNotificacionService.get_by_cliente(db, cliente_id)
    if not preferencias:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron preferencias para este cliente"
        )
    
    await PreferenciasNotificacionService.delete(db, preferencias)

@router.post(
    "/{cliente_id}/default",
    response_model=PreferenciasNotificacion,
    summary="Crear Preferencias por Defecto",
    description="""
    Crea o recupera las preferencias por defecto para un cliente.
    
    ## Parámetros
    * `cliente_id`: ID del cliente
    
    ## Respuesta
    * Preferencias por defecto
    
    ## Errores
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Preferencias por defecto creadas/recuperadas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "cliente_id": 1,
                        "notificaciones_email": true,
                        "notificaciones_sms": true,
                        "notificaciones_push": true,
                        "recordatorios_citas": true,
                        "promociones": true,
                        "horario_notificaciones": {
                            "inicio": "09:00",
                            "fin": "21:00"
                        }
                    }
                }
            }
        }
    }
)
async def create_default_preferencias(
    cliente_id: int,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Crea o recupera las preferencias por defecto para un cliente
    """
    return await PreferenciasNotificacionService.crear_preferencias_por_defecto(db, cliente_id)

@router.get(
    "/sin-preferencias",
    response_model=List[int],
    summary="Listar Clientes sin Preferencias",
    description="""
    Obtiene la lista de IDs de clientes que no tienen preferencias configuradas.
    
    ## Respuesta
    * Lista de IDs de clientes sin preferencias
    
    ## Errores
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Lista de clientes sin preferencias obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": [1, 2, 3]
                }
            }
        }
    }
)
async def get_clientes_sin_preferencias(
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Obtiene la lista de IDs de clientes que no tienen preferencias configuradas
    """
    return await PreferenciasNotificacionService.get_clientes_sin_preferencias(db) 