from openai import AsyncOpenAI
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.core.config import get_settings
from app.services.faq_service import FAQService
import json
import os

settings = get_settings()

class NLPService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.faq_service = FAQService()
        self.system_prompt = f"""Eres un asistente virtual amable y profesional para un salón de belleza. 
        Tu trabajo es ayudar a los clientes a:
        1. Agendar citas
        2. Responder preguntas sobre servicios
        3. Manejar cambios o cancelaciones de citas
        4. Proporcionar información general sobre el salón

        Horario de atención: {self.faq_service.faqs['horario']['respuesta']}

        Servicios disponibles:
        {self.faq_service._generar_lista_servicios()}

        Debes ser cordial y mantener un tono profesional pero cercano.
        Cuando los clientes quieran agendar una cita, necesitas obtener:
        - Tipo de servicio
        - Fecha y hora preferida
        - Nombre del cliente (si es nuevo)
        - Teléfono (si es nuevo)"""
        self.testing = os.getenv("TESTING", "false").lower() == "true"
        self._mock_response = None
        self._mock_exception = None

    def set_mock_response(self, response: Any) -> None:
        """Set a mock response for testing purposes"""
        if isinstance(response, Exception):
            self._mock_exception = response
            self._mock_response = None
        else:
            self._mock_response = response
            self._mock_exception = None

    async def analyze_message(self, message: str) -> Dict[str, Any]:
        """Analiza un mensaje y retorna la intención y otros detalles"""
        try:
            if self.testing:
                if self._mock_exception:
                    raise self._mock_exception
                if self._mock_response:
                    if hasattr(self._mock_response.choices[0].message, 'function_call'):
                        return json.loads(self._mock_response.choices[0].message.function_call.arguments)
                    return {
                        "intent": "error",
                        "sentimiento": "neutral",
                        "error": "Invalid mock response format"
                    }
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente especializado en analizar mensajes para una peluquería."},
                    {"role": "user", "content": message}
                ],
                functions=[{
                    "name": "analyze_message",
                    "description": "Analiza el mensaje del usuario",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "intent": {
                                "type": "string",
                                "enum": ["consulta_horarios", "agendar_cita", "consulta_servicios", "error"],
                                "description": "La intención del mensaje"
                            },
                            "servicio": {
                                "type": "string",
                                "description": "El servicio mencionado en el mensaje"
                            },
                            "sentimiento": {
                                "type": "string",
                                "enum": ["positivo", "negativo", "neutral"],
                                "description": "El sentimiento del mensaje"
                            },
                            "error": {
                                "type": "string",
                                "description": "Descripción del error si lo hay"
                            }
                        },
                        "required": ["intent", "sentimiento"]
                    }
                }],
                function_call={"name": "analyze_message"}
            )
            return json.loads(response.choices[0].message.function_call.arguments)
        except Exception as e:
            return {
                "intent": "error",
                "sentimiento": "neutral",
                "error": str(e)
            }

    async def generate_response(self, analysis: Dict[str, Any]) -> str:
        """Genera una respuesta basada en el análisis del mensaje"""
        try:
            if self.testing:
                if self._mock_exception:
                    raise self._mock_exception
                if self._mock_response:
                    return self._mock_response.choices[0].message.content
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente amable de una peluquería."},
                    {"role": "user", "content": f"Genera una respuesta para un mensaje con este análisis: {json.dumps(analysis)}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error al generar respuesta: {str(e)}"

    async def extract_appointment_details(self, message: str) -> Dict[str, Any]:
        """Extrae los detalles de una cita del mensaje"""
        try:
            if self.testing:
                if self._mock_exception:
                    raise self._mock_exception
                if self._mock_response:
                    if hasattr(self._mock_response.choices[0].message, 'function_call'):
                        return json.loads(self._mock_response.choices[0].message.function_call.arguments)
                    return {"error": "Invalid mock response format"}
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente especializado en extraer detalles de citas para una peluquería."},
                    {"role": "user", "content": message}
                ],
                functions=[{
                    "name": "extract_details",
                    "description": "Extrae los detalles de la cita del mensaje",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "servicio": {
                                "type": "string",
                                "description": "El servicio solicitado"
                            },
                            "fecha": {
                                "type": "string",
                                "format": "date",
                                "description": "La fecha de la cita (YYYY-MM-DD)"
                            },
                            "hora": {
                                "type": "string",
                                "description": "La hora de la cita (HH:MM)"
                            },
                            "duracion_estimada": {
                                "type": "integer",
                                "description": "Duración estimada en minutos"
                            }
                        },
                        "required": ["servicio", "fecha", "hora"]
                    }
                }],
                function_call={"name": "extract_details"}
            )
            return json.loads(response.choices[0].message.function_call.arguments)
        except Exception as e:
            return {"error": str(e)}

    def _get_mock_response(self) -> Any:
        """Get the current mock response"""
        return self._mock_response

    def _get_mock_exception(self) -> Optional[Exception]:
        """Get the current mock exception"""
        return self._mock_exception 