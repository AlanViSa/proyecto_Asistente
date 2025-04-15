import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from app.services.notification_service import NotificationService
from app.models.cita import Cita
from app.models.cliente import Cliente

@pytest.fixture
def notification_service():
    return NotificationService()

@pytest.fixture
def sample_appointment():
    cliente = Cliente(
        id=1,  # Assuming Cliente has an id field
        nombre="Ana García",
        telefono="+1234567890",
        email="ana@example.com"
    )
    
    return Cita(
        id=1,
        cliente=cliente,
        start_time=datetime.now() + timedelta(days=1),
        servicio="corte_dama",
        estado="confirmada",
        duracion_minutos=60
    )

@pytest.mark.asyncio
async def test_send_confirmation_message(notification_service):
    """Tests sending confirmation messages"""
    appointment = Cita(
        id=1,
        client=Cliente(id=1, name="Ana", phone="+1234567890", email="ana@example.com"),
        start_time=datetime.now() + timedelta(days=1),
        service="corte_dama",
        status="confirmada",
        duration_minutes=60
    )

    with patch.object(notification_service.whatsapp_service, 'send_message', new_callable=AsyncMock) as mock_send:
        await notification_service.send_confirmation_message(appointment)
        mock_send.assert_called_once()
        args = mock_send.call_args  # Corrected to call_args
        assert appointment.client.phone == args[0][0]
        assert "confirmed" in args[0][1].lower()

@pytest.mark.asyncio
async def test_send_reminder_message(notification_service):
    """Tests sending reminders"""
    appointment = Cita(
        id=1,
        client=Cliente(id=1, name="Ana", phone="+1234567890", email="ana@example.com"),
        start_time=datetime.now() + timedelta(hours=24),
        service="corte_dama",
        status="confirmada",
        duration_minutes=60
    )

    with patch.object(notification_service.whatsapp_service, 'send_message', new_callable=AsyncMock) as mock_send:
        await notification_service.send_reminder_message(appointment)
        mock_send.assert_called_once()
        args = mock_send.call_args  # Corrected to call_args
        assert appointment.client.phone == args[0][0]
        assert "remember" in args[0][1].lower()

@pytest.mark.asyncio
async def test_send_cancellation_message(notification_service):
    """Tests sending cancellation messages"""
    appointment = Cita(
        id=1,
        client=Cliente(id=1, name="Ana", phone="+1234567890", email="ana@example.com"),
        start_time=datetime.now() + timedelta(days=1),
        service="corte_dama",
        status="cancelled",
        duration_minutes=60
    )

    with patch.object(notification_service.whatsapp_service, 'send_message', new_callable=AsyncMock) as mock_send:
        await notification_service.send_cancellation_message(appointment)
        mock_send.assert_called_once()
        args = mock_send.call_args  # Corrected to call_args
        assert appointment.client.phone == args[0][0]
        assert "cancelled" in args[0][1].lower()

@pytest.mark.asyncio
async def test_send_message_error_handling(notification_service):
    """Tests error handling in message sending"""
    appointment = Cita(
        id=1,
        client=Cliente(id=1, name="Ana", phone="+1234567890", email="ana@example.com"),
        start_time=datetime.now() + timedelta(days=1),
        service="corte_dama",
        status="confirmed",
        duration_minutes=60
    )

    with patch.object(notification_service.whatsapp_service, 'send_message', new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = Exception("Sending Error")
        with pytest.raises(Exception) as exc_info:
            await notification_service.send_confirmation_message(appointment)
        assert str(exc_info.value) == "Sending Error"
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_check_and_send_reminders(notification_service):
    """Prueba la verificación y envío de recordatorios"""
    # Mock de la sesión de base de datos
    mock_db = MagicMock()

    # Mock of upcoming appointments
    mocked_appointments = [
        Cita(
            id=1,
            client=Cliente(id=1, name="Ana", phone="+1234567890", email="ana@example.com"),
            start_time=datetime.now() + timedelta(days=1),
            service="corte_dama",
            status="confirmed",
            duration_minutes=60,
            reminder_sent=False
        ),
        Cita(
            id=2,
            client=Cliente(id=2, name="Juan", phone="+0987654321", email="juan@example.com"),
            start_time=datetime.now() + timedelta(days=1),
            service="corte_caballero",
            status="confirmed",
            duration_minutes=30,
            reminder_sent=False
        )
    ]

    # Mock database query
    mocked_query = MagicMock()
    mocked_query.filter.return_value = mocked_query
    mocked_query.all.return_value = mocked_appointments
    mock_db.query.return_value = mocked_query

    with patch.object(notification_service.whatsapp_service, 'send_message', new_callable=AsyncMock) as mock_send:
        await notification_service.check_and_send_reminders(mock_db)

        # Verificar que se enviaron los recordatorios para ambas citas
        assert mock_send.call_count == 2
        
        # Verify that appointments were updated
        assert all(appointment.reminder_sent for appointment in mocked_appointments)
        mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_format_message(notification_service):
    """Tests message formatting"""
    template = "Welcome to {business_name}! Your appointment is at {time}"
    result = notification_service.format_message(
        template,
        time="14:30"
    )
    assert "Test Salon" in result
    assert "14:30" in result