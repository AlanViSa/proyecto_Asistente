"""
Pruebas de integración para los endpoints de citas
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.models.estado_cita import EstadoCita

def test_create_cita(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba la creación de una cita a través de la API"""
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
        "fecha": (datetime.now() + timedelta(days=1)).isoformat(),
        "hora": "10:00",
        "notas": "Notas de prueba"
    }
    response = client.post("/api/v1/citas", json=cita_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["cliente_id"] == cliente_id
    assert data["servicio_id"] == servicio_id
    assert data["fecha"] == cita_data["fecha"]
    assert data["hora"] == cita_data["hora"]
    assert data["notas"] == cita_data["notas"]
    assert data["estado"] == EstadoCita.PENDIENTE
    assert "id" in data

def test_create_cita_cliente_no_existe(client: TestClient, test_servicio_data):
    """Prueba la creación de una cita para un cliente que no existe"""
    # Crear servicio
    servicio_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = servicio_response.json()["id"]
    
    # Intentar crear cita
    cita_data = {
        "cliente_id": 999,
        "servicio_id": servicio_id,
        "fecha": (datetime.now() + timedelta(days=1)).isoformat(),
        "hora": "10:00",
        "notas": "Notas de prueba"
    }
    response = client.post("/api/v1/citas", json=cita_data)
    assert response.status_code == 404
    assert "cliente" in response.json()["detail"].lower()

def test_create_cita_servicio_no_existe(client: TestClient, test_cliente_data):
    """Prueba la creación de una cita para un servicio que no existe"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Intentar crear cita
    cita_data = {
        "cliente_id": cliente_id,
        "servicio_id": 999,
        "fecha": (datetime.now() + timedelta(days=1)).isoformat(),
        "hora": "10:00",
        "notas": "Notas de prueba"
    }
    response = client.post("/api/v1/citas", json=cita_data)
    assert response.status_code == 404
    assert "servicio" in response.json()["detail"].lower()

def test_get_cita(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba la obtención de una cita a través de la API"""
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
        "fecha": (datetime.now() + timedelta(days=1)).isoformat(),
        "hora": "10:00",
        "notas": "Notas de prueba"
    }
    create_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = create_response.json()["id"]
    
    # Obtener cita
    response = client.get(f"/api/v1/citas/{cita_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == cita_id
    assert data["cliente_id"] == cliente_id
    assert data["servicio_id"] == servicio_id
    assert data["fecha"] == cita_data["fecha"]
    assert data["hora"] == cita_data["hora"]
    assert data["notas"] == cita_data["notas"]
    assert data["estado"] == EstadoCita.PENDIENTE

def test_get_cita_not_found(client: TestClient):
    """Prueba la obtención de una cita que no existe"""
    response = client.get("/api/v1/citas/999")
    assert response.status_code == 404

def test_update_cita(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba la actualización de una cita a través de la API"""
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
        "fecha": (datetime.now() + timedelta(days=1)).isoformat(),
        "hora": "10:00",
        "notas": "Notas de prueba"
    }
    create_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = create_response.json()["id"]
    
    # Actualizar cita
    update_data = {
        "fecha": (datetime.now() + timedelta(days=2)).isoformat(),
        "hora": "11:00",
        "notas": "Notas actualizadas"
    }
    response = client.put(f"/api/v1/citas/{cita_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["fecha"] == update_data["fecha"]
    assert data["hora"] == update_data["hora"]
    assert data["notas"] == update_data["notas"]
    assert data["estado"] == EstadoCita.PENDIENTE

def test_update_cita_not_found(client: TestClient):
    """Prueba la actualización de una cita que no existe"""
    update_data = {
        "fecha": (datetime.now() + timedelta(days=2)).isoformat(),
        "hora": "11:00",
        "notas": "Notas actualizadas"
    }
    response = client.put("/api/v1/citas/999", json=update_data)
    assert response.status_code == 404

def test_cancel_cita(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba la cancelación de una cita a través de la API"""
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
        "fecha": (datetime.now() + timedelta(days=1)).isoformat(),
        "hora": "10:00",
        "notas": "Notas de prueba"
    }
    create_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = create_response.json()["id"]
    
    # Cancelar cita
    response = client.put(f"/api/v1/citas/{cita_id}/cancelar")
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == EstadoCita.CANCELADA

def test_complete_cita(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba la finalización de una cita a través de la API"""
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
        "fecha": (datetime.now() + timedelta(days=1)).isoformat(),
        "hora": "10:00",
        "notas": "Notas de prueba"
    }
    create_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = create_response.json()["id"]
    
    # Finalizar cita
    response = client.put(f"/api/v1/citas/{cita_id}/finalizar")
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == EstadoCita.COMPLETADA

def test_no_show_cita(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba el registro de no asistencia de una cita a través de la API"""
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
        "fecha": (datetime.now() + timedelta(days=1)).isoformat(),
        "hora": "10:00",
        "notas": "Notas de prueba"
    }
    create_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = create_response.json()["id"]
    
    # Registrar no asistencia
    response = client.put(f"/api/v1/citas/{cita_id}/no-show")
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == EstadoCita.NO_SHOW

def test_get_citas_cliente(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba la obtención de las citas de un cliente a través de la API"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear servicio
    servicio_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = servicio_response.json()["id"]
    
    # Crear varias citas para el cliente
    for i in range(3):
        cita_data = {
            "cliente_id": cliente_id,
            "servicio_id": servicio_id,
            "fecha": (datetime.now() + timedelta(days=i+1)).isoformat(),
            "hora": "10:00",
            "notas": f"Notas de prueba {i+1}"
        }
        client.post("/api/v1/citas", json=cita_data)
    
    # Obtener citas del cliente
    response = client.get(f"/api/v1/clientes/{cliente_id}/citas")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 3
    assert all(cita["cliente_id"] == cliente_id for cita in data)
    assert all("id" in cita for cita in data)
    assert all("fecha" in cita for cita in data)
    assert all("hora" in cita for cita in data)
    assert all("notas" in cita for cita in data)
    assert all("estado" in cita for cita in data) 