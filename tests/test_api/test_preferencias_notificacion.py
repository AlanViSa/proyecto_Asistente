"""
Integration tests for notification preferences endpoints.
"""
from fastapi.testclient import TestClient
from app.models.notification_type import NotificationType
from app.models.notification_channel import NotificationChannel

def test_create_preferencia(client: TestClient, test_cliente_data):
    """Prueba la creación de una preferencia de notificación a través de la API"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear preferencia
    preferencia_data = {
        "client_id": cliente_id,
        "type": NotificationType.REMINDER,
        "channel": NotificationChannel.EMAIL,
        "active": True
    }
    response = client.post("/api/v1/notification-preferences", json=preferencia_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["client_id"] == cliente_id
    assert data["type"] == NotificationType.REMINDER
    assert data["channel"] == NotificationChannel.EMAIL
    assert data["active"] is True
    assert "id" in data
    assert "fecha_creacion" in data
    assert "fecha_actualizacion" in data

def test_create_preferencia_cliente_no_existe(client: TestClient):
    """Prueba la creación de una preferencia para un cliente que no existe"""
    preferencia_data = {
        "cliente_id": 999,
        "type": NotificationType.REMINDER,
        "channel": NotificationChannel.EMAIL,
        "active": True
    }
    response = client.post("/api/v1/notification-preferences", json=preferencia_data)
    assert response.status_code == 404
    assert "client" in response.json()["detail"].lower()

def test_create_preferencia_duplicada(client: TestClient, test_cliente_data):
    """Prueba la creación de una preferencia duplicada"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear primera preferencia
    preferencia_data = {
        "client_id": cliente_id,
        "type": NotificationType.REMINDER,
        "channel": NotificationChannel.EMAIL,
        "active": True
    }
    client.post("/api/v1/notification-preferences", json=preferencia_data)
    
    # Intentar crear preferencia duplicada
    response = client.post("/api/v1/notification-preferences", json=preferencia_data)
    assert response.status_code == 400
    assert "preferencia" in response.json()["detail"].lower()

def test_get_preferencia(client: TestClient, test_cliente_data):
    """Prueba la obtención de una preferencia a través de la API"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear preferencia
    preferencia_data = {
        "client_id": cliente_id,
        "type": NotificationType.REMINDER,
        "channel": NotificationChannel.EMAIL,
        "active": True
    }
    create_response = client.post("/api/v1/notification-preferences", json=preferencia_data)
    preferencia_id = create_response.json()["id"]
    
    # Obtener preferencia
    response = client.get(f"/api/v1/preferencias-notificacion/{preferencia_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == preferencia_id
    assert data["client_id"] == cliente_id
    assert data["type"] == NotificationType.REMINDER
    assert data["channel"] == NotificationChannel.EMAIL
    assert data["active"] is True
    assert "creation_date" in data
    assert "update_date" in data

def test_get_preferencia_not_found(client: TestClient):
    """Prueba la obtención de una preferencia que no existe"""
    response = client.get("/api/v1/preferencias-notificacion/999")
    assert response.status_code == 404

def test_update_preferencia(client: TestClient, test_cliente_data):
    """Prueba la actualización de una preferencia a través de la API"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear preferencia
    preferencia_data = {
        "client_id": cliente_id,
        "type": NotificationType.REMINDER,
        "channel": NotificationChannel.EMAIL,
        "active": True
    }
    create_response = client.post("/api/v1/notification-preferences", json=preferencia_data)
    preferencia_id = create_response.json()["id"]
    
    # Actualizar preferencia
    update_data = {
        "active": False
    }
    response = client.put(f"/api/v1/notification-preferences/{preferencia_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["active"] is False
    assert data["type"] == NotificationType.REMINDER
    assert data["channel"] == NotificationChannel.EMAIL
    assert "update_date" in data

def test_update_preferencia_not_found(client: TestClient):
    """Prueba la actualización de una preferencia que no existe"""
    update_data = {
        "active": False
    }
    response = client.put("/api/v1/preferencias-notificacion/999", json=update_data)
    assert response.status_code == 404

def test_delete_preferencia(client: TestClient, test_cliente_data):
    """Prueba la eliminación de una preferencia a través de la API"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear preferencia
    preferencia_data = {
        "client_id": cliente_id,
        "type": NotificationType.REMINDER,
        "channel": NotificationChannel.EMAIL,
        "active": True
    }
    create_response = client.post("/api/v1/notification-preferences", json=preferencia_data)
    preferencia_id = create_response.json()["id"]
    
    # Eliminar preferencia
    response = client.delete(f"/api/v1/preferencias-notificacion/{preferencia_id}")
    assert response.status_code == 204
    
    # Verificar que la preferencia fue eliminada
    get_response = client.get(f"/api/v1/preferencias-notificacion/{preferencia_id}")
    assert get_response.status_code == 404

def test_delete_preferencia_not_found(client: TestClient):
    """Prueba la eliminación de una preferencia que no existe"""
    response = client.delete("/api/v1/preferencias-notificacion/999")
    assert response.status_code == 404

def test_get_preferencias_cliente(client: TestClient, test_cliente_data):
    """Test getting a client's preferences via the API."""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear varias preferencias para el cliente
    for notification_type in [NotificationType.REMINDER, NotificationType.CONFIRMATION]:
        for notification_channel in [NotificationChannel.EMAIL, NotificationChannel.SMS]:
            preferencia_data = {
                "client_id": cliente_id,
                "type": notification_type,
                "channel": notification_channel,
                "active": True
            }
            client.post("/api/v1/notification-preferences", json=preferencia_data)
    
    # Obtener preferencias del cliente
    response = client.get(f"/api/v1/clientes/{cliente_id}/preferencias-notificacion")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 4  # 2 types * 2 channels
    assert all(pref["client_id"] == cliente_id for pref in data)
    assert all("id" in pref for pref in data)
    assert all("tipo" in pref for pref in data)
    assert all("canal" in pref for pref in data)
    assert all("activo" in pref for pref in data)
    assert all("fecha_creacion" in pref for pref in data)
    assert all("fecha_actualizacion" in pref for pref in data)

def test_get_preferencias_cliente_not_found(client: TestClient):
    """Prueba la obtención de preferencias de un cliente que no existe"""
    response = client.get("/api/v1/clientes/999/preferencias-notificacion")
    assert response.status_code == 404 