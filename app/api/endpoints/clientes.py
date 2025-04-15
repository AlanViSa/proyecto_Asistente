from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.cliente import Client as ClientModel
from app.schemas.cliente import Client, ClientCreate, ClientUpdate

router = APIRouter()

@router.post("/", response_model=Client, status_code=status.HTTP_201_CREATED)
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    # Check if a client with the same phone or email already exists
    if client.email:
        existing_email = db.query(ClientModel).filter(ClientModel.email == client.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="A client with this email already exists.")

    existing_phone = db.query(ClientModel).filter(ClientModel.phone == client.phone).first()
    if existing_phone:
        raise HTTPException(status_code=400, detail="A client with this phone number already exists.")

    # Create the client
    db_client = ClientModel(
        name=client.name,
        phone=client.phone,
        email=client.email,
        preferences=client.preferences,
        is_active=True
    )
    db.add(db_client)
    try:
        db.commit()
        db.refresh(db_client)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not create the client. Internal error.")
    return db_client

@router.get("/", response_model=List[Client])
def read_clients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    clients = db.query(ClientModel).offset(skip).limit(limit).all()
    return clients

@router.get("/{client_id}", response_model=Client)
def read_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.put("/{client_id}", response_model=Client)
def update_client(client_id: int, client_update: ClientUpdate, db: Session = Depends(get_db)):
    db_client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    update_data = client_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_client, field, value)

    try:
        db.commit()
        db.refresh(db_client)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not update the client. The phone or email already exists.")
    return db_client

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    db_client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    db_client.is_active = False
    db.commit()
    return None