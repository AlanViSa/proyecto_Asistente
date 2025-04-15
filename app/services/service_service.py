"""
Service for salon service management
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import DatabaseError
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate

class ServiceService:
    """Service for salon service operations"""

    @staticmethod
    async def get_by_id(db: AsyncSession, service_id: int) -> Optional[Service]:
        """Gets a service by ID"""
        try:
            result = await db.execute(
                select(Service).where(Service.id == service_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting service by ID: {str(e)}")

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[Service]:
        """Gets a service by name"""
        try:
            result = await db.execute(
                select(Service).where(func.lower(Service.name) == func.lower(name))
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting service by name: {str(e)}")

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Service]:
        """Gets all services with pagination"""
        try:
            query = select(Service)
            
            if active_only:
                query = query.where(Service.is_active == True)
                
            query = query.order_by(Service.name).offset(skip).limit(limit)
            
            result = await db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting all services: {str(e)}")

    @staticmethod
    async def create(
        db: AsyncSession,
        service_in: ServiceCreate
    ) -> Service:
        """Creates a new service"""
        try:
            # Check if service with same name already exists
            existing_service = await ServiceService.get_by_name(db, service_in.name)
            if existing_service:
                raise ValueError(f"Service with name '{service_in.name}' already exists")
            
            service = Service(**service_in.dict())
            db.add(service)
            await db.commit()
            await db.refresh(service)
            return service
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error creating service: {str(e)}")

    @staticmethod
    async def update(
        db: AsyncSession,
        service: Service,
        service_in: ServiceUpdate
    ) -> Service:
        """Updates a service"""
        try:
            update_data = service_in.dict(exclude_unset=True)
            
            # Check name uniqueness if updating name
            if "name" in update_data and update_data["name"] != service.name:
                existing_service = await ServiceService.get_by_name(db, update_data["name"])
                if existing_service:
                    raise ValueError(f"Service with name '{update_data['name']}' already exists")
            
            # Update service attributes
            for field, value in update_data.items():
                setattr(service, field, value)
            
            db.add(service)
            await db.commit()
            await db.refresh(service)
            return service
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error updating service: {str(e)}")

    @staticmethod
    async def delete(db: AsyncSession, service: Service) -> None:
        """Deletes a service"""
        try:
            await db.delete(service)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error deleting service: {str(e)}")

    @staticmethod
    async def activate(db: AsyncSession, service: Service) -> Service:
        """Activates a service"""
        try:
            service.is_active = True
            db.add(service)
            await db.commit()
            await db.refresh(service)
            return service
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error activating service: {str(e)}")

    @staticmethod
    async def deactivate(db: AsyncSession, service: Service) -> Service:
        """Deactivates a service"""
        try:
            service.is_active = False
            db.add(service)
            await db.commit()
            await db.refresh(service)
            return service
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error deactivating service: {str(e)}") 