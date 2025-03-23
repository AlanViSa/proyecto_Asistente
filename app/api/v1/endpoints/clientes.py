"""
Endpoints para la gestión de clientes

Este módulo proporciona endpoints para:
- Listar clientes (solo administradores)
- Obtener detalles de un cliente específico
- Actualizar datos de cliente
- Eliminar clientes
- Activar/desactivar clientes (solo administradores)
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_cliente, get_current_admin
from app.services.cliente import ClienteService
from app.schemas.cliente import (
    Cliente,
    ClienteCreate,
    ClienteUpdate,
    ClienteInDB,
    ClienteList
)

router = APIRouter()

@router.get(
    "/",
    response_model=List[ClienteList],
    summary="Listar Clientes",
    description="""
    Obtiene la lista de clientes.
    Solo administradores pueden ver todos los clientes.
    Los clientes normales solo pueden verse a sí mismos.
    
    ## Parámetros
    * `skip`: Número de registros a saltar (paginación)
    * `limit`: Número máximo de registros a devolver (máx. 100)
    
    ## Respuesta
    * Lista de clientes con información básica
    
    ## Errores
    * 401: No autenticado
    * 403: No tienes permisos de administrador
    """,
    responses={
        200: {
            "description": "Lista de clientes obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": [{
                        "id": 1,
                        "email": "cliente@example.com",
                        "nombre": "Juan Pérez",
                        "telefono": "+1234567890",
                        "activo": true
                    }]
                }
            }
        }
    }
)
async def get_clientes(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Obtiene la lista de clientes.
    Solo administradores pueden ver todos los clientes.
    Los clientes normales solo pueden verse a sí mismos.
    """
    # TODO: Implementar lógica de administrador
    # Por ahora, cada cliente solo puede verse a sí mismo
    return [current_cliente]

@router.get(
    "/{cliente_id}",
    response_model=ClienteInDB,
    summary="Obtener Cliente",
    description="""
    Obtiene los detalles completos de un cliente específico.
    Solo administradores pueden ver cualquier cliente.
    Los clientes normales solo pueden verse a sí mismos.
    
    ## Parámetros
    * `cliente_id`: ID del cliente a consultar
    
    ## Respuesta
    * Detalles completos del cliente
    
    ## Errores
    * 404: Cliente no encontrado
    * 403: No tienes permiso para ver este cliente
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Detalles del cliente obtenidos exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "cliente@example.com",
                        "nombre": "Juan Pérez",
                        "telefono": "+1234567890",
                        "fecha_nacimiento": "1990-01-01",
                        "activo": true,
                        "fecha_registro": "2024-03-19T10:00:00"
                    }
                }
            }
        },
        404: {
            "description": "Cliente no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cliente no encontrado"
                    }
                }
            }
        }
    }
)
async def get_cliente(
    cliente_id: int,
    db: AsyncSession = Depends(get_db),
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Obtiene un cliente por su ID.
    Solo administradores pueden ver cualquier cliente.
    Los clientes normales solo pueden verse a sí mismos.
    """
    # TODO: Implementar lógica de administrador
    if cliente_id != current_cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este cliente"
        )
    return current_cliente

@router.put(
    "/{cliente_id}",
    response_model=Cliente,
    summary="Actualizar Cliente",
    description="""
    Actualiza los datos de un cliente existente.
    Solo administradores pueden actualizar cualquier cliente.
    Los clientes normales solo pueden actualizarse a sí mismos.
    
    ## Parámetros
    * `cliente_id`: ID del cliente a actualizar
    * `email`: Nuevo email (opcional)
    * `nombre`: Nuevo nombre (opcional)
    * `telefono`: Nuevo teléfono (opcional)
    * `fecha_nacimiento`: Nueva fecha de nacimiento (opcional)
    
    ## Respuesta
    * Detalles actualizados del cliente
    
    ## Errores
    * 404: Cliente no encontrado
    * 403: No tienes permiso para actualizar este cliente
    * 400: Email o teléfono ya en uso
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Cliente actualizado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "nuevo.email@example.com",
                        "nombre": "Juan Pérez Actualizado",
                        "telefono": "+0987654321",
                        "fecha_nacimiento": "1990-01-01",
                        "activo": true
                    }
                }
            }
        },
        400: {
            "description": "Error de validación",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Ya existe un cliente con este email"
                    }
                }
            }
        }
    }
)
async def update_cliente(
    *,
    db: AsyncSession = Depends(get_db),
    cliente_id: int,
    cliente_in: ClienteUpdate,
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Actualiza un cliente.
    Solo administradores pueden actualizar cualquier cliente.
    Los clientes normales solo pueden actualizarse a sí mismos.
    """
    # TODO: Implementar lógica de administrador
    if cliente_id != current_cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este cliente"
        )
    
    # Verificar si el email ya está en uso
    if cliente_in.email and cliente_in.email != current_cliente.email:
        cliente_exists = await ClienteService.get_by_email(db, email=cliente_in.email)
        if cliente_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un cliente con este email"
            )
    
    # Verificar si el teléfono ya está en uso
    if cliente_in.telefono and cliente_in.telefono != current_cliente.telefono:
        cliente_exists = await ClienteService.get_by_telefono(db, telefono=cliente_in.telefono)
        if cliente_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un cliente con este teléfono"
            )
    
    cliente = await ClienteService.update(db, current_cliente, cliente_in)
    return cliente

@router.delete(
    "/{cliente_id}",
    response_model=Cliente,
    summary="Eliminar Cliente",
    description="""
    Elimina un cliente del sistema.
    Solo administradores pueden eliminar cualquier cliente.
    Los clientes normales solo pueden eliminarse a sí mismos.
    
    ## Parámetros
    * `cliente_id`: ID del cliente a eliminar
    
    ## Respuesta
    * Detalles del cliente eliminado
    
    ## Errores
    * 404: Cliente no encontrado
    * 403: No tienes permiso para eliminar este cliente
    * 401: No autenticado
    * 400: No se puede eliminar un cliente con citas pendientes
    """,
    responses={
        200: {
            "description": "Cliente eliminado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "cliente@example.com",
                        "nombre": "Juan Pérez",
                        "telefono": "+1234567890",
                        "fecha_nacimiento": "1990-01-01",
                        "activo": false
                    }
                }
            }
        }
    }
)
async def delete_cliente(
    *,
    db: AsyncSession = Depends(get_db),
    cliente_id: int,
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Elimina un cliente.
    Solo administradores pueden eliminar cualquier cliente.
    Los clientes normales solo pueden eliminarse a sí mismos.
    """
    # TODO: Implementar lógica de administrador
    if cliente_id != current_cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este cliente"
        )
    
    await ClienteService.delete(db, current_cliente)
    return current_cliente

@router.patch(
    "/{cliente_id}/activar",
    response_model=Cliente,
    summary="Activar Cliente",
    description="""
    Activa un cliente desactivado.
    Solo disponible para administradores.
    
    ## Parámetros
    * `cliente_id`: ID del cliente a activar
    
    ## Respuesta
    * Detalles del cliente activado
    
    ## Errores
    * 404: Cliente no encontrado
    * 403: No tienes permisos de administrador
    * 401: No autenticado
    * 400: Cliente ya está activo
    """,
    responses={
        200: {
            "description": "Cliente activado exitosamente",
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
        }
    }
)
async def activar_cliente(
    *,
    db: AsyncSession = Depends(get_db),
    cliente_id: int,
    current_admin: Admin = Depends(get_current_admin)
) -> Any:
    """
    Activa un cliente.
    Solo administradores pueden activar clientes.
    """
    cliente = await ClienteService.get_by_id(db, cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    if cliente.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El cliente ya está activo"
        )
    
    cliente = await ClienteService.activar(db, cliente)
    return cliente

@router.patch(
    "/{cliente_id}/desactivar",
    response_model=Cliente,
    summary="Desactivar Cliente",
    description="""
    Desactiva un cliente activo.
    Solo disponible para administradores.
    
    ## Parámetros
    * `cliente_id`: ID del cliente a desactivar
    
    ## Respuesta
    * Detalles del cliente desactivado
    
    ## Errores
    * 404: Cliente no encontrado
    * 403: No tienes permisos de administrador
    * 401: No autenticado
    * 400: Cliente ya está desactivado
    * 400: No se puede desactivar un cliente con citas pendientes
    """,
    responses={
        200: {
            "description": "Cliente desactivado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "cliente@example.com",
                        "nombre": "Juan Pérez",
                        "telefono": "+1234567890",
                        "fecha_nacimiento": "1990-01-01",
                        "activo": false
                    }
                }
            }
        }
    }
)
async def desactivar_cliente(
    *,
    db: AsyncSession = Depends(get_db),
    cliente_id: int,
    current_admin: Admin = Depends(get_current_admin)
) -> Any:
    """
    Desactiva un cliente.
    Solo administradores pueden desactivar clientes.
    """
    cliente = await ClienteService.get_by_id(db, cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    if not cliente.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El cliente ya está desactivado"
        )
    
    # Verificar si tiene citas pendientes
    if await ClienteService.tiene_citas_pendientes(db, cliente_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede desactivar un cliente con citas pendientes"
        )
    
    cliente = await ClienteService.desactivar(db, cliente)
    return cliente 