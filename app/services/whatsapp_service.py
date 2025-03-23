from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from fastapi import HTTPException
from app.core.config import get_settings
from app.services.nlp_service import NLPService
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

settings = get_settings()

class WhatsAppService:
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.whatsapp_number = settings.TWILIO_WHATSAPP_NUMBER
        self.client = Client(self.account_sid, self.auth_token)
        self.nlp_service = NLPService()
        self.conversations: Dict[str, List[Dict[str, str]]] = {}

    async def send_message(
        self,
        to: str,
        message: str,
        media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envía un mensaje de WhatsApp a un número específico.
        
        Args:
            to: Número de teléfono del destinatario (formato: +521234567890)
            message: Contenido del mensaje
            media_url: URL opcional de una imagen o archivo para enviar
        
        Returns:
            Dict con la información de la respuesta de Twilio
        """
        try:
            # Asegurarse de que el número tenga el formato correcto para WhatsApp
            to_whatsapp = f"whatsapp:{to}"
            from_whatsapp = f"whatsapp:{self.whatsapp_number}"

            message_params = {
                "from_": from_whatsapp,
                "to": to_whatsapp,
                "body": message
            }

            if media_url:
                message_params["media_url"] = [media_url]

            message = self.client.messages.create(**message_params)

            # Guardar el mensaje en el historial de conversación
            if to not in self.conversations:
                self.conversations[to] = []
            self.conversations[to].append({
                "role": "assistant",
                "content": message.body
            })

            return {
                "status": "success",
                "message_sid": message.sid,
                "to": to,
                "content": message.body
            }

        except TwilioRestException as e:
            # Log the error but don't raise an HTTP exception
            print(f"Error al enviar mensaje de WhatsApp: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "to": to,
                "content": message
            }
        except Exception as e:
            # Log any other errors but don't raise an HTTP exception
            print(f"Error inesperado al enviar mensaje: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "to": to,
                "content": message
            }

    async def process_incoming_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un mensaje entrante de WhatsApp.
        
        Args:
            data: Datos del mensaje recibido de Twilio
        
        Returns:
            Dict con la respuesta procesada
        """
        try:
            # Extraer información relevante del mensaje
            from_number = data.get("From", "").replace("whatsapp:", "")
            message_body = data.get("Body", "")
            media_urls = []

            # Procesar archivos multimedia si existen
            num_media = int(data.get("NumMedia", 0))
            for i in range(num_media):
                media_url = data.get(f"MediaUrl{i}")
                if media_url:
                    media_urls.append(media_url)

            # Inicializar o recuperar el historial de conversación
            if from_number not in self.conversations:
                self.conversations[from_number] = []

            # Agregar el mensaje del usuario al historial
            self.conversations[from_number].append({
                "role": "user",
                "content": message_body
            })

            # Analizar el mensaje con NLP
            nlp_result = await self.nlp_service.analyze_message(
                message_body,
                self.conversations[from_number]
            )

            # Si es una solicitud de cita, extraer detalles específicos
            if nlp_result["analysis"]["intent"] == "agendar_cita":
                appointment_details = await self.nlp_service.extract_appointment_details(
                    message_body
                )
                nlp_result["appointment_details"] = appointment_details

            # Enviar la respuesta generada
            await self.send_message(
                from_number,
                nlp_result["response"]
            )

            return {
                "from": from_number,
                "message": message_body,
                "media_urls": media_urls,
                "timestamp": data.get("Timestamp"),
                "message_sid": data.get("MessageSid"),
                "nlp_analysis": nlp_result["analysis"]
            }

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error al procesar mensaje entrante: {str(e)}"
            )

    async def send_appointment_confirmation(
        self,
        phone_number: str,
        appointment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envía un mensaje de confirmación de cita.
        
        Args:
            phone_number: Número de teléfono del cliente
            appointment_details: Detalles de la cita (fecha, hora, servicio, etc.)
        
        Returns:
            Dict con la información de la respuesta
        """
        message = (
            f"¡Hola! Tu cita ha sido confirmada:\n\n"
            f"📅 Fecha: {appointment_details['fecha']}\n"
            f"⏰ Hora: {appointment_details['hora']}\n"
            f"💇 Servicio: {appointment_details['servicio']}\n\n"
            f"Para cancelar o reprogramar tu cita, responde a este mensaje.\n"
            f"¡Te esperamos!"
        )

        return await self.send_message(phone_number, message)

    async def send_appointment_reminder(
        self,
        phone_number: str,
        appointment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envía un recordatorio de cita.
        
        Args:
            phone_number: Número de teléfono del cliente
            appointment_details: Detalles de la cita (fecha, hora, servicio, etc.)
        
        Returns:
            Dict con la información de la respuesta
        """
        message = (
            f"¡Hola! Te recordamos tu cita para mañana:\n\n"
            f"📅 Fecha: {appointment_details['fecha']}\n"
            f"⏰ Hora: {appointment_details['hora']}\n"
            f"💇 Servicio: {appointment_details['servicio']}\n\n"
            f"Si necesitas hacer algún cambio, responde a este mensaje.\n"
            f"¡Te esperamos!"
        )

        return await self.send_message(phone_number, message) 