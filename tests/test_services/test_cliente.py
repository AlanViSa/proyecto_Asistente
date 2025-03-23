"""
Pruebas unitarias para el servicio de clientes
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.cliente import ClienteService
from app.schemas.cliente import ClienteCreate, ClienteUpdate
from app.models.cliente import Cliente

@pytest.mark.asyncio
async def test_create_cliente(db_session: AsyncSession, test_user_data):
    """Prueba la creación de un cliente"""
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    assert cliente.id is not None
    assert cliente.email == test_user_data["email"]
    assert cliente.nombre == test_user_data["nombre"]
    assert cliente.telefono == test_user_data["telefono"]
    assert cliente.activo is True

@pytest.mark.asyncio
async def test_get_cliente_by_id(db_session: AsyncSession, test_user_data):
    """Prueba la obtención de un cliente por ID"""
    # Crear cliente
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    # Obtener cliente
    cliente_db = await ClienteService.get_by_id(db_session, cliente.id)
    
    assert cliente_db is not None
    assert cliente_db.id == cliente.id
    assert cliente_db.email == cliente.email

@pytest.mark.asyncio
async def test_get_cliente_by_email(db_session: AsyncSession, test_user_data):
    """Prueba la obtención de un cliente por email"""
    # Crear cliente
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    # Obtener cliente
    cliente_db = await ClienteService.get_by_email(db_session, cliente.email)
    
    assert cliente_db is not None
    assert cliente_db.id == cliente.id
    assert cliente_db.email == cliente.email

@pytest.mark.asyncio
async def test_update_cliente(db_session: AsyncSession, test_user_data):
    """Prueba la actualización de un cliente"""
    # Crear cliente
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    # Actualizar cliente
    update_data = {"nombre": "Nuevo Nombre"}
    cliente_update = ClienteUpdate(**update_data)
    cliente_updated = await ClienteService.update(db_session, cliente, cliente_update)
    
    assert cliente_updated.nombre == "Nuevo Nombre"
    assert cliente_updated.email == cliente.email

@pytest.mark.asyncio
async def test_deactivate_cliente(db_session: AsyncSession, test_user_data):
    """Prueba la desactivación de un cliente"""
    # Crear cliente
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    # Desactivar cliente
    cliente_deactivated = await ClienteService.deactivate(db_session, cliente)
    
    assert cliente_deactivated.activo is False

@pytest.mark.asyncio
async def test_activate_cliente(db_session: AsyncSession, test_user_data):
    """Prueba la activación de un cliente"""
    # Crear cliente
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    # Desactivar cliente
    await ClienteService.deactivate(db_session, cliente)
    
    # Activar cliente
    cliente_activated = await ClienteService.activate(db_session, cliente)
    
    assert cliente_activated.activo is True

@pytest.mark.asyncio
async def test_delete_cliente(db_session: AsyncSession, test_user_data):
    """Prueba la eliminación de un cliente"""
    # Crear cliente
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    # Eliminar cliente
    await ClienteService.delete(db_session, cliente)
    
    # Verificar que el cliente fue eliminado
    cliente_db = await ClienteService.get_by_id(db_session, cliente.id)
    assert cliente_db is None 