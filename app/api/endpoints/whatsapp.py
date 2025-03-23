from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.whatsapp_service import WhatsAppService
from typing import Dict, Any
import json

router = APIRouter()
whatsapp_service = WhatsAppService()

@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Endpoint para recibir webhooks de Twilio WhatsApp.
    """
    try:
        # Obtener los datos del formulario
        form_data = await request.form()
        message_data = dict(form_data)

        # Procesar el mensaje en segundo plano
        background_tasks.add_task(
            process_whatsapp_message,
            message_data,
            db
        )

        return {"status": "success", "message": "Mensaje recibido y siendo procesado"}

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al procesar webhook: {str(e)}"
        )

async def process_whatsapp_message(data: Dict[str, Any], db: Session):
    """
    Procesa un mensaje de WhatsApp recibido.
    """
    try:
        # Procesar el mensaje usando el servicio de WhatsApp
        processed_message = await whatsapp_service.process_incoming_message(data)

        # Aquí implementaremos la lógica de procesamiento del mensaje
        # Por ejemplo:
        # - Detectar si es una solicitud de cita
        # - Responder preguntas frecuentes
        # - Manejar cancelaciones o cambios de cita
        # Por ahora, solo enviamos un mensaje de confirmación
        
        response_message = (
            "¡Gracias por tu mensaje! En breve te atenderemos. "
            "Si deseas agendar una cita, por favor indícanos el servicio y "
            "horario que prefieres."
        )

        await whatsapp_service.send_message(
            processed_message["from"],
            response_message
        )

    except Exception as e:
        # Aquí deberíamos loguear el error para debugging
        print(f"Error procesando mensaje de WhatsApp: {str(e)}")
        # No re-lanzamos la excepción porque esto se ejecuta en segundo plano 