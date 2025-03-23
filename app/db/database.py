"""
Configuración y utilidades de la base de datos
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

# Crear el motor de base de datos asíncrono
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DATABASE_ECHO
)

# Crear el generador de sesiones asíncronas
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

class DatabaseError(Exception):
    """Excepción base para errores de base de datos"""
    pass

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Generador de sesiones de base de datos asíncronas
    
    Yields:
        AsyncSession: Sesión de base de datos asíncrona
        
    Raises:
        DatabaseError: Si hay un error al conectar o usar la base de datos
    """
    async with async_session_maker() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise DatabaseError(f"Error de base de datos: {str(e)}")
        finally:
            await session.close() 