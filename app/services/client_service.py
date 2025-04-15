"""
Service for client management
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.db.database import DatabaseError
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate
from app.core.security import get_password_hash, verify_password

class ClientService:
    """Service for client-related operations"""

    @staticmethod
    async def get_by_id(db: AsyncSession, client_id: int) -> Optional[Client]:
        """Gets a client by ID"""
        try:
            result = await db.execute(
                select(Client).where(Client.id == client_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting client by ID: {str(e)}")

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[Client]:
        """Gets a client by email"""
        try:
            result = await db.execute(
                select(Client).where(Client.email == email)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting client by email: {str(e)}")

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Client]:
        """Gets all clients with pagination"""
        try:
            result = await db.execute(
                select(Client)
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting all clients: {str(e)}")

    @staticmethod
    async def create(
        db: AsyncSession,
        client_in: ClientCreate
    ) -> Client:
        """Creates a new client"""
        try:
            # Check if email already exists
            existing_client = await ClientService.get_by_email(db, client_in.email)
            if existing_client:
                raise ValueError("Email already registered")
            
            # Create client with hashed password
            client_data = client_in.dict()
            hashed_password = get_password_hash(client_data.pop("password"))
            
            client = Client(
                **client_data,
                hashed_password=hashed_password,
                is_active=True,
                is_admin=False
            )
            
            db.add(client)
            await db.commit()
            await db.refresh(client)
            return client
        except IntegrityError:
            await db.rollback()
            raise ValueError("Email or phone already registered")
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error creating client: {str(e)}")

    @staticmethod
    async def update(
        db: AsyncSession,
        client: Client,
        client_in: ClientUpdate
    ) -> Client:
        """Updates a client"""
        try:
            update_data = client_in.dict(exclude_unset=True)
            
            # Handle password update
            if "password" in update_data:
                update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            
            # Update client attributes
            for field, value in update_data.items():
                setattr(client, field, value)
            
            db.add(client)
            await db.commit()
            await db.refresh(client)
            return client
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error updating client: {str(e)}")

    @staticmethod
    async def delete(db: AsyncSession, client: Client) -> None:
        """Deletes a client"""
        try:
            await db.delete(client)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error deleting client: {str(e)}")

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[Client]:
        """
        Authenticates a client with email and password
        
        Args:
            db: Database session
            email: Client email
            password: Client password
            
        Returns:
            Client: Authenticated client or None if authentication fails
        """
        client = await ClientService.get_by_email(db, email)
        if not client:
            return None
        if not verify_password(password, client.hashed_password):
            return None
        return client

    @staticmethod
    async def update_last_login(
        db: AsyncSession,
        client: Client
    ) -> Client:
        """Updates the last login timestamp"""
        try:
            client.last_login = datetime.utcnow()
            db.add(client)
            await db.commit()
            await db.refresh(client)
            return client
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error updating last login: {str(e)}") 