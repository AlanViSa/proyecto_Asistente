from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.cliente import Cliente as ClienteModel
from app.schemas.cliente import Cliente, ClienteCreate, ClienteUpdate

router = APIRouter()

@router.post("/", response_model=Cliente, status_code=status.HTTP_201_CREATED)
def create_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    # Verificar si ya existe un cliente con el mismo teléfono o email
    if cliente.email:
        existing_email = db.query(ClienteModel).filter(ClienteModel.email == cliente.email).first()
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Ya existe un cliente con este email."
            )
    
    existing_phone = db.query(ClienteModel).filter(ClienteModel.telefono == cliente.telefono).first()
    if existing_phone:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un cliente con este teléfono."
        )

    # Crear el cliente
    db_cliente = ClienteModel(
        nombre=cliente.nombre,
        telefono=cliente.telefono,
        email=cliente.email,
        preferencias=cliente.preferencias,
        activo=True
    )
    db.add(db_cliente)
    try:
        db.commit()
        db.refresh(db_cliente)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se pudo crear el cliente. Error interno."
        )
    return db_cliente

@router.get("/", response_model=List[Cliente])
def read_clientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    clientes = db.query(ClienteModel).offset(skip).limit(limit).all()
    return clientes

@router.get("/{cliente_id}", response_model=Cliente)
def read_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.put("/{cliente_id}", response_model=Cliente)
def update_cliente(
    cliente_id: int, 
    cliente_update: ClienteUpdate, 
    db: Session = Depends(get_db)
):
    db_cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
    if db_cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    update_data = cliente_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_cliente, field, value)
    
    try:
        db.commit()
        db.refresh(db_cliente)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se pudo actualizar el cliente. El teléfono o email ya existe."
        )
    return db_cliente

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cliente(cliente_id: int, db: Session = Depends(get_db)):
    db_cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
    if db_cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    db_cliente.activo = False
    db.commit()
    return None 