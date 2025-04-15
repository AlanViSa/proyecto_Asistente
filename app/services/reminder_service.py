"""
Service for handling reminder processing and delivery.
"""
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.reminder import Reminder
from app.models.appointment import AppointmentStatus
from app.core.notifications import NotificationService


class ReminderService:
    """
    Service class for reminder-related business logic.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService()
    
    def process_pending_reminders(self) -> int:
        """
        Process all pending reminders that are due.
        
        Returns:
            int: Number of reminders processed
        """
        # Get all pending reminders that are due
        pending_reminders = self.db.query(Reminder).filter(
            and_(
                Reminder.sent == False,
                Reminder.scheduled_time <= datetime.now(),
                # Only process reminders for pending/confirmed appointments
                Reminder.appointment.has(
                    status=AppointmentStatus.PENDING
                ) | Reminder.appointment.has(
                    status=AppointmentStatus.CONFIRMED
                )
            )
        ).all()
        
        sent_count = 0
        for reminder in pending_reminders:
            if self._send_reminder(reminder):
                sent_count += 1
                
                # Mark as sent
                reminder.sent = True
                self.db.add(reminder)
        
        # Commit all changes
        if sent_count > 0:
            self.db.commit()
            
        return sent_count
    
    def _send_reminder(self, reminder: Reminder) -> bool:
        """
        Send a single reminder notification.
        
        Args:
            reminder: The reminder to send
            
        Returns:
            bool: True if successfully sent, False otherwise
        """
        appointment = reminder.appointment
        user = appointment.user
        
        # Skip if user has no phone
        if not user.phone:
            return False
        
        # Attempt to send the message
        try:
            self.notification_service.send_sms(
                to_number=user.phone,
                message=reminder.message
            )
            return True
        except Exception as e:
            # Log the error but don't fail the entire batch
            print(f"Error sending reminder {reminder.id}: {str(e)}")
            return False
    
    def get_pending_reminders(self) -> List[Reminder]:
        """
        Get all pending reminders.
        
        Returns:
            List[Reminder]: List of pending reminders
        """
        return self.db.query(Reminder).filter(
            Reminder.sent == False
        ).order_by(Reminder.scheduled_time).all()
    
    def reschedule_reminders_for_appointment(self, appointment_id: int) -> None:
        """
        Delete and reschedule reminders for an appointment.
        Used when an appointment is rescheduled.
        
        Args:
            appointment_id: The ID of the appointment to reschedule reminders for
        """
        # Delete existing reminders
        self.db.query(Reminder).filter(
            Reminder.appointment_id == appointment_id,
            Reminder.sent == False
        ).delete()
        
        # Get the appointment and call the appointment service to reschedule
        from app.services.appointment_service import AppointmentService
        appointment_service = AppointmentService(self.db)
        appointment = self.db.query(appointment_service.get_appointment_by_id(appointment_id))
        
        # Only reschedule if the appointment exists and is still active
        if appointment and appointment.status in [AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]:
            appointment_service._schedule_reminders(appointment) 