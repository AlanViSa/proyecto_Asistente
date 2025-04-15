"""
Endpoints for reminder management
"""
from typing import Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_active_user, get_current_active_admin
from app.models.client import Client
from app.models.appointment import Appointment
from app.models.reminder import Reminder
from app.schemas.reminder import (
    Reminder as ReminderSchema,
    ReminderCreate,
    ReminderUpdate
)
from app.services.reminder_service import ReminderService

router = APIRouter()

@router.get(
    "/",
    response_model=List[ReminderSchema],
    summary="List Reminders",
    description="List all reminders. Admin only."
)
async def read_reminders(
    skip: int = 0,
    limit: int = 100,
    sent: bool = None,
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_admin),
) -> Any:
    """
    Retrieve all reminders. Admin only.
    """
    query = db.query(Reminder)
    
    # Filter by sent status if provided
    if sent is not None:
        query = query.filter(Reminder.sent == sent)
    
    reminders = query.order_by(Reminder.scheduled_time).offset(skip).limit(limit).all()
    return reminders

@router.get(
    "/appointment/{appointment_id}",
    response_model=List[ReminderSchema],
    summary="Get Reminders for Appointment",
    description="Get all reminders for a specific appointment."
)
async def read_appointment_reminders(
    appointment_id: int = Path(..., title="Appointment ID"),
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve all reminders for a specific appointment.
    """
    # Check if the appointment exists and belongs to the current user (unless admin)
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Check if the user has permission to access this appointment
    if not current_user.is_admin and appointment.client_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    reminders = db.query(Reminder).filter(
        Reminder.appointment_id == appointment_id
    ).order_by(Reminder.scheduled_time).all()
    
    return reminders

@router.post(
    "/",
    response_model=ReminderSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create Reminder",
    description="Create a new reminder. Admin only."
)
async def create_reminder(
    reminder_in: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_admin),
) -> Any:
    """
    Create a new reminder. Admin only.
    """
    # Check if the appointment exists
    appointment = db.query(Appointment).filter(Appointment.id == reminder_in.appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Create the reminder
    reminder = Reminder(
        appointment_id=reminder_in.appointment_id,
        scheduled_time=reminder_in.scheduled_time,
        message=reminder_in.message,
        sent=False
    )
    
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    
    return reminder

@router.put(
    "/{reminder_id}",
    response_model=ReminderSchema,
    summary="Update Reminder",
    description="Update a reminder. Admin only."
)
async def update_reminder(
    reminder_in: ReminderUpdate,
    reminder_id: int = Path(..., title="Reminder ID"),
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_admin),
) -> Any:
    """
    Update a reminder. Admin only.
    """
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    # Update reminder fields
    for key, value in reminder_in.dict(exclude_unset=True).items():
        setattr(reminder, key, value)
    
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    
    return reminder

@router.delete(
    "/{reminder_id}",
    response_model=ReminderSchema,
    summary="Delete Reminder",
    description="Delete a reminder. Admin only."
)
async def delete_reminder(
    reminder_id: int = Path(..., title="Reminder ID"),
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_admin),
) -> Any:
    """
    Delete a reminder. Admin only.
    """
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    db.delete(reminder)
    db.commit()
    
    return reminder

@router.post(
    "/process",
    summary="Process Pending Reminders",
    description="Process all pending reminders manually. Admin only."
)
async def process_reminders(
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_admin),
) -> Any:
    """
    Process all pending reminders manually. Admin only.
    """
    reminder_service = ReminderService(db)
    processed_count = reminder_service.process_pending_reminders()
    
    return {
        "status": "success",
        "processed_count": processed_count,
        "message": f"Processed {processed_count} reminders"
    } 