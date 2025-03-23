import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json
from app.main import app
from app.models.cliente import Cliente
from app.models.cita import Cita

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_client_data():
    return {
        "nombre": "Ana García",
        "telefono": "+1234567890",
        "email": "ana@example.com"
    }

@pytest.fixture
def sample_appointment_data(sample_client_data):
    return {
        "cliente": sample_client_data,
        "fecha_hora": (datetime.now() + timedelta(days=1)).isoformat(),
        "servicio": "corte_dama",
        "duracion_minutos": 60
    }

def test_create_client(client, sample_client_data):
    """Prueba la creación de un cliente a través de la API"""
    response = client.post("/api/v1/clientes/", json=sample_client_data)
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == sample_client_data["nombre"]
    assert data["telefono"] == sample_client_data["telefono"]
    assert data["email"] == sample_client_data["email"]
    return data

def test_create_and_get_client(client, sample_client_data):
    """Prueba la creación y obtención de un cliente"""
    # Crear cliente
    response = client.post("/api/v1/clientes/", json=sample_client_data)
    assert response.status_code == 201
    created = response.json()
    client_id = created["id"]
    
    # Obtener cliente
    response = client.get(f"/api/v1/clientes/{client_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == client_id
    assert data["nombre"] == sample_client_data["nombre"]

def test_create_appointment(client, sample_appointment_data):
    """Prueba la creación de una cita"""
    # Primero crear el cliente
    client_response = client.post("/api/v1/clientes/", json=sample_appointment_data["cliente"])
    assert client_response.status_code == 201
    client_data = client_response.json()
    
    # Crear la cita
    appointment_data = {
        "cliente_id": client_data["id"],
        "fecha_hora": sample_appointment_data["fecha_hora"],
        "servicio": sample_appointment_data["servicio"],
        "duracion_minutos": sample_appointment_data["duracion_minutos"]
    }
    response = client.post("/api/v1/citas/", json=appointment_data)
    assert response.status_code == 201
    data = response.json()
    assert data["cliente_id"] == client_data["id"]
    assert data["servicio"] == sample_appointment_data["servicio"]

def test_appointment_workflow(client):
    """Prueba el flujo completo de trabajo con citas"""
    # 1. Crear cliente
    client_data = {
        "nombre": "Juan Pérez",
        "telefono": "+1234567890",
        "email": "juan@example.com"
    }
    client_response = client.post("/api/v1/clientes/", json=client_data)
    assert client_response.status_code == 201
    client_id = client_response.json()["id"]
    
    # 2. Crear cita
    appointment_data = {
        "cliente_id": client_id,
        "fecha_hora": (datetime.now() + timedelta(days=1)).isoformat(),
        "servicio": "corte_caballero",
        "duracion_minutos": 30
    }
    appointment_response = client.post("/api/v1/citas/", json=appointment_data)
    assert appointment_response.status_code == 201
    appointment_id = appointment_response.json()["id"]
    
    # 3. Obtener cita
    get_response = client.get(f"/api/v1/citas/{appointment_id}")
    assert get_response.status_code == 200
    appointment = get_response.json()
    assert appointment["id"] == appointment_id
    assert appointment["cliente_id"] == client_id
    
    # 4. Actualizar cita
    update_data = {
        "estado": "confirmada"
    }
    update_response = client.patch(f"/api/v1/citas/{appointment_id}", json=update_data)
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["estado"] == "confirmada"

def test_nlp_endpoint(client):
    """Prueba el endpoint de procesamiento de lenguaje natural"""
    message = "¿Cuál es el horario de atención?"
    response = client.post("/api/v1/nlp/analyze", json={"message": message})
    assert response.status_code == 200
    data = response.json()
    assert "intent" in data
    assert "sentimiento" in data
    assert "response" in data
    assert isinstance(data["response"], str)
    assert data["intent"] == "consulta_horarios"
    assert data["sentimiento"] in ["positivo", "neutral", "negativo"]

def test_appointment_scheduling_flow(client):
    """Prueba el flujo completo de programación de citas usando NLP"""
    # 1. Crear cliente
    client_data = {
        "nombre": "Laura Martínez",
        "telefono": "+1234567890",
        "email": "laura@example.com"
    }
    client_response = client.post("/api/v1/clientes/", json=client_data)
    assert client_response.status_code == 201
    client_id = client_response.json()["id"]
    
    # 2. Analizar mensaje para agendar cita
    message = "Quiero agendar un corte de dama para mañana a las 2:30 PM"
    nlp_response = client.post("/api/v1/nlp/analyze", json={"message": message})
    assert nlp_response.status_code == 200
    nlp_data = nlp_response.json()
    assert nlp_data["analysis"]["intent"] == "agendar_cita"
    
    # 3. Crear cita basada en el análisis
    appointment_data = {
        "cliente_id": client_id,
        "fecha_hora": (datetime.now() + timedelta(days=1)).replace(hour=14, minute=30).isoformat(),
        "servicio": "corte_dama",
        "duracion_minutos": 60
    }
    appointment_response = client.post("/api/v1/citas/", json=appointment_data)
    assert appointment_response.status_code == 201
    appointment = appointment_response.json()
    assert appointment["cliente_id"] == client_id
    assert appointment["servicio"] == "corte_dama"

def test_error_handling(client):
    """Prueba el manejo de errores en los endpoints"""
    # 1. Cliente no existente
    response = client.get("/api/v1/clientes/999999")
    assert response.status_code == 404
    
    # 2. Cita no existente
    response = client.get("/api/v1/citas/999999")
    assert response.status_code == 404
    
    # 3. Datos inválidos de cliente
    invalid_client = {
        "nombre": "",  # Nombre vacío
        "telefono": "123"  # Teléfono inválido
    }
    response = client.post("/api/v1/clientes/", json=invalid_client)
    assert response.status_code == 422
    
    # 4. Datos inválidos de cita
    invalid_appointment = {
        "cliente_id": 1,
        "fecha_hora": "fecha_invalida",
        "servicio": "servicio_inexistente"
    }
    response = client.post("/api/v1/citas/", json=invalid_appointment)
    assert response.status_code == 422 