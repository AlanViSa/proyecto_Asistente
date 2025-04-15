"""
Service for handling appointment business logic.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.appointment import Appointment, AppointmentStatus
from app.models.service import Service
from app.models.reminder import Reminder
from app.core.config import settings
from app.core.notifications import NotificationService


class AppointmentService:
    """
    Service class for appointment-related business logic.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService()
    
    def check_availability(
        self, 
        requested_time: datetime, 
        duration_minutes: int,
        exclude_appointment_id: Optional[int] = None
    ) -> bool:
        """
        Check if a time slot is available.
        
        Args:
            requested_time: The requested appointment time
            duration_minutes: Duration of the appointment in minutes
            exclude_appointment_id: Optional ID of appointment to exclude from check (for updates)
            
        Returns:
            bool: True if the time slot is available, False otherwise
        """
        # Check if within business hours
        opening_hour = int(settings.HORARIO_APERTURA.split(":")[0])
        closing_hour = int(settings.HORARIO_CIERRE.split(":")[0])
        
        if requested_time.hour < opening_hour or requested_time.hour >= closing_hour:
            return False
        
        # Check if in the past
        if requested_time < datetime.now():
            return False
            
        # Calculate end time
        end_time = requested_time + timedelta(minutes=duration_minutes)
        
        # Query for overlapping appointments
        query = self.db.query(Appointment).filter(
            and_(
                Appointment.status.in_([
                    AppointmentStatus.PENDING,
                    AppointmentStatus.CONFIRMED,
                ]),
                or_(
                    # New appointment starts during an existing one
                    and_(
                        Appointment.datetime <= requested_time,
                        requested_time < Appointment.datetime + timedelta(minutes=Appointment.duration)
                    ),
                    # New appointment ends during an existing one
                    and_(
                        Appointment.datetime < end_time,
                        end_time <= Appointment.datetime + timedelta(minutes=Appointment.duration)
                    ),
                    # New appointment completely contains an existing one
                    and_(
                        requested_time <= Appointment.datetime,
                        Appointment.datetime + timedelta(minutes=Appointment.duration) <= end_time
                    )
                )
            )
        )
        
        # Exclude the current appointment if we're updating
        if exclude_appointment_id:
            query = query.filter(Appointment.id != exclude_appointment_id)
        
        # If any overlapping appointments exist, the time is not available
        return query.count() == 0
    
    def create_appointment(
        self, 
        user_id: int, 
        service_id: int, 
        datetime: datetime,
        notes: Optional[str] = None
    ) -> Appointment:
        """
        Create a new appointment.
        
        Args:
            user_id: User ID for the appointment
            service_id: Service ID for the appointment
            datetime: When the appointment is scheduled
            notes: Optional notes for the appointment
            
        Returns:
            Appointment: The created appointment object
        """
        # Get the service to determine duration
        service = self.db.query(Service).filter(Service.id == service_id).first()
        
        # Create the appointment
        appointment = Appointment(
            user_id=user_id,
            service_id=service_id,
            datetime=datetime,
            duration=service.duration,
            status=AppointmentStatus.PENDING,
            notes=notes
        )
        
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        
        # Schedule reminders
        self._schedule_reminders(appointment)
        
        # Send confirmation notification
        self._notify_appointment_created(appointment)
        
        return appointment
    
    def _schedule_reminders(self, appointment: Appointment) -> None:
        """
        Schedule reminders for an appointment.
        
        Args:
            appointment: The appointment to schedule reminders for
        """
        # Schedule reminder for 24 hours before
        reminder_time_24h = appointment.datetime - timedelta(hours=24)
        if reminder_time_24h > datetime.now():
            reminder_24h = Reminder(
                appointment_id=appointment.id,
                scheduled_time=reminder_time_24h,
                sent=False,
                message=f"Recordatorio: Tiene una cita mañana a las {appointment.datetime.strftime('%H:%M')}."
            )
            self.db.add(reminder_24h)
        
        # Schedule reminder for 1 hour before
        reminder_time_1h = appointment.datetime - timedelta(hours=1)
        if reminder_time_1h > datetime.now():
            reminder_1h = Reminder(
                appointment_id=appointment.id,
                scheduled_time=reminder_time_1h,
                sent=False,
                message=f"Recordatorio: Tiene una cita en 1 hora a las {appointment.datetime.strftime('%H:%M')}."
            )
            self.db.add(reminder_1h)
        
        self.db.commit()
    
    def _notify_appointment_created(self, appointment: Appointment) -> None:
        """
        Send notification for appointment creation.
        
        Args:
            appointment: The newly created appointment
        """
        # Get user and service information for the message
        user = appointment.user
        service = appointment.service
        
        message = (
            f"Su cita para {service.name} ha sido agendada para "
            f"{appointment.datetime.strftime('%d/%m/%Y a las %H:%M')}. "
            f"Duración estimada: {service.duration} minutos."
        )
        
        # Only attempt to send if user has phone number
        if user.phone:
            try:
                self.notification_service.send_sms(
                    to_number=user.phone,
                    message=message
                )
            except Exception as e:
                # Log the error but don't fail the appointment creation
                print(f"Error sending notification: {str(e)}")
    
    def get_upcoming_appointments(self, user_id: Optional[int] = None) -> List[Appointment]:
        """
        Get list of upcoming appointments, optionally filtered by user.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            List[Appointment]: List of upcoming appointments
        """
        query = self.db.query(Appointment).filter(
            and_(
                Appointment.datetime >= datetime.now(),
                Appointment.status.in_([
                    AppointmentStatus.PENDING, 
                    AppointmentStatus.CONFIRMED
                ])
            )
        ).order_by(Appointment.datetime)
        
        if user_id:
            query = query.filter(Appointment.user_id == user_id)
            
        return query.all() 