from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, text, select
from typing import List
from datetime import datetime, timedelta
from app.db.database import get_db
from app.models.cita import Cita as CitaModel, EstadoCita
from app.models.cliente import Cliente as ClienteModel
from app.schemas.cita import Cita, CitaCreate, CitaUpdate, CitaResponse
from app.services.notification_service import NotificationService

router = APIRouter()
notification_service = NotificationService()

@router.post("/", response_model=Cita, status_code=status.HTTP_201_CREATED)
async def create_cita(
    cita: CitaCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Verificar que el cliente existe
    cliente = db.query(ClienteModel).filter(ClienteModel.id == cita.cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    # Verificar si ya existe una cita en el mismo horario
    fecha_fin = cita.fecha_hora + timedelta(minutes=cita.duracion_minutos)
    
    # Buscar citas que se solapan
    citas_existentes = db.query(CitaModel).filter(
        and_(
            CitaModel.estado != EstadoCita.CANCELADA,
            CitaModel.fecha_hora < fecha_fin,
            CitaModel.fecha_hora + timedelta(minutes=30) > cita.fecha_hora
        )
    ).all()
    
    if citas_existentes:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una cita programada para este horario"
        )
    
    # Crear la cita
    db_cita = CitaModel(
        cliente_id=cita.cliente_id,
        fecha_hora=cita.fecha_hora,
        duracion_minutos=cita.duracion_minutos,
        servicio=cita.servicio,
        notas=cita.notas,
        estado=EstadoCita.PENDIENTE,
        recordatorio_enviado=False
    )
    db.add(db_cita)
    try:
        db.commit()
        db.refresh(db_cita)
        
        # Enviar confirmación de cita en segundo plano
        try:
            background_tasks.add_task(
                notification_service.send_confirmation_message,
                db_cita,
                cliente_id=cliente.id,
                telefono=cliente.telefono
            )
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error al enviar mensaje de confirmación: {str(e)}")
            
        return db_cita
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo crear la cita: {str(e)}"
        )

@router.get("/", response_model=List[Cita])
def read_citas(
    skip: int = 0, 
    limit: int = 100, 
    fecha_inicio: datetime = None,
    fecha_fin: datetime = None,
    db: Session = Depends(get_db)
):
    query = db.query(CitaModel)
    
    if fecha_inicio:
        query = query.filter(CitaModel.fecha_hora >= fecha_inicio)
    if fecha_fin:
        query = query.filter(CitaModel.fecha_hora <= fecha_fin)
        
    citas = query.order_by(CitaModel.fecha_hora).offset(skip).limit(limit).all()
    return citas

@router.get("/{cita_id}", response_model=Cita)
def read_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = db.query(CitaModel).filter(CitaModel.id == cita_id).first()
    if cita is None:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita

@router.put("/{cita_id}", response_model=Cita)
async def update_cita(
    cita_id: int, 
    cita_update: CitaUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_cita = db.query(CitaModel).filter(CitaModel.id == cita_id).first()
    if db_cita is None:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    update_data = cita_update.model_dump(exclude_unset=True)
    
    # Si se está actualizando la fecha/hora, verificar disponibilidad
    if "fecha_hora" in update_data or "duracion_minutos" in update_data:
        nueva_fecha = update_data.get("fecha_hora", db_cita.fecha_hora)
        nueva_duracion = update_data.get("duracion_minutos", db_cita.duracion_minutos)
        fecha_fin = nueva_fecha + timedelta(minutes=nueva_duracion)
        
        cita_existente = db.query(CitaModel).filter(
            CitaModel.id != cita_id,
            CitaModel.fecha_hora < fecha_fin,
            CitaModel.fecha_hora + timedelta(minutes=CitaModel.duracion_minutos) > nueva_fecha,
            CitaModel.estado != EstadoCita.CANCELADA
        ).first()
        
        if cita_existente:
            raise HTTPException(
                status_code=400,
                detail="Ya existe una cita programada para este horario"
            )
    
    # Si se está actualizando el estado a CONFIRMADA, enviar confirmación
    if "estado" in update_data and update_data["estado"] == EstadoCita.CONFIRMADA:
        background_tasks.add_task(
            notification_service.send_appointment_confirmation,
            db_cita
        )
    
    for field, value in update_data.items():
        setattr(db_cita, field, value)
    
    try:
        db.commit()
        db.refresh(db_cita)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se pudo actualizar la cita"
        )
    return db_cita

@router.delete("/{cita_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cita(
    cita_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_cita = db.query(CitaModel).filter(CitaModel.id == cita_id).first()
    if db_cita is None:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Enviar notificación de cancelación
    message = (
        "Tu cita ha sido cancelada. Si deseas reagendar, "
        "por favor contáctanos o responde a este mensaje."
    )
    background_tasks.add_task(
        notification_service.whatsapp_service.send_message,
        db_cita.cliente.telefono,
        message
    )
    
    db_cita.estado = EstadoCita.CANCELADA
    db.commit()
    return None

@router.patch("/{cita_id}", response_model=CitaResponse)
async def patch_cita(
    cita_id: int,
    cita_update: CitaUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> CitaModel:
    """
    Actualiza una cita existente.
    """
    try:
        # Obtener la cita con el cliente precargado
        cita = db.query(CitaModel).join(CitaModel.cliente).filter(CitaModel.id == cita_id).first()
        if not cita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró la cita con ID {cita_id}"
            )

        # Actualizar solo los campos proporcionados
        update_data = cita_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cita, field, value)

        # Si se está confirmando la cita, enviar mensaje de confirmación
        if cita_update.estado == EstadoCita.CONFIRMADA:
            try:
                await notification_service.send_confirmation_message(cita, db)
            except Exception as e:
                print(f"Error al enviar mensaje de confirmación: {str(e)}")
                # No fallamos la actualización si el mensaje falla

        db.commit()
        db.refresh(cita)
        return cita

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la cita: {str(e)}"
        ) 