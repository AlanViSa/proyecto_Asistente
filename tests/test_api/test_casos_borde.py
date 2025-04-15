"""
Tests for edge cases and special validations
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
    """Tests creating a client with empty fields"""
    client_data = {
        "email": "",
        "name": "",
        "surname": "",
        "phone": "",
        "address": ""
    }
    response = client.post("/api/v1/clients", json=client_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_cliente_campos_muy_largos(client: TestClient):
    """Tests creating a client with very long fields"""
    client_data = {
        "email": "a" * 100 + "@email.com",
        "name": "a" * 100,
        "surname": "a" * 100,
        "phone": "1" * 20,
        "address": "a" * 500
    }
    response = client.post("/api/v1/clients", json=client_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_cliente_caracteres_especiales(client: TestClient):
    """Tests creating a client with special characters"""
    client_data = {
        "email": "test!@#$%^&*()@email.com",
        "name": "Test!@#$%^&*()",
        "surname": "User!@#$%^&*()",
        "phone": "123-456-7890",
        "address": "123 Test St!@#$%^&*()"
    }
    response = client.post("/api/v1/clients", json=client_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_cita_fecha_pasado(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba la creación de una cita con fecha en el pasado"""
    # Crear cliente
    client_response = client.post("/api/v1/clients", json=test_cliente_data)
    client_id = client_response.json()["id"]
    
    # Crear servicio
    service_response = client.post("/api/v1/services", json=test_servicio_data)
    service_id = service_response.json()["id"]
    
    # Crear cita con fecha en el pasado
    appointment_data = {
        "client_id": client_id,
        "service_id": service_id,
        "date": (datetime.now() - timedelta(days=1)).date().isoformat(),
        "time": "10:00",
        "notes": "Test appointment"
    }
    response = client.post("/api/v1/appointments", json=appointment_data)
    assert response.status_code == 400
    assert "date" in response.json()["detail"].lower()

def test_crear_cita_hora_invalida(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests creating an appointment with an invalid time"""
    # Crear cliente
    client_response = client.post("/api/v1/clients", json=test_cliente_data)
    client_id = client_response.json()["id"]
    
    # Crear servicio
    service_response = client.post("/api/v1/services", json=test_servicio_data)
    service_id = service_response.json()["id"]
    
    # Crear cita con hora inválida
    appointment_data = {
        "client_id": client_id,
        "service_id": service_id,
        "date": (datetime.now() + timedelta(days=1)).date().isoformat(),
        "time": "25:00",
        "notes": "Test appointment"
    }
    response = client.post("/api/v1/appointments", json=appointment_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_cita_horario_no_disponible(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests creating an appointment at a unavailable time"""
    # Crear cliente
    client_response = client.post("/api/v1/clients", json=test_cliente_data)
    client_id = client_response.json()["id"]
    
    # Crear servicio
    service_response = client.post("/api/v1/services", json=test_servicio_data)
    service_id = service_response.json()["id"]
    
    # Crear primera cita
    appointment_data = {
        "client_id": client_id,
        "service_id": service_id,
        "date": (datetime.now() + timedelta(days=1)).date().isoformat(),
        "time": "10:00",
        "notes": "Test appointment"
    }
    client.post("/api/v1/appointments", json=appointment_data)
    
    # Intentar crear segunda cita en el mismo horario
    response = client.post("/api/v1/appointments", json=appointment_data)
    assert response.status_code == 400
    assert "time" in response.json()["detail"].lower()

def test_crear_notificacion_canal_invalido(client: TestClient, test_cliente_data):
    """Tests creating a notification with an invalid channel"""
    # Crear cliente
    client_response = client.post("/api/v1/clients", json=test_cliente_data)
    client_id = client_response.json()["id"]
    
    # Crear notificación con canal inválido
    notification_data = {
        "client_id": client_id,
        "type": TipoNotificacion.CITA_PROGRAMADA,
        "message": "Test notification",
        "channel": "INVALID_CHANNEL"
    }
    response = client.post("/api/v1/notifications", json=notification_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_recordatorio_frecuencia_invalida(client: TestClient, test_cliente_data):
    """Tests creating a reminder with an invalid frequency"""
    # Crear cliente
    client_response = client.post("/api/v1/clients", json=test_cliente_data)
    client_id = client_response.json()["id"]
    
    # Crear recordatorio con frecuencia inválida
    reminder_data = {
        "client_id": client_id,
        "type": TipoRecordatorio.CITA,
        "title": "Test reminder",
        "message": "Test message",
        "reminder_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "frequency": "INVALID_FREQUENCY"
    }
    response = client.post("/api/v1/reminders", json=reminder_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_preferencia_notificacion_horario_invalido(client: TestClient, test_cliente_data):
    """Tests creating a notification preference with an invalid time"""
    # Crear cliente
    client_response = client.post("/api/v1/clients", json=test_cliente_data)
    client_id = client_response.json()["id"]
    
    # Crear preferencia con horario inválido
    preference_data = {
        "client_id": client_id,
        "notification_type": TipoNotificacion.CITA_PROGRAMADA,
        "channels": ["EMAIL"],
        "start_time": "25:00",
        "end_time": "18:00",
        "week_days": ["LUNES"]
    }
    response = client.post("/api/v1/notification-preferences", json=preference_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_preferencia_notificacion_dias_invalidos(client: TestClient, test_cliente_data):
    """Tests creating a notification preference with invalid days"""
    # Crear cliente
    client_response = client.post("/api/v1/clients", json=test_cliente_data)
    client_id = client_response.json()["id"]
    
    # Crear preferencia con días inválidos
    preference_data = {
        "client_id": client_id,
        "notification_type": TipoNotificacion.CITA_PROGRAMADA,
        "channels": ["EMAIL"],
        "start_time": "09:00",
        "end_time": "18:00",
        "week_days": ["INVALID_DAY"]
    }
    response = client.post("/api/v1/notification-preferences", json=preference_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_servicio_precio_negativo(client: TestClient):
    """Tests creating a service with a negative price"""
    service_data = {
        "name": "Test Service",
        "description": "Test Description",
        "duration": 30,
        "price": -100,
        "state": "ACTIVO"
    }
    response = client.post("/api/v1/services", json=service_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower()

def test_crear_servicio_duracion_negativa(client: TestClient):
    """Tests creating a service with a negative duration"""
    service_data = {
        "name": "Test Service",
        "description": "Test Description",
        "duration": -30,
        "price": 100,
        "state": "ACTIVO"
    }
    response = client.post("/api/v1/services", json=service_data)
    assert response.status_code == 422
    data = response.json()
    assert "validation error" in data["detail"][0]["msg"].lower() 