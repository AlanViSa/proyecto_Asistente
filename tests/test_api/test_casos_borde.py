"""
Pruebas para casos de borde y validaciones especiales
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.models.estado_cliente import EstadoCliente
from app.models.estado_cita import EstadoCita
from app.models.estado_notificacion import EstadoNotificacion
from app.models.estado_recordatorio import EstadoRecordatorio
from app.models.tipo_notificacion import TipoNotificacion
from app.models.tipo_recordatorio import TipoRecordatorio

def test_crear_cliente_campos_vacios(client: TestClient):
    """Prueba la creación de un cliente con campos vacíos"""
    cliente_data = {
        "email": "",
        "nombre": "",
        "apellido": "",
        "telefono": "",
        "direccion": ""
    }
    response = client.post("/api/v1/clientes", json=cliente_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_cliente_campos_muy_largos(client: TestClient):
    """Prueba la creación de un cliente con campos muy largos"""
    cliente_data = {
        "email": "a" * 100 + "@email.com",
        "nombre": "a" * 100,
        "apellido": "a" * 100,
        "telefono": "1" * 20,
        "direccion": "a" * 500
    }
    response = client.post("/api/v1/clientes", json=cliente_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_cliente_caracteres_especiales(client: TestClient):
    """Prueba la creación de un cliente con caracteres especiales"""
    cliente_data = {
        "email": "test!@#$%^&*()@email.com",
        "nombre": "Test!@#$%^&*()",
        "apellido": "User!@#$%^&*()",
        "telefono": "123-456-7890",
        "direccion": "123 Test St!@#$%^&*()"
    }
    response = client.post("/api/v1/clientes", json=cliente_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_cita_fecha_pasado(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba la creación de una cita con fecha en el pasado"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear servicio
    servicio_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = servicio_response.json()["id"]
    
    # Crear cita con fecha en el pasado
    cita_data = {
        "cliente_id": cliente_id,
        "servicio_id": servicio_id,
        "fecha": (datetime.now() - timedelta(days=1)).date().isoformat(),
        "hora": "10:00",
        "notas": "Cita de prueba"
    }
    response = client.post("/api/v1/citas", json=cita_data)
    assert response.status_code == 400
    assert "fecha" in response.json()["detail"].lower()

def test_crear_cita_hora_invalida(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba la creación de una cita con hora inválida"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear servicio
    servicio_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = servicio_response.json()["id"]
    
    # Crear cita con hora inválida
    cita_data = {
        "cliente_id": cliente_id,
        "servicio_id": servicio_id,
        "fecha": (datetime.now() + timedelta(days=1)).date().isoformat(),
        "hora": "25:00",
        "notas": "Cita de prueba"
    }
    response = client.post("/api/v1/citas", json=cita_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_cita_horario_no_disponible(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba la creación de una cita en horario no disponible"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear servicio
    servicio_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = servicio_response.json()["id"]
    
    # Crear primera cita
    cita_data = {
        "cliente_id": cliente_id,
        "servicio_id": servicio_id,
        "fecha": (datetime.now() + timedelta(days=1)).date().isoformat(),
        "hora": "10:00",
        "notas": "Cita de prueba"
    }
    client.post("/api/v1/citas", json=cita_data)
    
    # Intentar crear segunda cita en el mismo horario
    response = client.post("/api/v1/citas", json=cita_data)
    assert response.status_code == 400
    assert "horario" in response.json()["detail"].lower()

def test_crear_notificacion_canal_invalido(client: TestClient, test_cliente_data):
    """Prueba la creación de una notificación con canal inválido"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear notificación con canal inválido
    notificacion_data = {
        "cliente_id": cliente_id,
        "tipo": TipoNotificacion.CITA_PROGRAMADA,
        "mensaje": "Test notification",
        "canal": "INVALID_CHANNEL"
    }
    response = client.post("/api/v1/notificaciones", json=notificacion_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_recordatorio_frecuencia_invalida(client: TestClient, test_cliente_data):
    """Prueba la creación de un recordatorio con frecuencia inválida"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear recordatorio con frecuencia inválida
    recordatorio_data = {
        "cliente_id": cliente_id,
        "tipo": TipoRecordatorio.CITA,
        "titulo": "Test reminder",
        "mensaje": "Test message",
        "fecha_recordatorio": (datetime.now() + timedelta(days=1)).isoformat(),
        "frecuencia": "INVALID_FREQUENCY"
    }
    response = client.post("/api/v1/recordatorios", json=recordatorio_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_preferencia_notificacion_horario_invalido(client: TestClient, test_cliente_data):
    """Prueba la creación de una preferencia de notificación con horario inválido"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear preferencia con horario inválido
    preferencia_data = {
        "cliente_id": cliente_id,
        "tipo_notificacion": TipoNotificacion.CITA_PROGRAMADA,
        "canales": ["EMAIL"],
        "horario_inicio": "25:00",
        "horario_fin": "18:00",
        "dias_semana": ["LUNES"]
    }
    response = client.post("/api/v1/preferencias-notificacion", json=preferencia_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_preferencia_notificacion_dias_invalidos(client: TestClient, test_cliente_data):
    """Prueba la creación de una preferencia de notificación con días inválidos"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear preferencia con días inválidos
    preferencia_data = {
        "cliente_id": cliente_id,
        "tipo_notificacion": TipoNotificacion.CITA_PROGRAMADA,
        "canales": ["EMAIL"],
        "horario_inicio": "09:00",
        "horario_fin": "18:00",
        "dias_semana": ["INVALID_DAY"]
    }
    response = client.post("/api/v1/preferencias-notificacion", json=preferencia_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_servicio_precio_negativo(client: TestClient):
    """Prueba la creación de un servicio con precio negativo"""
    servicio_data = {
        "nombre": "Test Service",
        "descripcion": "Test Description",
        "duracion": 30,
        "precio": -100,
        "estado": "ACTIVO"
    }
    response = client.post("/api/v1/servicios", json=servicio_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_servicio_duracion_negativa(client: TestClient):
    """Prueba la creación de un servicio con duración negativa"""
    servicio_data = {
        "nombre": "Test Service",
        "descripcion": "Test Description",
        "duracion": -30,
        "precio": 100,
        "estado": "ACTIVO"
    }
    response = client.post("/api/v1/servicios", json=servicio_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower() 