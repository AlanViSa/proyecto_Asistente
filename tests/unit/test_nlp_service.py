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
    """Tests the analysis of a FAQ query message"""
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
        
        result = await nlp_service.analyze_message("What are the opening hours?")
        
        assert result["intent"] == "faq_query"
        assert result["sentiment"] == "neutral"
        assert result["faq_key"] == "schedule"

@pytest.mark.asyncio
async def test_analyze_message_appointment():
    """Tests the analysis of an appointment request message"""
    nlp_service = NLPService()
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                function_call=MagicMock(
                    arguments='{"intent": "schedule_appointment", "service": "haircut_woman", "sentiment": "positive"}'
                )
            )
        )
    ]

    with patch.object(nlp_service.client, "chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await nlp_service.analyze_message("I want to schedule a haircut for a woman")
        
        assert result["intent"] == "schedule_appointment"
        assert result["service"] == "haircut_woman"
        assert result["sentiment"] == "positive"

@pytest.mark.asyncio
async def test_extract_appointment_details():
    """Tests the extraction of appointment details"""
    nlp_service = NLPService()
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                function_call=MagicMock(
                    arguments='''
                    {
                        "service": "haircut_woman",
                        "date": "2024-03-22",
                        "time": "14:30",
                        "estimated_duration": 60
                    }
                    '''
                )
            )
        )
    ]

    with patch.object(nlp_service.client, "chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await nlp_service.extract_appointment_details("I want a haircut for a woman tomorrow at 2:30 PM")
        
        assert result["service"] == "haircut_woman"
        assert result["date"] == "2024-03-22"
        assert result["time"] == "14:30"
        assert result["estimated_duration"] == 60

@pytest.mark.asyncio
async def test_analyze_message_error_handling():
    """Tests error handling in message analysis"""
    nlp_service = NLPService()
    
    with patch.object(nlp_service.client, "chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        result = await nlp_service.analyze_message("What is the schedule?")
        
        assert result["intent"] == "error"
        assert result["sentiment"] == "neutral"
        assert result["error"] == "API Error"

@pytest.mark.asyncio
async def test_generate_response():
    """Tests response generation"""
    nlp_service = NLPService()
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="This is a test response"
            )
        )
    ]

    analysis_result = {
        "intent": "faq_query",
        "sentiment": "neutral",
        "faq_key": "schedule"
    }

    with patch.object(nlp_service.client, "chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await nlp_service.generate_response(analysis_result)
        
        assert result == "This is a test response"