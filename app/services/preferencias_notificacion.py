"""
Alias for NotificationPreferenceService for backwards compatibility
"""
from app.services.notification_preference_service import NotificationPreferenceService

# Create Spanish alias for the service
PreferenciasNotificacionService = NotificationPreferenceService

# Legacy imports for backward compatibility
from app.models.client import Client as Cliente

"""
Servicio para la gestión de preferencias de notificación
"""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import DatabaseError
from app.models.preferencias_notificacion import PreferenciasNotificacion
from app.schemas.preferencias_notificacion import PreferenciasNotificacionCreate, PreferenciasNotificacionUpdate

class PreferenciasNotificacionService:
    """Servicio para gestionar preferencias de notificación"""

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        preferencias_id: int
    ) -> Optional[PreferenciasNotificacion]:
        """Obtiene las preferencias por ID"""
        try:
            result = await db.execute(
                select(PreferenciasNotificacion)
                .where(PreferenciasNotificacion.id == preferencias_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener preferencias: {str(e)}")

    @staticmethod
    async def get_by_cliente(
        db: AsyncSession,
        cliente_id: int
    ) -> Optional[PreferenciasNotificacion]:
        """Obtiene las preferencias de un cliente"""
        try:
            result = await db.execute(
                select(PreferenciasNotificacion)
                .where(PreferenciasNotificacion.cliente_id == cliente_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener preferencias del cliente: {str(e)}")

    @staticmethod
    async def create(
        db: AsyncSession,
        preferencias_in: PreferenciasNotificacionCreate
    ) -> PreferenciasNotificacion:
        """Crea nuevas preferencias de notificación"""
        try:
            preferencias = PreferenciasNotificacion(
                cliente_id=preferencias_in.cliente_id,
                email_habilitado=preferencias_in.email_habilitado,
                sms_habilitado=preferencias_in.sms_habilitado,
                whatsapp_habilitado=preferencias_in.whatsapp_habilitado,
                recordatorio_24h=preferencias_in.recordatorio_24h,
                recordatorio_2h=preferencias_in.recordatorio_2h,
                zona_horaria=preferencias_in.zona_horaria
            )
            db.add(preferencias)
            await db.commit()
            await db.refresh(preferencias)
            return preferencias
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al crear preferencias: {str(e)}")

    @staticmethod
    async def update(
        db: AsyncSession,
        preferencias: PreferenciasNotificacion,
        preferencias_in: PreferenciasNotificacionUpdate
    ) -> PreferenciasNotificacion:
        """Actualiza preferencias existentes"""
        try:
            update_data = preferencias_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(preferencias, field, value)
            await db.commit()
            await db.refresh(preferencias)
            return preferencias
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al actualizar preferencias: {str(e)}")

    @staticmethod
    async def delete(
        db: AsyncSession,
        preferencias: PreferenciasNotificacion
    ) -> None:
        """Elimina preferencias de notificación"""
        try:
            await db.delete(preferencias)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al eliminar preferencias: {str(e)}")

    @staticmethod
    async def get_clientes_sin_preferencias(
        db: AsyncSession
    ) -> List[int]:
        """
        Obtiene los IDs de clientes que no tienen preferencias configuradas
        
        Útil para identificar clientes que necesitan configuración inicial
        """
        try:
            # Subconsulta para obtener los cliente_id que ya tienen preferencias
            subquery = select(PreferenciasNotificacion.cliente_id)
            
            # Consulta principal que obtiene los cliente_id que no están en la subconsulta
            query = select(Cliente.id).where(
                Cliente.id.not_in(subquery)
            )
            
            result = await db.execute(query)
            return [row[0] for row in result.all()]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener clientes sin preferencias: {str(e)}")

    @staticmethod
    async def crear_preferencias_por_defecto(
        db: AsyncSession,
        cliente_id: int
    ) -> PreferenciasNotificacion:
        """
        Crea preferencias por defecto para un cliente
        
        Útil cuando se crea un nuevo cliente o para clientes existentes sin preferencias
        """
        try:
            # Verificar si ya existen preferencias
            preferencias_existentes = await PreferenciasNotificacionService.get_by_cliente(
                db, cliente_id
            )
            if preferencias_existentes:
                return preferencias_existentes
            
            # Crear preferencias por defecto
            preferencias_in = PreferenciasNotificacionCreate(
                cliente_id=cliente_id,
                email_habilitado=True,
                sms_habilitado=False,
                whatsapp_habilitado=False,
                recordatorio_24h=True,
                recordatorio_2h=True,
                zona_horaria="America/Mexico_City"
            )
            
            return await PreferenciasNotificacionService.create(db, preferencias_in)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al crear preferencias por defecto: {str(e)}") 