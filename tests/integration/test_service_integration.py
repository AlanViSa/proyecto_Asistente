import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.nlp_service import NLPService
from app.services.faq_service import FAQService
from app.services.notification_service import NotificationService
from app.models.cliente import Cliente
from app.models.cita import Cita, EstadoCita

@pytest.fixture
def services():
    """Fixture que proporciona todas las instancias de servicios necesarias"""
    return {
        "nlp": NLPService(),
        "faq": FAQService(),
        "notification": NotificationService()
    }

@pytest.fixture
def sample_client():
    """Fixture que proporciona un cliente de ejemplo"""
    return Cliente(
        id=1,
        nombre="Ana García",
        telefono="+1234567890",
        email="ana@example.com"
    )

@pytest.mark.asyncio
async def test_nlp_faq_integration(services):
    """Prueba la integración entre el servicio NLP y FAQ"""
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

    with patch.object(services["nlp"].client, "chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await services["nlp"].analyze_message("¿Cuál es el horario de atención?")
        
        assert result["intent"] == "consulta_horarios"
        assert result["faq_key"] == "horario"
        assert "horario" in services["faq"].get_faq("horario")["respuesta"].lower()

@pytest.mark.asyncio
async def test_nlp_appointment_integration(services, sample_client):
    """Prueba la integración del proceso completo de agendar una cita"""
    # Mock para el análisis inicial del mensaje
    mock_analysis = MagicMock()
    mock_analysis.choices = [
        MagicMock(
            message=MagicMock(
                function_call=MagicMock(
                    arguments='{"intent": "agendar_cita", "servicio": "corte_dama", "sentimiento": "positivo"}'
                )
            )
        )
    ]

    # Mock para la extracción de detalles
    mock_details = MagicMock()
    mock_details.choices = [
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

    with patch.object(services["nlp"].client, "chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(side_effect=[mock_analysis, mock_details])
        
        # Analizar mensaje inicial
        result = await services["nlp"].analyze_message(
            "Quiero agendar un corte de dama para mañana a las 2:30 PM"
        )
        
        assert result["intent"] == "agendar_cita"
        assert result["servicio"] == "corte_dama"
        
        # Extraer detalles
        details = await services["nlp"].extract_appointment_details(
            "Quiero el corte de dama mañana a las 2:30 PM"
        )
        
        assert details["servicio"] == "corte_dama"
        assert details["fecha"] == "2024-03-22"
        assert details["hora"] == "14:30"

@pytest.mark.asyncio
async def test_appointment_notification_integration(services, sample_client):
    """Prueba la integración entre la creación de citas y el envío de notificaciones"""
    # Crear una cita de prueba
    cita = Cita(
        id=1,
        cliente=sample_client,
        fecha_hora=datetime.now() + timedelta(days=1),
        servicio="corte_dama",
        estado=EstadoCita.CONFIRMADA,
        duracion_minutos=60
    )

    # Mock para el servicio de WhatsApp
    with patch.object(services["notification"].whatsapp_service, 'client') as mock_client:
        mock_messages = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM123"
        mock_message.body = "Test message"
        mock_messages.create.return_value = mock_message
        mock_client.messages = mock_messages

        # Enviar confirmación
        await services["notification"].send_confirmation_message(cita)

        # Verificar que se llamó al método create con los parámetros correctos
        mock_messages.create.assert_called_once()
        args = mock_messages.create.call_args[1]
        assert args["to"] == f"whatsapp:{cita.cliente.telefono}"
        assert "confirmada" in args["body"].lower()

@pytest.mark.asyncio
async def test_error_handling_integration(services):
    """Prueba el manejo de errores integrado entre servicios"""
    # Probar servicio inválido
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                function_call=MagicMock(
                    arguments='{"intent": "agendar_cita", "servicio": "servicio_invalido", "sentimiento": "neutral"}'
                )
            )
        )
    ]

    with patch.object(services["nlp"].client, "chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(return_value=mock_response)

        result = await services["nlp"].analyze_message(
            "Quiero agendar un servicio que no existe"
        )

        assert result["intent"] == "agendar_cita"
        assert result["servicio"] == "servicio_invalido"
        assert result["sentimiento"] == "neutral"

@pytest.mark.asyncio
async def test_full_appointment_flow(services, sample_client):
    """Prueba el flujo completo de una cita desde el mensaje inicial hasta la notificación"""
    # Mocks para las respuestas de OpenAI
    mock_analysis = MagicMock()
    mock_analysis.choices = [
        MagicMock(
            message=MagicMock(
                function_call=MagicMock(
                    arguments='{"intent": "agendar_cita", "servicio": "corte_dama", "sentimiento": "positivo"}'
                )
            )
        )
    ]

    mock_details = MagicMock()
    mock_details.choices = [
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

    with patch.object(services["nlp"].client, "chat") as mock_chat, \
         patch.object(services["notification"].whatsapp_service, 'client') as mock_twilio:

        mock_chat.completions.create = AsyncMock(side_effect=[mock_analysis, mock_details])
        
        mock_messages = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM123"
        mock_message.body = "Test message"
        mock_messages.create.return_value = mock_message
        mock_twilio.messages = mock_messages

        # 1. Analizar mensaje inicial
        result = await services["nlp"].analyze_message(
            "Quiero agendar un corte de dama para mañana a las 2:30 PM"
        )
        assert result["intent"] == "agendar_cita"
        assert result["servicio"] == "corte_dama"

        # 2. Extraer detalles
        details = await services["nlp"].extract_appointment_details(
            "Quiero el corte de dama mañana a las 2:30 PM"
        )
        assert details["servicio"] == "corte_dama"
        assert details["fecha"] == "2024-03-22"
        assert details["hora"] == "14:30"

        # 3. Crear cita
        cita = Cita(
            id=1,
            cliente=sample_client,
            fecha_hora=datetime.strptime(f"{details['fecha']} {details['hora']}", "%Y-%m-%d %H:%M"),
            servicio=details["servicio"],
            estado=EstadoCita.CONFIRMADA,
            duracion_minutos=details["duracion_estimada"]
        )

        # 4. Enviar confirmación
        await services["notification"].send_confirmation_message(cita)

        # Verificar que se llamó al método create con los parámetros correctos
        mock_messages.create.assert_called_once()
        args = mock_messages.create.call_args[1]
        assert args["to"] == f"whatsapp:{cita.cliente.telefono}"
        assert "confirmada" in args["body"].lower() 