"""
Service for managing blocked schedule slots
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import DatabaseError
from app.models.blocked_schedule import BlockedSchedule
from app.schemas.blocked_schedule import BlockedScheduleCreate, BlockedScheduleUpdate

class BlockedScheduleService:
    """Service for managing schedule blocks (times when no appointments can be made)"""

    @staticmethod
    async def get_by_id(db: AsyncSession, block_id: int) -> Optional[BlockedSchedule]:
        """Gets a blocked schedule by ID"""
        try:
            result = await db.execute(
                select(BlockedSchedule).where(BlockedSchedule.id == block_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting blocked schedule: {str(e)}")

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[BlockedSchedule]:
        """Gets all blocked schedules with pagination"""
        try:
            result = await db.execute(
                select(BlockedSchedule)
                .where(BlockedSchedule.is_active == True)
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting blocked schedules: {str(e)}")

    @staticmethod
    async def create(
        db: AsyncSession,
        block_in: BlockedScheduleCreate
    ) -> BlockedSchedule:
        """Creates a new blocked schedule"""
        try:
            block = BlockedSchedule(**block_in.dict())
            db.add(block)
            await db.commit()
            await db.refresh(block)
            return block
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error creating blocked schedule: {str(e)}")

    @staticmethod
    async def update(
        db: AsyncSession,
        block: BlockedSchedule,
        block_in: BlockedScheduleUpdate
    ) -> BlockedSchedule:
        """Updates a blocked schedule"""
        try:
            # Update fields from input
            for field, value in block_in.dict(exclude_unset=True).items():
                setattr(block, field, value)
            
            db.add(block)
            await db.commit()
            await db.refresh(block)
            return block
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error updating blocked schedule: {str(e)}")

    @staticmethod
    async def delete(db: AsyncSession, block: BlockedSchedule) -> None:
        """Deletes a blocked schedule"""
        try:
            await db.delete(block)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error deleting blocked schedule: {str(e)}")

    @staticmethod
    async def is_time_blocked(
        db: AsyncSession,
        datetime_obj: datetime,
        duration_minutes: int
    ) -> bool:
        """
        Checks if a given time is within a blocked schedule
        
        Args:
            db: Database session
            datetime_obj: Datetime to check
            duration_minutes: Duration of the time slot in minutes
            
        Returns:
            bool: True if the time is blocked, False otherwise
        """
        try:
            # Calculate the appointment end time
            end_time = datetime_obj + timedelta(minutes=duration_minutes)
            
            # Query for any active blocked schedules that overlap with the time slot
            result = await db.execute(
                select(BlockedSchedule).where(
                    and_(
                        BlockedSchedule.is_active == True,
                        or_(
                            # Blocked schedule starts during the appointment time
                            and_(
                                BlockedSchedule.start_date >= datetime_obj,
                                BlockedSchedule.start_date < end_time
                            ),
                            # Blocked schedule ends during the appointment time
                            and_(
                                BlockedSchedule.end_date > datetime_obj,
                                BlockedSchedule.end_date <= end_time
                            ),
                            # Blocked schedule encompasses the appointment time
                            and_(
                                BlockedSchedule.start_date <= datetime_obj,
                                BlockedSchedule.end_date >= end_time
                            )
                        )
                    )
                )
            )
            
            # If we found any blocking schedules, the time is blocked
            blocked = result.first() is not None
            return blocked
            
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error checking if time is blocked: {str(e)}") 