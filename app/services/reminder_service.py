"""
Service for reminder management
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import DatabaseError
from app.models.reminder import Reminder, ReminderStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.client import Client
from app.schemas.reminder import ReminderCreate, ReminderUpdate

class ReminderService:
    """Service for reminder operations"""

    @staticmethod
    async def get_by_id(db: AsyncSession, reminder_id: int) -> Optional[Reminder]:
        """Gets a reminder by ID"""
        try:
            result = await db.execute(
                select(Reminder).where(Reminder.id == reminder_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting reminder by ID: {str(e)}")

    @staticmethod
    async def get_by_appointment(db: AsyncSession, appointment_id: int) -> List[Reminder]:
        """Gets reminders for an appointment"""
        try:
            result = await db.execute(
                select(Reminder).where(Reminder.appointment_id == appointment_id)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting reminders by appointment: {str(e)}")

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Reminder]:
        """Gets all reminders"""
        try:
            result = await db.execute(
                select(Reminder)
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting all reminders: {str(e)}")

    @staticmethod
    async def get_pending_reminders(db: AsyncSession) -> List[Reminder]:
        """
        Gets all pending reminders that should be sent now
        
        Returns reminders where:
        - Status is PENDING
        - Scheduled time is in the past
        - The associated appointment is still CONFIRMED
        """
        try:
            now = datetime.utcnow()
            
            # Join with appointment to filter by appointment status
            result = await db.execute(
                select(Reminder)
                .join(Appointment, Reminder.appointment_id == Appointment.id)
                .where(
                    and_(
                        Reminder.status == ReminderStatus.PENDING,
                        Reminder.scheduled_time <= now,
                        Appointment.status == AppointmentStatus.CONFIRMED
                    )
                )
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting pending reminders: {str(e)}")

    @staticmethod
    async def create(
        db: AsyncSession,
        reminder_in: ReminderCreate
    ) -> Reminder:
        """Creates a new reminder"""
        try:
            reminder = Reminder(**reminder_in.dict())
            db.add(reminder)
            await db.commit()
            await db.refresh(reminder)
            return reminder
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error creating reminder: {str(e)}")

    @staticmethod
    async def update(
        db: AsyncSession,
        reminder: Reminder,
        reminder_in: ReminderUpdate
    ) -> Reminder:
        """Updates a reminder"""
        try:
            update_data = reminder_in.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(reminder, field, value)
            
            db.add(reminder)
            await db.commit()
            await db.refresh(reminder)
            return reminder
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error updating reminder: {str(e)}")

    @staticmethod
    async def delete(db: AsyncSession, reminder: Reminder) -> None:
        """Deletes a reminder"""
        try:
            await db.delete(reminder)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error deleting reminder: {str(e)}")
            
    @staticmethod
    async def mark_as_sent(db: AsyncSession, reminder: Reminder) -> Reminder:
        """Marks a reminder as sent"""
        try:
            reminder.status = ReminderStatus.SENT
            reminder.sent_at = datetime.utcnow()
            
            db.add(reminder)
            await db.commit()
            await db.refresh(reminder)
            return reminder
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error marking reminder as sent: {str(e)}")

    @staticmethod
    async def create_appointment_reminder(
        db: AsyncSession, 
        appointment_id: int,
        hours_before: int = 24
    ) -> Reminder:
        """
        Creates a reminder for an appointment
        
        Args:
            db: Database session
            appointment_id: Appointment ID
            hours_before: Hours before the appointment to send the reminder
            
        Returns:
            Reminder: The created reminder
        """
        try:
            # Get the appointment
            result = await db.execute(
                select(Appointment).where(Appointment.id == appointment_id)
            )
            appointment = result.scalar_one_or_none()
            
            if not appointment:
                raise ValueError(f"Appointment with ID {appointment_id} not found")
                
            # Calculate scheduled time
            scheduled_time = appointment.datetime - timedelta(hours=hours_before)
            
            # Create the reminder
            reminder_data = ReminderCreate(
                appointment_id=appointment_id,
                type="APPOINTMENT",
                scheduled_time=scheduled_time,
                status=ReminderStatus.PENDING
            )
            
            return await ReminderService.create(db, reminder_data)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error creating appointment reminder: {str(e)}")
            
    @staticmethod
    async def cancel_appointment_reminders(db: AsyncSession, appointment_id: int) -> None:
        """
        Cancels all pending reminders for an appointment
        
        Args:
            db: Database session
            appointment_id: Appointment ID
        """
        try:
            # Get all pending reminders for the appointment
            result = await db.execute(
                select(Reminder).where(
                    and_(
                        Reminder.appointment_id == appointment_id,
                        Reminder.status == ReminderStatus.PENDING
                    )
                )
            )
            reminders = list(result.scalars().all())
            
            # Cancel each reminder
            for reminder in reminders:
                reminder.status = ReminderStatus.CANCELLED
                db.add(reminder)
                
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error cancelling appointment reminders: {str(e)}") 