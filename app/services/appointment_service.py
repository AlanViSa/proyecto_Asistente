"""
Service for appointment management
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, time
import re

from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import DatabaseError
from app.core.config import get_settings
from app.models.appointment import Appointment, AppointmentStatus
from app.models.service import Service
from app.models.client import Client
from app.models.blocked_schedule import BlockedSchedule
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.services.reminder_service import ReminderService

settings = get_settings()

class AppointmentService:
    """Service for appointment operations"""
    
    # Slot duration in minutes
    DEFAULT_SLOT_DURATION = 30
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession, 
        appointment_id: int
    ) -> Optional[Appointment]:
        """Get an appointment by ID"""
        try:
            result = await db.execute(
                select(Appointment)
                .options(joinedload(Appointment.client), joinedload(Appointment.service))
                .where(Appointment.id == appointment_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting appointment by ID: {str(e)}")
    
    @staticmethod
    async def get_by_client(
        db: AsyncSession,
        client_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Appointment]:
        """Get appointments for a client"""
        try:
            result = await db.execute(
                select(Appointment)
                .options(joinedload(Appointment.service))
                .where(Appointment.client_id == client_id)
                .order_by(Appointment.datetime.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting appointments by client: {str(e)}")
    
    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_cancelled: bool = False
    ) -> List[Appointment]:
        """Get all appointments"""
        try:
            query = select(Appointment)\
                .options(joinedload(Appointment.client), joinedload(Appointment.service))\
                .order_by(Appointment.datetime)
                
            if not include_cancelled:
                query = query.where(Appointment.status != AppointmentStatus.CANCELLED)
                
            query = query.offset(skip).limit(limit)
            
            result = await db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting all appointments: {str(e)}")
    
    @staticmethod
    async def get_appointments_for_day(
        db: AsyncSession,
        date: datetime.date
    ) -> List[Appointment]:
        """Get all appointments for a specific day"""
        try:
            # Create datetime bounds for the day
            start_date = datetime.combine(date, time.min)
            end_date = datetime.combine(date, time.max)
            
            result = await db.execute(
                select(Appointment)
                .options(joinedload(Appointment.client), joinedload(Appointment.service))
                .where(
                    and_(
                        Appointment.datetime >= start_date,
                        Appointment.datetime <= end_date,
                        Appointment.status != AppointmentStatus.CANCELLED
                    )
                )
                .order_by(Appointment.datetime)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting appointments for day: {str(e)}")
    
    @staticmethod
    async def create(
        db: AsyncSession,
        appointment_in: AppointmentCreate
    ) -> Appointment:
        """Create a new appointment"""
        try:
            # Check if the service exists
            service_result = await db.execute(
                select(Service).where(Service.id == appointment_in.service_id)
            )
            service = service_result.scalar_one_or_none()
            
            if not service:
                raise ValueError(f"Service with ID {appointment_in.service_id} not found")
            
            # Check if the client exists
            client_result = await db.execute(
                select(Client).where(Client.id == appointment_in.client_id)
            )
            client = client_result.scalar_one_or_none()
            
            if not client:
                raise ValueError(f"Client with ID {appointment_in.client_id} not found")
            
            # Check appointment availability
            is_available = await AppointmentService.is_slot_available(
                db, 
                appointment_in.datetime, 
                service.duration
            )
            
            if not is_available:
                raise ValueError(f"The slot at {appointment_in.datetime} is not available")
            
            # Create appointment
            appointment = Appointment(**appointment_in.dict())
            db.add(appointment)
            await db.commit()
            await db.refresh(appointment)
            
            # Schedule reminder
            await ReminderService.create_appointment_reminder(db, appointment.id)
            
            return appointment
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error creating appointment: {str(e)}")
    
    @staticmethod
    async def update(
        db: AsyncSession,
        appointment: Appointment,
        appointment_in: AppointmentUpdate
    ) -> Appointment:
        """Update an appointment"""
        try:
            update_data = appointment_in.dict(exclude_unset=True)
            
            # If changing datetime, check availability
            if "datetime" in update_data and update_data["datetime"] != appointment.datetime:
                # Get service for duration check
                service_result = await db.execute(
                    select(Service).where(Service.id == appointment.service_id)
                )
                service = service_result.scalar_one_or_none()
                
                if not service:
                    raise ValueError(f"Service with ID {appointment.service_id} not found")
                
                # Check if new slot is available
                is_available = await AppointmentService.is_slot_available(
                    db, 
                    update_data["datetime"], 
                    service.duration,
                    exclude_appointment_id=appointment.id
                )
                
                if not is_available:
                    raise ValueError(f"The slot at {update_data['datetime']} is not available")
                
                # Cancel existing reminders and reschedule
                await ReminderService.cancel_appointment_reminders(db, appointment.id)
            
            # Update appointment fields
            for field, value in update_data.items():
                setattr(appointment, field, value)
            
            db.add(appointment)
            await db.commit()
            await db.refresh(appointment)
            
            # If datetime was changed, schedule new reminders
            if "datetime" in update_data:
                await ReminderService.create_appointment_reminder(db, appointment.id)
            
            return appointment
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error updating appointment: {str(e)}")
    
    @staticmethod
    async def delete(db: AsyncSession, appointment: Appointment) -> None:
        """Delete an appointment"""
        try:
            # Cancel reminders first
            await ReminderService.cancel_appointment_reminders(db, appointment.id)
            
            # Delete the appointment
            await db.delete(appointment)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error deleting appointment: {str(e)}")
    
    @staticmethod
    async def cancel(db: AsyncSession, appointment: Appointment) -> Appointment:
        """Cancel an appointment"""
        try:
            appointment.status = AppointmentStatus.CANCELLED
            
            db.add(appointment)
            await db.commit()
            await db.refresh(appointment)
            
            # Cancel any pending reminders
            await ReminderService.cancel_appointment_reminders(db, appointment.id)
            
            return appointment
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error cancelling appointment: {str(e)}")
    
    @staticmethod
    async def confirm(db: AsyncSession, appointment: Appointment) -> Appointment:
        """Confirm an appointment"""
        try:
            appointment.status = AppointmentStatus.CONFIRMED
            
            db.add(appointment)
            await db.commit()
            await db.refresh(appointment)
            
            # Create a reminder if needed
            if appointment.datetime > datetime.utcnow():
                await ReminderService.create_appointment_reminder(db, appointment.id)
            
            return appointment
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error confirming appointment: {str(e)}")
    
    @staticmethod
    async def complete(db: AsyncSession, appointment: Appointment) -> Appointment:
        """Mark an appointment as completed"""
        try:
            appointment.status = AppointmentStatus.COMPLETED
            
            db.add(appointment)
            await db.commit()
            await db.refresh(appointment)
            
            # Cancel any pending reminders
            await ReminderService.cancel_appointment_reminders(db, appointment.id)
            
            return appointment
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error completing appointment: {str(e)}")
    
    @staticmethod
    async def is_slot_available(
        db: AsyncSession, 
        datetime_slot: datetime, 
        duration_minutes: int,
        exclude_appointment_id: Optional[int] = None
    ) -> bool:
        """
        Check if a time slot is available
        
        Args:
            db: Database session
            datetime_slot: The start time to check
            duration_minutes: Duration of the appointment in minutes
            exclude_appointment_id: Appointment ID to exclude from check (for updates)
            
        Returns:
            bool: True if the slot is available, False otherwise
        """
        try:
            # Check business hours
            if not AppointmentService._is_within_business_hours(datetime_slot, duration_minutes):
                return False
            
            # Calculate end time
            end_time = datetime_slot + timedelta(minutes=duration_minutes)
            
            # Check for existing appointments in the same time slot
            query = select(Appointment).where(
                and_(
                    Appointment.status != AppointmentStatus.CANCELLED,
                    or_(
                        # Appointment starts during the slot
                        and_(
                            Appointment.datetime >= datetime_slot,
                            Appointment.datetime < end_time
                        ),
                        # Appointment ends during the slot
                        and_(
                            Appointment.datetime < datetime_slot,
                            Appointment.datetime + func.make_interval(mins=Appointment.duration) > datetime_slot
                        )
                    )
                )
            )
            
            # Exclude the appointment we're updating
            if exclude_appointment_id:
                query = query.where(Appointment.id != exclude_appointment_id)
            
            result = await db.execute(query)
            existing_appointments = list(result.scalars().all())
            
            if existing_appointments:
                return False
            
            # Check for blocked schedules
            blocked_result = await db.execute(
                select(BlockedSchedule).where(
                    and_(
                        BlockedSchedule.start_time <= end_time,
                        BlockedSchedule.end_time >= datetime_slot
                    )
                )
            )
            blocked_schedules = list(blocked_result.scalars().all())
            
            if blocked_schedules:
                return False
            
            return True
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error checking slot availability: {str(e)}")
    
    @staticmethod
    def _is_within_business_hours(datetime_slot: datetime, duration_minutes: int) -> bool:
        """
        Check if the appointment fits within business hours
        
        Args:
            datetime_slot: The appointment start time
            duration_minutes: Duration of the appointment in minutes
            
        Returns:
            bool: True if the appointment fits within business hours
        """
        # Extract date components for business hours check
        slot_date = datetime_slot.date()
        slot_time = datetime_slot.time()
        end_time = (datetime_slot + timedelta(minutes=duration_minutes)).time()
        
        # Weekend check (0 = Monday, 6 = Sunday)
        if datetime_slot.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Parse business hours from settings
        try:
            # Convert "HH:MM" to time objects
            opening_time = time.fromisoformat(settings.HORARIO_APERTURA)
            closing_time = time.fromisoformat(settings.HORARIO_CIERRE)
            
            # Check if appointment starts and ends within business hours
            if slot_time < opening_time or end_time > closing_time:
                return False
                
            return True
        except (ValueError, AttributeError):
            # Default to 9am-5pm if format is invalid
            default_opening = time(9, 0)
            default_closing = time(17, 0)
            
            if slot_time < default_opening or end_time > default_closing:
                return False
                
            return True
    
    @staticmethod
    async def get_available_slots(
        db: AsyncSession,
        date: datetime.date,
        service_id: int,
        slot_duration: int = DEFAULT_SLOT_DURATION
    ) -> List[datetime]:
        """
        Get available time slots for a specific date and service
        
        Args:
            db: Database session
            date: The date to check
            service_id: Service ID to check duration
            slot_duration: Duration of slots in minutes (default 30)
            
        Returns:
            List[datetime]: List of available slot start times
        """
        try:
            # Get service information for duration
            service_result = await db.execute(
                select(Service).where(Service.id == service_id)
            )
            service = service_result.scalar_one_or_none()
            
            if not service:
                raise ValueError(f"Service with ID {service_id} not found")
            
            # Get business hours
            try:
                opening_time = time.fromisoformat(settings.HORARIO_APERTURA)
                closing_time = time.fromisoformat(settings.HORARIO_CIERRE)
            except (ValueError, AttributeError):
                # Default to 9am-5pm if format is invalid
                opening_time = time(9, 0)
                closing_time = time(17, 0)
            
            # Get all appointments for the day
            appointments = await AppointmentService.get_appointments_for_day(db, date)
            
            # Get blocked schedules for the day
            start_datetime = datetime.combine(date, time.min)
            end_datetime = datetime.combine(date, time.max)
            
            blocked_result = await db.execute(
                select(BlockedSchedule).where(
                    and_(
                        BlockedSchedule.start_time <= end_datetime,
                        BlockedSchedule.end_time >= start_datetime
                    )
                )
            )
            blocked_schedules = list(blocked_result.scalars().all())
            
            # Generate all possible slots for the day
            available_slots = []
            current_slot = datetime.combine(date, opening_time)
            end_of_day = datetime.combine(date, closing_time)
            
            while current_slot + timedelta(minutes=service.duration) <= end_of_day:
                # Check if this slot is available
                is_available = await AppointmentService.is_slot_available(
                    db, current_slot, service.duration
                )
                
                if is_available:
                    available_slots.append(current_slot)
                
                # Move to next slot
                current_slot += timedelta(minutes=slot_duration)
            
            return available_slots
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting available slots: {str(e)}")

    @staticmethod
    async def block_schedule(
        db: AsyncSession, 
        start_time: datetime,
        end_time: datetime,
        reason: str = "Blocked by admin"
    ) -> BlockedSchedule:
        """
        Block a time period in the schedule
        
        Args:
            db: Database session
            start_time: Start time of the block
            end_time: End time of the block
            reason: Reason for blocking
            
        Returns:
            BlockedSchedule: The created blocked schedule
        """
        try:
            blocked_schedule = BlockedSchedule(
                start_time=start_time,
                end_time=end_time,
                reason=reason
            )
            
            db.add(blocked_schedule)
            await db.commit()
            await db.refresh(blocked_schedule)
            
            return blocked_schedule
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error blocking schedule: {str(e)}")

    @staticmethod
    async def unblock_schedule(
        db: AsyncSession,
        blocked_schedule_id: int
    ) -> None:
        """
        Remove a schedule block
        
        Args:
            db: Database session
            blocked_schedule_id: ID of the blocked schedule to remove
        """
        try:
            result = await db.execute(
                select(BlockedSchedule).where(BlockedSchedule.id == blocked_schedule_id)
            )
            blocked_schedule = result.scalar_one_or_none()
            
            if not blocked_schedule:
                raise ValueError(f"Blocked schedule with ID {blocked_schedule_id} not found")
            
            await db.delete(blocked_schedule)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error unblocking schedule: {str(e)}")

    @staticmethod
    async def get_blocked_schedules(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[BlockedSchedule]:
        """
        Get all blocked schedules, optionally filtered by date range
        
        Args:
            db: Database session
            start_date: Optional start date filter
            end_date: Optional end date filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[BlockedSchedule]: List of blocked schedules
        """
        try:
            query = select(BlockedSchedule).order_by(BlockedSchedule.start_time)
            
            if start_date:
                query = query.where(BlockedSchedule.end_time >= start_date)
            
            if end_date:
                query = query.where(BlockedSchedule.start_time <= end_date)
            
            query = query.offset(skip).limit(limit)
            
            result = await db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting blocked schedules: {str(e)}") 