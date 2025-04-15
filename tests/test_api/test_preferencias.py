"""
Integration tests for the notification preferences endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.schemas.preferencias_notificacion import PreferenciasNotificacionCreate, PreferenciasNotificacionUpdate

def test_create_preferences(client: TestClient, test_user_data, test_preferences_data):
    """Tests the creation of notification preferences via the API"""
    # Create client first
    client_response = client.post("/api/v1/clients", json=test_user_data)
    client_id = client_response.json()["id"]
    
    # Create preferences
    preferences_data = test_preferences_data.copy()
    preferences_data["client_id"] = client_id
    response = client.post("/api/v1/preferences", json=preferences_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["cliente_id"] == cliente_id
    assert data["email_habilitado"] == preferencias_data["email_habilitado"]
    assert data["sms_habilitado"] == preferencias_data["sms_habilitado"]
    assert data["whatsapp_habilitado"] == preferencias_data["whatsapp_habilitado"]
    assert data["zona_horaria"] == preferencias_data["zona_horaria"]
    assert "id" in data

def test_create_preferences_client_does_not_exist(client: TestClient, test_preferences_data):
    """Tests creating preferences for a client that does not exist"""
    preferences_data = test_preferences_data.copy()
    preferences_data["client_id"] = 999
    response = client.post("/api/v1/preferences", json=preferences_data)
    assert response.status_code == 404

def test_create_duplicate_preferences(client: TestClient, test_user_data, test_preferences_data):
    """Tests creating duplicate preferences for a client"""
    # Create client
    client_response = client.post("/api/v1/clients", json=test_user_data)
    client_id = client_response.json()["id"]
    
    # Create first preferences
    preferences_data = test_preferences_data.copy()
    preferences_data["client_id"] = client_id
    client.post("/api/v1/preferences", json=preferences_data)
    
    # Attempt to create second preferences
    response = client.post("/api/v1/preferences", json=preferences_data)
    assert response.status_code == 400
    assert "client_id" in response.json()["detail"].lower()

def test_get_preferences(client: TestClient, test_user_data, test_preferences_data):
    """Tests getting notification preferences via the API"""
    # Create client and preferences
    client_response = client.post("/api/v1/clients", json=test_user_data)
    client_id = client_response.json()["id"]
    
    preferences_data = test_preferences_data.copy()
    preferences_data["client_id"] = client_id
    create_response = client.post("/api/v1/preferences", json=preferences_data)
    preferences_id = create_response.json()["id"]
    
    # Get preferences
    response = client.get(f"/api/v1/preferences/{preferences_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == preferences_id
    assert data["client_id"] == client_id
    assert data["email_enabled"] == preferences_data["email_enabled"]
    assert data["sms_enabled"] == preferences_data["sms_enabled"]
    assert data["whatsapp_enabled"] == preferences_data["whatsapp_enabled"]
    assert data["time_zone"] == preferences_data["time_zone"]

def test_get_preferences_not_found(client: TestClient):
    """Tests getting preferences that do not exist"""
    response = client.get("/api/v1/preferences/999")
    assert response.status_code == 404

def test_get_preferences_by_client(client: TestClient, test_user_data, test_preferences_data):
    """Tests getting preferences by client via the API"""
    # Create client and preferences
    client_response = client.post("/api/v1/clients", json=test_user_data)
    client_id = client_response.json()["id"]
    
    preferences_data = test_preferences_data.copy()
    preferences_data["client_id"] = client_id
    client.post("/api/v1/preferences", json=preferences_data)
    
    # Get client preferences
    response = client.get(f"/api/v1/clients/{client_id}/preferences")
    assert response.status_code == 200
    data = response.json()
    
    assert data["client_id"] == client_id
    assert data["email_enabled"] == preferences_data["email_enabled"]
    assert data["sms_enabled"] == preferences_data["sms_enabled"]
    assert data["whatsapp_enabled"] == preferences_data["whatsapp_enabled"]
    assert data["time_zone"] == preferences_data["time_zone"]

def test_update_preferences(client: TestClient, test_user_data, test_preferences_data):
    """Tests updating notification preferences via the API"""
    # Create client and preferences
    client_response = client.post("/api/v1/clients", json=test_user_data)
    client_id = client_response.json()["id"]
    
    preferences_data = test_preferences_data.copy()
    preferences_data["client_id"] = client_id
    create_response = client.post("/api/v1/preferences", json=preferences_data)
    preferences_id = create_response.json()["id"]
    
    # Update preferences
    update_data = {
        "email_enabled": False,
        "sms_enabled": True,
        "whatsapp_enabled": False,
        "time_zone": "America/New_York"
    }
    response = client.put(f"/api/v1/preferences/{preferences_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["email_enabled"] is False
    assert data["sms_enabled"] is True
    assert data["whatsapp_enabled"] is False
    assert data["time_zone"] == "America/New_York"

def test_update_preferences_not_found(client: TestClient):
    """Tests updating preferences that do not exist"""
    update_data = {
        "email_enabled": False,
        "sms_enabled": True,
        "whatsapp_enabled": False,
        "time_zone": "America/New_York"
    }
    response = client.put("/api/v1/preferences/999", json=update_data)
    assert response.status_code == 404

def test_update_preferences_invalid_time_zone(client: TestClient, test_user_data, test_preferences_data):
    """Tests updating preferences with an invalid time zone"""
    # Create client and preferences
    client_response = client.post("/api/v1/clients", json=test_user_data)
    client_id = client_response.json()["id"]
    
    preferences_data = test_preferences_data.copy()
    preferences_data["client_id"] = client_id
    create_response = client.post("/api/v1/preferences", json=preferences_data)
    preferences_id = create_response.json()["id"]
    
    # Update preferences with invalid time zone
    update_data = {"time_zone": "Zona/Invalida"}
    response = client.put(f"/api/v1/preferences/{preferences_id}", json=update_data)
    assert response.status_code == 422
    assert "time_zone" in response.json()["detail"].lower()

def test_delete_preferences(client: TestClient, test_user_data, test_preferences_data):
    """Tests deleting notification preferences via the API"""
    # Create client and preferences
    client_response = client.post("/api/v1/clients", json=test_user_data)
    client_id = client_response.json()["id"]
    
    preferences_data = test_preferences_data.copy()
    preferences_data["client_id"] = client_id
    create_response = client.post("/api/v1/preferences", json=preferences_data)
    preferences_id = create_response.json()["id"]
    
    # Delete preferences
    response = client.delete(f"/api/v1/preferences/{preferences_id}")
    assert response.status_code == 204
    
    # Verify that preferences were deleted
    get_response = client.get(f"/api/v1/preferences/{preferences_id}")
    assert get_response.status_code == 404

def test_delete_preferences_not_found(client: TestClient):
    """Tests deleting preferences that do not exist"""
    response = client.delete("/api/v1/preferences/999")
    assert response.status_code == 404 