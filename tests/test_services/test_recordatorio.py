"""
Pruebas unitarias para el servicio de recordatorios
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
from app.services.notification import NotificationChannel

@pytest.mark.asyncio
async def test_get_citas_para_recordar(db_session: AsyncSession, test_user_data, test_cita_data):
    """Prueba la obtención de citas para recordar"""
    # Crear cliente y cita
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    # Crear cita para dentro de 24 horas
    fecha_hora = datetime.now() + timedelta(hours=24)
    cita_data = test_cita_data.copy()
    cita_data["fecha_hora"] = fecha_hora.isoformat()
    cita_data["estado"] = EstadoCita.CONFIRMADA
    
    cita_in = CitaCreate(**cita_data)
    cita = await CitaService.create(db_session, cita_in)
    
    # Obtener citas para recordar
    citas = await RecordatorioService.get_citas_para_recordar(db_session, "24h")
    
    assert len(citas) > 0
    assert cita.id in [c.id for c in citas]

@pytest.mark.asyncio
async def test_recordatorio_ya_enviado(db_session: AsyncSession, test_user_data, test_cita_data):
    """Prueba la verificación de recordatorios ya enviados"""
    # Crear cliente y cita
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    cita_in = CitaCreate(**test_cita_data)
    cita = await CitaService.create(db_session, cita_in)
    
    # Verificar que no hay recordatorios enviados
    ya_enviado = await RecordatorioService._recordatorio_ya_enviado(
        db_session, cita.id, "24h", NotificationChannel.EMAIL
    )
    assert ya_enviado is False
    
    # Registrar un recordatorio
    await RecordatorioService.registrar_recordatorio(
        db_session,
        cita,
        "24h",
        NotificationChannel.EMAIL,
        True
    )
    
    # Verificar que ahora sí hay un recordatorio enviado
    ya_enviado = await RecordatorioService._recordatorio_ya_enviado(
        db_session, cita.id, "24h", NotificationChannel.EMAIL
    )
    assert ya_enviado is True

@pytest.mark.asyncio
async def test_get_canales_cliente(db_session: AsyncSession, test_user_data):
    """Prueba la obtención de canales de notificación del cliente"""
    # Crear cliente sin preferencias
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    # Verificar canales por defecto
    canales = await RecordatorioService._get_canales_cliente(cliente)
    assert NotificationChannel.EMAIL in canales
    
    # Crear preferencias con email y WhatsApp habilitados
    await RecordatorioService.crear_preferencias_por_defecto(db_session, cliente.id)
    
    # Verificar canales actualizados
    canales = await RecordatorioService._get_canales_cliente(cliente)
    assert NotificationChannel.EMAIL in canales
    assert NotificationChannel.WHATSAPP not in canales  # Por defecto está deshabilitado

@pytest.mark.asyncio
async def test_recordatorio_habilitado(db_session: AsyncSession, test_user_data):
    """Prueba la verificación de recordatorios habilitados"""
    # Crear cliente sin preferencias
    cliente_in = ClienteCreate(**test_user_data)
    cliente = await ClienteService.create(db_session, cliente_in)
    
    # Verificar que por defecto todos los recordatorios están habilitados
    assert await RecordatorioService._recordatorio_habilitado(cliente, "24h") is True
    assert await RecordatorioService._recordatorio_habilitado(cliente, "2h") is True
    
    # Crear preferencias con recordatorio de 2h deshabilitado
    await RecordatorioService.crear_preferencias_por_defecto(db_session, cliente.id)
    
    # Verificar que el recordatorio de 2h está deshabilitado
    assert await RecordatorioService._recordatorio_habilitado(cliente, "2h") is False

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