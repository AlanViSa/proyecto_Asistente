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
        "name": "Ana García",
        "phone": "+1234567890",
        "email": "ana@example.com",
    }


def sample_appointment_data(sample_client_data):
    return {
        "cliente": sample_client_data,
        "fecha_hora": (datetime.now() + timedelta(days=1)).isoformat(),
        "servicio": "corte_dama",
        "duracion_minutos": 60
    }


def test_create_client(client, sample_client_data):
    """Tests the creation of a client through the API"""
    response = client.post("/api/v1/clients/", json=sample_client_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_client_data["name"]
    assert data["phone"] == sample_client_data["phone"]
    assert data["email"] == sample_client_data["email"]
    return data


def test_create_and_get_client(client, sample_client_data):
    """Tests the creation and retrieval of a client"""
    # Create client
    response = client.post("/api/v1/clients/", json=sample_client_data)
    assert response.status_code == 201
    # Get client
    created = response.json()
    client_id = created["id"]
    
    # Obtener cliente
    response = client.get(f"/api/v1/clientes/{client_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == client_id
    assert data["name"] == sample_client_data["name"]


def test_create_appointment(client, sample_appointment_data):
    """Tests the creation of an appointment"""
    # First create the client
    client_response = client.post("/api/v1/clients/", json=sample_appointment_data["cliente"])
    assert client_response.status_code == 201
    client_data = client_response.json()
    
    # Create the appointment
    appointment_data = {
        "client_id": client_data["id"],
        "date_time": sample_appointment_data["fecha_hora"],
        "service": sample_appointment_data["servicio"],
        "duration_minutes": sample_appointment_data["duracion_minutos"],
    }
    response = client.post("/api/v1/appointments/", json=appointment_data)
    assert response.status_code == 201
    data = response.json()
    assert data["client_id"] == client_data["id"]
    assert data["service"] == sample_appointment_data["servicio"]


def test_appointment_workflow(client):
    """Tests the complete workflow of appointments"""
    # 1. Create client
    client_data = {
        "name": "Juan Pérez",
        "phone": "+1234567890",
        "email": "juan@example.com",
    }
    client_response = client.post("/api/v1/clients/", json=client_data)
    assert client_response.status_code == 201
    client_id = client_response.json()["id"]
    
    # 2. Create appointment
    appointment_data = {
        "client_id": client_id,
        "date_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "service": "corte_caballero",
        "duration_minutes": 30,
    }
    appointment_response = client.post("/api/v1/appointments/", json=appointment_data)
    assert appointment_response.status_code == 201
    appointment_id = appointment_response.json()["id"]
    
    # 3. Get appointment
    get_response = client.get(f"/api/v1/appointments/{appointment_id}")
    assert get_response.status_code == 200
    appointment = get_response.json()
    assert appointment["id"] == appointment_id
    assert appointment["client_id"] == client_id
    
    # 4. Update appointment
    update_data = {
        "status": "confirmed",
    }
    update_response = client.patch(f"/api/v1/appointments/{appointment_id}", json=update_data)
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == "confirmed"


def test_nlp_endpoint(client):
    """Tests the natural language processing endpoint"""
    message = "What are the business hours?"
    response = client.post("/api/v1/nlp/analyze", json={"message": message})
    assert response.status_code == 200
    data = response.json()
    assert "intent" in data
    assert "sentiment" in data
    assert "response" in data
    assert isinstance(data["response"], str)
    assert data["intent"] == "check_hours"
    assert data["sentiment"] in ["positive", "neutral", "negative"]


def test_appointment_scheduling_flow(client):
    """Tests the complete flow of scheduling appointments using NLP"""
    # 1. Create client
    client_data = {
        "name": "Laura Martínez",
        "phone": "+1234567890",
        "email": "laura@example.com",
    }
    client_response = client.post("/api/v1/clients/", json=client_data)
    assert client_response.status_code == 201
    client_id = client_response.json()["id"]
    
    # 2. Analizar mensaje para agendar cita
    message = "Quiero agendar un corte de dama para mañana a las 2:30 PM"
    nlp_response = client.post("/api/v1/nlp/analyze", json={"message": message})
    assert nlp_response.status_code == 200
    nlp_data = nlp_response.json()
    assert nlp_data["analysis"]["intent"] == "agendar_cita"

    # 3. Create appointment based on the analysis
    appointment_data = {
        "client_id": client_id,
        "date_time": (datetime.now() + timedelta(days=1))
        .replace(hour=14, minute=30)
        .isoformat(),
        "service": "corte_dama",
        "duration_minutes": 60,
    }
    appointment_response = client.post("/api/v1/appointments/", json=appointment_data)
    assert appointment_response.status_code == 201
    appointment = appointment_response.json()
    assert appointment["client_id"] == client_id
    assert appointment["service"] == "corte_dama"


def test_error_handling(client):
    """Tests error handling in the endpoints"""
    # 1. Non-existent client
    response = client.get("/api/v1/clients/999999")
    assert response.status_code == 404
    
    # 2. Non-existent appointment
    response = client.get("/api/v1/appointments/999999")
    assert response.status_code == 404
    
    # 3. Invalid client data
    invalid_client = {
        "name": "",  # Empty name
        "phone": "123"  # Invalid phone
    }
    response = client.post("/api/v1/clients/", json=invalid_client)
    assert response.status_code == 422
    
    # 4. Invalid appointment data
    invalid_appointment = {
        "client_id": 1,
        "date_time": "invalid_date",
        "service": "non_existent_service",
    }
    response = client.post("/api/v1/appointments/", json=invalid_appointment)
    assert response.status_code == 422