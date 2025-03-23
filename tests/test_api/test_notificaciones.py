"""
Pruebas de integración para los endpoints de notificaciones
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.models.estado_cita import EstadoCita
from app.services.notification import NotificationChannel

def test_get_notificaciones_pendientes(client: TestClient, test_user_data, test_cita_data):
    """Prueba la obtención de notificaciones pendientes a través de la API"""
    # Crear cliente y cita
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear cita para dentro de 24 horas
    fecha_hora = datetime.now() + timedelta(hours=24)
    cita_data = test_cita_data.copy()
    cita_data["cliente_id"] = cliente_id
    cita_data["fecha_hora"] = fecha_hora.isoformat()
    cita_data["estado"] = EstadoCita.CONFIRMADA
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Obtener notificaciones pendientes
    response = client.get("/api/v1/notificaciones/pendientes")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) > 0
    assert any(notificacion["cita_id"] == cita_id for notificacion in data)
    assert all("id" in notificacion for notificacion in data)
    assert all("cita_id" in notificacion for notificacion in data)
    assert all("tipo" in notificacion for notificacion in data)
    assert all("canal" in notificacion for notificacion in data)
    assert all("estado" in notificacion for notificacion in data)

def test_get_notificaciones_cita(client: TestClient, test_user_data, test_cita_data):
    """Prueba la obtención de notificaciones de una cita a través de la API"""
    # Crear cliente y cita
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    cita_data = test_cita_data.copy()
    cita_data["cliente_id"] = cliente_id
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Obtener notificaciones de la cita
    response = client.get(f"/api/v1/citas/{cita_id}/notificaciones")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 2  # Debería tener al menos las notificaciones de 24h y 2h
    assert all(notificacion["cita_id"] == cita_id for notificacion in data)
    assert all("id" in notificacion for notificacion in data)
    assert all("tipo" in notificacion for notificacion in data)
    assert all("canal" in notificacion for notificacion in data)
    assert all("estado" in notificacion for notificacion in data)

def test_get_notificaciones_cita_not_found(client: TestClient):
    """Prueba la obtención de notificaciones de una cita que no existe"""
    response = client.get("/api/v1/citas/999/notificaciones")
    assert response.status_code == 404

def test_marcar_notificacion_enviada(client: TestClient, test_user_data, test_cita_data):
    """Prueba el marcado de una notificación como enviada a través de la API"""
    # Crear cliente y cita
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    cita_data = test_cita_data.copy()
    cita_data["cliente_id"] = cliente_id
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Obtener notificaciones de la cita
    notificaciones_response = client.get(f"/api/v1/citas/{cita_id}/notificaciones")
    notificaciones = notificaciones_response.json()
    
    # Marcar la primera notificación como enviada
    notificacion_id = notificaciones[0]["id"]
    response = client.put(f"/api/v1/notificaciones/{notificacion_id}/enviada")
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == "ENVIADA"
    assert data["fecha_envio"] is not None

def test_marcar_notificacion_enviada_not_found(client: TestClient):
    """Prueba el marcado de una notificación que no existe como enviada"""
    response = client.put("/api/v1/notificaciones/999/enviada")
    assert response.status_code == 404

def test_marcar_notificacion_fallida(client: TestClient, test_user_data, test_cita_data):
    """Prueba el marcado de una notificación como fallida a través de la API"""
    # Crear cliente y cita
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    cita_data = test_cita_data.copy()
    cita_data["cliente_id"] = cliente_id
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Obtener notificaciones de la cita
    notificaciones_response = client.get(f"/api/v1/citas/{cita_id}/notificaciones")
    notificaciones = notificaciones_response.json()
    
    # Marcar la primera notificación como fallida
    notificacion_id = notificaciones[0]["id"]
    error_message = "Error de conexión"
    response = client.put(
        f"/api/v1/notificaciones/{notificacion_id}/fallida",
        json={"error": error_message}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == "FALLIDA"
    assert data["error"] == error_message
    assert data["fecha_intento"] is not None

def test_marcar_notificacion_fallida_not_found(client: TestClient):
    """Prueba el marcado de una notificación que no existe como fallida"""
    response = client.put(
        "/api/v1/notificaciones/999/fallida",
        json={"error": "Error de prueba"}
    )
    assert response.status_code == 404

def test_get_estadisticas_notificaciones(client: TestClient, test_user_data, test_cita_data):
    """Prueba la obtención de estadísticas de notificaciones a través de la API"""
    # Crear cliente y cita
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    cita_data = test_cita_data.copy()
    cita_data["cliente_id"] = cliente_id
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Obtener notificaciones de la cita
    notificaciones_response = client.get(f"/api/v1/citas/{cita_id}/notificaciones")
    notificaciones = notificaciones_response.json()
    
    # Marcar algunas notificaciones como enviadas y fallidas
    for i, notificacion in enumerate(notificaciones[:2]):
        if i == 0:
            client.put(f"/api/v1/notificaciones/{notificacion['id']}/enviada")
        else:
            client.put(
                f"/api/v1/notificaciones/{notificacion['id']}/fallida",
                json={"error": "Error de prueba"}
            )
    
    # Obtener estadísticas
    inicio = (datetime.now() - timedelta(hours=1)).isoformat()
    fin = (datetime.now() + timedelta(hours=1)).isoformat()
    response = client.get(f"/api/v1/notificaciones/estadisticas?inicio={inicio}&fin={fin}")
    assert response.status_code == 200
    data = response.json()
    
    assert "total_enviadas" in data
    assert "exitosas" in data
    assert "fallidas" in data
    assert "por_tipo" in data
    assert "por_canal" in data
    assert data["exitosas"] >= 1
    assert data["fallidas"] >= 1

def test_get_notificaciones_por_canal(client: TestClient, test_user_data, test_cita_data):
    """Prueba la obtención de notificaciones por canal a través de la API"""
    # Crear cliente y cita
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    cita_data = test_cita_data.copy()
    cita_data["cliente_id"] = cliente_id
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Obtener notificaciones por canal
    for canal in NotificationChannel:
        response = client.get(f"/api/v1/notificaciones/canal/{canal.value}")
        assert response.status_code == 200
        data = response.json()
        
        assert all(notificacion["canal"] == canal.value for notificacion in data)
        assert all("id" in notificacion for notificacion in data)
        assert all("cita_id" in notificacion for notificacion in data)
        assert all("tipo" in notificacion for notificacion in data)
        assert all("estado" in notificacion for notificacion in data) 