"""
API endpoints for appointment management

This module provides endpoints for:
- Listing client appointments
- Getting details of a specific appointment
- Creating new appointments
- Updating existing appointments
- Deleting appointments
- Confirming pending appointments
- Canceling appointments
- Filtering appointments by date
"""
from datetime import datetime, timedelta
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_active_admin, get_current_active_user
from app.models.client import Client
from app.models.appointment import AppointmentStatus
from app.models.service import Service
from app.models.user import User

# Import schemas (to be created or renamed)
from app.schemas.appointment import (
    Appointment,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentList,
    AppointmentResponse
)
from app.services.appointment_service import AppointmentService

router = APIRouter()

@router.get(
    "/",
    response_model=List[AppointmentResponse],
    summary="List Appointments",
    description="Retrieve all appointments (admin users) or user's own appointments."
)
async def read_appointments(
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    status: AppointmentStatus = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve appointments.
    """
    query = db.query(Appointment)
    
    # Filter by status if provided
    if status:
        query = query.filter(Appointment.status == status)
    
    # Filter by user unless admin
    if not current_user.is_admin:
        query = query.filter(Appointment.user_id == current_user.id)
    
    appointments = query.order_by(Appointment.datetime).offset(skip).limit(limit).all()
    return appointments

@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Appointment",
    description="Create a new appointment."
)
async def create_appointment(
    *,
    db: Session = Depends(get_db),
    appointment_in: AppointmentCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new appointment.
    """
    # Check if service exists
    service = db.query(Service).filter(
        Service.id == appointment_in.service_id,
        Service.is_active == True
    ).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or inactive"
        )
    
    # Use appointment service to check availability and create appointment
    appointment_service = AppointmentService(db)
    
    # Check if the requested time is available
    if not appointment_service.check_availability(appointment_in.datetime, service.duration):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected time is not available"
        )
    
    # Create the appointment
    appointment = appointment_service.create_appointment(
        user_id=current_user.id,
        service_id=appointment_in.service_id,
        datetime=appointment_in.datetime,
        notes=appointment_in.notes
    )
    
    return appointment

@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Get Appointment",
    description="Get details of a specific appointment."
)
async def read_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get appointment by ID.
    """
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check permissions
    if not current_user.is_admin and appointment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this appointment"
        )
    
    return appointment

@router.put(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Update Appointment",
    description="Update an existing appointment."
)
async def update_appointment(
    *,
    db: Session = Depends(get_db),
    appointment_id: int,
    appointment_in: AppointmentUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update an appointment.
    """
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check permissions
    if not current_user.is_admin and appointment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this appointment"
        )
    
    # Check if we can still update (not allow updates to past appointments)
    if appointment.datetime < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update past appointments"
        )
    
    # Check if service exists if service_id is being updated
    if appointment_in.service_id and appointment_in.service_id != appointment.service_id:
        service = db.query(Service).filter(
            Service.id == appointment_in.service_id,
            Service.is_active == True
        ).first()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found or inactive"
            )
    
    # If datetime is being updated, check availability
    if appointment_in.datetime and appointment_in.datetime != appointment.datetime:
        appointment_service = AppointmentService(db)
        
        # Get service duration
        service = db.query(Service).filter(Service.id == appointment.service_id).first()
        
        # Check if the requested time is available (excluding this appointment)
        if not appointment_service.check_availability(
            appointment_in.datetime,
            service.duration,
            exclude_appointment_id=appointment_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected time is not available"
            )
    
    # Update appointment
    update_data = appointment_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appointment, field, value)
    
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment

@router.delete(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Cancel Appointment",
    description="Cancel an appointment."
)
async def cancel_appointment(
    *,
    db: Session = Depends(get_db),
    appointment_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Cancel an appointment.
    """
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check permissions
    if not current_user.is_admin and appointment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to cancel this appointment"
        )
    
    # Check if we can still cancel (e.g., not allow cancellations < 24h before)
    cancellation_window = datetime.now() + timedelta(hours=24)
    if appointment.datetime < cancellation_window:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel appointments less than 24 hours before scheduled time"
        )
    
    # Update status to cancelled
    appointment.status = AppointmentStatus.CANCELLED
    
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment

@router.get(
    "/appointments/date/{date}",
    response_model=List[AppointmentList],
    summary="List Appointments by Date",
    description="""
    Gets all appointments for a specific date.
    
    Parameters:
    - **date**: Date to query (format: YYYY-MM-DD)
    
    Response:
    - List of appointments for the specified date
    """,
    responses={
        200: {
            "description": "Successfully retrieved list of appointments",
            "content": {
                "application/json": {
                    "example": [{
                        "id": 1,
                        "datetime": "2024-03-20T10:00:00",
                        "duration_minutes": 30,
                        "status": "PENDING",
                        "service_id": 1
                    }]
                }
            }
        }
    }
)
async def get_appointments_by_date(
    date: datetime,
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_user)
) -> Any:
    """
    Gets all appointments for a specific date.
    Regular users can only see their own appointments.
    Admins can see all appointments.
    """
    # Logic to filter by date would go here
    return [] 