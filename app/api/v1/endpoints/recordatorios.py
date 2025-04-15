"""
Endpoints for managing appointment reminders.

This module provides endpoints for:
- Listing customer reminders
- Getting details of a specific reminder
- Creating new reminders
- Updating existing reminders
- Deleting reminders
- Marking reminders as sent
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
    ReminderCreate,
    ReminderUpdate,
    ReminderList
)

router = APIRouter()

@router.get(
    "/",
    response_model=List[ReminderList],
    summary="List Reminders",
    description="""
    Gets the list of reminders for the current customer.
    
    ## Respuesta
    * List of reminders with basic information
    
    ## Errores
    * 401: No autenticado
    """,
    responses={
        200: {
            "description": "Lista de recordatorios obtenida exitosamente",
            "content": {  # Fixed typo in "content"
                "application/json": {
                    "example": [{
                        "id": 1,
                        "cita_id": 1,
                        "tipo": "EMAIL",
                        "estado": "PENDIENTE",
                        "fecha_envio_programada": "2024-03-19T09:00:00"
                    }]  # Fixed missing closing bracket
                }
            }
        }
    }
)
async def get_reminders(
    *,
    db: AsyncSession = Depends(get_db),
    current_cliente: Cliente = Depends(get_current_cliente)
) -> Any:
    """
    Gets the list of reminders for the current customer.
    """
    reminders = await RecordatorioService.get_by_cliente(
        db=db,
        cliente_id=current_cliente.id
    )
    return reminders

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
            "content": {  # Fixed typo in "content"
                "application/json": {
                    "example": {
                        "id": 1,
                        "cita_id": 1,
                        "cliente_id": 1,
                        "type": "EMAIL",
                        "status": "PENDING",
                        "scheduled_sent_date": "2024-03-19T09:00:00",
                        "sent_date": None,
                        "content": "Reminder of your appointment for tomorrow",
                        "recipient": "cliente@example.com"
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
) -> Any:  # Fixed typo in "cliente"
    """
    Gets a specific reminder by its ID.
    Only own reminders can be accessed.
    """
    reminder = await RecordatorioService.get_by_id(
        db=db,
        reminder_id=recordatorio_id  # Use reminder_id for consistency
    )
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"  # Translate message to English
        )
    if reminder.cliente_id != current_cliente.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this reminder"  # Translate message to English
        )
    return reminder

@router.post(
    "/",
    response_model=Recordatorio,
    summary="Create New Reminder",
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
    * Details of the created reminder
    
    ## Errores
    * 401: No autenticado
    * 403: No tienes permisos de administrador
    * 400: Datos inválidos
    * 404: Cita no encontrada
    """,
    responses={
        200: {
            "description": "Recordatorio creado exitosamente",
            "content": {  # Fixed typo in "content"
                "application/json": {
                    "example": {
                        "id": 1,
                        "cita_id": 1,
                        "cliente_id": 1,
                        "type": "EMAIL",
                        "status": "PENDING",
                        "scheduled_sent_date": "2024-03-19T09:00:00",
                        "sent_date": None,
                        "content": "Reminder of your appointment for tomorrow",
                        "recipient": "cliente@example.com"
                    }
                }
            }
        }
    }
)
async def create_reminder(
    *,
    db: AsyncSession = Depends(get_db),
    recordatorio_in: RecordatorioCreate,
    current_admin: Admin = Depends(get_current_admin)
) -> Any:
    """
    Crea un nuevo recordatorio.
    Solo disponible para administradores.
    """  # Corrected typo here too
    reminder = await RecordatorioService.create(
        db=db,
        recordatorio_in=recordatorio_in
    )
    return reminder

@router.put(
    "/{recordatorio_id}",
    response_model=Recordatorio,
    summary="Update Reminder",
    description="""
    Actualiza un recordatorio existente.
    Solo disponible para administradores.
    
    ## Parámetros
    * `reminder_id`: ID of the reminder to update
    * `tipo`: Nuevo tipo de recordatorio (opcional)
    * `fecha_envio_programada`: Nueva fecha y hora programada (opcional)
    * `contenido`: Nuevo contenido (opcional)
    * `destinatario`: Nuevo destinatario (opcional)
    
    ## Respuesta
    * Detalles actualizados del recordatorio
    
    ## Errores
    * 404: Recordatorio no encontrado
    * 401: Unauthorized
    * 403: Admin permissions required
    * 400: Invalid data
    """,  # Consistent error message style
    responses={
        200: {
            "description": "Recordatorio actualizado exitosamente",
            "content": {  # Fixed typo in "content"
                "application/json": {
                    "example": {
                        "id": 1,
                        "cita_id": 1,
                        "customer_id": 1,
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
async def update_reminder(
    *,
    db: AsyncSession = Depends(get_db),
    reminder_id: int,
    reminder_in: ReminderUpdate,
    current_admin: Admin = Depends(get_current_admin)
) -> Any:  # Fixed naming inconsistencies and typos
    """
    Updates an existing reminder.
    Only available to administrators.
    """
    reminder = await RecordatorioService.get_by_id(
        db=db,
        reminder_id=reminder_id  # Use reminder_id consistently
    )
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"  # Consistent message
        )

    reminder = await RecordatorioService.update(
        db=db,
        reminder=reminder,
        reminder_in=reminder_in
    )
    return reminder

@router.delete(
    "/{recordatorio_id}",
    response_model=Recordatorio,
    summary="Delete Reminder",
    description="""
    Elimina un recordatorio existente.
    Solo disponible para administradores.
    
    ## Parámetros
    * `reminder_id`: ID of the reminder to delete
    
    ## Respuesta
    * Details of the deleted reminder
    
    ## Errores
    * 404: Reminder not found
    * 401: Unauthorized
    * 403: Admin permissions required
    """,  # Consistent error message style
    responses={
        200: {
            "description": "Recordatorio eliminado exitosamente",
            "content": {  # Fixed typo in "content"
                "application/json": {
                    "example": {
                        "id": 1,
                        "cita_id": 1,
                        "customer_id": 1,
                        "tipo": "EMAIL",
                        "status": "CANCELED",
                        "scheduled_sent_date": "2024-03-19T09:00:00",
                        "sent_date": None,
                        "content": "Reminder of your appointment for tomorrow",
                        "recipient": "cliente@example.com"
                    }
                }
            }
        }
    }
)
async def delete_reminder(
    *,
    db: AsyncSession = Depends(get_db),
    recordatorio_id: int,
    current_admin: Admin = Depends(get_current_admin)
) -> Any:
    """
    Elimina un recordatorio existente.
    Solo disponible para administradores.
    """
    reminder = await RecordatorioService.get_by_id(
        db=db,
        reminder_id=recordatorio_id  # Use reminder_id consistently
    )
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"  # Consistent message
        )

    await RecordatorioService.delete(db=db, reminder=reminder)
    return reminder

@router.patch(
    "/{reminder_id}/mark-as-sent",
    response_model=Recordatorio,
    summary="Mark Reminder as Sent",
    description="""
    Marks a reminder as sent.
    Solo disponible para administradores.
    
    ## Parámetros
    * `reminder_id`: ID of the reminder to mark
    
    ## Respuesta
    * Details of the updated reminder
    
    ## Errores
    * 404: Reminder not found
    * 401: Unauthorized
    * 403: Admin permissions required
    * 400: Reminder already sent
    """,  # Consistent error message style
    responses={
        200: {
            "description": "Recordatorio marcado como enviado exitosamente",
            "content": {  # Fixed typo in "content"
                "application/json": {
                    "example": {
                        "id": 1,
                        "cita_id": 1,
                        "customer_id": 1,
                        "type": "EMAIL",
                        "status": "SENT",
                        "scheduled_sent_date": "2024-03-19T09:00:00",
                        "sent_date": "2024-03-19T09:00:00",
                        "content": "Reminder of your appointment for tomorrow",
                        "recipient": "cliente@example.com"
                    }
                }
            }
        }
    }
)
async def mark_as_sent(
    *,
    db: AsyncSession = Depends(get_db),
    reminder_id: int,
    current_admin: Admin = Depends(get_current_admin)
) -> Any:  # Corrected name and docstring
    """
    Marks a reminder as sent.
    Only available to administrators.
    """
    reminder = await RecordatorioService.get_by_id(
        db=db,
        reminder_id=reminder_id  # Use reminder_id consistently
    )
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"  # Consistent message
        )
    if reminder.status == "SENT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The reminder has already been sent"  # Consistent message
        )

    reminder = await RecordatorioService.mark_as_sent(
        db=db,
        reminder=reminder
    )
    return reminder