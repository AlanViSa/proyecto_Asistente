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
        id=1,
        nombre="Ana García",
        telefono="+1234567890",
        email="ana@example.com"
    )
    
    return Cita(
        id=1,
        cliente=cliente,
        fecha_hora=datetime.now() + timedelta(days=1),
        servicio="corte_dama",
        estado="confirmada",
        duracion_minutos=60
    )

@pytest.mark.asyncio
async def test_send_confirmation_message(notification_service):
    """Prueba el envío de mensajes de confirmación"""
    cita = Cita(
        id=1,
        cliente=Cliente(id=1, nombre="Ana", telefono="+1234567890", email="ana@example.com"),
        fecha_hora=datetime.now() + timedelta(days=1),
        servicio="corte_dama",
        estado="confirmada",
        duracion_minutos=60
    )

    with patch.object(notification_service.whatsapp_service, 'send_message', new_callable=AsyncMock) as mock_send:
        await notification_service.send_confirmation_message(cita)
        mock_send.assert_called_once()
        args = mock_send.call_args
        assert cita.cliente.telefono == args[0][0]
        assert "confirmada" in args[0][1].lower()

@pytest.mark.asyncio
async def test_send_reminder_message(notification_service):
    """Prueba el envío de recordatorios"""
    cita = Cita(
        id=1,
        cliente=Cliente(id=1, nombre="Ana", telefono="+1234567890", email="ana@example.com"),
        fecha_hora=datetime.now() + timedelta(hours=24),
        servicio="corte_dama",
        estado="confirmada",
        duracion_minutos=60
    )

    with patch.object(notification_service.whatsapp_service, 'send_message', new_callable=AsyncMock) as mock_send:
        await notification_service.send_reminder_message(cita)
        mock_send.assert_called_once()
        args = mock_send.call_args
        assert cita.cliente.telefono == args[0][0]
        assert "recordamos" in args[0][1].lower()

@pytest.mark.asyncio
async def test_send_cancellation_message(notification_service):
    """Prueba el envío de mensajes de cancelación"""
    cita = Cita(
        id=1,
        cliente=Cliente(id=1, nombre="Ana", telefono="+1234567890", email="ana@example.com"),
        fecha_hora=datetime.now() + timedelta(days=1),
        servicio="corte_dama",
        estado="cancelada",
        duracion_minutos=60
    )

    with patch.object(notification_service.whatsapp_service, 'send_message', new_callable=AsyncMock) as mock_send:
        await notification_service.send_cancellation_message(cita)
        mock_send.assert_called_once()
        args = mock_send.call_args
        assert cita.cliente.telefono == args[0][0]
        assert "cancelada" in args[0][1].lower()

@pytest.mark.asyncio
async def test_send_message_error_handling(notification_service):
    """Prueba el manejo de errores en el envío de mensajes"""
    cita = Cita(
        id=1,
        cliente=Cliente(id=1, nombre="Ana", telefono="+1234567890", email="ana@example.com"),
        fecha_hora=datetime.now() + timedelta(days=1),
        servicio="corte_dama",
        estado="confirmada",
        duracion_minutos=60
    )

    with patch.object(notification_service.whatsapp_service, 'send_message', new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = Exception("Error de envío")
        with pytest.raises(Exception) as exc_info:
            await notification_service.send_confirmation_message(cita)
        assert str(exc_info.value) == "Error de envío"
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_check_and_send_reminders(notification_service):
    """Prueba la verificación y envío de recordatorios"""
    # Mock de la sesión de base de datos
    mock_db = MagicMock()
    
    # Mock de citas próximas
    mock_appointments = [
        Cita(
            id=1,
            cliente=Cliente(id=1, nombre="Ana", telefono="+1234567890", email="ana@example.com"),
            fecha_hora=datetime.now() + timedelta(days=1),
            servicio="corte_dama",
            estado="confirmada",
            duracion_minutos=60,
            recordatorio_enviado=False
        ),
        Cita(
            id=2,
            cliente=Cliente(id=2, nombre="Juan", telefono="+0987654321", email="juan@example.com"),
            fecha_hora=datetime.now() + timedelta(days=1),
            servicio="corte_caballero",
            estado="confirmada",
            duracion_minutos=30,
            recordatorio_enviado=False
        )
    ]

    # Mock de la consulta a la base de datos
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = mock_appointments
    mock_db.query.return_value = mock_query

    with patch.object(notification_service.whatsapp_service, 'send_message', new_callable=AsyncMock) as mock_send:
        await notification_service.check_and_send_reminders(mock_db)

        # Verificar que se enviaron los recordatorios para ambas citas
        assert mock_send.call_count == 2
        
        # Verificar que se actualizaron las citas
        assert all(cita.recordatorio_enviado for cita in mock_appointments)
        mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_format_message(notification_service):
    """Prueba el formateo de mensajes"""
    template = "Bienvenido a {business_name}! Tu cita es a las {hora}"
    result = notification_service.format_message(
        template,
        hora="14:30"
    )
    assert "Test Salon" in result
    assert "14:30" in result 