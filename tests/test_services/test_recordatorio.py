"""
Unit tests for the reminders service
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.recordatorio import RecordatorioService
from app.services.cita import CitaService
from app.services.cliente import ClienteService
from app.schemas.cita import CitaCreate
from app.schemas.cliente import ClienteCreate
from app.models.cita import EstadoCita
from app.models.preferencias_notificacion import NotificationChannel

@pytest.mark.asyncio
async def test_get_appointments_to_remind(db_session: AsyncSession, test_user_data, test_appointment_data):
    """Tests getting appointments to remind"""
    # Create client and appointment
    client_in = ClienteCreate(**test_user_data)
    client = await ClienteService.create(db_session, client_in)

    # Create appointment for within 24 hours
    date_time = datetime.now() + timedelta(hours=24)
    appointment_data = test_appointment_data.copy()
    appointment_data["date_time"] = date_time.isoformat()
    appointment_data["status"] = EstadoCita.CONFIRMADA

    appointment_in = CitaCreate(**appointment_data)
    appointment = await CitaService.create(db_session, appointment_in)

    # Get appointments to remind
    appointments = await RecordatorioService.get_citas_para_recordar(db_session, "24h")

    assert len(appointments) > 0
    assert appointment.id in [c.id for c in appointments]

@pytest.mark.asyncio
async def test_reminder_already_sent(db_session: AsyncSession, test_user_data, test_appointment_data):
    """Tests checking for reminders already sent"""
    # Create client and appointment
    client_in = ClienteCreate(**test_user_data)
    client = await ClienteService.create(db_session, client_in)

    appointment_in = CitaCreate(**test_appointment_data)
    appointment = await CitaService.create(db_session, appointment_in)

    # Verify that no reminders have been sent
    already_sent = await RecordatorioService._reminder_already_sent(
        db_session, appointment.id, "24h", NotificationChannel.EMAIL
    )
    assert already_sent is False

    # Register a reminder
    await RecordatorioService.register_reminder(
        db_session,
        appointment,
        "24h",
        NotificationChannel.EMAIL,
        True
    )

    # Verify that a reminder has now been sent
    already_sent = await RecordatorioService._reminder_already_sent(
        db_session, appointment.id, "24h", NotificationChannel.EMAIL
    )
    assert already_sent is True

@pytest.mark.asyncio
async def test_get_client_channels(db_session: AsyncSession, test_user_data):
    """Tests getting client notification channels"""
    # Create client without preferences
    client_in = ClienteCreate(**test_user_data)
    client = await ClienteService.create(db_session, client_in)

    # Verify default channels
    channels = await RecordatorioService._get_client_channels(client)
    assert NotificationChannel.EMAIL in channels

    # Create preferences with email and WhatsApp enabled
    await RecordatorioService.create_default_preferences(db_session, client.id)

    # Verify updated channels
    channels = await RecordatorioService._get_client_channels(client)
    assert NotificationChannel.EMAIL in channels
    assert NotificationChannel.WHATSAPP in channels

@pytest.mark.asyncio
async def test_reminder_enabled(db_session: AsyncSession, test_user_data):
    """Tests checking for enabled reminders"""
    # Create client without preferences
    client_in = ClienteCreate(**test_user_data)
    client = await ClienteService.create(db_session, client_in)

    # Verify that by default all reminders are enabled
    assert await RecordatorioService._reminder_enabled(client, "24h") is True
    assert await RecordatorioService._reminder_enabled(client, "2h") is True

    # Create preferences with 2h reminder disabled
    await RecordatorioService.create_default_preferences(db_session, client.id)

    # Verify that the 2h reminder is disabled
    assert await RecordatorioService._reminder_enabled(client, "2h") is False

@pytest.mark.asyncio
async def test_ajustar_zona_horaria(db_session: AsyncSession, test_user_data):
    """Prueba el ajuste de zona horaria"""
    # Crear cliente sin preferencias
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    # Fecha de prueba
    fecha = datetime.now()
    
    # Verificar que sin preferencias se usa la zona horaria por defecto
    fecha_ajustada = await RecordatorioService._ajustar_zona_horaria(fecha, cliente)
    assert fecha_ajustada == fecha.astimezone(ZoneInfo("America/Mexico_City"))
    
    # Crear preferencias con zona horaria diferente
    await RecordatorioService.crear_preferencias_por_defecto(db_session, cliente.id)
    
    # Verificar que se usa la zona horaria del cliente
    fecha_ajustada = await RecordatorioService._ajustar_zona_horaria(fecha, cliente)
    assert fecha_ajustada == fecha.astimezone(ZoneInfo("America/Mexico_City"))

@pytest.mark.asyncio
async def test_get_estadisticas_recordatorios(db_session: AsyncSession, test_user_data, test_cita_data):
    """Prueba la obtención de estadísticas de recordatorios"""
    # Crear cliente y cita
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    cita_in = CitaCreate(**test_cita_data)
    cita = await CitaService.create(db_session, cita_in)
    
    # Registrar algunos recordatorios
    await RecordatorioService.registrar_recordatorio(
        db_session,
        cita,
        "24h",
        NotificationChannel.EMAIL,
        True
    )
    
    await RecordatorioService.registrar_recordatorio(
        db_session,
        cita,
        "2h",
        NotificationChannel.EMAIL,
        False,
        "Error de envío"
    )
    
    # Obtener estadísticas
    inicio = datetime.now() - timedelta(hours=1)
    fin = datetime.now() + timedelta(hours=1)
    stats = await RecordatorioService.get_estadisticas_recordatorios(db_session, inicio, fin)
    
    assert stats["total_enviados"] == 2
    assert stats["exitosos"] == 1
    assert stats["fallidos"] == 1
    assert stats["por_tipo"]["24h"] == 1
    assert stats["por_tipo"]["2h"] == 0
    assert stats["por_canal"]["email"] == 1 