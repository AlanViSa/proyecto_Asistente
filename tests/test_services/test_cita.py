"""
Unit tests for the appointment service
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.cita import CitaService
from app.services.cliente import ClienteService
from app.schemas.cita import CitaCreate, CitaUpdate
from app.schemas.cliente import ClienteCreate
from app.models.cita import EstadoCita

@pytest.mark.asyncio
async def test_create_cita(db_session: AsyncSession, test_user_data, test_cita_data):
    """Tests the creation of an appointment"""
    # Create client first
    client_in = ClienteCreate(**test_user_data)
    client = await ClienteService.create(db_session, client_in)

    # Create appointment
    appointment_in = CitaCreate(**test_cita_data)
    appointment = await CitaService.create(db_session, appointment_in)

    assert appointment.id is not None
    assert appointment.client_id == client.id
    assert appointment.status == EstadoCita.PENDIENTE
    assert appointment.service == test_cita_data["service"]
    assert appointment.duration_minutes == test_cita_data["duration_minutes"]

@pytest.mark.asyncio
async def test_get_cita_by_id(db_session: AsyncSession, test_user_data, test_cita_data):
    """Tests getting an appointment by ID"""
    # Create client and appointment
    client_in = ClienteCreate(**test_user_data)
    client = await ClienteService.create(db_session, client_in)

    appointment_in = CitaCreate(**test_cita_data)
    appointment = await CitaService.create(db_session, appointment_in)

    # Get appointment
    appointment_db = await CitaService.get_by_id(db_session, appointment.id)

    assert appointment_db is not None
    assert appointment_db.id == appointment.id
    assert appointment_db.client_id == appointment.client_id

@pytest.mark.asyncio
async def test_update_cita(db_session: AsyncSession, test_user_data, test_cita_data):
    """Tests updating an appointment"""
    # Create client and appointment
    client_in = ClienteCreate(**test_user_data)
    client = await ClienteService.create(db_session, client_in)

    appointment_in = CitaCreate(**test_cita_data)
    appointment = await CitaService.create(db_session, appointment_in)

    # Update appointment
    update_data = {"status": EstadoCita.CONFIRMADA}
    appointment_update = CitaUpdate(**update_data)
    appointment_updated = await CitaService.update(db_session, appointment, appointment_update)

    assert appointment_updated.status == EstadoCita.CONFIRMADA
    assert appointment_updated.client_id == appointment.client_id

@pytest.mark.asyncio
async def test_cancel_cita(db_session: AsyncSession, test_user_data, test_cita_data):
    """Tests canceling an appointment"""
    # Create client and appointment
    client_in = ClienteCreate(**test_user_data)
    client = await ClienteService.create(db_session, client_in)

    appointment_in = CitaCreate(**test_cita_data)
    appointment = await CitaService.create(db_session, appointment_in)

    # Cancel appointment
    appointment_canceled = await CitaService.cancel(db_session, appointment)

    assert appointment_canceled.status == EstadoCita.CANCELADA
    assert appointment_canceled.client_id == appointment.client_id

@pytest.mark.asyncio
async def test_complete_cita(db_session: AsyncSession, test_user_data, test_cita_data):
    """Tests completing an appointment"""
    # Create client and appointment
    client_in = ClienteCreate(**test_user_data)
    client = await ClienteService.create(db_session, client_in)

    appointment_in = CitaCreate(**test_cita_data)
    appointment = await CitaService.create(db_session, appointment_in)

    # Confirm appointment first
    await CitaService.confirm(db_session, appointment)

    # Complete appointment
    appointment_completed = await CitaService.complete(db_session, appointment)

    assert appointment_completed.status == EstadoCita.COMPLETADA
    assert appointment_completed.client_id == appointment.client_id

@pytest.mark.asyncio
async def test_no_show_cita(db_session: AsyncSession, test_user_data, test_cita_data):
    """Tests registering a no-show for an appointment"""
    # Create client and appointment
    client_in = ClienteCreate(**test_user_data)
    client = await ClienteService.create(db_session, client_in)

    appointment_in = CitaCreate(**test_cita_data)
    appointment = await CitaService.create(db_session, appointment_in)

    # Confirm appointment first
    await CitaService.confirm(db_session, appointment)

    # Register no-show
    appointment_no_show = await CitaService.no_show(db_session, appointment)

    assert appointment_no_show.status == EstadoCita.NO_ASISTIO
    assert appointment_no_show.client_id == appointment.client_id

@pytest.mark.asyncio
async def test_check_availability(db_session: AsyncSession, test_user_data, test_cita_data):
    """Tests checking availability"""
    # Create client and appointment
    client_in = ClienteCreate(**test_user_data)
    client = await ClienteService.create(db_session, client_in)

    appointment_in = CitaCreate(**test_cita_data)
    appointment = await CitaService.create(db_session, appointment_in)

    # Check availability
    date_time = datetime.fromisoformat(test_cita_data["date_time"])
    is_available = await CitaService.check_availability(db_session, date_time)

    assert is_available is False  # Not available because there is already an appointment at that time

    # Check availability at another time
    date_time_available = date_time + timedelta(hours=2)
    is_available = await CitaService.check_availability(db_session, date_time_available)

    assert is_available is True  # Available because there are no appointments at that time