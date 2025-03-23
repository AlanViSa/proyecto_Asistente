from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    """Clase base para todos los modelos SQLAlchemy"""
    pass

# Importar todos los modelos aquí para que Alembic los detecte
from app.models.cliente import Cliente
from app.models.cita import Cita 