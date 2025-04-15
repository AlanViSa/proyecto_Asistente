"""
Service for notification preference management
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import DatabaseError
from app.models.notification_preference import NotificationPreference, NotificationType
from app.models.client import Client
from app.schemas.notification_preference import NotificationPreferenceCreate, NotificationPreferenceUpdate

class NotificationPreferenceService:
    """Service for notification preference operations"""

    @staticmethod
    async def get_by_id(db: AsyncSession, preference_id: int) -> Optional[NotificationPreference]:
        """Gets a notification preference by ID"""
        try:
            result = await db.execute(
                select(NotificationPreference).where(NotificationPreference.id == preference_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting notification preference by ID: {str(e)}")

    @staticmethod
    async def get_by_client(db: AsyncSession, client_id: int) -> Optional[NotificationPreference]:
        """Gets a notification preference by client ID"""
        try:
            result = await db.execute(
                select(NotificationPreference).where(NotificationPreference.client_id == client_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting notification preference by client ID: {str(e)}")

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[NotificationPreference]:
        """Gets all notification preferences"""
        try:
            result = await db.execute(
                select(NotificationPreference)
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting all notification preferences: {str(e)}")

    @staticmethod
    async def create_or_update(
        db: AsyncSession,
        client_id: int,
        preference_in: NotificationPreferenceCreate
    ) -> NotificationPreference:
        """Creates or updates notification preferences for a client"""
        try:
            # Check if preferences already exist
            existing_preference = await NotificationPreferenceService.get_by_client(db, client_id)
            
            if existing_preference:
                # Update existing preferences
                for field, value in preference_in.dict().items():
                    setattr(existing_preference, field, value)
                
                db.add(existing_preference)
                await db.commit()
                await db.refresh(existing_preference)
                return existing_preference
            else:
                # Create new preferences
                new_preference = NotificationPreference(
                    client_id=client_id,
                    **preference_in.dict()
                )
                
                db.add(new_preference)
                await db.commit()
                await db.refresh(new_preference)
                return new_preference
                
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error creating or updating notification preference: {str(e)}")

    @staticmethod
    async def update(
        db: AsyncSession,
        preference: NotificationPreference,
        preference_in: NotificationPreferenceUpdate
    ) -> NotificationPreference:
        """Updates a notification preference"""
        try:
            update_data = preference_in.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(preference, field, value)
            
            db.add(preference)
            await db.commit()
            await db.refresh(preference)
            return preference
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error updating notification preference: {str(e)}")

    @staticmethod
    async def delete(db: AsyncSession, preference: NotificationPreference) -> None:
        """Deletes a notification preference"""
        try:
            await db.delete(preference)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error deleting notification preference: {str(e)}")

    @staticmethod
    async def get_or_create_default(db: AsyncSession, client_id: int) -> NotificationPreference:
        """
        Gets or creates default notification preferences for a client
        
        Args:
            db: Database session
            client_id: Client ID
            
        Returns:
            NotificationPreference: The client's notification preferences
        """
        try:
            # Check if preferences already exist
            existing_preference = await NotificationPreferenceService.get_by_client(db, client_id)
            
            if existing_preference:
                return existing_preference
            
            # Create default preferences
            default_preference = NotificationPreference(
                client_id=client_id,
                appointment_reminder=NotificationType.SMS,
                appointment_confirmation=NotificationType.SMS,
                promotional=NotificationType.NONE,
                reminder_hours_before=24,
                notifications_enabled=True
            )
            
            db.add(default_preference)
            await db.commit()
            await db.refresh(default_preference)
            return default_preference
            
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error getting or creating default notification preference: {str(e)}")

    @staticmethod
    async def toggle_notifications(db: AsyncSession, client_id: int, enabled: bool) -> NotificationPreference:
        """
        Toggles all notifications for a client
        
        Args:
            db: Database session
            client_id: Client ID
            enabled: Whether notifications should be enabled
            
        Returns:
            NotificationPreference: The updated notification preferences
        """
        try:
            preference = await NotificationPreferenceService.get_or_create_default(db, client_id)
            preference.notifications_enabled = enabled
            
            db.add(preference)
            await db.commit()
            await db.refresh(preference)
            return preference
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error toggling notifications: {str(e)}") 