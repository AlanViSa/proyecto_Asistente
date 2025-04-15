"""
API endpoints for client management

This module provides endpoints for:
- Listing clients (only administrators)
- Getting details of a specific client
- Updating client data
- Deleting clients
- Activating/deactivating clients (only administrators)
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_cliente, get_current_admin
from app.services.cliente import ClienteService
from app.schemas.cliente import (
    Cliente,
    ClienteCreate,
    ClienteUpdate,
    ClienteInDB,
    ClienteList,
    ClientResponse
)
from app.core.security import get_current_user, get_password_hash
from app.db.database import get_db as db_session
from app.models.cliente import Client

router = APIRouter()

@router.get(
    "/clients/",
    response_model=List[ClientResponse],
    summary="Get all clients",
    description="""
    Retrieve clients.
    
    - **Admin users**: Can see all clients
    - **Regular users**: Can only see themselves
    
    Parameters:
    - **skip**: Number of clients to skip (pagination)
    - **limit**: Maximum number of clients to return
    - **is_active**: Filter by active status
    """,
    responses={
        200: {
            "description": "List of clients retrieved successfully",
            "content": {
                "application/json": {
                    "example": [{
                        "id": 1,
                        "email": "cliente@example.com",
                        "nombre": "Juan Pérez",
                        "telefono": "+1234567890",
                        "activo": true
                    }]
                }
            }
        }
    }
)
async def get_clients(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(db_session),
    current_user: Client = Depends(get_current_user)
):
    """
    Retrieve clients.
    
    - **Admin users**: Can see all clients
    - **Regular users**: Can only see themselves
    
    Parameters:
    - **skip**: Number of clients to skip (pagination)
    - **limit**: Maximum number of clients to return
    - **is_active**: Filter by active status
    """
    if not current_user.is_admin:
        # Regular users can only see themselves
        return [current_user]
    
    # Admin users can see all clients
    query = db.query(Client)
    
    if is_active is not None:
        query = query.filter(Client.is_active == is_active)
    
    clients = query.offset(skip).limit(limit).all()
    return clients

@router.get(
    "/clients/{client_id}",
    response_model=ClientResponse,
    summary="Get client by ID",
    description="""
    Retrieve a specific client by ID.
    
    - **Admin users**: Can see any client
    - **Regular users**: Can only see themselves
    
    Parameters:
    - **client_id**: The ID of the client to retrieve
    """,
    responses={
        200: {
            "description": "Client details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "cliente@example.com",
                        "nombre": "Juan Pérez",
                        "telefono": "+1234567890",
                        "fecha_nacimiento": "1990-01-01",
                        "activo": true,
                        "fecha_registro": "2024-03-19T10:00:00"
                    }
                }
            }
        },
        404: {
            "description": "Client not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Client not found"
                    }
                }
            }
        }
    }
)
async def get_client(
    client_id: int,
    db: Session = Depends(db_session),
    current_user: Client = Depends(get_current_user)
):
    """
    Retrieve a specific client by ID.
    
    - **Admin users**: Can see any client
    - **Regular users**: Can only see themselves
    
    Parameters:
    - **client_id**: The ID of the client to retrieve
    """
    if not current_user.is_admin and current_user.id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this client"
        )
    
    client = db.query(Client).filter(Client.id == client_id).first()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client

@router.post(
    "/clients/",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new client",
    description="""
    Create a new client.
    
    - **Admin users**: Can create any client
    - **Regular users**: Cannot create clients
    
    Parameters:
    - **client_data**: Client information
    """,
    responses={
        200: {
            "description": "Client created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "nuevo.email@example.com",
                        "nombre": "Juan Pérez Actualizado",
                        "telefono": "+0987654321",
                        "fecha_nacimiento": "1990-01-01",
                        "activo": true
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email already registered"
                    }
                }
            }
        }
    }
)
async def create_client(
    client_data: ClienteCreate,
    db: Session = Depends(db_session),
    current_user: Client = Depends(get_current_user)
):
    """
    Create a new client.
    
    - **Admin users**: Can create any client
    - **Regular users**: Cannot create clients
    
    Parameters:
    - **client_data**: Client information
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create clients"
        )
    
    # Check if email already exists
    existing_client = db.query(Client).filter(Client.email == client_data.email).first()
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone already exists
    existing_phone = db.query(Client).filter(Client.phone == client_data.phone).first()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create new client
    hashed_password = get_password_hash(client_data.password)
    db_client = Client(
        email=client_data.email,
        full_name=client_data.full_name,
        phone=client_data.phone,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False
    )
    
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.put(
    "/clients/{client_id}",
    response_model=ClientResponse,
    summary="Update client",
    description="""
    Update a client.
    
    - **Admin users**: Can update any client
    - **Regular users**: Can only update themselves
    
    Parameters:
    - **client_id**: The ID of the client to update
    - **client_data**: Updated client information
    """,
    responses={
        200: {
            "description": "Client updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "nuevo.email@example.com",
                        "nombre": "Juan Pérez Actualizado",
                        "telefono": "+0987654321",
                        "fecha_nacimiento": "1990-01-01",
                        "activo": true
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email already registered"
                    }
                }
            }
        }
    }
)
async def update_client(
    client_id: int,
    client_data: ClienteUpdate,
    db: Session = Depends(db_session),
    current_user: Client = Depends(get_current_user)
):
    """
    Update a client.
    
    - **Admin users**: Can update any client
    - **Regular users**: Can only update themselves
    
    Parameters:
    - **client_id**: The ID of the client to update
    - **client_data**: Updated client information
    """
    if not current_user.is_admin and current_user.id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this client"
        )
    
    client = db.query(Client).filter(Client.id == client_id).first()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Check email uniqueness if provided
    if client_data.email and client_data.email != client.email:
        existing_client = db.query(Client).filter(Client.email == client_data.email).first()
        if existing_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check phone uniqueness if provided
    if client_data.phone and client_data.phone != client.phone:
        existing_phone = db.query(Client).filter(Client.phone == client_data.phone).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Update client data
    if client_data.email:
        client.email = client_data.email
    if client_data.full_name:
        client.full_name = client_data.full_name
    if client_data.phone:
        client.phone = client_data.phone
    if client_data.password:
        client.hashed_password = get_password_hash(client_data.password)
    
    db.commit()
    db.refresh(client)
    return client

@router.delete(
    "/clients/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete client",
    description="""
    Delete a client.
    
    - **Admin users**: Can delete any client
    - **Regular users**: Cannot delete clients
    
    Parameters:
    - **client_id**: The ID of the client to delete
    """,
    responses={
        204: {
            "description": "Client deleted successfully"
        }
    }
)
async def delete_client(
    client_id: int,
    db: Session = Depends(db_session),
    current_user: Client = Depends(get_current_user)
):
    """
    Delete a client.
    
    - **Admin users**: Can delete any client
    - **Regular users**: Cannot delete clients
    
    Parameters:
    - **client_id**: The ID of the client to delete
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete clients"
        )
    
    client = db.query(Client).filter(Client.id == client_id).first()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    db.delete(client)
    db.commit()

@router.patch(
    "/clients/{client_id}/activate",
    response_model=ClientResponse,
    summary="Activate client",
    description="""
    Activate a client.
    
    - **Admin users only**: Can activate clients
    
    Parameters:
    - **client_id**: The ID of the client to activate
    """,
    responses={
        200: {
            "description": "Client activated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "cliente@example.com",
                        "nombre": "Juan Pérez",
                        "telefono": "+1234567890",
                        "fecha_nacimiento": "1990-01-01",
                        "activo": true
                    }
                }
            }
        }
    }
)
async def activate_client(
    client_id: int,
    db: Session = Depends(db_session),
    current_user: Client = Depends(get_current_user)
):
    """
    Activate a client.
    
    - **Admin users only**: Can activate clients
    
    Parameters:
    - **client_id**: The ID of the client to activate
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to activate clients"
        )
    
    client = db.query(Client).filter(Client.id == client_id).first()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    client.is_active = True
    db.commit()
    db.refresh(client)
    return client

@router.patch(
    "/clients/{client_id}/deactivate",
    response_model=ClientResponse,
    summary="Deactivate client",
    description="""
    Deactivate a client.
    
    - **Admin users only**: Can deactivate clients
    
    Parameters:
    - **client_id**: The ID of the client to deactivate
    """,
    responses={
        200: {
            "description": "Client deactivated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "cliente@example.com",
                        "nombre": "Juan Pérez",
                        "telefono": "+1234567890",
                        "fecha_nacimiento": "1990-01-01",
                        "activo": false
                    }
                }
            }
        }
    }
)
async def deactivate_client(
    client_id: int,
    db: Session = Depends(db_session),
    current_user: Client = Depends(get_current_user)
):
    """
    Deactivate a client.
    
    - **Admin users only**: Can deactivate clients
    
    Parameters:
    - **client_id**: The ID of the client to deactivate
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to deactivate clients"
        )
    
    client = db.query(Client).filter(Client.id == client_id).first()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    client.is_active = False
    db.commit()
    db.refresh(client)
    return client 