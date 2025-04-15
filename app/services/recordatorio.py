"""
Service for managing appointment reminders.
"""
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import DatabaseError
from app.models.cita import Cita, EstadoCita
from app.models.cliente import Cliente
from app.models.recordatorio_enviado import RecordatorioEnviado
from app.services.notification import NotificationService, NotificationTemplate, NotificationChannel
from sqlalchemy import select, and_, exists
from typing import List, Dict, Set, Optional
from zoneinfo import ZoneInfo

class RecordatorioService:
    """Service to manage appointment reminders"""

    REMINDERS = {"24h": {"hours": 24, "template": NotificationTemplate.REMINDER}, "2h": {"hours": 2, "template": NotificationTemplate.REMINDER}}
    """Reminders configuration"""


    @staticmethod
    async def _get_canales_cliente(cliente) -> Set[NotificationChannel]:
        """Obtiene los canales habilitados para un cliente"""
        canales = set()
        if not hasattr(cliente, 'preferencias_notificacion'):
            # Si no tiene preferencias, usar valores por defecto
            return { NotificationChannel.EMAIL }
            
        prefs = cliente.preferencias_notificacion
        if prefs.email_habilitado and cliente.email:
            canales.add(NotificationChannel.EMAIL)
        if prefs.sms_habilitado and cliente.telefono:
            canales.add(NotificationChannel.SMS)
        if prefs.whatsapp_habilitado and cliente.telefono:
            canales.add(NotificationChannel.WHATSAPP)
            
        return canales or { NotificationChannel.EMAIL }  # Email as fallback

    @staticmethod
    async def _reminder_already_sent(db: AsyncSession, appointment_id: int, reminder_type: str, channel: NotificationChannel) -> bool:
        """Check if a reminder has already been sent"""
        query = select(
            exists().where(
                and_(
                    RecordatorioEnviado.appointment_id == appointment_id,
                    RecordatorioEnviado.reminder_type == reminder_type,
                    RecordatorioEnviado.channel == channel,
                    RecordatorioEnviado.successful == True
                )
            )
        )
        result = await db.execute(query)
        return result.scalar()

    @staticmethod
    async def _reminder_enabled(client: Cliente, reminder_type: str) -> bool:
        """Check if a reminder type is enabled for the client"""
        if not hasattr(cliente, 'preferencias_notificacion'):
            return True  # By default, all reminders are enabled
            
        prefs = cliente.preferencias_notificacion
        if reminder_type == "24h":
            return prefs.reminder_24h
        elif reminder_type == "2h":
            return prefs.reminder_2h
        return True

    @staticmethod
    async def _adjust_timezone(date: datetime, client: Cliente) -> datetime:
        """
        Adjust a date to the client's timezone

        """
        if not hasattr(cliente, 'preferencias_notificacion'):
            return fecha
            
        zona = cliente.preferencias_notificacion.zona_horaria or "America/Mexico_City"
        return fecha.astimezone(ZoneInfo(zona))

    @staticmethod
    async def get_appointments_to_remind(db: AsyncSession, reminder_type: str) -> List[Cita]:
        """
        Get the appointments that need reminders
        
        Args:
            db: Database session
            reminder_type: Reminder type ("24h" or "2h")
            
        Returns:
            List of appointments that need reminders
        """
        try:
            if reminder_type not in RecordatorioService.REMINDERS:
                raise ValueError(f"Invalid reminder type: {reminder_type}")
                
            hours = RecordatorioService.REMINDERS[reminder_type]["hours"]
            
            # Calculate the time range for reminders
            now = datetime.now()
            start_range = now + timedelta(hours=hours - 0.5)  # 30 minutes margin
            end_range = now + timedelta(hours=hours + 0.5)
            
            query = (select(Cita).options(joinedload(Cita.client).joinedload(Cliente.notification_preferences)).where(and_(
                # Only confirmed appointments
                Cita.status == EstadoCita.CONFIRMADA,
                # Appointments within the reminder time range
                Cita.date_time >= start_range,
                Cita.date_time <= end_range
            )))
            
            result = await db.execute(query)
            appointments = list(result.unique().scalars().all())
            
            # Filter appointments based on client's reminder preferences
            return [
                appointment for appointment in appointments
                if await RecordatorioService._reminder_enabled(appointment.client, reminder_type)
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting appointments for reminder: {str(e)}")

    @staticmethod
    async def register_reminder(db: AsyncSession, appointment: Cita, reminder_type: str, channel: NotificationChannel, successful: bool, error: Optional[str] = None) -> None:
        """Register a sent reminder"""
        try:
            recordatorio = RecordatorioEnviado(
                appointment_id = appointment.id,
                reminder_type = reminder_type,
                channel = channel,
                successful = successful,
                error = error
            )
            db.add(recordatorio)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error registering reminder: {str(e)}")

    @staticmethod
    async def send_reminders(db: AsyncSession) -> Dict[str, int]:
        """
        Send reminders for upcoming appointments

        Returns:
            Dict with the count of sent reminders by type

        Raises:
            DatabaseError: If there is an error processing the reminders
        """
        try:
            results = {reminder_type: 0 for reminder_type in RecordatorioService.REMINDERS.keys()}

            for reminder_type in RecordatorioService.REMINDERS:
                appointments = await RecordatorioService.get_appointments_to_remind(db, reminder_type)

                for appointment in appointments:
                    # Adjust the appointment date to the client's timezone
                    local_date = await RecordatorioService._adjust_timezone(appointment.date_time, appointment.client)

                    # Get enabled channels for the client
                    channels = await RecordatorioService._get_canales_cliente(appointment.client)

                    for channel in channels:
                        # Check if this reminder has already been sent
                        if await RecordatorioService._reminder_already_sent(db, appointment.id, reminder_type, channel):
                            continue

                        # Send reminder
                        try:
                            success = await NotificationService.notify_appointment_status(appointment=appointment, template=RecordatorioService.REMINDERS[reminder_type]["template"], channels=[channel], local_date=local_date)  # Pass the adjusted date

                            # Register the result
                            await RecordatorioService.register_reminder(db=db, appointment=appointment, reminder_type=reminder_type, channel=channel, successful=success)

                            if success:
                                results[reminder_type] += 1

                        except Exception as e:
                            # Register the error
                            await RecordatorioService.register_reminder(db=db, appointment=appointment, reminder_type=reminder_type, channel=channel, successful=False, error=str(e))

            return results
        except Exception as e:
            raise DatabaseError(f"Error sending reminders: {str(e)}")

    @staticmethod
    async def get_reminder_statistics(db: AsyncSession, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get statistics of sent reminders
        
        Args:
            db: Database session
            start_date: Period start date
            end_date: Period end date
            
        Returns:
            Dict with reminder statistics
        """
        try:
            query = select(RecordatorioEnviado).where(
                and_(
                    RecordatorioEnviado.created_at >= fecha_inicio,
                    RecordatorioEnviado.created_at <= fecha_fin
                ))

            result = await db.execute(query)
            recordatorios = result.scalars().all()

            stats = {
                "total_enviados": len(recordatorios),
                "exitosos": len([r for r in recordatorios if r.exitoso]),
                "fallidos": len([r for r in recordatorios if not r.exitoso]),
                "por_tipo": {},
                "por_canal": {}}

            # Statistics by reminder type
            for reminder_type in RecordatorioService.REMINDERS:
                stats["por_tipo"][reminder_type] = len([r for r in recordatorios if r.reminder_type == reminder_type and r.successful])

            # Statistics by channel
            for canal in NotificationChannel:
                stats["por_canal"][canal.value] = len([r for r in recordatorios if r.channel == canal.value and r.successful])

            return stats
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting statistics: {str(e)}")

    @staticmethod
    async def schedule_reminders(appointment: Cita) -> None:
        """
        Schedule reminders for an appointment
        
        Args:
            appointment: Appointment to schedule reminders for

        Note:
            This method can be expanded to use a queue system
            like Celery or RQ to schedule reminders
        """
        # TODO: Implement queue system to schedule reminders
        # For now, reminders are handled through a cron job
        pass 