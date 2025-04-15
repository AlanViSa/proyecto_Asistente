# Integration tests for appointment endpoints
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.models.estado_cita import EstadoCita  # Assuming this maps to appointment status

def test_create_cita(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests the creation of an appointment via the API"""
    # Create customer
    customer_response = client.post("/api/v1/clientes", json=test_cliente_data)
    customer_id = customer_response.json()["id"]
    
    # Create service
    service_response = client.post("/api/v1/servicios", json=test_servicio_data)
    service_id = service_response.json()["id"]
    
    # Create appointment
    appointment_data = {
        "customer_id": customer_id,
        "service_id": service_id,
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "time": "10:00",
        "notes": "Test notes"
    }
    response = client.post("/api/v1/citas", json=appointment_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["customer_id"] == customer_id
    assert data["service_id"] == service_id
    assert data["date"] == appointment_data["date"]
    assert data["time"] == appointment_data["time"]
    assert data["notes"] == appointment_data["notes"]
    assert data["status"] == EstadoCita.PENDIENTE  # Assuming PENDIENTE maps to pending
    assert "id" in data

def test_create_cita_cliente_no_existe(client: TestClient, test_servicio_data):
    """Tests creating an appointment for a non-existent customer"""
    # Create service
    service_response = client.post("/api/v1/servicios", json=test_servicio_data)
    service_id = service_response.json()["id"]
    
    # Attempt to create appointment
    appointment_data = {
        "customer_id": 999,
        "service_id": service_id,
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "time": "10:00",
        "notes": "Test notes"
    }
    response = client.post("/api/v1/citas", json=appointment_data)
    assert response.status_code == 404
    assert "customer" in response.json()["detail"].lower()

def test_create_cita_servicio_no_existe(client: TestClient, test_cliente_data):
    """Tests creating an appointment for a non-existent service"""
    # Create customer
    customer_response = client.post("/api/v1/clientes", json=test_cliente_data)
    customer_id = customer_response.json()["id"]
    
    # Attempt to create appointment
    appointment_data = {
        "customer_id": customer_id,
        "service_id": 999,
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "time": "10:00",
        "notes": "Test notes"
    }
    response = client.post("/api/v1/citas", json=appointment_data)
    assert response.status_code == 404
    assert "service" in response.json()["detail"].lower()

def test_get_cita(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests retrieving an appointment via the API"""
    # Create customer
    customer_response = client.post("/api/v1/clientes", json=test_cliente_data)
    customer_id = customer_response.json()["id"]
    
    # Create service
    service_response = client.post("/api/v1/servicios", json=test_servicio_data)
    service_id = service_response.json()["id"]
    
    # Create appointment
    appointment_data = {
        "customer_id": customer_id,
        "service_id": service_id,
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "time": "10:00",
        "notes": "Test notes"
    }
    create_response = client.post("/api/v1/citas", json=appointment_data)
    appointment_id = create_response.json()["id"]
    
    # Get appointment
    response = client.get(f"/api/v1/citas/{appointment_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == appointment_id
    assert data["customer_id"] == customer_id
    assert data["service_id"] == service_id
    assert data["date"] == appointment_data["date"]
    assert data["time"] == appointment_data["time"]
    assert data["notes"] == appointment_data["notes"]
    assert data["status"] == EstadoCita.PENDIENTE

def test_get_cita_not_found(client: TestClient):
    """Tests retrieving a non-existent appointment"""
    response = client.get("/api/v1/citas/999")
    assert response.status_code == 404

def test_update_cita(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests updating an appointment via the API"""
    # Create customer
    customer_response = client.post("/api/v1/clientes", json=test_cliente_data)
    customer_id = customer_response.json()["id"]
    
    # Create service
    service_response = client.post("/api/v1/servicios", json=test_servicio_data)
    service_id = service_response.json()["id"]
    
    # Create appointment
    appointment_data = {
        "customer_id": customer_id,
        "service_id": service_id,
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "time": "10:00",
        "notes": "Test notes"
    }
    create_response = client.post("/api/v1/citas", json=appointment_data)
    appointment_id = create_response.json()["id"]
    
    # Update appointment
    update_data = {
        "date": (datetime.now() + timedelta(days=2)).isoformat(),
        "time": "11:00",
        "notes": "Updated notes"
    }
    response = client.put(f"/api/v1/citas/{appointment_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["date"] == update_data["date"]
    assert data["time"] == update_data["time"]
    assert data["notes"] == update_data["notes"]
    assert data["status"] == EstadoCita.PENDIENTE

def test_update_cita_not_found(client: TestClient):
    """Tests updating a non-existent appointment"""
    update_data = {
        "date": (datetime.now() + timedelta(days=2)).isoformat(),
        "time": "11:00",
        "notes": "Updated notes"
    }
    response = client.put("/api/v1/citas/999", json=update_data)
    assert response.status_code == 404

def test_cancel_cita(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests cancelling an appointment via the API"""
    # Create customer
    customer_response = client.post("/api/v1/clientes", json=test_cliente_data)
    customer_id = customer_response.json()["id"]
    
    # Create service
    service_response = client.post("/api/v1/servicios", json=test_servicio_data)
    service_id = service_response.json()["id"]
    
    # Create appointment
    appointment_data = {
        "customer_id": customer_id,
        "service_id": service_id,
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "time": "10:00",
        "notes": "Test notes"
    }
    create_response = client.post("/api/v1/citas", json=appointment_data)
    appointment_id = create_response.json()["id"]
    
    # Cancel appointment
    response = client.put(f"/api/v1/citas/{appointment_id}/cancelar")
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == EstadoCita.CANCELADA  # Assuming CANCELADA maps to cancelled

def test_complete_cita(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests completing an appointment via the API"""
    # Create customer
    customer_response = client.post("/api/v1/clientes", json=test_cliente_data)
    customer_id = customer_response.json()["id"]
    
    # Create service
    service_response = client.post("/api/v1/servicios", json=test_servicio_data)
    service_id = service_response.json()["id"]
    
    # Create appointment
    appointment_data = {
        "customer_id": customer_id,
        "service_id": service_id,
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "time": "10:00",
        "notes": "Test notes"
    }
    create_response = client.post("/api/v1/citas", json=appointment_data)
    appointment_id = create_response.json()["id"]
    
    # Complete appointment
    response = client.put(f"/api/v1/citas/{appointment_id}/finalizar")
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == EstadoCita.COMPLETADA  # Assuming COMPLETADA maps to completed

def test_no_show_cita(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests registering a no-show for an appointment via the API"""
    # Create customer
    customer_response = client.post("/api/v1/clientes", json=test_cliente_data)
    customer_id = customer_response.json()["id"]
    
    # Create service
    service_response = client.post("/api/v1/servicios", json=test_servicio_data)
    service_id = service_response.json()["id"]
    
    # Create appointment
    appointment_data = {
        "customer_id": customer_id,
        "service_id": service_id,
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "time": "10:00",
        "notes": "Test notes"
    }
    create_response = client.post("/api/v1/citas", json=appointment_data)
    appointment_id = create_response.json()["id"]
    
    # Register no-show
    response = client.put(f"/api/v1/citas/{appointment_id}/no-show")
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == EstadoCita.NO_SHOW

def test_get_citas_cliente(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests retrieving a customer's appointments via the API"""
    # Create customer
    customer_response = client.post("/api/v1/clientes", json=test_cliente_data)
    customer_id = customer_response.json()["id"]
    
    # Create service
    service_response = client.post("/api/v1/servicios", json=test_servicio_data)
    service_id = service_response.json()["id"]
    
    # Create multiple appointments for the customer
    for i in range(3):
        appointment_data = {
            "customer_id": customer_id,
            "service_id": service_id,
            "date": (datetime.now() + timedelta(days=i+1)).isoformat(),
            "time": "10:00",
            "notes": f"Test notes {i+1}"
        }
        client.post("/api/v1/citas", json=appointment_data)
    
    # Get customer appointments
    response = client.get(f"/api/v1/clientes/{customer_id}/citas")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 3
    assert all(appointment["customer_id"] == customer_id for appointment in data)
    assert all("id" in appointment for appointment in data)
    assert all("date" in appointment for appointment in data)
    assert all("time" in appointment for appointment in data)
    assert all("notes" in appointment for appointment in data)
    assert all("status" in appointment for appointment in data)