"""
Service for managing clients
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import DatabaseError
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate, ClienteUpdate
from app.services.preferencias_notificacion import NotificationPreferencesService

class ClienteService:
    """Service for CRUD operations on clients"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, client_id: int) -> Optional[Cliente]:
        """Gets a client by their ID"""
        try:
            result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener cliente por ID: {str(e)}")

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[Cliente]:
        """Gets a client by their email"""
        try:
            result = await db.execute(select(Cliente).where(Cliente.email == email))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener cliente por email: {str(e)}")

    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> Optional[Cliente]:
        """Gets a client by their phone number"""
        try:
            result = await db.execute(select(Cliente).where(Cliente.telefono == telefono))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener cliente por teléfono: {str(e)}")

    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Cliente]:
        """Gets a list of clients with pagination"""
        try:
            result = await db.execute(select(Cliente).offset(skip).limit(limit))
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener lista de clientes: {str(e)}")

    @staticmethod
    async def create(db: AsyncSession, client_in: ClienteCreate) -> Cliente:
        """Creates a new client"""
        try:
            cliente = Cliente(
                name=client_in.name,
                email=client_in.email,
                phone=client_in.phone,
                is_active=True
            )
            db.add(cliente)
            await db.commit()
            await db.refresh(client)

            # Crear preferencias por defecto para el nuevo cliente
            await PreferenciasNotificacionService.crear_preferencias_por_defecto(db, cliente.id)
            
            return cliente
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al crear cliente: {str(e)}")

    @staticmethod
    async def update(db: AsyncSession, client: Cliente, client_in: ClienteUpdate) -> Cliente:
        """Updates an existing client"""
        try:
            update_data = client_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(client, field, value)
            await db.commit()
            await db.refresh(client)
            return client
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al actualizar cliente: {str(e)}")

    @staticmethod
    async def delete(db: AsyncSession, cliente: Cliente) -> None:
        """Elimina un cliente"""
        try: 
            await db.delete(cliente)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al eliminar cliente: {str(e)}")

    @staticmethod
    async def deactivate(db: AsyncSession, client: Cliente) -> Cliente:
        """Deactivates a client"""
        try:
            client.is_active = False
            await db.commit()
            await db.refresh(client)
            return client
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al desactivar cliente: {str(e)}") 