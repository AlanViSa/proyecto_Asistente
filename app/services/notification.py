"""
Servicio para el manejo de notificaciones a través de diferentes canales
"""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import logging
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.models.cita import Cita, EstadoCita

logger = logging.getLogger(__name__)

class NotificationChannel(str, Enum):
    """Canales disponibles para notificaciones"""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"

class NotificationTemplate(str, Enum):
    """Templates disponibles para notificaciones"""
    CITA_CREADA = "cita_creada"
    CITA_CONFIRMADA = "cita_confirmada"
    CITA_CANCELADA = "cita_cancelada"
    CITA_COMPLETADA = "cita_completada"
    CITA_NO_ASISTIO = "cita_no_asistio"
    RECORDATORIO = "recordatorio"

class NotificationService:
    """Servicio para envío de notificaciones"""

    @staticmethod
    def _format_datetime(dt: datetime, zona_horaria: Optional[str] = None) -> str:
        """
        Formatea una fecha y hora para mostrar en notificaciones
        
        Args:
            dt: Fecha y hora a formatear
            zona_horaria: Zona horaria del cliente (opcional)
        """
        if zona_horaria:
            try:
                tz = ZoneInfo(zona_horaria)
                local_dt = dt.astimezone(tz)
            except Exception as e:
                logger.warning(f"Error al convertir zona horaria {zona_horaria}: {e}")
                tz = ZoneInfo(settings.TIMEZONE)
                local_dt = dt.astimezone(tz)
        else:
            tz = ZoneInfo(settings.TIMEZONE)
            local_dt = dt.astimezone(tz)
            
        return local_dt.strftime("%d/%m/%Y %H:%M")

    @staticmethod
    def _get_template_content(
        template: NotificationTemplate,
        context: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Obtiene el contenido del template para diferentes canales
        
        Args:
            template: Tipo de template a usar
            context: Variables para el template
            
        Returns:
            Dict con el contenido para cada tipo de mensaje (asunto y cuerpo)
        """
        templates = {
            NotificationTemplate.CITA_CREADA: {
                "subject": "Cita Programada",
                "body": (
                    f"Hola {context['nombre_cliente']},\n\n"
                    f"Tu cita ha sido programada para el {context['fecha_hora']}.\n"
                    f"Servicio: {context['servicio']}\n"
                    f"Duración: {context['duracion']} minutos\n\n"
                    "Por favor, confirma tu asistencia."
                )
            },
            NotificationTemplate.CITA_CONFIRMADA: {
                "subject": "Cita Confirmada",
                "body": (
                    f"Hola {context['nombre_cliente']},\n\n"
                    f"Tu cita para el {context['fecha_hora']} ha sido confirmada.\n"
                    "¡Te esperamos!"
                )
            },
            NotificationTemplate.CITA_CANCELADA: {
                "subject": "Cita Cancelada",
                "body": (
                    f"Hola {context['nombre_cliente']},\n\n"
                    f"Tu cita para el {context['fecha_hora']} ha sido cancelada.\n"
                    "Si deseas reagendar, por favor contáctanos."
                )
            },
            NotificationTemplate.CITA_COMPLETADA: {
                "subject": "Cita Completada",
                "body": (
                    f"Hola {context['nombre_cliente']},\n\n"
                    f"Gracias por tu visita. Tu cita del {context['fecha_hora']} "
                    "ha sido completada.\n¡Esperamos verte pronto!"
                )
            },
            NotificationTemplate.CITA_NO_ASISTIO: {
                "subject": "No Asistencia a Cita",
                "body": (
                    f"Hola {context['nombre_cliente']},\n\n"
                    f"Notamos que no pudiste asistir a tu cita del {context['fecha_hora']}.\n"
                    "Si deseas reagendar, por favor contáctanos."
                )
            },
            NotificationTemplate.RECORDATORIO: {
                "subject": "Recordatorio de Cita",
                "body": (
                    f"Hola {context['nombre_cliente']},\n\n"
                    f"Te recordamos tu cita programada para el {context['fecha_hora']}.\n"
                    f"Servicio: {context['servicio']}\n"
                    "¡Te esperamos!"
                )
            }
        }
        
        return templates.get(template, {
            "subject": "Notificación",
            "body": "Sin contenido"
        })

    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        body: str
    ) -> bool:
        """
        Envía un email usando SMTP
        
        Args:
            to_email: Dirección de correo del destinatario
            subject: Asunto del correo
            body: Cuerpo del correo
            
        Returns:
            bool: True si el envío fue exitoso, False si no
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
            logger.error(f"Error enviando email: {str(e)}")
            return False

    @staticmethod
    async def notify_appointment_status(
        cita: Cita,
        template: NotificationTemplate,
        channels: Optional[list[NotificationChannel]] = None,
        fecha_local: Optional[datetime] = None
    ) -> bool:
        """
        Envía una notificación sobre el estado de una cita
        
        Args:
            cita: Cita sobre la que notificar
            template: Template a usar
            channels: Canales a usar (opcional)
            fecha_local: Fecha y hora en la zona horaria del cliente (opcional)
            
        Returns:
            True si se envió al menos una notificación exitosamente
        """
        if not channels:
            channels = [NotificationChannel.EMAIL]
            
        # Obtener zona horaria del cliente si está disponible
        zona_horaria = None
        if hasattr(cita.cliente, 'preferencias_notificacion'):
            zona_horaria = cita.cliente.preferencias_notificacion.zona_horaria
            
        # Usar fecha local proporcionada o formatear la fecha de la cita
        fecha_formateada = (
            fecha_local.strftime("%d/%m/%Y %H:%M")
            if fecha_local
            else NotificationService._format_datetime(cita.fecha_hora, zona_horaria)
        )
            
        context = {
            "nombre_cliente": cita.cliente.nombre,
            "fecha_hora": fecha_formateada,
            "servicio": "Servicio",  # TODO: Agregar servicio a la cita
            "duracion": "60"  # TODO: Agregar duración a la cita
        }
        
        content = NotificationService._get_template_content(template, context)
        success = False
        
        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL and cita.cliente.email:
                    if await NotificationService.send_email(
                        cita.cliente.email,
                        content["subject"],
                        content["body"]
                    ):
                        success = True
                        
                elif channel == NotificationChannel.SMS and cita.cliente.telefono:
                    # TODO: Implementar envío de SMS
                    logger.info(f"SMS no implementado para {cita.cliente.telefono}")
                    
                elif channel == NotificationChannel.WHATSAPP and cita.cliente.telefono:
                    # TODO: Implementar envío de WhatsApp
                    logger.info(f"WhatsApp no implementado para {cita.cliente.telefono}")
                    
            except Exception as e:
                logger.error(f"Error enviando notificación por {channel}: {str(e)}")
                
        return success 