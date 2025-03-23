"""
Pruebas de integración para los endpoints de preferencias de notificación
"""
import pytest
from fastapi.testclient import TestClient
from app.schemas.preferencias_notificacion import PreferenciasNotificacionCreate, PreferenciasNotificacionUpdate

def test_create_preferencias(client: TestClient, test_user_data, test_preferencias_data):
    """Prueba la creación de preferencias de notificación a través de la API"""
    # Crear cliente primero
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear preferencias
    preferencias_data = test_preferencias_data.copy()
    preferencias_data["cliente_id"] = cliente_id
    response = client.post("/api/v1/preferencias", json=preferencias_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["cliente_id"] == cliente_id
    assert data["email_habilitado"] == preferencias_data["email_habilitado"]
    assert data["sms_habilitado"] == preferencias_data["sms_habilitado"]
    assert data["whatsapp_habilitado"] == preferencias_data["whatsapp_habilitado"]
    assert data["zona_horaria"] == preferencias_data["zona_horaria"]
    assert "id" in data

def test_create_preferencias_cliente_no_existe(client: TestClient, test_preferencias_data):
    """Prueba la creación de preferencias para un cliente que no existe"""
    preferencias_data = test_preferencias_data.copy()
    preferencias_data["cliente_id"] = 999
    response = client.post("/api/v1/preferencias", json=preferencias_data)
    assert response.status_code == 404

def test_create_preferencias_duplicadas(client: TestClient, test_user_data, test_preferencias_data):
    """Prueba la creación de preferencias duplicadas para un cliente"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear primeras preferencias
    preferencias_data = test_preferencias_data.copy()
    preferencias_data["cliente_id"] = cliente_id
    client.post("/api/v1/preferencias", json=preferencias_data)
    
    # Intentar crear segundas preferencias
    response = client.post("/api/v1/preferencias", json=preferencias_data)
    assert response.status_code == 400
    assert "cliente_id" in response.json()["detail"].lower()

def test_get_preferencias(client: TestClient, test_user_data, test_preferencias_data):
    """Prueba la obtención de preferencias de notificación a través de la API"""
    # Crear cliente y preferencias
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    preferencias_data = test_preferencias_data.copy()
    preferencias_data["cliente_id"] = cliente_id
    create_response = client.post("/api/v1/preferencias", json=preferencias_data)
    preferencias_id = create_response.json()["id"]
    
    # Obtener preferencias
    response = client.get(f"/api/v1/preferencias/{preferencias_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == preferencias_id
    assert data["cliente_id"] == cliente_id
    assert data["email_habilitado"] == preferencias_data["email_habilitado"]
    assert data["sms_habilitado"] == preferencias_data["sms_habilitado"]
    assert data["whatsapp_habilitado"] == preferencias_data["whatsapp_habilitado"]
    assert data["zona_horaria"] == preferencias_data["zona_horaria"]

def test_get_preferencias_not_found(client: TestClient):
    """Prueba la obtención de preferencias que no existen"""
    response = client.get("/api/v1/preferencias/999")
    assert response.status_code == 404

def test_get_preferencias_cliente(client: TestClient, test_user_data, test_preferencias_data):
    """Prueba la obtención de preferencias por cliente a través de la API"""
    # Crear cliente y preferencias
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    preferencias_data = test_preferencias_data.copy()
    preferencias_data["cliente_id"] = cliente_id
    client.post("/api/v1/preferencias", json=preferencias_data)
    
    # Obtener preferencias del cliente
    response = client.get(f"/api/v1/clientes/{cliente_id}/preferencias")
    assert response.status_code == 200
    data = response.json()
    
    assert data["cliente_id"] == cliente_id
    assert data["email_habilitado"] == preferencias_data["email_habilitado"]
    assert data["sms_habilitado"] == preferencias_data["sms_habilitado"]
    assert data["whatsapp_habilitado"] == preferencias_data["whatsapp_habilitado"]
    assert data["zona_horaria"] == preferencias_data["zona_horaria"]

def test_update_preferencias(client: TestClient, test_user_data, test_preferencias_data):
    """Prueba la actualización de preferencias de notificación a través de la API"""
    # Crear cliente y preferencias
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    preferencias_data = test_preferencias_data.copy()
    preferencias_data["cliente_id"] = cliente_id
    create_response = client.post("/api/v1/preferencias", json=preferencias_data)
    preferencias_id = create_response.json()["id"]
    
    # Actualizar preferencias
    update_data = {
        "email_habilitado": False,
        "sms_habilitado": True,
        "whatsapp_habilitado": False,
        "zona_horaria": "America/New_York"
    }
    response = client.put(f"/api/v1/preferencias/{preferencias_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["email_habilitado"] is False
    assert data["sms_habilitado"] is True
    assert data["whatsapp_habilitado"] is False
    assert data["zona_horaria"] == "America/New_York"

def test_update_preferencias_not_found(client: TestClient):
    """Prueba la actualización de preferencias que no existen"""
    update_data = {
        "email_habilitado": False,
        "sms_habilitado": True,
        "whatsapp_habilitado": False,
        "zona_horaria": "America/New_York"
    }
    response = client.put("/api/v1/preferencias/999", json=update_data)
    assert response.status_code == 404

def test_update_preferencias_zona_horaria_invalida(client: TestClient, test_user_data, test_preferencias_data):
    """Prueba la actualización de preferencias con zona horaria inválida"""
    # Crear cliente y preferencias
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    preferencias_data = test_preferencias_data.copy()
    preferencias_data["cliente_id"] = cliente_id
    create_response = client.post("/api/v1/preferencias", json=preferencias_data)
    preferencias_id = create_response.json()["id"]
    
    # Actualizar preferencias con zona horaria inválida
    update_data = {"zona_horaria": "Zona/Invalida"}
    response = client.put(f"/api/v1/preferencias/{preferencias_id}", json=update_data)
    assert response.status_code == 422
    assert "zona_horaria" in response.json()["detail"].lower()

def test_delete_preferencias(client: TestClient, test_user_data, test_preferencias_data):
    """Prueba la eliminación de preferencias de notificación a través de la API"""
    # Crear cliente y preferencias
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    preferencias_data = test_preferencias_data.copy()
    preferencias_data["cliente_id"] = cliente_id
    create_response = client.post("/api/v1/preferencias", json=preferencias_data)
    preferencias_id = create_response.json()["id"]
    
    # Eliminar preferencias
    response = client.delete(f"/api/v1/preferencias/{preferencias_id}")
    assert response.status_code == 204
    
    # Verificar que las preferencias fueron eliminadas
    get_response = client.get(f"/api/v1/preferencias/{preferencias_id}")
    assert get_response.status_code == 404

def test_delete_preferencias_not_found(client: TestClient):
    """Prueba la eliminación de preferencias que no existen"""
    response = client.delete("/api/v1/preferencias/999")
    assert response.status_code == 404 