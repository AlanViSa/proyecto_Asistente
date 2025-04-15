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
    # Verify that the client exists
    client = db.query(ClienteModel).filter(ClienteModel.id == cita.client_id).first()
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    # Verify if an appointment already exists at the same time
    end_time = cita.date_time + timedelta(minutes=cita.duration_minutes)
    
    # Find overlapping appointments
    existing_appointments = db.query(CitaModel).filter(
        and_(
            CitaModel.status != EstadoCita.CANCELADA,
            CitaModel.date_time < end_time,
            CitaModel.date_time + timedelta(minutes=30) > cita.date_time
        )
    ).all()
    
    if citas_existentes:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una cita programada para este horario"
        )# Already exists an appointment scheduled for this time
    
    # Create the appointment
    db_appointment = CitaModel(
        client_id=cita.client_id,
        date_time=cita.date_time,
        duration_minutes=cita.duration_minutes,
        service=cita.service,
        notes=cita.notes,
        status=EstadoCita.PENDIENTE,
        reminder_sent=False
    )
    db.add(db_cita)
    try:
        db.commit()
        db.refresh(db_cita)
        
        # Enviar confirmación de cita en segundo plano
        try:
            background_tasks.add_task( # Send appointment confirmation in the background
                notification_service.send_confirmation_message, 
                db_appointment,
                client_id=client.id,
                phone=client.phone
            )
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error al enviar mensaje de confirmación: {str(e)}")
            
        return db_cita
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Could not create the appointment: {str(e)}"
        )

@router.get("/", response_model=List[Cita])
def read_appointments(
    skip: int = 0, 
    limit: int = 100, 
    start_date: datetime = None,
    end_date: datetime = None,
    db: Session = Depends(get_db)
):
    query = db.query(CitaModel)
    
    if start_date:
        query = query.filter(CitaModel.date_time >= start_date)
    if end_date:
        query = query.filter(CitaModel.date_time <= end_date)
        
    appointments = query.order_by(CitaModel.date_time).offset(skip).limit(limit).all()
    return appointments

@router.get("/{appointment_id}", response_model=Cita)
def read_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.query(CitaModel).filter(CitaModel.id == appointment_id).first()
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@router.put("/{appointment_id}", response_model=Cita)
async def update_appointment(
    appointment_id: int, 
    appointment_update: CitaUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_cita = db.query(CitaModel).filter(CitaModel.id == cita_id).first()
    if db_cita is None:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    update_data = appointment_update.model_dump(exclude_unset=True)
    
    # If date/time is being updated, verify availability
    if "date_time" in update_data or "duration_minutes" in update_data:
        new_date = update_data.get("date_time", db_appointment.date_time)
        new_duration = update_data.get("duration_minutes", db_appointment.duration_minutes)
        end_time = new_date + timedelta(minutes=new_duration)
        
        existing_appointment = db.query(CitaModel).filter(
            CitaModel.id != appointment_id,
            CitaModel.date_time < end_time,
            CitaModel.date_time + timedelta(minutes=CitaModel.duration_minutes) > new_date,
            CitaModel.status != EstadoCita.CANCELADA
        ).first()
        
        if existing_appointment:
            raise HTTPException(
                status_code=400,
                detail="Ya existe una cita programada para este horario"
            )
    
    # Si se está actualizando el estado a CONFIRMADA, enviar confirmación
    if "estado" in update_data and update_data["estado"] == EstadoCita.CONFIRMADA:
        background_tasks.add_task( # If the status is being updated to CONFIRMED, send confirmation
            notification_service.send_appointment_confirmation,
            db_cita
        )
    
    for field, value in update_data.items():
        setattr(db_appointment, field, value)
    
    try:
        db.commit()
        db.refresh(db_cita)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se pudo actualizar la cita"
        )
    return db_appointment

@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_cita = db.query(CitaModel).filter(CitaModel.id == appointment_id).first()
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
    
    db_cita.status = EstadoCita.CANCELADA
    db.commit()
    return None

@router.patch("/{appointment_id}", response_model=CitaResponse)
async def patch_appointment(
    appointment_id: int,
    appointment_update: CitaUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> CitaModel:
    """
    Actualiza una cita existente.
    """ # Updates an existing appointment
    try:
        # Get the appointment with the client preloaded
        appointment = db.query(CitaModel).join(CitaModel.client).filter(CitaModel.id == appointment_id).first()
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment with ID {appointment_id} not found"
            )

        # Actualizar solo los campos proporcionados
        update_data = cita_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cita, field, value)

        # If the appointment is being confirmed, send confirmation message
        if appointment_update.status == EstadoCita.CONFIRMADA:
            try:
                await notification_service.send_confirmation_message(appointment, db)
            except Exception as e:
                print(f"Error al enviar mensaje de confirmación: {str(e)}")
                # We don't fail the update if the message fails

        db.commit()
        db.refresh(appointment)
        return appointment

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la cita: {str(e)}"
        ) 