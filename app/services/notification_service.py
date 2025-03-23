from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.cita import Cita, EstadoCita
from app.services.whatsapp_service import WhatsAppService
from typing import List, Dict, Any, Optional
from app.core.config import get_settings

settings = get_settings()

class NotificationService:
    def __init__(self):
        self.whatsapp_service = WhatsAppService()

    def format_message(self, template: str, **kwargs) -> str:
        """
        Formatea un mensaje usando un template y variables.
        """
        return template.format(
            business_name=settings.BUSINESS_NAME,
            **kwargs
        )

    async def send_confirmation_message(
        self,
        cita: Cita,
        cliente_id: Optional[int] = None,
        telefono: Optional[str] = None
    ) -> None:
        """
        Envía un mensaje de confirmación para una cita nueva.
        """
        message = self.format_message(
            "¡Hola! Tu cita en {business_name} ha sido confirmada:\n"
            "📅 Fecha: {fecha}\n"
            "⏰ Hora: {hora}\n"
            "💇 Servicio: {servicio}\n"
            "Te esperamos!",
            fecha=cita.fecha_hora.strftime("%d/%m/%Y"),
            hora=cita.fecha_hora.strftime("%H:%M"),
            servicio=cita.servicio
        )
        # Usar el teléfono proporcionado o intentar obtenerlo de la cita
        phone = telefono or (cita.cliente.telefono if hasattr(cita, 'cliente') else None)
        if not phone:
            raise ValueError("No se pudo obtener el número de teléfono del cliente")
            
        await self.whatsapp_service.send_message(phone, message)

    async def send_reminder_message(self, cita: Cita) -> None:
        """
        Envía un recordatorio 24 horas antes de la cita.
        """
        message = self.format_message(
            "¡Hola! Te recordamos tu cita mañana en {business_name}:\n"
            "📅 Fecha: {fecha}\n"
            "⏰ Hora: {hora}\n"
            "💇 Servicio: {servicio}\n"
            "¡Te esperamos!",
            fecha=cita.fecha_hora.strftime("%d/%m/%Y"),
            hora=cita.fecha_hora.strftime("%H:%M"),
            servicio=cita.servicio
        )
        await self.whatsapp_service.send_message(cita.cliente.telefono, message)

    async def send_cancellation_message(self, cita: Cita) -> None:
        """
        Envía un mensaje de confirmación de cancelación.
        """
        message = self.format_message(
            "Tu cita en {business_name} ha sido cancelada:\n"
            "📅 Fecha: {fecha}\n"
            "⏰ Hora: {hora}\n"
            "💇 Servicio: {servicio}\n"
            "Esperamos verte pronto.",
            fecha=cita.fecha_hora.strftime("%d/%m/%Y"),
            hora=cita.fecha_hora.strftime("%H:%M"),
            servicio=cita.servicio
        )
        await self.whatsapp_service.send_message(cita.cliente.telefono, message)

    async def check_and_send_reminders(self, db: Session) -> None:
        """
        Verifica y envía recordatorios para las citas del día siguiente.
        """
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)

        citas = db.query(Cita).filter(
            Cita.fecha_hora.between(tomorrow_start, tomorrow_end),
            Cita.estado == EstadoCita.CONFIRMADA,
            Cita.recordatorio_enviado == False
        ).all()

        for cita in citas:
            await self.send_reminder_message(cita)
            cita.recordatorio_enviado = True
            db.add(cita)

        db.commit()

    async def send_appointment_notifications(self, db: Session):
        """
        Envía notificaciones para las citas programadas.
        - Recordatorios 24 horas antes
        - Confirmaciones después de agendar
        - Seguimiento después de la cita
        """
        try:
            # Obtener citas para recordatorios (24 horas antes)
            tomorrow = datetime.now() + timedelta(days=1)
            tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)

            pending_reminders = db.query(Cita).filter(
                Cita.fecha_hora.between(tomorrow_start, tomorrow_end),
                Cita.estado == EstadoCita.CONFIRMADA,
                Cita.recordatorio_enviado == False
            ).all()

            # Enviar recordatorios
            for cita in pending_reminders:
                await self.send_reminder_message(cita)
                cita.recordatorio_enviado = True
                db.add(cita)

            db.commit()

        except Exception as e:
            db.rollback()
            print(f"Error enviando notificaciones: {str(e)}")

    async def _send_reminder(self, cita: Cita):
        """
        Envía un recordatorio para una cita específica.
        """
        await self.send_reminder_message(cita)

    async def send_appointment_confirmation(self, cita: Cita):
        """
        Envía una confirmación inmediata cuando se agenda una cita.
        """
        appointment_details = {
            "fecha": cita.fecha_hora.strftime("%d/%m/%Y"),
            "hora": cita.fecha_hora.strftime("%H:%M"),
            "servicio": cita.servicio
        }

        await self.whatsapp_service.send_appointment_confirmation(
            cita.cliente.telefono,
            appointment_details
        )

    async def send_follow_up(self, cita: Cita):
        """
        Envía un mensaje de seguimiento después de la cita.
        """
        message = (
            f"¡Hola! Esperamos que hayas disfrutado tu visita a nuestro salón. "
            f"Nos encantaría conocer tu experiencia y saber si hay algo en lo que "
            f"podamos mejorar. ¡Gracias por tu preferencia!"
        )

        await self.whatsapp_service.send_message(
            cita.cliente.telefono,
            message
        ) 