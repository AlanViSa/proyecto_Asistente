import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from app.services.nlp_service import NLPService
import json

@pytest.fixture
def nlp_service():
    return NLPService()

@pytest.mark.asyncio
async def test_analyze_message_faq():
    """Prueba el análisis de un mensaje de consulta de FAQ"""
    nlp_service = NLPService()
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                function_call=MagicMock(
                    arguments='{"intent": "consulta_horarios", "sentimiento": "neutral", "faq_key": "horario"}'
                )
            )
        )
    ]

    with patch.object(nlp_service.client, "chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await nlp_service.analyze_message("¿Cuál es el horario de atención?")
        
        assert result["intent"] == "consulta_horarios"
        assert result["sentimiento"] == "neutral"
        assert result["faq_key"] == "horario"

@pytest.mark.asyncio
async def test_analyze_message_appointment():
    """Prueba el análisis de un mensaje de solicitud de cita"""
    nlp_service = NLPService()
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                function_call=MagicMock(
                    arguments='{"intent": "agendar_cita", "servicio": "corte_dama", "sentimiento": "positivo"}'
                )
            )
        )
    ]

    with patch.object(nlp_service.client, "chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await nlp_service.analyze_message("Quiero agendar un corte de dama")
        
        assert result["intent"] == "agendar_cita"
        assert result["servicio"] == "corte_dama"
        assert result["sentimiento"] == "positivo"

@pytest.mark.asyncio
async def test_extract_appointment_details():
    """Prueba la extracción de detalles de una cita"""
    nlp_service = NLPService()
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                function_call=MagicMock(
                    arguments='''
                    {
                        "servicio": "corte_dama",
                        "fecha": "2024-03-22",
                        "hora": "14:30",
                        "duracion_estimada": 60
                    }
                    '''
                )
            )
        )
    ]

    with patch.object(nlp_service.client, "chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await nlp_service.extract_appointment_details("Quiero el corte de dama mañana a las 2:30 PM")
        
        assert result["servicio"] == "corte_dama"
        assert result["fecha"] == "2024-03-22"
        assert result["hora"] == "14:30"
        assert result["duracion_estimada"] == 60

@pytest.mark.asyncio
async def test_analyze_message_error_handling():
    """Prueba el manejo de errores en el análisis de mensajes"""
    nlp_service = NLPService()
    
    with patch.object(nlp_service.client, "chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        result = await nlp_service.analyze_message("¿Cuál es el horario?")
        
        assert result["intent"] == "error"
        assert result["sentimiento"] == "neutral"
        assert result["error"] == "API Error"

@pytest.mark.asyncio
async def test_generate_response():
    """Prueba la generación de respuestas"""
    nlp_service = NLPService()
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="Esta es una respuesta de prueba"
            )
        )
    ]

    analysis = {
        "intent": "consulta_horarios",
        "sentimiento": "neutral",
        "faq_key": "horario"
    }

    with patch.object(nlp_service.client, "chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await nlp_service.generate_response(analysis)
        
        assert result == "Esta es una respuesta de prueba" 