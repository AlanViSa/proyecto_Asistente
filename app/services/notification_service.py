"""
Service for notification handling through multiple channels
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import logging
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.appointment import Appointment, AppointmentStatus
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

class NotificationChannel(str, Enum):
    """Available notification channels"""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"

class NotificationTemplate(str, Enum):
    """Available notification templates"""
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_CONFIRMED = "appointment_confirmed"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    APPOINTMENT_COMPLETED = "appointment_completed"
    APPOINTMENT_NO_SHOW = "appointment_no_show"
    REMINDER = "reminder"

class NotificationService:
    """Service for sending notifications"""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()

    @staticmethod
    def _format_datetime(dt: datetime, timezone: Optional[str] = None) -> str:
        """
        Formats a date and time for display in notifications
        
        Args:
            dt: Date and time to format
            timezone: Client's timezone (optional)
        """
        if timezone:
            try:
                tz = ZoneInfo(timezone)
                local_dt = dt.astimezone(tz)
            except Exception as e:
                logger.warning(f"Error converting timezone {timezone}: {e}")
                tz = ZoneInfo(settings.TIMEZONE)
                local_dt = dt.astimezone(tz)
        else:
            tz = ZoneInfo(settings.TIMEZONE)
            local_dt = dt.astimezone(tz)
            
        return local_dt.strftime("%m/%d/%Y %H:%M")

    @staticmethod
    def _get_template_content(
        template: NotificationTemplate,
        context: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Gets template content for different channels
        
        Args:
            template: Template type to use
            context: Variables for the template
            
        Returns:
            Dict with content for each message type (subject and body)
        """
        templates = {
            NotificationTemplate.APPOINTMENT_CREATED: {
                "subject": "Appointment Scheduled",
                "body": (
                    f"Hello {context['client_name']},\n\n"
                    f"Your appointment has been scheduled for {context['datetime']}.\n"
                    f"Service: {context['service']}\n"
                    f"Duration: {context['duration']} minutes\n\n"
                    "Please confirm your attendance."
                )
            },
            NotificationTemplate.APPOINTMENT_CONFIRMED: {
                "subject": "Appointment Confirmed",
                "body": (
                    f"Hello {context['client_name']},\n\n"
                    f"Your appointment for {context['datetime']} has been confirmed.\n"
                    "We'll see you soon!"
                )
            },
            NotificationTemplate.APPOINTMENT_CANCELLED: {
                "subject": "Appointment Cancelled",
                "body": (
                    f"Hello {context['client_name']},\n\n"
                    f"Your appointment for {context['datetime']} has been cancelled.\n"
                    "If you would like to reschedule, please contact us."
                )
            },
            NotificationTemplate.APPOINTMENT_COMPLETED: {
                "subject": "Appointment Completed",
                "body": (
                    f"Hello {context['client_name']},\n\n"
                    f"Thank you for your visit. Your appointment on {context['datetime']} "
                    "has been completed.\nWe hope to see you again soon!"
                )
            },
            NotificationTemplate.APPOINTMENT_NO_SHOW: {
                "subject": "Missed Appointment",
                "body": (
                    f"Hello {context['client_name']},\n\n"
                    f"We noticed you were unable to attend your appointment on {context['datetime']}.\n"
                    "If you would like to reschedule, please contact us."
                )
            },
            NotificationTemplate.REMINDER: {
                "subject": "Appointment Reminder",
                "body": (
                    f"Hello {context['client_name']},\n\n"
                    f"This is a reminder of your appointment scheduled for {context['datetime']}.\n"
                    f"Service: {context['service']}\n"
                    "We look forward to seeing you!"
                )
            }
        }
        
        return templates.get(template, {
            "subject": "Notification",
            "body": "No content"
        })

    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        body: str
    ) -> bool:
        """
        Sends an email using SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            
        Returns:
            bool: True if sending was successful, False if not
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USER
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD.get_secret_value())
                server.send_message(msg)
            
            return True
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    @staticmethod
    async def notify_appointment_status(
        appointment: Appointment,
        template: NotificationTemplate,
        channels: Optional[List[NotificationChannel]] = None,
        local_datetime: Optional[datetime] = None
    ) -> bool:
        """
        Sends a notification about an appointment status
        
        Args:
            appointment: Appointment to notify about
            template: Template to use
            channels: Channels to use (optional)
            local_datetime: Date and time in the client's timezone (optional)
            
        Returns:
            True if at least one notification was sent successfully
        """
        if not channels:
            channels = [NotificationChannel.EMAIL]
            
        # Get client timezone if available
        timezone = None
        if hasattr(appointment.client, 'notification_preferences'):
            timezone = appointment.client.notification_preferences.timezone
            
        # Use provided local datetime or format appointment datetime
        formatted_datetime = (
            local_datetime.strftime("%m/%d/%Y %H:%M")
            if local_datetime
            else NotificationService._format_datetime(appointment.datetime, timezone)
        )
            
        context = {
            "client_name": appointment.client.full_name,
            "datetime": formatted_datetime,
            "service": appointment.service.name if appointment.service else "Service",
            "duration": str(appointment.duration_minutes)
        }
        
        content = NotificationService._get_template_content(template, context)
        success = False
        
        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL and appointment.client.email:
                    if await NotificationService.send_email(
                        appointment.client.email,
                        content["subject"],
                        content["body"]
                    ):
                        success = True
                        
                elif channel == NotificationChannel.SMS and appointment.client.phone:
                    # TODO: Implement SMS sending
                    logger.info(f"SMS not implemented for {appointment.client.phone}")
                    
                elif channel == NotificationChannel.WHATSAPP and appointment.client.phone:
                    # TODO: Implement WhatsApp sending
                    logger.info(f"WhatsApp not implemented for {appointment.client.phone}")
                    
            except Exception as e:
                logger.error(f"Error sending notification via {channel}: {str(e)}")
                
        return success
        
    async def format_message(self, template: str, **kwargs) -> str:
        """
        Formats a message using a template and variables.
        """
        return template.format(
            business_name=settings.BUSINESS_NAME,
            **kwargs
        )

    async def send_confirmation_message(
        self,
        appointment: Appointment,
        client_id: Optional[int] = None,
        phone: Optional[str] = None
    ) -> None:
        """
        Sends a confirmation message for a new appointment.
        """
        message = self.format_message(
            "Hello! Your appointment at {business_name} has been confirmed:\n"
            "📅 Date: {date}\n"
            "⏰ Time: {time}\n"
            "💇 Service: {service}\n"
            "We look forward to seeing you!",
            date=appointment.datetime.strftime("%m/%d/%Y"),
            time=appointment.datetime.strftime("%H:%M"),
            service=appointment.service.name if appointment.service else "Service"
        )
        # Use provided phone or try to get it from the appointment
        client_phone = phone or (appointment.client.phone if hasattr(appointment, 'client') else None)
        if not client_phone:
            raise ValueError("Could not obtain client phone number")
            
        await self.whatsapp_service.send_message(client_phone, message)

    async def send_reminder_message(self, appointment: Appointment) -> None:
        """
        Sends a reminder 24 hours before the appointment.
        """
        message = self.format_message(
            "Hello! This is a reminder of your appointment tomorrow at {business_name}:\n"
            "📅 Date: {date}\n"
            "⏰ Time: {time}\n"
            "💇 Service: {service}\n"
            "We look forward to seeing you!",
            date=appointment.datetime.strftime("%m/%d/%Y"),
            time=appointment.datetime.strftime("%H:%M"),
            service=appointment.service.name if appointment.service else "Service"
        )
        await self.whatsapp_service.send_message(appointment.client.phone, message)

    async def send_cancellation_message(self, appointment: Appointment) -> None:
        """
        Sends a cancellation confirmation message.
        """
        message = self.format_message(
            "Your appointment at {business_name} has been cancelled:\n"
            "📅 Date: {date}\n"
            "⏰ Time: {time}\n"
            "💇 Service: {service}\n"
            "We hope to see you soon.",
            date=appointment.datetime.strftime("%m/%d/%Y"),
            time=appointment.datetime.strftime("%H:%M"),
            service=appointment.service.name if appointment.service else "Service" 
        )
        await self.whatsapp_service.send_message(appointment.client.phone, message)

    async def check_and_send_reminders(self, db: Session) -> None:
        """
        Checks and sends reminders for appointments scheduled for the next day.
        """
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)

        appointments = db.query(Appointment).filter(
            Appointment.datetime.between(tomorrow_start, tomorrow_end),
            Appointment.status == AppointmentStatus.CONFIRMED,
            Appointment.reminder_sent == False
        ).all()

        for appointment in appointments:
            await self.send_reminder_message(appointment)
            appointment.reminder_sent = True
            db.add(appointment)

        db.commit()

    async def send_appointment_notifications(self, db: Session):
        """
        Sends notifications for scheduled appointments.
        - Reminders 24 hours before
        - Confirmations after scheduling
        - Follow-up after the appointment
        """
        try:
            # Get appointments for reminders (24 hours before)
            tomorrow = datetime.now() + timedelta(days=1)
            tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)

            pending_reminders = db.query(Appointment).filter(
                Appointment.datetime.between(tomorrow_start, tomorrow_end),
                Appointment.status == AppointmentStatus.CONFIRMED,
                Appointment.reminder_sent == False
            ).all()

            # Send reminders
            for appointment in pending_reminders:
                await self.send_reminder_message(appointment)
                appointment.reminder_sent = True
                db.add(appointment)

            db.commit()

        except Exception as e:
            db.rollback()
            print(f"Error sending notifications: {str(e)}")

    async def _send_reminder(self, appointment: Appointment):
        """
        Sends a reminder for a specific appointment.
        """
        await self.send_reminder_message(appointment)

    async def send_appointment_confirmation(self, appointment: Appointment):
        """
        Sends an immediate confirmation when an appointment is scheduled.
        """
        appointment_details = {
            "date": appointment.datetime.strftime("%m/%d/%Y"),
            "time": appointment.datetime.strftime("%H:%M"),
            "service": appointment.service.name if appointment.service else "Service"
        }

        await self.whatsapp_service.send_appointment_confirmation(
            appointment.client.phone,
            appointment_details
        )

    async def send_follow_up(self, appointment: Appointment):
        """
        Sends a follow-up message after the appointment.
        """
        message = (
            f"¡Hola! Esperamos que hayas disfrutado tu visita a nuestro salón. "
            f"Nos encantaría conocer tu experiencia y saber si hay algo en lo que "
            f"podamos mejorar. ¡Gracias por tu preferencia!"
        )

        await self.whatsapp_service.send_message(
            appointment.client.phone,
            message
        ) 