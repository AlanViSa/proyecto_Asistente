"""
Database configuration and utilities
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
import logging
from sqlalchemy.sql import text

from app.core.config import settings

logger = logging.getLogger("app.db.database")

# Create the async database engine
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE
)

# Create the async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Base class for SQLAlchemy models
Base = declarative_base()

class DatabaseError(Exception):
    """Base exception for database errors"""
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async database session generator
    
    Yields:
        AsyncSession: Async database session
        
    Raises:
        DatabaseError: If there's an error connecting to or using the database
    """
    async with async_session_maker() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise DatabaseError(f"Database error: {str(e)}")
        finally:
            await session.close()

# Database instance for app lifecycle management
class Database:
    def __init__(self):
        self.engine = engine
        self.session_maker = async_session_maker
    
    async def connect(self):
        """Connect to the database"""
        # The connection is established when needed
        pass
    
    async def close(self):
        """Close all database connections"""
        await self.engine.dispose()
    
    async def session(self):
        """Get a database session"""
        return async_session_maker()

async def check_db_connection():
    """
    Check database connection.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        db = async_session_maker()
        await db.execute(text("SELECT 1"))
        await db.close()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection error: {str(e)}")
        return False 