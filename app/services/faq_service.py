from typing import Dict, Any, List
import json
from datetime import datetime, time, timedelta
from app.core.config import get_settings

settings = get_settings()

class FAQService:
    def __init__(self):
        # Horarios del salón
        self.horario_apertura = time(9, 0)  # 9:00 AM
        self.horario_cierre = time(20, 0)   # 8:00 PM
        
        # Servicios disponibles y sus duraciones estimadas (en minutos)
        self.servicios = {
            "corte_dama": {
                "nombre": "Corte de Dama",
                "duracion": 60,
                "descripcion": "Incluye lavado, corte y peinado"
            },
            "corte_caballero": {
                "nombre": "Corte de Caballero",
                "duracion": 30,
                "descripcion": "Incluye lavado y corte"
            },
            "tinte": {
                "nombre": "Tinte",
                "duracion": 120,
                "descripcion": "Incluye aplicación de tinte, lavado y peinado"
            },
            "mechas": {
                "nombre": "Mechas",
                "duracion": 180,
                "descripcion": "Incluye decoloración, matización, lavado y peinado"
            },
            "peinado": {
                "nombre": "Peinado",
                "duracion": 60,
                "descripcion": "Incluye lavado y peinado especial"
            },
            "tratamiento": {
                "nombre": "Tratamiento Capilar",
                "duracion": 90,
                "descripcion": "Tratamiento personalizado según tipo de cabello"
            }
        }
        
        # Preguntas frecuentes y sus respuestas
        self.faqs = {
            "horario": {
                "pregunta": "¿Cuál es su horario de atención?",
                "respuesta": f"Nuestro horario de atención es de {self.horario_apertura.strftime('%I:%M %p')} "
                           f"a {self.horario_cierre.strftime('%I:%M %p')}, de lunes a sábado."
            },
            "servicios": {
                "pregunta": "¿Qué servicios ofrecen?",
                "respuesta": self._generar_lista_servicios()
            },
            "estacionamiento": {
                "pregunta": "¿Tienen estacionamiento?",
                "respuesta": "Sí, contamos con estacionamiento gratuito para nuestros clientes."
            },
            "pago": {
                "pregunta": "¿Qué métodos de pago aceptan?",
                "respuesta": "Aceptamos efectivo, tarjetas de crédito/débito y transferencias bancarias."
            },
            "cancelacion": {
                "pregunta": "¿Cuál es su política de cancelación?",
                "respuesta": "Puedes cancelar o reprogramar tu cita hasta 24 horas antes sin cargo. "
                           "Cancelaciones con menos tiempo pueden generar un cargo del 50%."
            }
        }

    def _generar_lista_servicios(self) -> str:
        """Genera una lista formateada de servicios disponibles."""
        respuesta = "Nuestros servicios principales son:\n\n"
        for servicio in self.servicios.values():
            respuesta += f"📌 {servicio['nombre']} ({servicio['duracion']} min)\n"
            respuesta += f"   {servicio['descripcion']}\n\n"
        return respuesta

    def get_servicio_info(self, servicio_key: str) -> Dict[str, Any]:
        """
        Obtiene información detallada de un servicio específico.
        """
        return self.servicios.get(servicio_key, None)

    def get_duracion_servicio(self, servicio_key: str) -> int:
        """
        Obtiene la duración estimada de un servicio.
        """
        servicio = self.servicios.get(servicio_key)
        return servicio["duracion"] if servicio else 60  # Default 60 minutos

    def get_faq_response(self, pregunta_key: str) -> str:
        """
        Obtiene la respuesta a una pregunta frecuente.
        """
        faq = self.faqs.get(pregunta_key)
        return faq["respuesta"] if faq else None

    def es_horario_disponible(self, fecha_hora: datetime) -> bool:
        """
        Verifica si una hora específica está dentro del horario de atención.
        """
        hora = fecha_hora.time()
        return self.horario_apertura <= hora <= self.horario_cierre

    def get_siguiente_horario_disponible(self, fecha_hora: datetime) -> datetime:
        """
        Obtiene el siguiente horario disponible si el solicitado está fuera de horario.
        """
        if fecha_hora.time() < self.horario_apertura:
            return fecha_hora.replace(
                hour=self.horario_apertura.hour,
                minute=self.horario_apertura.minute
            )
        elif fecha_hora.time() > self.horario_cierre:
            siguiente_dia = fecha_hora + timedelta(days=1)
            return siguiente_dia.replace(
                hour=self.horario_apertura.hour,
                minute=self.horario_apertura.minute
            )
        return fecha_hora

    def validar_servicio(self, servicio: str) -> bool:
        """
        Valida si un servicio existe en el catálogo.
        """
        return servicio.lower() in self.servicios

    def get_faq(self, key: str) -> Dict[str, str]:
        """
        Obtiene la información de una FAQ por su clave.
        """
        if key in self.faqs:
            return self.faqs[key]
        return {
            "pregunta": "",
            "respuesta": "Lo siento, no tengo información sobre esa pregunta."
        } 