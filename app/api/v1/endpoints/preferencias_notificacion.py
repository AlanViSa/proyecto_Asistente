"""
Endpoints to manage client notification preferences

This module provides endpoints for:
- Getting a client's notification preferences
- Creating new notification preferences
- Updating existing preferences
- Deleting preferences
- Creating default preferences
- Listing clients without configured preferences
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.services.preferencias_notificacion import NotificationPreferenceService
from app.schemas.preferencias_notificacion import (NotificationPreference, NotificationPreferenceCreate, NotificationPreferenceUpdate
)

router = APIRouter()

@router.get(
    "/{client_id}",
    response_model=NotificationPreference,
    summary="Get Notification Preferences",
    description="""
    Gets the notification preferences for a specific client.

    ## Parameters
    * `client_id`: ID of the client to query

    ## Response
    * Client's notification preferences

    ## Errors
    * 404: No preferences found for this client
    * 401: Not authenticated
    """,
    responses={
        200: {
            "description": "Preferences retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "client_id": 1,
                        "email_notifications": True,
                        "sms_notifications": True,
                        "push_notifications": False,
                        "appointment_reminders": True,
                        "promotions": False,
                        "notification_timeframe": {"start": "09:00", "end": "21:00"},
                    }
                }
            }
        },
        404: {
            "description": "Preferences not found",
            "content": {
                "application/json": {
                    "example": {"detail": "No preferences found for this client"}
                }
            }
        },
    }
)
async def get_preferences(client_id: int, db: AsyncSession = Depends(deps.get_db)):
    """
    Gets the notification preferences for a client
    """
    preferences = await NotificationPreferenceService.get_by_client(db, client_id)
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No preferences found for this client",
        )
    return preferences

@router.post(
    "",
    response_model=NotificationPreference,
    summary="Create Notification Preferences",
    description="Creates new notification preferences for a client.",
)
async def create_preferences(
    preferences_in: NotificationPreferenceCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Creates new notification preferences for a client
    """
    # Check if preferences already exist for this client
    existing_preferences = await NotificationPreferenceService.get_by_client(
        db, preferences_in.client_id
    )
    if existing_preferences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preferences already exist for this client",
        )

    return await NotificationPreferenceService.create(db, preferences_in)

@router.put(
    "/{client_id}",
    response_model=NotificationPreference,
    summary="Update Notification Preferences",
    description="""
    Updates a client's notification preferences.

    ## Parameters
    * `client_id`: ID of the client
    * `email_notifications`: Enable/disable email notifications
    * `sms_notifications`: Enable/disable SMS notifications
    * `push_notifications`: Enable/disable push notifications
    * `appointment_reminders`: Enable/disable appointment reminders
    * `promotions`: Enable/disable promotion notifications
    * `notification_timeframe`: Update allowed timeframe

    ## Response
    * Updated preferences

    ## Errors
    * 404: No preferences found for this client
    * 401: Not authenticated
    """,
    responses={
        200: {
            "description": "Preferences updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "client_id": 1,
                        "email_notifications": True,
                        "sms_notifications": False,
                        "push_notifications": True,
                        "appointment_reminders": True,
                        "promotions": False,
                        "notification_timeframe": {"start": "10:00", "end": "20:00"},
                    }
                }
            }
        },
    }
)
async def update_preferences(
    client_id: int,
    preferences_in: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Updates a client's notification preferences
    """
    preferences = await NotificationPreferenceService.get_by_client(db, client_id)
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No preferences found for this client",
        )

    return await NotificationPreferenceService.update(
        db, preferences, preferences_in
    )

@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Notification Preferences",
    description="""
    Deletes a client's notification preferences.

    ## Parameters
    * `client_id`: ID of the client

    ## Response
    * 204: Preferences deleted successfully

    ## Errors
    * 404: No preferences found for this client
    * 401: Not authenticated
    """,
    responses={
        204: {
            "description": "Preferences deleted successfully"
        },
        404: {
            "description": "Preferences not found",
            "content": {
                "application/json": {
                    "example": {"detail": "No preferences found for this client"}
                }
            }
        },
    }
)
async def delete_preferences(client_id: int, db: AsyncSession = Depends(deps.get_db)):
    """
    Deletes a client's notification preferences
    """
    preferences = await NotificationPreferenceService.get_by_client(db, client_id)
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No preferences found for this client",
        )

    await NotificationPreferenceService.delete(db, preferences)

@router.post(
    "/{client_id}/default",
    response_model=NotificationPreference,
    summary="Create Default Preferences",
    description="""
    Creates or retrieves default preferences for a client.

    ## Parameters
    * `client_id`: ID of the client

    ## Response
    * Default preferences

    ## Errors
    * 401: Not authenticated
    """,
    responses={
        200: {
            "description": "Default preferences created/retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "client_id": 1,
                        "email_notifications": True,
                        "sms_notifications": True,
                        "push_notifications": True,
                        "appointment_reminders": True,
                        "promotions": True,
                        "notification_timeframe": {"start": "09:00", "end": "21:00"},
                    }
                }
            }
        },
    }
)
async def create_default_preferences(client_id: int, db: AsyncSession = Depends(deps.get_db)):
    """
    Creates or retrieves default preferences for a client
    """
    return await NotificationPreferenceService.create_default_preferences(
        db, client_id
    )

@router.get(
    "/without-preferences",
    response_model=List[int],
    summary="List Clients Without Preferences",
    description="""
    Gets the list of client IDs that do not have preferences configured.

    ## Response
    * List of client IDs without preferences

    ## Errors
    * 401: Not authenticated
    """,
    responses={
        200: {
            "description": "List of clients without preferences retrieved successfully",
            "content": {"application/json": {"example": [1, 2, 3]}},
        },
    }
)
async def get_clients_without_preferences(db: AsyncSession = Depends(deps.get_db)):
    """
    Gets the list of client IDs that do not have preferences configured
    """
    return await NotificationPreferenceService.get_clients_without_preferences(db)