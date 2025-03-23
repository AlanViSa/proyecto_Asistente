"""
Servicio para la gestión de citas
"""
from typing import List, Optional, Tuple, Set
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from sqlalchemy import select, and_, or_, not_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import DatabaseError
from app.models.cita import Cita, EstadoCita
from app.models.cliente import Cliente
from app.schemas.cita import CitaCreate, CitaUpdate
from app.core.config import settings
from app.services.notification import NotificationService, NotificationTemplate
from app.services.horario_bloqueado import HorarioBloqueadoService

class CitaService:
    """Servicio para operaciones CRUD de citas"""

    # Días de la semana (0 = Lunes, 6 = Domingo)
    DIAS_NO_LABORABLES: Set[int] = {5, 6}  # Por defecto: Sábado y Domingo

    @staticmethod
    def _parse_business_hours() -> Tuple[time, time]:
        """
        Convierte las cadenas de horario comercial en objetos time
        
        Returns:
            Tuple[time, time]: Hora de inicio y fin del horario comercial
        """
        # Acceder a los valores directamente ya que no son SecretStr
        start_time = str(settings.BUSINESS_HOURS_START)
        end_time = str(settings.BUSINESS_HOURS_END)
        
        start_hour, start_minute = map(int, start_time.split(":"))
        end_hour, end_minute = map(int, end_time.split(":"))
        return time(start_hour, start_minute), time(end_hour, end_minute)

    @staticmethod
    def _is_business_day(fecha: datetime) -> bool:
        """
        Verifica si una fecha corresponde a un día laborable
        
        Args:
            fecha: Fecha a verificar
            
        Returns:
            bool: True si es un día laborable, False si no
        """
        # Convertir a la zona horaria del negocio
        tz = ZoneInfo(settings.TIMEZONE)
        fecha_local = fecha.astimezone(tz)
        
        # weekday() retorna 0-6 (0=Lunes, 6=Domingo)
        return fecha_local.weekday() not in CitaService.DIAS_NO_LABORABLES

    @staticmethod
    def _is_within_business_hours(fecha_hora: datetime, duracion_minutos: int) -> bool:
        """
        Verifica si una cita está dentro del horario comercial
        
        Args:
            fecha_hora: Fecha y hora de la cita
            duracion_minutos: Duración de la cita en minutos
            
        Returns:
            bool: True si la cita está dentro del horario comercial
        """
        # Verificar primero si es un día laborable
        if not CitaService._is_business_day(fecha_hora):
            return False

        # Convertir la fecha_hora a la zona horaria del negocio
        tz = ZoneInfo(settings.TIMEZONE)
        fecha_hora_local = fecha_hora.astimezone(tz)
        hora_fin_local = fecha_hora_local + timedelta(minutes=duracion_minutos)
        
        # Obtener horario comercial
        hora_inicio, hora_fin = CitaService._parse_business_hours()
        
        # Verificar que tanto el inicio como el fin de la cita estén dentro del horario
        hora_cita = fecha_hora_local.time()
        hora_fin_cita = hora_fin_local.time()
        
        return (
            hora_inicio <= hora_cita <= hora_fin and
            hora_inicio <= hora_fin_cita <= hora_fin
        )

    @staticmethod
    async def get_by_id(db: AsyncSession, cita_id: int) -> Optional[Cita]:
        """Obtiene una cita por su ID"""
        try:
            result = await db.execute(
                select(Cita)
                .options(joinedload(Cita.cliente))
                .where(Cita.id == cita_id)
            )
            return result.unique().scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener cita por ID: {str(e)}")

    @staticmethod
    async def get_by_cliente(
        db: AsyncSession,
        cliente_id: int,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[EstadoCita] = None
    ) -> List[Cita]:
        """Obtiene las citas de un cliente con filtros"""
        try:
            query = (
                select(Cita)
                .options(joinedload(Cita.cliente))
                .where(Cita.cliente_id == cliente_id)
            )
            
            if estado:
                query = query.where(Cita.estado == estado)
            
            query = query.offset(skip).limit(limit)
            result = await db.execute(query)
            return list(result.unique().scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener citas del cliente: {str(e)}")

    @staticmethod
    async def get_by_fecha(
        db: AsyncSession,
        fecha: datetime,
        cliente_id: Optional[int] = None
    ) -> List[Cita]:
        """Obtiene las citas para una fecha específica"""
        try:
            fecha_inicio = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
            fecha_fin = fecha_inicio + timedelta(days=1)
            
            query = (
                select(Cita)
                .options(joinedload(Cita.cliente))
                .where(
                    and_(
                        Cita.fecha_hora >= fecha_inicio,
                        Cita.fecha_hora < fecha_fin
                    )
                )
            )
            
            if cliente_id:
                query = query.where(Cita.cliente_id == cliente_id)
            
            result = await db.execute(query)
            return list(result.unique().scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener citas por fecha: {str(e)}")

    @staticmethod
    async def check_availability(
        db: AsyncSession,
        fecha_hora: datetime,
        duracion_minutos: int,
        exclude_cita_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si un horario está disponible
        
        Args:
            db: Sesión de base de datos
            fecha_hora: Fecha y hora propuesta
            duracion_minutos: Duración de la cita en minutos
            exclude_cita_id: ID de cita a excluir de la verificación (para updates)
            
        Returns:
            bool: True si el horario está disponible, False si no
            
        Raises:
            DatabaseError: Si hay un error al verificar la disponibilidad
        """
        try:
            # Verificar horario comercial
            if not CitaService._is_within_business_hours(fecha_hora, duracion_minutos):
                return False

            # Verificar si el horario está bloqueado
            if await HorarioBloqueadoService.is_horario_bloqueado(db, fecha_hora, duracion_minutos):
                return False

            # Calcular el rango de tiempo de la cita propuesta
            hora_fin = fecha_hora + timedelta(minutes=duracion_minutos)
            
            # Construir la consulta base
            query = select(Cita).where(
                and_(
                    # Excluir citas canceladas
                    Cita.estado != EstadoCita.CANCELADA,
                    # Verificar superposición de horarios
                    or_(
                        # La cita existente comienza durante la nueva cita
                        and_(
                            Cita.fecha_hora >= fecha_hora,
                            Cita.fecha_hora < hora_fin
                        ),
                        # La cita existente termina durante la nueva cita
                        and_(
                            Cita.fecha_hora + timedelta(minutes=Cita.duracion_minutos) > fecha_hora,
                            Cita.fecha_hora + timedelta(minutes=Cita.duracion_minutos) <= hora_fin
                        ),
                        # La cita existente abarca completamente la nueva cita
                        and_(
                            Cita.fecha_hora <= fecha_hora,
                            Cita.fecha_hora + timedelta(minutes=Cita.duracion_minutos) >= hora_fin
                        )
                    )
                )
            )
            
            # Si estamos actualizando una cita, excluirla de la verificación
            if exclude_cita_id:
                query = query.where(Cita.id != exclude_cita_id)
            
            result = await db.execute(query)
            conflicting_citas = result.scalars().all()
            
            return len(conflicting_citas) == 0
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al verificar disponibilidad: {str(e)}")

    @staticmethod
    async def create(
        db: AsyncSession,
        cita_in: CitaCreate,
        cliente_id: int
    ) -> Cita:
        """Crea una nueva cita"""
        try:
            cita = Cita(
                cliente_id=cliente_id,
                fecha_hora=cita_in.fecha_hora,
                servicio=cita_in.servicio,
                duracion_minutos=cita_in.duracion_minutos,
                estado=EstadoCita.PENDIENTE,
                notas=cita_in.notas
            )
            db.add(cita)
            await db.commit()
            await db.refresh(cita)
            
            # Enviar notificación de cita creada
            await NotificationService.notify_appointment_status(
                cita=cita,
                template=NotificationTemplate.CITA_CREADA
            )
            
            return cita
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al crear cita: {str(e)}")

    @staticmethod
    async def update(
        db: AsyncSession,
        cita: Cita,
        cita_in: CitaUpdate
    ) -> Cita:
        """Actualiza una cita existente"""
        try:
            update_data = cita_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(cita, field, value)
            await db.commit()
            await db.refresh(cita)
            return cita
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al actualizar cita: {str(e)}")

    @staticmethod
    async def delete(db: AsyncSession, cita: Cita) -> None:
        """Elimina una cita"""
        try:
            await db.delete(cita)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al eliminar cita: {str(e)}")

    @staticmethod
    async def cancel(db: AsyncSession, cita: Cita) -> Cita:
        """Cancela una cita"""
        try:
            cita.estado = EstadoCita.CANCELADA
            await db.commit()
            await db.refresh(cita)
            
            # Enviar notificación de cita cancelada
            await NotificationService.notify_appointment_status(
                cita=cita,
                template=NotificationTemplate.CITA_CANCELADA
            )
            
            return cita
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al cancelar cita: {str(e)}")

    @staticmethod
    async def confirm(db: AsyncSession, cita: Cita) -> Cita:
        """Confirma una cita"""
        try:
            cita.estado = EstadoCita.CONFIRMADA
            await db.commit()
            await db.refresh(cita)
            
            # Enviar notificación de cita confirmada
            await NotificationService.notify_appointment_status(
                cita=cita,
                template=NotificationTemplate.CITA_CONFIRMADA
            )
            
            return cita
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al confirmar cita: {str(e)}")

    @staticmethod
    async def complete(db: AsyncSession, cita: Cita) -> Cita:
        """Marca una cita como completada"""
        try:
            cita.estado = EstadoCita.COMPLETADA
            await db.commit()
            await db.refresh(cita)
            
            # Enviar notificación de cita completada
            await NotificationService.notify_appointment_status(
                cita=cita,
                template=NotificationTemplate.CITA_COMPLETADA
            )
            
            return cita
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al completar cita: {str(e)}")

    @staticmethod
    async def mark_no_show(db: AsyncSession, cita: Cita) -> Cita:
        """Marca una cita como no asistida"""
        try:
            cita.estado = EstadoCita.NO_ASISTIO
            await db.commit()
            await db.refresh(cita)
            
            # Enviar notificación de no asistencia
            await NotificationService.notify_appointment_status(
                cita=cita,
                template=NotificationTemplate.CITA_NO_ASISTIO
            )
            
            return cita
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al marcar cita como no asistida: {str(e)}") 