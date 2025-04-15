"""
Database configuration and utilities
"""
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
import logging
from sqlalchemy.sql import text
import os

from app.core.config import settings

logger = logging.getLogger("app.db.database")

# Base class for SQLAlchemy models
Base = declarative_base()

# Determine database type from URL
is_sqlite = "sqlite" in settings.DATABASE_URL.lower()
is_postgres = "postgresql" in settings.DATABASE_URL.lower()

# Handle database URL for different engines
if is_sqlite:
    # SQLite URLs for sync and async
    sync_url = settings.DATABASE_URL
    # For SQLite, we use a regular engine since SQLite doesn't support async
    async_url = sync_url
    connect_args = {"check_same_thread": False}
elif is_postgres:
    # PostgreSQL URLs for sync and async
    if "+asyncpg" in settings.DATABASE_URL:
        async_url = settings.DATABASE_URL
        sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    else:
        sync_url = settings.DATABASE_URL
        async_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    connect_args = {}
else:
    # Default fallback
    sync_url = settings.DATABASE_URL
    async_url = settings.DATABASE_URL
    connect_args = {}

# Create synchronous engine
engine = create_engine(
    sync_url,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    connect_args=connect_args,
    pool_recycle=settings.DB_POOL_RECYCLE
)

# Create the async engine if not SQLite
if not is_sqlite:
    async_engine = create_async_engine(
        async_url,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE
    )
else:
    # For SQLite, use sync engine since SQLite doesn't support async
    async_engine = engine

# Create synchronous session maker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create the async session maker if not SQLite
if not is_sqlite:
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )
else:
    # For SQLite, we'll use the sync session for both
    async_session_maker = None

class DatabaseError(Exception):
    """Base exception for database errors"""
    pass

# Synchronous database session
def get_db() -> Generator[Session, None, None]:
    """
    Synchronous database session generator
    
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(f"Database error: {str(e)}")
    finally:
        db.close()

# Async database session
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async database session generator
    
    Yields:
        AsyncSession: Async database session
    """
    if is_sqlite:
        # For SQLite, we'll use the sync session since SQLite doesn't support async
        db = SessionLocal()
        try:
            yield db  # type: ignore
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseError(f"Database error: {str(e)}")
        finally:
            db.close()
    else:
        # For async-compatible databases
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
        self.sync_engine = engine
        self.session_maker = SessionLocal
        self.sync_session_maker = SessionLocal
        self.is_sqlite = is_sqlite
    
    async def connect(self):
        """Connect to the database"""
        # The connection is established when needed
        pass
    
    async def close(self):
        """Close all database connections"""
        if not self.is_sqlite and async_engine is not engine:
            await async_engine.dispose()
        self.sync_engine.dispose()
    
    async def session(self):
        """Get a database session"""
        if self.is_sqlite:
            return self.sync_session_maker()
        else:
            return async_session_maker()
    
    def sync_session(self):
        """Get a synchronous database session"""
        return self.sync_session_maker()

async def check_db_connection():
    """
    Check database connection.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        if is_sqlite:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
        else:
            async_db = async_session_maker()
            await async_db.execute(text("SELECT 1"))
            await async_db.close()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection error: {str(e)}")
        return False 