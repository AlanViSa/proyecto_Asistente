"""
Configuración de pruebas
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.database import get_db
from app.main import app
from app.core.config import settings

# Crear motor de base de datos para pruebas
TEST_DATABASE_URL = settings.DATABASE_URL + "_test"
engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Crear un event loop para las pruebas"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    """Crear motor de base de datos para pruebas"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Crear sesión de base de datos para pruebas"""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
def client(db_session: AsyncSession) -> Generator:
    """Crear cliente de prueba"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data():
    """Datos de usuario de prueba"""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "nombre": "Test User",
        "telefono": "1234567890"
    }

@pytest.fixture
def test_cita_data():
    """Datos de cita de prueba"""
    return {
        "fecha_hora": "2024-03-20T10:00:00",
        "estado": "PENDIENTE",
        "cliente_id": 1,
        "servicio": "Corte de Cabello",
        "duracion_minutos": 30
    }

@pytest.fixture
def test_preferencias_data():
    """Datos de preferencias de notificación de prueba"""
    return {
        "cliente_id": 1,
        "email_habilitado": True,
        "sms_habilitado": False,
        "whatsapp_habilitado": False,
        "recordatorio_24h": True,
        "recordatorio_2h": True,
        "zona_horaria": "America/Mexico_City"
    } 