"""
Unit tests for the client service
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.cliente import ClientService
from app.schemas.cliente import ClientCreate, ClientUpdate
from app.models.cliente import Client

@pytest.mark.asyncio
async def test_create_client(db_session: AsyncSession, test_user_data):
    """Tests the creation of a client"""
    client_in = ClientCreate(**test_user_data)
    client = await ClientService.create(db_session, client_in)
    
    assert client.id is not None
    assert client.email == test_user_data["email"]
    assert client.name == test_user_data["name"]
    assert client.phone == test_user_data["phone"]
    assert client.active is True

@pytest.mark.asyncio
async def test_get_client_by_id(db_session: AsyncSession, test_user_data):
    """Tests getting a client by ID"""
    # Create client
    client_in = ClientCreate(**test_user_data)
    client = await ClientService.create(db_session, client_in)
    
    # Get client
    client_db = await ClientService.get_by_id(db_session, client.id)
    
    assert client_db is not None
    assert client_db.id == client.id
    assert client_db.email == client.email

@pytest.mark.asyncio
async def test_get_client_by_email(db_session: AsyncSession, test_user_data):
    """Tests getting a client by email"""
    # Create client
    client_in = ClientCreate(**test_user_data)
    client = await ClientService.create(db_session, client_in)
    
    # Get client
    client_db = await ClientService.get_by_email(db_session, client.email)
    
    assert client_db is not None
    assert client_db.id == client.id
    assert client_db.email == client.email

@pytest.mark.asyncio
async def test_update_client(db_session: AsyncSession, test_user_data):
    """Tests updating a client"""
    # Create client
    client_in = ClientCreate(**test_user_data)
    client = await ClientService.create(db_session, client_in)
    
    # Update client
    update_data = {"name": "New Name"}
    client_update = ClientUpdate(**update_data)
    client_updated = await ClientService.update(db_session, client, client_update)
    
    assert client_updated.name == "New Name"
    assert client_updated.email == client.email

@pytest.mark.asyncio
async def test_deactivate_client(db_session: AsyncSession, test_user_data):
    """Tests deactivating a client"""
    # Create client
    client_in = ClientCreate(**test_user_data)
    client = await ClientService.create(db_session, client_in)
    
    # Deactivate client
    client_deactivated = await ClientService.deactivate(db_session, client)
    
    assert client_deactivated.active is False

@pytest.mark.asyncio
async def test_activate_client(db_session: AsyncSession, test_user_data):
    """Tests activating a client"""
    # Create client
    client_in = ClientCreate(**test_user_data)
    client = await ClientService.create(db_session, client_in)
    
    # Deactivate client
    await ClientService.deactivate(db_session, client)
    
    # Activate client
    client_activated = await ClientService.activate(db_session, client)
    
    assert client_activated.active is True

@pytest.mark.asyncio
async def test_delete_client(db_session: AsyncSession, test_user_data):
    """Tests deleting a client"""
    # Create client
    client_in = ClientCreate(**test_user_data)
    client = await ClientService.create(db_session, client_in)
    
    # Delete client
    await ClientService.delete(db_session, client)
    
    # Verify that the client was deleted
    client_db = await ClientService.get_by_id(db_session, client.id)
    assert client_db is None