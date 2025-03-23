"""
Pruebas de integración para los endpoints de recordatorios
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.models.estado_cita import EstadoCita
from app.services.notification import NotificationChannel
from app.models.estado_recordatorio import EstadoRecordatorio
from app.models.tipo_recordatorio import TipoRecordatorio

def test_get_recordatorios_pendientes(client: TestClient, test_user_data, test_cita_data):
    """Prueba la obtención de recordatorios pendientes a través de la API"""
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
    
    # Obtener recordatorios pendientes
    response = client.get("/api/v1/recordatorios/pendientes")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) > 0
    assert any(recordatorio["cita_id"] == cita_id for recordatorio in data)
    assert all("id" in recordatorio for recordatorio in data)
    assert all("cita_id" in recordatorio for recordatorio in data)
    assert all("tipo" in recordatorio for recordatorio in data)
    assert all("estado" in recordatorio for recordatorio in data)

def test_get_recordatorios_cita(client: TestClient, test_user_data, test_cita_data):
    """Prueba la obtención de recordatorios de una cita a través de la API"""
    # Crear cliente y cita
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    cita_data = test_cita_data.copy()
    cita_data["cliente_id"] = cliente_id
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Obtener recordatorios de la cita
    response = client.get(f"/api/v1/citas/{cita_id}/recordatorios")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 2  # Debería tener al menos los recordatorios de 24h y 2h
    assert all(recordatorio["cita_id"] == cita_id for recordatorio in data)
    assert all("id" in recordatorio for recordatorio in data)
    assert all("tipo" in recordatorio for recordatorio in data)
    assert all("estado" in recordatorio for recordatorio in data)

def test_get_recordatorios_cita_not_found(client: TestClient):
    """Prueba la obtención de recordatorios de una cita que no existe"""
    response = client.get("/api/v1/citas/999/recordatorios")
    assert response.status_code == 404

def test_marcar_recordatorio_enviado(client: TestClient, test_user_data, test_cita_data):
    """Prueba el marcado de un recordatorio como enviado a través de la API"""
    # Crear cliente y cita
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    cita_data = test_cita_data.copy()
    cita_data["cliente_id"] = cliente_id
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Obtener recordatorios de la cita
    recordatorios_response = client.get(f"/api/v1/citas/{cita_id}/recordatorios")
    recordatorios = recordatorios_response.json()
    
    # Marcar el primer recordatorio como enviado
    recordatorio_id = recordatorios[0]["id"]
    response = client.put(f"/api/v1/recordatorios/{recordatorio_id}/enviado")
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == "ENVIADO"
    assert data["fecha_envio"] is not None

def test_marcar_recordatorio_enviado_not_found(client: TestClient):
    """Prueba el marcado de un recordatorio que no existe como enviado"""
    response = client.put("/api/v1/recordatorios/999/enviado")
    assert response.status_code == 404

def test_marcar_recordatorio_fallido(client: TestClient, test_user_data, test_cita_data):
    """Prueba el marcado de un recordatorio como fallido a través de la API"""
    # Crear cliente y cita
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    cita_data = test_cita_data.copy()
    cita_data["cliente_id"] = cliente_id
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Obtener recordatorios de la cita
    recordatorios_response = client.get(f"/api/v1/citas/{cita_id}/recordatorios")
    recordatorios = recordatorios_response.json()
    
    # Marcar el primer recordatorio como fallido
    recordatorio_id = recordatorios[0]["id"]
    error_message = "Error de conexión"
    response = client.put(
        f"/api/v1/recordatorios/{recordatorio_id}/fallido",
        json={"error": error_message}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == "FALLIDO"
    assert data["error"] == error_message
    assert data["fecha_intento"] is not None

def test_marcar_recordatorio_fallido_not_found(client: TestClient):
    """Prueba el marcado de un recordatorio que no existe como fallido"""
    response = client.put(
        "/api/v1/recordatorios/999/fallido",
        json={"error": "Error de prueba"}
    )
    assert response.status_code == 404

def test_get_estadisticas_recordatorios(client: TestClient, test_user_data, test_cita_data):
    """Prueba la obtención de estadísticas de recordatorios a través de la API"""
    # Crear cliente y cita
    cliente_response = client.post("/api/v1/clientes", json=test_user_data)
    cliente_id = cliente_response.json()["id"]
    
    cita_data = test_cita_data.copy()
    cita_data["cliente_id"] = cliente_id
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Obtener recordatorios de la cita
    recordatorios_response = client.get(f"/api/v1/citas/{cita_id}/recordatorios")
    recordatorios = recordatorios_response.json()
    
    # Marcar algunos recordatorios como enviados y fallidos
    for i, recordatorio in enumerate(recordatorios[:2]):
        if i == 0:
            client.put(f"/api/v1/recordatorios/{recordatorio['id']}/enviado")
        else:
            client.put(
                f"/api/v1/recordatorios/{recordatorio['id']}/fallido",
                json={"error": "Error de prueba"}
            )
    
    # Obtener estadísticas
    inicio = (datetime.now() - timedelta(hours=1)).isoformat()
    fin = (datetime.now() + timedelta(hours=1)).isoformat()
    response = client.get(f"/api/v1/recordatorios/estadisticas?inicio={inicio}&fin={fin}")
    assert response.status_code == 200
    data = response.json()
    
    assert "total_enviados" in data
    assert "exitosos" in data
    assert "fallidos" in data
    assert "por_tipo" in data
    assert "por_canal" in data
    assert data["exitosos"] >= 1
    assert data["fallidos"] >= 1

def test_create_recordatorio(client: TestClient, test_cliente_data):
    """Prueba la creación de un recordatorio a través de la API"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear recordatorio
    recordatorio_data = {
        "cliente_id": cliente_id,
        "tipo": TipoRecordatorio.CITA,
        "titulo": "Recordatorio de cita",
        "mensaje": "Tienes una cita programada para mañana",
        "fecha_recordatorio": (datetime.now() + timedelta(days=1)).isoformat(),
        "frecuencia": None
    }
    response = client.post("/api/v1/recordatorios", json=recordatorio_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["cliente_id"] == cliente_id
    assert data["tipo"] == TipoRecordatorio.CITA
    assert data["titulo"] == recordatorio_data["titulo"]
    assert data["mensaje"] == recordatorio_data["mensaje"]
    assert data["fecha_recordatorio"] == recordatorio_data["fecha_recordatorio"]
    assert data["frecuencia"] is None
    assert data["estado"] == EstadoRecordatorio.PENDIENTE
    assert "id" in data
    assert "fecha_creacion" in data
    assert "fecha_actualizacion" in data

def test_create_recordatorio_cliente_no_existe(client: TestClient):
    """Prueba la creación de un recordatorio para un cliente que no existe"""
    recordatorio_data = {
        "cliente_id": 999,
        "tipo": TipoRecordatorio.CITA,
        "titulo": "Recordatorio de cita",
        "mensaje": "Tienes una cita programada para mañana",
        "fecha_recordatorio": (datetime.now() + timedelta(days=1)).isoformat(),
        "frecuencia": None
    }
    response = client.post("/api/v1/recordatorios", json=recordatorio_data)
    assert response.status_code == 404
    assert "cliente" in response.json()["detail"].lower()

def test_create_recordatorio_recurrente(client: TestClient, test_cliente_data):
    """Prueba la creación de un recordatorio recurrente a través de la API"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear recordatorio recurrente
    recordatorio_data = {
        "cliente_id": cliente_id,
        "tipo": TipoRecordatorio.GENERAL,
        "titulo": "Recordatorio recurrente",
        "mensaje": "Este es un recordatorio recurrente",
        "fecha_recordatorio": (datetime.now() + timedelta(days=1)).isoformat(),
        "frecuencia": "DIARIO"
    }
    response = client.post("/api/v1/recordatorios", json=recordatorio_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["cliente_id"] == cliente_id
    assert data["tipo"] == TipoRecordatorio.GENERAL
    assert data["titulo"] == recordatorio_data["titulo"]
    assert data["mensaje"] == recordatorio_data["mensaje"]
    assert data["fecha_recordatorio"] == recordatorio_data["fecha_recordatorio"]
    assert data["frecuencia"] == "DIARIO"
    assert data["estado"] == EstadoRecordatorio.PENDIENTE
    assert "id" in data
    assert "fecha_creacion" in data
    assert "fecha_actualizacion" in data

def test_get_recordatorio(client: TestClient, test_cliente_data):
    """Prueba la obtención de un recordatorio a través de la API"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear recordatorio
    recordatorio_data = {
        "cliente_id": cliente_id,
        "tipo": TipoRecordatorio.CITA,
        "titulo": "Recordatorio de cita",
        "mensaje": "Tienes una cita programada para mañana",
        "fecha_recordatorio": (datetime.now() + timedelta(days=1)).isoformat(),
        "frecuencia": None
    }
    create_response = client.post("/api/v1/recordatorios", json=recordatorio_data)
    recordatorio_id = create_response.json()["id"]
    
    # Obtener recordatorio
    response = client.get(f"/api/v1/recordatorios/{recordatorio_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == recordatorio_id
    assert data["cliente_id"] == cliente_id
    assert data["tipo"] == TipoRecordatorio.CITA
    assert data["titulo"] == recordatorio_data["titulo"]
    assert data["mensaje"] == recordatorio_data["mensaje"]
    assert data["fecha_recordatorio"] == recordatorio_data["fecha_recordatorio"]
    assert data["frecuencia"] is None
    assert data["estado"] == EstadoRecordatorio.PENDIENTE
    assert "fecha_creacion" in data
    assert "fecha_actualizacion" in data

def test_get_recordatorio_not_found(client: TestClient):
    """Prueba la obtención de un recordatorio que no existe"""
    response = client.get("/api/v1/recordatorios/999")
    assert response.status_code == 404

def test_update_recordatorio(client: TestClient, test_cliente_data):
    """Prueba la actualización de un recordatorio a través de la API"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear recordatorio
    recordatorio_data = {
        "cliente_id": cliente_id,
        "tipo": TipoRecordatorio.CITA,
        "titulo": "Recordatorio de cita",
        "mensaje": "Tienes una cita programada para mañana",
        "fecha_recordatorio": (datetime.now() + timedelta(days=1)).isoformat(),
        "frecuencia": None
    }
    create_response = client.post("/api/v1/recordatorios", json=recordatorio_data)
    recordatorio_id = create_response.json()["id"]
    
    # Actualizar recordatorio
    update_data = {
        "titulo": "Recordatorio actualizado",
        "mensaje": "Mensaje actualizado",
        "fecha_recordatorio": (datetime.now() + timedelta(days=2)).isoformat()
    }
    response = client.put(f"/api/v1/recordatorios/{recordatorio_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["titulo"] == update_data["titulo"]
    assert data["mensaje"] == update_data["mensaje"]
    assert data["fecha_recordatorio"] == update_data["fecha_recordatorio"]
    assert data["estado"] == EstadoRecordatorio.PENDIENTE
    assert "fecha_actualizacion" in data

def test_update_recordatorio_not_found(client: TestClient):
    """Prueba la actualización de un recordatorio que no existe"""
    update_data = {
        "titulo": "Recordatorio actualizado",
        "mensaje": "Mensaje actualizado",
        "fecha_recordatorio": (datetime.now() + timedelta(days=2)).isoformat()
    }
    response = client.put("/api/v1/recordatorios/999", json=update_data)
    assert response.status_code == 404

def test_delete_recordatorio(client: TestClient, test_cliente_data):
    """Prueba la eliminación de un recordatorio a través de la API"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear recordatorio
    recordatorio_data = {
        "cliente_id": cliente_id,
        "tipo": TipoRecordatorio.CITA,
        "titulo": "Recordatorio de cita",
        "mensaje": "Tienes una cita programada para mañana",
        "fecha_recordatorio": (datetime.now() + timedelta(days=1)).isoformat(),
        "frecuencia": None
    }
    create_response = client.post("/api/v1/recordatorios", json=recordatorio_data)
    recordatorio_id = create_response.json()["id"]
    
    # Eliminar recordatorio
    response = client.delete(f"/api/v1/recordatorios/{recordatorio_id}")
    assert response.status_code == 204
    
    # Verificar que el recordatorio fue eliminado
    get_response = client.get(f"/api/v1/recordatorios/{recordatorio_id}")
    assert get_response.status_code == 404

def test_delete_recordatorio_not_found(client: TestClient):
    """Prueba la eliminación de un recordatorio que no existe"""
    response = client.delete("/api/v1/recordatorios/999")
    assert response.status_code == 404

def test_get_recordatorios_cliente(client: TestClient, test_cliente_data):
    """Prueba la obtención de los recordatorios de un cliente a través de la API"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear varios recordatorios para el cliente
    for i in range(3):
        recordatorio_data = {
            "cliente_id": cliente_id,
            "tipo": TipoRecordatorio.CITA,
            "titulo": f"Recordatorio {i+1}",
            "mensaje": f"Mensaje {i+1}",
            "fecha_recordatorio": (datetime.now() + timedelta(days=i+1)).isoformat(),
            "frecuencia": None
        }
        client.post("/api/v1/recordatorios", json=recordatorio_data)
    
    # Obtener recordatorios del cliente
    response = client.get(f"/api/v1/clientes/{cliente_id}/recordatorios")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 3
    assert all(rec["cliente_id"] == cliente_id for rec in data)
    assert all("id" in rec for rec in data)
    assert all("tipo" in rec for rec in data)
    assert all("titulo" in rec for rec in data)
    assert all("mensaje" in rec for rec in data)
    assert all("fecha_recordatorio" in rec for rec in data)
    assert all("frecuencia" in rec for rec in data)
    assert all("estado" in rec for rec in data)
    assert all("fecha_creacion" in rec for rec in data)
    assert all("fecha_actualizacion" in rec for rec in data)

def test_get_recordatorios_cliente_not_found(client: TestClient):
    """Prueba la obtención de recordatorios de un cliente que no existe"""
    response = client.get("/api/v1/clientes/999/recordatorios")
    assert response.status_code == 404

def test_marcar_recordatorio_completado(client: TestClient, test_cliente_data):
    """Prueba el marcado de un recordatorio como completado a través de la API"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear recordatorio
    recordatorio_data = {
        "cliente_id": cliente_id,
        "tipo": TipoRecordatorio.CITA,
        "titulo": "Recordatorio de cita",
        "mensaje": "Tienes una cita programada para mañana",
        "fecha_recordatorio": (datetime.now() + timedelta(days=1)).isoformat(),
        "frecuencia": None
    }
    create_response = client.post("/api/v1/recordatorios", json=recordatorio_data)
    recordatorio_id = create_response.json()["id"]
    
    # Marcar como completado
    response = client.put(f"/api/v1/recordatorios/{recordatorio_id}/completar")
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == EstadoRecordatorio.COMPLETADO
    assert "fecha_completado" in data

def test_marcar_recordatorio_completado_not_found(client: TestClient):
    """Prueba el marcado de un recordatorio que no existe como completado"""
    response = client.put("/api/v1/recordatorios/999/completar")
    assert response.status_code == 404 