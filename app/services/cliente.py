"""
Servicio para la gestión de clientes
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import DatabaseError
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate, ClienteUpdate
from app.services.preferencias_notificacion import PreferenciasNotificacionService

class ClienteService:
    """Servicio para operaciones CRUD de clientes"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, cliente_id: int) -> Optional[Cliente]:
        """Obtiene un cliente por su ID"""
        try:
            result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener cliente por ID: {str(e)}")

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[Cliente]:
        """Obtiene un cliente por su email"""
        try:
            result = await db.execute(select(Cliente).where(Cliente.email == email))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener cliente por email: {str(e)}")

    @staticmethod
    async def get_by_telefono(db: AsyncSession, telefono: str) -> Optional[Cliente]:
        """Obtiene un cliente por su número de teléfono"""
        try:
            result = await db.execute(select(Cliente).where(Cliente.telefono == telefono))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener cliente por teléfono: {str(e)}")

    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Cliente]:
        """Obtiene una lista de clientes con paginación"""
        try:
            result = await db.execute(select(Cliente).offset(skip).limit(limit))
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener lista de clientes: {str(e)}")

    @staticmethod
    async def create(db: AsyncSession, cliente_in: ClienteCreate) -> Cliente:
        """Crea un nuevo cliente"""
        try:
            cliente = Cliente(
                nombre=cliente_in.nombre,
                email=cliente_in.email,
                telefono=cliente_in.telefono,
                activo=True
            )
            db.add(cliente)
            await db.commit()
            await db.refresh(cliente)

            # Crear preferencias por defecto para el nuevo cliente
            await PreferenciasNotificacionService.crear_preferencias_por_defecto(db, cliente.id)
            
            return cliente
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al crear cliente: {str(e)}")

    @staticmethod
    async def update(db: AsyncSession, cliente: Cliente, cliente_in: ClienteUpdate) -> Cliente:
        """Actualiza un cliente existente"""
        try:
            update_data = cliente_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(cliente, field, value)
            await db.commit()
            await db.refresh(cliente)
            return cliente
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
    async def deactivate(db: AsyncSession, cliente: Cliente) -> Cliente:
        """Desactiva un cliente"""
        try:
            cliente.activo = False
            await db.commit()
            await db.refresh(cliente)
            return cliente
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseError(f"Error al desactivar cliente: {str(e)}") 