"""
Pruebas de integración entre diferentes módulos del sistema
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.models.estado_cita import EstadoCita
from app.models.estado_notificacion import EstadoNotificacion
from app.models.estado_recordatorio import EstadoRecordatorio
from app.models.tipo_notificacion import TipoNotificacion
from app.models.tipo_recordatorio import TipoRecordatorio

def test_creacion_cita_genera_notificaciones_y_recordatorios(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba que al crear una cita se generen las notificaciones y recordatorios correspondientes"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear servicio
    servicio_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = servicio_response.json()["id"]
    
    # Crear cita
    cita_data = {
        "cliente_id": cliente_id,
        "servicio_id": servicio_id,
        "fecha": (datetime.now() + timedelta(days=1)).date().isoformat(),
        "hora": "10:00",
        "notas": "Cita de prueba"
    }
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Verificar que se creó la notificación
    notificaciones_response = client.get(f"/api/v1/clientes/{cliente_id}/notificaciones")
    assert notificaciones_response.status_code == 200
    notificaciones = notificaciones_response.json()
    
    cita_notificacion = next(
        (n for n in notificaciones if n["tipo"] == TipoNotificacion.CITA_PROGRAMADA),
        None
    )
    assert cita_notificacion is not None
    assert cita_notificacion["estado"] == EstadoNotificacion.PENDIENTE
    assert cita_notificacion["cita_id"] == cita_id
    
    # Verificar que se creó el recordatorio
    recordatorios_response = client.get(f"/api/v1/clientes/{cliente_id}/recordatorios")
    assert recordatorios_response.status_code == 200
    recordatorios = recordatorios_response.json()
    
    cita_recordatorio = next(
        (r for r in recordatorios if r["tipo"] == TipoRecordatorio.CITA),
        None
    )
    assert cita_recordatorio is not None
    assert cita_recordatorio["estado"] == EstadoRecordatorio.PENDIENTE
    assert cita_recordatorio["cita_id"] == cita_id

def test_cancelacion_cita_actualiza_notificaciones(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba que al cancelar una cita se actualicen las notificaciones correspondientes"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear servicio
    servicio_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = servicio_response.json()["id"]
    
    # Crear cita
    cita_data = {
        "cliente_id": cliente_id,
        "servicio_id": servicio_id,
        "fecha": (datetime.now() + timedelta(days=1)).date().isoformat(),
        "hora": "10:00",
        "notas": "Cita de prueba"
    }
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Cancelar cita
    client.put(f"/api/v1/citas/{cita_id}/cancelar")
    
    # Verificar que se actualizó la notificación
    notificaciones_response = client.get(f"/api/v1/clientes/{cliente_id}/notificaciones")
    assert notificaciones_response.status_code == 200
    notificaciones = notificaciones_response.json()
    
    cita_notificacion = next(
        (n for n in notificaciones if n["tipo"] == TipoNotificacion.CITA_CANCELADA),
        None
    )
    assert cita_notificacion is not None
    assert cita_notificacion["estado"] == EstadoNotificacion.PENDIENTE
    assert cita_notificacion["cita_id"] == cita_id

def test_completar_cita_actualiza_recordatorios(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba que al completar una cita se actualicen los recordatorios correspondientes"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear servicio
    servicio_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = servicio_response.json()["id"]
    
    # Crear cita
    cita_data = {
        "cliente_id": cliente_id,
        "servicio_id": servicio_id,
        "fecha": (datetime.now() + timedelta(days=1)).date().isoformat(),
        "hora": "10:00",
        "notas": "Cita de prueba"
    }
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Completar cita
    client.put(f"/api/v1/citas/{cita_id}/completar")
    
    # Verificar que se actualizó el recordatorio
    recordatorios_response = client.get(f"/api/v1/clientes/{cliente_id}/recordatorios")
    assert recordatorios_response.status_code == 200
    recordatorios = recordatorios_response.json()
    
    cita_recordatorio = next(
        (r for r in recordatorios if r["tipo"] == TipoRecordatorio.CITA),
        None
    )
    assert cita_recordatorio is not None
    assert cita_recordatorio["estado"] == EstadoRecordatorio.COMPLETADO
    assert cita_recordatorio["cita_id"] == cita_id

def test_actualizar_preferencias_notificacion_afecta_notificaciones(client: TestClient, test_cliente_data):
    """Prueba que al actualizar las preferencias de notificación se afecten las notificaciones futuras"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear preferencia de notificación
    preferencia_data = {
        "cliente_id": cliente_id,
        "tipo_notificacion": TipoNotificacion.CITA_PROGRAMADA,
        "canales": ["EMAIL", "SMS"],
        "horario_inicio": "09:00",
        "horario_fin": "18:00",
        "dias_semana": ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
    }
    preferencia_response = client.post("/api/v1/preferencias-notificacion", json=preferencia_data)
    preferencia_id = preferencia_response.json()["id"]
    
    # Actualizar preferencia
    update_data = {
        "canales": ["EMAIL"],
        "horario_inicio": "10:00",
        "horario_fin": "19:00"
    }
    client.put(f"/api/v1/preferencias-notificacion/{preferencia_id}", json=update_data)
    
    # Verificar que la preferencia se actualizó
    preferencia_response = client.get(f"/api/v1/preferencias-notificacion/{preferencia_id}")
    assert preferencia_response.status_code == 200
    preferencia = preferencia_response.json()
    
    assert preferencia["canales"] == ["EMAIL"]
    assert preferencia["horario_inicio"] == "10:00"
    assert preferencia["horario_fin"] == "19:00"

def test_activar_desactivar_cliente_afecta_citas(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba que al activar/desactivar un cliente se afecten sus citas"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear servicio
    servicio_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = servicio_response.json()["id"]
    
    # Crear cita
    cita_data = {
        "cliente_id": cliente_id,
        "servicio_id": servicio_id,
        "fecha": (datetime.now() + timedelta(days=1)).date().isoformat(),
        "hora": "10:00",
        "notas": "Cita de prueba"
    }
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Desactivar cliente
    client.put(f"/api/v1/clientes/{cliente_id}/desactivar")
    
    # Verificar que no se pueden crear nuevas citas
    nueva_cita_data = {
        "cliente_id": cliente_id,
        "servicio_id": servicio_id,
        "fecha": (datetime.now() + timedelta(days=2)).date().isoformat(),
        "hora": "11:00",
        "notas": "Nueva cita"
    }
    nueva_cita_response = client.post("/api/v1/citas", json=nueva_cita_data)
    assert nueva_cita_response.status_code == 400
    assert "cliente inactivo" in nueva_cita_response.json()["detail"].lower()
    
    # Activar cliente
    client.put(f"/api/v1/clientes/{cliente_id}/activar")
    
    # Verificar que se pueden crear nuevas citas
    nueva_cita_response = client.post("/api/v1/citas", json=nueva_cita_data)
    assert nueva_cita_response.status_code == 200 