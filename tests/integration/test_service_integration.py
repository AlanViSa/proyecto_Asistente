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
    """Fixture that provides all necessary service instances."""
    return {
        "nlp": NLPService(),
        "faq": FAQService(),
        "notification": NotificationService()
    }

@pytest.fixture
def sample_client():
    """Fixture that provides a sample client."""
    return Cliente(
        id=1,
        name="Ana García",
        phone="+1234567890",
        email="ana@example.com",
    )

@pytest.mark.asyncio
async def test_nlp_faq_integration(services):
    """Tests the integration between the NLP and FAQ services."""
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

        result = await services["nlp"].analyze_message("What are the business hours?")

        assert result["intent"] == "check_schedule"
        assert result["faq_key"] == "horario"
        assert "horario" in services["faq"].get_faq("horario")["answer"].lower()

@pytest.mark.asyncio
async def test_nlp_appointment_integration(services, sample_client):
    """Tests the integration of the complete appointment scheduling process."""
    # Mock for initial message analysis
    mock_analysis = MagicMock()
    mock_analysis.choices = [
      MagicMock(
            message=MagicMock(
                function_call=MagicMock(
                    arguments='{"intent": "schedule_appointment", "service": "haircut_female", "sentiment": "positive"}'
                )
            )
        )
    ]

    # Mock para la extracción de detalles
    mock_details = MagicMock()
    mock_details.choices = [MagicMock(
        message=MagicMock(
            function_call=MagicMock(
                arguments='''
                {
                    "service": "haircut_female",
                    "date": "2024-03-22",
                    "time": "14:30",
                    "estimated_duration": 60
                }
                '''
            )
        )
    )]

    with patch.object(services["nlp"].client, "chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(
            side_effect=[mock_analysis, mock_details])

        # Analyze initial message
        result = await services["nlp"].analyze_message(
            "I want to schedule a haircut for tomorrow at 2:30 PM"
        )

        assert result["intent"] == "schedule_appointment"
        assert result["service"] == "haircut_female"

        # Extract details
        details = await services["nlp"].extract_appointment_details(
            "I want the haircut tomorrow at 2:30 PM"
        )

        assert details["service"] == "haircut_female"
        assert details["date"] == "2024-03-22"
        assert details["time"] == "14:30"


@pytest.mark.asyncio
async def test_appointment_notification_integration(services, sample_client):
    """Tests the integration between appointment creation and sending notifications."""
    # Create a test appointment
    appointment = Cita(
        id=1,
        client=sample_client,
        datetime=datetime.now() + timedelta(days=1),
        service="haircut_female",
        status=EstadoCita.CONFIRMED,
        duration_minutes=60
    ]

    # Mock for the WhatsApp service
    with patch.object(services["notification"].whatsapp_service, 'client') as mock_client:
        mock_messages = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM123"
        mock_message.body = "Test message"
        mock_messages.create.return_value = mock_message

        mock_client.messages = mock_messages

        # Send confirmation
        await services["notification"].send_confirmation_message(appointment)

        # Verify that the create method was called with the correct parameters
        mock_messages.create.assert_called_once()
        args = mock_messages.create.call_args[1]
        assert args["to"] == f"whatsapp:{appointment.client.phone}"
        assert "confirmed" in args["body"].lower()

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
            "I want to schedule a service that does not exist"
        )

        assert result["intent"] == "schedule_appointment"
        assert result["service"] == "invalid_service"
        assert result["sentiment"] == "neutral"

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
                      "service": "haircut_female",
                      "date": "2024-03-22",
                      "time": "14:30",
                      "estimated_duration": 60
                  }
                  '''
              )
          )
        )
    ]

    with patch.object(services["nlp"].client, "chat") as mock_chat, \
            patch.object(services["notification"].whatsapp_service,
                         'client') as mock_twilio:

      mock_chat.completions.create = AsyncMock(side_effect=[mock_analysis, mock_details])

      mock_messages = MagicMock()
      mock_message = MagicMock()
      mock_message.sid = "SM123"
      mock_message.body = "Test message"
      mock_messages.create.return_value = mock_message
      mock_twilio.messages = mock_messages

      # 1. Analyze initial message
      result = await services["nlp"].analyze_message(
          "I want to schedule a haircut for tomorrow at 2:30 PM"
      )
      assert result["intent"] == "schedule_appointment"
      assert result["service"] == "haircut_female"

      # 2. Extract details
      details = await services["nlp"].extract_appointment_details(
          "I want the haircut tomorrow at 2:30 PM"
      )
      assert details["service"] == "haircut_female"
      assert details["date"] == "2024-03-22"
      assert details["time"] == "14:30"

      # 3. Create appointment
      appointment = Cita(
          id=1,
          client=sample_client,
          datetime=datetime.strptime(
              f"{details['date']} {details['time']}", "%Y-%m-%d %H:%M"
          ),
          service=details["service"],
          status=EstadoCita.CONFIRMED,
          duration_minutes=details["estimated_duration"]
      )

      # 4. Send confirmation
      await services["notification"].send_confirmation_message(appointment)

      # Verify that the create method was called with the correct parameters
      mock_messages.create.assert_called_once()
      args = mock_messages.create.call_args[1]
      assert args["to"] == f"whatsapp:{appointment.client.phone}"
      assert "confirmed" in args["body"].lower()