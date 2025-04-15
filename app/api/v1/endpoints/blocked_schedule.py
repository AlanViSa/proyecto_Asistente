"""
Endpoints for blocked schedule management
"""
from typing import Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_active_user, get_current_active_admin
from app.models.client import Client
from app.models.blocked_schedule import BlockedSchedule
from app.schemas.blocked_schedule import (
    BlockedSchedule as BlockedScheduleSchema,
    BlockedScheduleCreate,
    BlockedScheduleUpdate
)

router = APIRouter()

@router.get(
    "/",
    response_model=List[BlockedScheduleSchema],
    summary="List Blocked Schedules",
    description="List all blocked time slots."
)
async def read_blocked_schedules(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve all blocked time slots.
    """
    query = db.query(BlockedSchedule)
    
    # Filter by active status if requested
    if active_only:
        query = query.filter(BlockedSchedule.is_active == True)
    
    blocked_schedules = query.order_by(BlockedSchedule.start_time).offset(skip).limit(limit).all()
    return blocked_schedules

@router.post(
    "/",
    response_model=BlockedScheduleSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create Blocked Schedule",
    description="Block a time slot. Admin only."
)
async def create_blocked_schedule(
    blocked_schedule_in: BlockedScheduleCreate,
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_admin),
) -> Any:
    """
    Create a new blocked time slot. Admin only.
    """
    # Validate time range
    if blocked_schedule_in.end_time <= blocked_schedule_in.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )
    
    # Create the blocked schedule
    blocked_schedule = BlockedSchedule(
        start_time=blocked_schedule_in.start_time,
        end_time=blocked_schedule_in.end_time,
        reason=blocked_schedule_in.reason,
        is_active=True
    )
    
    db.add(blocked_schedule)
    db.commit()
    db.refresh(blocked_schedule)
    
    return blocked_schedule

@router.get(
    "/{blocked_schedule_id}",
    response_model=BlockedScheduleSchema,
    summary="Get Blocked Schedule",
    description="Get details of a specific blocked time slot."
)
async def read_blocked_schedule(
    blocked_schedule_id: int = Path(..., title="Blocked Schedule ID"),
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve a specific blocked time slot.
    """
    blocked_schedule = db.query(BlockedSchedule).filter(BlockedSchedule.id == blocked_schedule_id).first()
    if not blocked_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blocked schedule not found"
        )
    
    return blocked_schedule

@router.put(
    "/{blocked_schedule_id}",
    response_model=BlockedScheduleSchema,
    summary="Update Blocked Schedule",
    description="Update a blocked time slot. Admin only."
)
async def update_blocked_schedule(
    blocked_schedule_in: BlockedScheduleUpdate,
    blocked_schedule_id: int = Path(..., title="Blocked Schedule ID"),
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_admin),
) -> Any:
    """
    Update a blocked time slot. Admin only.
    """
    blocked_schedule = db.query(BlockedSchedule).filter(BlockedSchedule.id == blocked_schedule_id).first()
    if not blocked_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blocked schedule not found"
        )
    
    # Validate time range if both start and end times are provided
    if blocked_schedule_in.start_time and blocked_schedule_in.end_time:
        if blocked_schedule_in.end_time <= blocked_schedule_in.start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time"
            )
    
    # Update blocked schedule fields
    for key, value in blocked_schedule_in.dict(exclude_unset=True).items():
        setattr(blocked_schedule, key, value)
    
    db.add(blocked_schedule)
    db.commit()
    db.refresh(blocked_schedule)
    
    return blocked_schedule

@router.delete(
    "/{blocked_schedule_id}",
    response_model=BlockedScheduleSchema,
    summary="Delete Blocked Schedule",
    description="Delete a blocked time slot. Admin only."
)
async def delete_blocked_schedule(
    blocked_schedule_id: int = Path(..., title="Blocked Schedule ID"),
    db: Session = Depends(get_db),
    current_user: Client = Depends(get_current_active_admin),
) -> Any:
    """
    Delete a blocked time slot. Admin only.
    """
    blocked_schedule = db.query(BlockedSchedule).filter(BlockedSchedule.id == blocked_schedule_id).first()
    if not blocked_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blocked schedule not found"
        )
    
    # Instead of deleting, set is_active to False
    blocked_schedule.is_active = False
    db.add(blocked_schedule)
    db.commit()
    db.refresh(blocked_schedule)
    
    return blocked_schedule 