"""
Service for managing blocked time slots
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
    """Service for CRUD operations on blocked time slots"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, horario_id: int) -> Optional[HorarioBloqueado]:
        """Gets a blocked time slot by its ID"""
        try:
            result = await db.execute(
                select(HorarioBloqueado).where(HorarioBloqueado.id == horario_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener horario bloqueado: {str(e)}")
    
    @staticmethod
    async def get_by_date(
        db: AsyncSession,
        date: datetime,
        include_partials: bool = True
    ) -> List[HorarioBloqueado]:
        """
        Gets blocked time slots for a specific date
        
        Args:
        db: Database session
        date: Date to query
        include_partials: If True, includes blocks that partially intersect with the date
        
        Returns:
        List of blocked time slots
        """
        try:
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            if include_partials:
                # Include blocks that intersect with the day
                query = select(HorarioBloqueado).where(
                    or_(
                        # Block starts during the day
                        and_(
                            HorarioBloqueado.start_date >= start_date,
                            HorarioBloqueado.start_date <= end_date
                        ),
                        
                        # Block ends during the day
                        and_(
                            HorarioBloqueado.end_date >= start_date,
                            HorarioBloqueado.end_date <= end_date
                        ),
                        # Bloqueo abarca todo el día
                        and_(
                            HorarioBloqueado.fecha_inicio <= fecha_inicio,
                            HorarioBloqueado.fecha_fin >= fecha_fin
                        )
                    )
                )
            else:
                # Only blocks completely contained within the day
                query = select(HorarioBloqueado).where(
                    and_(
                        HorarioBloqueado.start_date >= start_date,
                        HorarioBloqueado.fecha_fin <= fecha_fin
                    )
                )
            
            result = await db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener horarios bloqueados por fecha: {str(e)}")
    
    @staticmethod
    async def get_by_range(
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> List[HorarioBloqueado]:
        """Gets blocked time slots within a date range"""
        try:
            query = select(HorarioBloqueado).where(
                or_(
                    # Block starts during the range
                    and_(
                        HorarioBloqueado.start_date >= start_date,
                        HorarioBloqueado.start_date <= end_date
                    ),
                    # Block ends during the range
                    and_(
                        HorarioBloqueado.end_date >= start_date,
                        HorarioBloqueado.end_date <= end_date
                    ),
                    # Block spans the entire range
                    and_(
                        HorarioBloqueado.start_date <= start_date,
                        HorarioBloqueado.end_date >= end_date
                    )
                )
            )
            result = await db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting blocked time slots by range: {str(e)}")
    
    @staticmethod
    async def create(
        db: AsyncSession,
        blocked_time_in: HorarioBloqueadoCreate
    ) -> HorarioBloqueado:
        """Creates a new blocked time slot"""
        try:
            blocked_time = HorarioBloqueado(
                start_date=blocked_time_in.start_date,
                end_date=blocked_time_in.end_date,
                reason=blocked_time_in.reason,
                description=blocked_time_in.description
            )
            db.add(blocked_time)
            await db.commit()
            await db.refresh(blocked_time)
            return blocked_time
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error creating blocked time slot: {str(e)}")
    
    @staticmethod
    async def update(
        db: AsyncSession,
        blocked_time: HorarioBloqueado,
        blocked_time_in: HorarioBloqueadoUpdate
    ) -> HorarioBloqueado:
        """Updates an existing blocked time slot"""
        try:
            update_data = blocked_time_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(blocked_time, field, value)
            await db.commit()
            await db.refresh(blocked_time)
            return blocked_time
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error updating blocked time slot: {str(e)}")
    
    @staticmethod
    async def delete(db: AsyncSession, blocked_time: HorarioBloqueado) -> None:
        """Deletes a blocked time slot"""
        try:
            await db.delete(blocked_time)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error deleting blocked time slot: {str(e)}")
    
    @staticmethod
    async def is_time_slot_blocked(
        db: AsyncSession,
        date_time: datetime,
        duration_minutes: int
    ) -> bool:
        """
        Checks if a time slot is blocked
        
        Args:
        db: Database session
        date_time: Date and time to check
        duration_minutes: Duration in minutes
        
        Returns:
        bool: True if the time slot is blocked, False otherwise
        """
        try:
            end_time = date_time + timedelta(minutes=duration_minutes)
            
            query = select(HorarioBloqueado).where(
                or_(
                    # The time slot starts during a block
                    and_(
                        HorarioBloqueado.start_date <= date_time,
                        HorarioBloqueado.end_date > date_time
                    ),
                    # The time slot ends during a block
                    and_(
                        HorarioBloqueado.start_date < end_time,
                        HorarioBloqueado.end_date >= end_time
                    ),
                    # The time slot is completely within a block
                    and_(
                        HorarioBloqueado.start_date <= date_time,
                        HorarioBloqueado.end_date >= end_time
                    )
                )
            )
            
            result = await db.execute(query)
            return result.first() is not None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error checking blocked time slot: {str(e)}")