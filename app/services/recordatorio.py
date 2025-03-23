"""
Servicio para la gestión de recordatorios de citas
"""
from typing import List, Dict, Set, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import DatabaseError
from app.models.cita import Cita, EstadoCita
from app.models.cliente import Cliente
from app.models.recordatorio_enviado import RecordatorioEnviado
from app.services.notification import NotificationService, NotificationTemplate, NotificationChannel

class RecordatorioService:
    """Servicio para gestionar recordatorios de citas"""

    # Configuración de recordatorios
    RECORDATORIOS = {
        "24h": {"horas": 24, "template": NotificationTemplate.RECORDATORIO},
        "2h": {"horas": 2, "template": NotificationTemplate.RECORDATORIO}
    }

    @staticmethod
    async def _get_canales_cliente(cliente) -> Set[NotificationChannel]:
        """Obtiene los canales habilitados para un cliente"""
        canales = set()
        if not hasattr(cliente, 'preferencias_notificacion'):
            # Si no tiene preferencias, usar valores por defecto
            return {NotificationChannel.EMAIL}
            
        prefs = cliente.preferencias_notificacion
        if prefs.email_habilitado and cliente.email:
            canales.add(NotificationChannel.EMAIL)
        if prefs.sms_habilitado and cliente.telefono:
            canales.add(NotificationChannel.SMS)
        if prefs.whatsapp_habilitado and cliente.telefono:
            canales.add(NotificationChannel.WHATSAPP)
            
        return canales or {NotificationChannel.EMAIL}  # Email como fallback

    @staticmethod
    async def _recordatorio_ya_enviado(
        db: AsyncSession,
        cita_id: int,
        tipo_recordatorio: str,
        canal: NotificationChannel
    ) -> bool:
        """Verifica si un recordatorio ya fue enviado"""
        query = select(exists().where(
            and_(
                RecordatorioEnviado.cita_id == cita_id,
                RecordatorioEnviado.tipo_recordatorio == tipo_recordatorio,
                RecordatorioEnviado.canal == canal,
                RecordatorioEnviado.exitoso == True
            )
        ))
        result = await db.execute(query)
        return result.scalar()

    @staticmethod
    async def _recordatorio_habilitado(
        cliente: Cliente,
        tipo_recordatorio: str
    ) -> bool:
        """Verifica si un tipo de recordatorio está habilitado para el cliente"""
        if not hasattr(cliente, 'preferencias_notificacion'):
            return True  # Por defecto, todos los recordatorios están habilitados
            
        prefs = cliente.preferencias_notificacion
        if tipo_recordatorio == "24h":
            return prefs.recordatorio_24h
        elif tipo_recordatorio == "2h":
            return prefs.recordatorio_2h
        return True

    @staticmethod
    async def _ajustar_zona_horaria(
        fecha: datetime,
        cliente: Cliente
    ) -> datetime:
        """Ajusta una fecha a la zona horaria del cliente"""
        if not hasattr(cliente, 'preferencias_notificacion'):
            return fecha
            
        zona = cliente.preferencias_notificacion.zona_horaria or "America/Mexico_City"
        return fecha.astimezone(ZoneInfo(zona))

    @staticmethod
    async def get_citas_para_recordar(
        db: AsyncSession,
        tipo_recordatorio: str
    ) -> List[Cita]:
        """
        Obtiene las citas que necesitan recordatorio
        
        Args:
            db: Sesión de base de datos
            tipo_recordatorio: Tipo de recordatorio ("24h" o "2h")
            
        Returns:
            Lista de citas que necesitan recordatorio
        """
        try:
            if tipo_recordatorio not in RecordatorioService.RECORDATORIOS:
                raise ValueError(f"Tipo de recordatorio no válido: {tipo_recordatorio}")
                
            horas = RecordatorioService.RECORDATORIOS[tipo_recordatorio]["horas"]
            
            # Calcular el rango de tiempo para los recordatorios
            ahora = datetime.now()
            inicio_rango = ahora + timedelta(hours=horas - 0.5)  # 30 minutos de margen
            fin_rango = ahora + timedelta(hours=horas + 0.5)
            
            query = (
                select(Cita)
                .options(
                    joinedload(Cita.cliente).joinedload(Cliente.preferencias_notificacion)
                )
                .where(
                    and_(
                        # Solo citas confirmadas
                        Cita.estado == EstadoCita.CONFIRMADA,
                        # Citas dentro del rango de tiempo para recordatorio
                        Cita.fecha_hora >= inicio_rango,
                        Cita.fecha_hora <= fin_rango
                    )
                )
            )
            
            result = await db.execute(query)
            citas = list(result.unique().scalars().all())
            
            # Filtrar citas según las preferencias de recordatorio del cliente
            return [
                cita for cita in citas
                if await RecordatorioService._recordatorio_habilitado(cita.cliente, tipo_recordatorio)
            ]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener citas para recordatorio: {str(e)}")

    @staticmethod
    async def registrar_recordatorio(
        db: AsyncSession,
        cita: Cita,
        tipo_recordatorio: str,
        canal: NotificationChannel,
        exitoso: bool,
        error: Optional[str] = None
    ) -> None:
        """Registra un recordatorio enviado"""
        try:
            recordatorio = RecordatorioEnviado(
                cita_id=cita.id,
                tipo_recordatorio=tipo_recordatorio,
                canal=canal,
                exitoso=exitoso,
                error=error
            )
            db.add(recordatorio)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al registrar recordatorio: {str(e)}")

    @staticmethod
    async def enviar_recordatorios(db: AsyncSession) -> Dict[str, int]:
        """
        Envía recordatorios para las citas próximas
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            Dict con el conteo de recordatorios enviados por tipo
            
        Raises:
            DatabaseError: Si hay un error al procesar los recordatorios
        """
        try:
            resultados = {tipo: 0 for tipo in RecordatorioService.RECORDATORIOS.keys()}
            
            for tipo_recordatorio in RecordatorioService.RECORDATORIOS:
                citas = await RecordatorioService.get_citas_para_recordar(db, tipo_recordatorio)
                
                for cita in citas:
                    # Ajustar la fecha de la cita a la zona horaria del cliente
                    fecha_local = await RecordatorioService._ajustar_zona_horaria(cita.fecha_hora, cita.cliente)
                    
                    # Obtener canales habilitados para el cliente
                    canales = await RecordatorioService._get_canales_cliente(cita.cliente)
                    
                    for canal in canales:
                        # Verificar si ya se envió este recordatorio
                        if await RecordatorioService._recordatorio_ya_enviado(
                            db, cita.id, tipo_recordatorio, canal
                        ):
                            continue
                        
                        # Enviar recordatorio
                        try:
                            success = await NotificationService.notify_appointment_status(
                                cita=cita,
                                template=RecordatorioService.RECORDATORIOS[tipo_recordatorio]["template"],
                                channels=[canal],
                                fecha_local=fecha_local  # Pasar la fecha ajustada
                            )
                            
                            # Registrar el resultado
                            await RecordatorioService.registrar_recordatorio(
                                db=db,
                                cita=cita,
                                tipo_recordatorio=tipo_recordatorio,
                                canal=canal,
                                exitoso=success
                            )
                            
                            if success:
                                resultados[tipo_recordatorio] += 1
                                
                        except Exception as e:
                            # Registrar el error
                            await RecordatorioService.registrar_recordatorio(
                                db=db,
                                cita=cita,
                                tipo_recordatorio=tipo_recordatorio,
                                canal=canal,
                                exitoso=False,
                                error=str(e)
                            )
            
            return resultados
        except Exception as e:
            raise DatabaseError(f"Error al enviar recordatorios: {str(e)}")

    @staticmethod
    async def get_estadisticas_recordatorios(
        db: AsyncSession,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> Dict:
        """
        Obtiene estadísticas de los recordatorios enviados
        
        Args:
            db: Sesión de base de datos
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            
        Returns:
            Dict con estadísticas de recordatorios
        """
        try:
            query = select(RecordatorioEnviado).where(
                and_(
                    RecordatorioEnviado.created_at >= fecha_inicio,
                    RecordatorioEnviado.created_at <= fecha_fin
                )
            )
            
            result = await db.execute(query)
            recordatorios = result.scalars().all()
            
            stats = {
                "total_enviados": len(recordatorios),
                "exitosos": len([r for r in recordatorios if r.exitoso]),
                "fallidos": len([r for r in recordatorios if not r.exitoso]),
                "por_tipo": {},
                "por_canal": {}
            }
            
            # Estadísticas por tipo de recordatorio
            for tipo in RecordatorioService.RECORDATORIOS:
                stats["por_tipo"][tipo] = len([
                    r for r in recordatorios
                    if r.tipo_recordatorio == tipo and r.exitoso
                ])
            
            # Estadísticas por canal
            for canal in NotificationChannel:
                stats["por_canal"][canal.value] = len([
                    r for r in recordatorios
                    if r.canal == canal.value and r.exitoso
                ])
            
            return stats
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener estadísticas: {str(e)}")

    @staticmethod
    async def programar_recordatorios(cita: Cita) -> None:
        """
        Programa los recordatorios para una cita
        
        Args:
            cita: Cita para la que programar recordatorios
            
        Note:
            Este método se puede expandir para usar un sistema de colas
            como Celery o RQ para programar los recordatorios
        """
        # TODO: Implementar sistema de colas para programar recordatorios
        # Por ahora, los recordatorios se manejan a través de un cron job
        pass 