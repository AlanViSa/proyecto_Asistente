"""
Pruebas unitarias para el servicio de citas
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
    """Prueba la creación de una cita"""
    # Crear cliente primero
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    # Crear cita
    cita_in = CitaCreate(**test_cita_data)
    cita = await CitaService.create(db_session, cita_in)
    
    assert cita.id is not None
    assert cita.cliente_id == cliente.id
    assert cita.estado == EstadoCita.PENDIENTE
    assert cita.servicio == test_cita_data["servicio"]
    assert cita.duracion_minutos == test_cita_data["duracion_minutos"]

@pytest.mark.asyncio
async def test_get_cita_by_id(db_session: AsyncSession, test_user_data, test_cita_data):
    """Prueba la obtención de una cita por ID"""
    # Crear cliente y cita
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    cita_in = CitaCreate(**test_cita_data)
    cita = await CitaService.create(db_session, cita_in)
    
    # Obtener cita
    cita_db = await CitaService.get_by_id(db_session, cita.id)
    
    assert cita_db is not None
    assert cita_db.id == cita.id
    assert cita_db.cliente_id == cita.cliente_id

@pytest.mark.asyncio
async def test_update_cita(db_session: AsyncSession, test_user_data, test_cita_data):
    """Prueba la actualización de una cita"""
    # Crear cliente y cita
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    cita_in = CitaCreate(**test_cita_data)
    cita = await CitaService.create(db_session, cita_in)
    
    # Actualizar cita
    update_data = {"estado": EstadoCita.CONFIRMADA}
    cita_update = CitaUpdate(**update_data)
    cita_updated = await CitaService.update(db_session, cita, cita_update)
    
    assert cita_updated.estado == EstadoCita.CONFIRMADA
    assert cita_updated.cliente_id == cita.cliente_id

@pytest.mark.asyncio
async def test_cancel_cita(db_session: AsyncSession, test_user_data, test_cita_data):
    """Prueba la cancelación de una cita"""
    # Crear cliente y cita
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    cita_in = CitaCreate(**test_cita_data)
    cita = await CitaService.create(db_session, cita_in)
    
    # Cancelar cita
    cita_canceled = await CitaService.cancel(db_session, cita)
    
    assert cita_canceled.estado == EstadoCita.CANCELADA
    assert cita_canceled.cliente_id == cita.cliente_id

@pytest.mark.asyncio
async def test_complete_cita(db_session: AsyncSession, test_user_data, test_cita_data):
    """Prueba la finalización de una cita"""
    # Crear cliente y cita
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    cita_in = CitaCreate(**test_cita_data)
    cita = await CitaService.create(db_session, cita_in)
    
    # Confirmar cita primero
    await CitaService.confirm(db_session, cita)
    
    # Completar cita
    cita_completed = await CitaService.complete(db_session, cita)
    
    assert cita_completed.estado == EstadoCita.COMPLETADA
    assert cita_completed.cliente_id == cita.cliente_id

@pytest.mark.asyncio
async def test_no_show_cita(db_session: AsyncSession, test_user_data, test_cita_data):
    """Prueba el registro de no asistencia a una cita"""
    # Crear cliente y cita
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    cita_in = CitaCreate(**test_cita_data)
    cita = await CitaService.create(db_session, cita_in)
    
    # Confirmar cita primero
    await CitaService.confirm(db_session, cita)
    
    # Registrar no asistencia
    cita_no_show = await CitaService.no_show(db_session, cita)
    
    assert cita_no_show.estado == EstadoCita.NO_ASISTIO
    assert cita_no_show.cliente_id == cita.cliente_id

@pytest.mark.asyncio
async def test_check_availability(db_session: AsyncSession, test_user_data, test_cita_data):
    """Prueba la verificación de disponibilidad"""
    # Crear cliente y cita
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    cita_in = CitaCreate(**test_cita_data)
    cita = await CitaService.create(db_session, cita_in)
    
    # Verificar disponibilidad
    fecha_hora = datetime.fromisoformat(test_cita_data["fecha_hora"])
    is_available = await CitaService.check_availability(db_session, fecha_hora)
    
    assert is_available is False  # No disponible porque ya hay una cita en ese horario
    
    # Verificar disponibilidad en otro horario
    fecha_hora_available = fecha_hora + timedelta(hours=2)
    is_available = await CitaService.check_availability(db_session, fecha_hora_available)
    
    assert is_available is True  # Disponible porque no hay citas en ese horario 