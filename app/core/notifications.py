"""
Notification system for sending SMS and WhatsApp messages using Twilio.
"""
import logging
import os
from enum import Enum
from typing import Optional, Dict, Any

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from fastapi import HTTPException

logger = logging.getLogger("app.core.notifications")

class NotificationType(str, Enum):
    """Types of notifications that can be sent."""
    SMS = "sms"
    WHATSAPP = "whatsapp"


class NotificationService:
    """Service for sending SMS and WhatsApp notifications using Twilio."""
    
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_phone: Optional[str] = None,
        from_whatsapp: Optional[str] = None
    ):
        """
        Initialize the Twilio notification service.
        
        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_phone: Twilio phone number for SMS
            from_whatsapp: Twilio phone number for WhatsApp
        """
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_phone = from_phone or os.getenv("TWILIO_PHONE_NUMBER")
        self.from_whatsapp = from_whatsapp or os.getenv("TWILIO_WHATSAPP_NUMBER", self.from_phone)
        
        # Initialize Twilio client if credentials are available
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")
                self.client = None
        else:
            logger.warning("Twilio credentials not found, notifications will be logged only")
            self.client = None
    
    async def send_notification(
        self,
        to_phone: str,
        message: str,
        notification_type: NotificationType = NotificationType.SMS,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a notification to a user.
        
        Args:
            to_phone: Recipient's phone number
            message: Message content
            notification_type: Type of notification (SMS or WhatsApp)
            extra_data: Additional data for the notification
            
        Returns:
            Dict: Information about the sent message
        """
        # Validate phone number format (simple validation)
        if not to_phone or not to_phone.startswith("+"):
            logger.error(f"Invalid phone number format: {to_phone}")
            raise HTTPException(status_code=400, detail="Invalid phone number format")
        
        # Format the 'to' number for WhatsApp
        if notification_type == NotificationType.WHATSAPP:
            to_formatted = f"whatsapp:{to_phone}"
            from_formatted = f"whatsapp:{self.from_whatsapp}"
        else:
            to_formatted = to_phone
            from_formatted = self.from_phone
            
        # Log the notification
        logger.info(f"Sending {notification_type} to {to_phone}: {message}")
        
        # If Twilio is not configured, just log the message
        if not self.client:
            logger.info(f"Twilio not configured. Would send: {message} to {to_formatted}")
            return {"status": "logged_only", "to": to_phone, "message": message}
            
        # Send the message via Twilio
        try:
            twilio_message = self.client.messages.create(
                body=message,
                from_=from_formatted,
                to=to_formatted,
                **extra_data or {}
            )
            
            logger.info(f"Message sent successfully. SID: {twilio_message.sid}")
            
            return {
                "status": "sent",
                "message_sid": twilio_message.sid,
                "to": to_phone,
                "type": notification_type
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio error: {str(e)}")
            
            # Return detailed error information
            return {
                "status": "error",
                "error_code": e.code,
                "error_message": str(e),
                "to": to_phone,
                "type": notification_type
            }
            
        except Exception as e:
            logger.error(f"Unexpected error sending notification: {str(e)}")
            
            return {
                "status": "error",
                "error_message": str(e),
                "to": to_phone, 
                "type": notification_type
            }
            
    async def send_appointment_confirmation(self, phone: str, client_name: str, 
                                           service_name: str, appointment_date: str, 
                                           appointment_time: str) -> Dict[str, Any]:
        """
        Send appointment confirmation message.
        
        Args:
            phone: Client's phone number
            client_name: Client's name
            service_name: Service name
            appointment_date: Formatted date of appointment
            appointment_time: Formatted time of appointment
            
        Returns:
            Dict: Information about the sent message
        """
        message = (
            f"Hola {client_name}, tu cita para {service_name} ha sido confirmada "
            f"para el {appointment_date} a las {appointment_time}. "
            f"Gracias por elegir nuestro salón."
        )
        
        return await self.send_notification(
            to_phone=phone,
            message=message,
            notification_type=NotificationType.SMS
        )
        
    async def send_appointment_reminder(self, phone: str, client_name: str, 
                                       service_name: str, appointment_date: str, 
                                       appointment_time: str) -> Dict[str, Any]:
        """
        Send appointment reminder message.
        
        Args:
            phone: Client's phone number
            client_name: Client's name
            service_name: Service name
            appointment_date: Formatted date of appointment
            appointment_time: Formatted time of appointment
            
        Returns:
            Dict: Information about the sent message
        """
        message = (
            f"Recordatorio: Hola {client_name}, tienes una cita para {service_name} "
            f"mañana {appointment_date} a las {appointment_time}. "
            f"Por favor confirma respondiendo SI o NO."
        )
        
        return await self.send_notification(
            to_phone=phone,
            message=message,
            notification_type=NotificationType.SMS
        )


# Create a singleton instance
notification_service = NotificationService() 