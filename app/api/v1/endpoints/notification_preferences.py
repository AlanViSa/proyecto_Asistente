"""
Endpoints for notification preference management
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_active_user, get_current_active_admin
from app.models.client import Client
from app.models.notification_preference import NotificationPreference
from app.schemas.notification_preference import (
    NotificationPreference as NotificationPreferenceSchema,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate
)

router = APIRouter()

@router.get(
    "/",
    response_model=List[NotificationPreferenceSchema],
    summary="List Notification Preferences",
    description="List all notification preferences. Admin only."
)
async def read_notification_preferences(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_admin),
) -> Any:
    """
    Retrieve all notification preferences. Admin only.
    """
    preferences = db.query(NotificationPreference).offset(skip).limit(limit).all()
    return preferences

@router.get(
    "/me",
    response_model=NotificationPreferenceSchema,
    summary="Get My Notification Preferences",
    description="Get the current user's notification preferences."
)
async def read_own_notification_preferences(
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve the current user's notification preferences.
    """
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.client_id == current_user.id
    ).first()
    
    if not preferences:
        # Create default preferences if none exist
        preferences = NotificationPreference(client_id=current_user.id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return preferences

@router.get(
    "/{client_id}",
    response_model=NotificationPreferenceSchema,
    summary="Get Client's Notification Preferences",
    description="Get a specific client's notification preferences. Admin only."
)
async def read_client_notification_preferences(
    client_id: int = Path(..., title="Client ID"),
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_admin),
) -> Any:
    """
    Retrieve a specific client's notification preferences. Admin only.
    """
    # Check if client exists
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.client_id == client_id
    ).first()
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification preferences not found"
        )
    
    return preferences

@router.put(
    "/me",
    response_model=NotificationPreferenceSchema,
    summary="Update My Notification Preferences",
    description="Update the current user's notification preferences."
)
async def update_own_notification_preferences(
    preferences_in: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_user),
) -> Any:
    """
    Update the current user's notification preferences.
    """
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.client_id == current_user.id
    ).first()
    
    if not preferences:
        # Create preferences if none exist
        new_preferences = NotificationPreference(client_id=current_user.id, **preferences_in.dict(exclude_unset=True))
        db.add(new_preferences)
        db.commit()
        db.refresh(new_preferences)
        return new_preferences
    
    # Update preferences
    for key, value in preferences_in.dict(exclude_unset=True).items():
        setattr(preferences, key, value)
    
    db.add(preferences)
    db.commit()
    db.refresh(preferences)
    return preferences

@router.put(
    "/{client_id}",
    response_model=NotificationPreferenceSchema,
    summary="Update Client's Notification Preferences",
    description="Update a specific client's notification preferences. Admin only."
)
async def update_client_notification_preferences(
    preferences_in: NotificationPreferenceUpdate,
    client_id: int = Path(..., title="Client ID"),
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_admin),
) -> Any:
    """
    Update a specific client's notification preferences. Admin only.
    """
    # Check if client exists
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.client_id == client_id
    ).first()
    
    if not preferences:
        # Create preferences if none exist
        new_preferences = NotificationPreference(client_id=client_id, **preferences_in.dict(exclude_unset=True))
        db.add(new_preferences)
        db.commit()
        db.refresh(new_preferences)
        return new_preferences
    
    # Update preferences
    for key, value in preferences_in.dict(exclude_unset=True).items():
        setattr(preferences, key, value)
    
    db.add(preferences)
    db.commit()
    db.refresh(preferences)
    return preferences 