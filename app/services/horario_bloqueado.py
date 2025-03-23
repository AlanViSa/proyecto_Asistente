"""
Servicio para la gestión de horarios bloqueados
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import DatabaseError
from app.models.horario_bloqueado import HorarioBloqueado
from app.schemas.horario_bloqueado import HorarioBloqueadoCreate, HorarioBloqueadoUpdate

class HorarioBloqueadoService:
    """Servicio para operaciones CRUD de horarios bloqueados"""

    @staticmethod
    async def get_by_id(db: AsyncSession, horario_id: int) -> Optional[HorarioBloqueado]:
        """Obtiene un horario bloqueado por su ID"""
        try:
            result = await db.execute(
                select(HorarioBloqueado).where(HorarioBloqueado.id == horario_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener horario bloqueado: {str(e)}")

    @staticmethod
    async def get_by_fecha(
        db: AsyncSession,
        fecha: datetime,
        incluir_parciales: bool = True
    ) -> List[HorarioBloqueado]:
        """
        Obtiene los horarios bloqueados para una fecha específica
        
        Args:
            db: Sesión de base de datos
            fecha: Fecha a consultar
            incluir_parciales: Si True, incluye bloqueos que intersectan parcialmente con la fecha
            
        Returns:
            Lista de horarios bloqueados
        """
        try:
            fecha_inicio = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
            fecha_fin = fecha.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            if incluir_parciales:
                # Incluir bloqueos que intersectan con el día
                query = select(HorarioBloqueado).where(
                    or_(
                        # Bloqueo comienza durante el día
                        and_(
                            HorarioBloqueado.fecha_inicio >= fecha_inicio,
                            HorarioBloqueado.fecha_inicio <= fecha_fin
                        ),
                        # Bloqueo termina durante el día
                        and_(
                            HorarioBloqueado.fecha_fin >= fecha_inicio,
                            HorarioBloqueado.fecha_fin <= fecha_fin
                        ),
                        # Bloqueo abarca todo el día
                        and_(
                            HorarioBloqueado.fecha_inicio <= fecha_inicio,
                            HorarioBloqueado.fecha_fin >= fecha_fin
                        )
                    )
                )
            else:
                # Solo bloqueos contenidos completamente en el día
                query = select(HorarioBloqueado).where(
                    and_(
                        HorarioBloqueado.fecha_inicio >= fecha_inicio,
                        HorarioBloqueado.fecha_fin <= fecha_fin
                    )
                )
            
            result = await db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener horarios bloqueados por fecha: {str(e)}")

    @staticmethod
    async def get_by_rango(
        db: AsyncSession,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> List[HorarioBloqueado]:
        """Obtiene los horarios bloqueados en un rango de fechas"""
        try:
            query = select(HorarioBloqueado).where(
                or_(
                    # Bloqueo comienza durante el rango
                    and_(
                        HorarioBloqueado.fecha_inicio >= fecha_inicio,
                        HorarioBloqueado.fecha_inicio <= fecha_fin
                    ),
                    # Bloqueo termina durante el rango
                    and_(
                        HorarioBloqueado.fecha_fin >= fecha_inicio,
                        HorarioBloqueado.fecha_fin <= fecha_fin
                    ),
                    # Bloqueo abarca todo el rango
                    and_(
                        HorarioBloqueado.fecha_inicio <= fecha_inicio,
                        HorarioBloqueado.fecha_fin >= fecha_fin
                    )
                )
            )
            result = await db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener horarios bloqueados por rango: {str(e)}")

    @staticmethod
    async def create(
        db: AsyncSession,
        horario_in: HorarioBloqueadoCreate
    ) -> HorarioBloqueado:
        """Crea un nuevo horario bloqueado"""
        try:
            horario = HorarioBloqueado(
                fecha_inicio=horario_in.fecha_inicio,
                fecha_fin=horario_in.fecha_fin,
                motivo=horario_in.motivo,
                descripcion=horario_in.descripcion
            )
            db.add(horario)
            await db.commit()
            await db.refresh(horario)
            return horario
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al crear horario bloqueado: {str(e)}")

    @staticmethod
    async def update(
        db: AsyncSession,
        horario: HorarioBloqueado,
        horario_in: HorarioBloqueadoUpdate
    ) -> HorarioBloqueado:
        """Actualiza un horario bloqueado existente"""
        try:
            update_data = horario_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(horario, field, value)
            await db.commit()
            await db.refresh(horario)
            return horario
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al actualizar horario bloqueado: {str(e)}")

    @staticmethod
    async def delete(db: AsyncSession, horario: HorarioBloqueado) -> None:
        """Elimina un horario bloqueado"""
        try:
            await db.delete(horario)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al eliminar horario bloqueado: {str(e)}")

    @staticmethod
    async def is_horario_bloqueado(
        db: AsyncSession,
        fecha_hora: datetime,
        duracion_minutos: int
    ) -> bool:
        """
        Verifica si un horario está bloqueado
        
        Args:
            db: Sesión de base de datos
            fecha_hora: Fecha y hora a verificar
            duracion_minutos: Duración en minutos
            
        Returns:
            bool: True si el horario está bloqueado, False si no
        """
        try:
            hora_fin = fecha_hora + timedelta(minutes=duracion_minutos)
            
            query = select(HorarioBloqueado).where(
                or_(
                    # El horario comienza durante un bloqueo
                    and_(
                        HorarioBloqueado.fecha_inicio <= fecha_hora,
                        HorarioBloqueado.fecha_fin > fecha_hora
                    ),
                    # El horario termina durante un bloqueo
                    and_(
                        HorarioBloqueado.fecha_inicio < hora_fin,
                        HorarioBloqueado.fecha_fin >= hora_fin
                    ),
                    # El horario está completamente dentro de un bloqueo
                    and_(
                        HorarioBloqueado.fecha_inicio <= fecha_hora,
                        HorarioBloqueado.fecha_fin >= hora_fin
                    )
                )
            )
            
            result = await db.execute(query)
            return result.first() is not None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al verificar horario bloqueado: {str(e)}") 