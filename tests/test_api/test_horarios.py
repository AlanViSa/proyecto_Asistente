"""
Pruebas de integración para los endpoints de horarios
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.models.estado_horario import EstadoHorario

def test_create_horario(client: TestClient, test_horario_data):
    """Prueba la creación de un horario a través de la API"""
    response = client.post("/api/v1/horarios", json=test_horario_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["dia_semana"] == test_horario_data["dia_semana"]
    assert data["hora_inicio"] == test_horario_data["hora_inicio"]
    assert data["hora_fin"] == test_horario_data["hora_fin"]
    assert data["estado"] == EstadoHorario.ACTIVO
    assert "id" in data

def test_create_horario_solapado(client: TestClient, test_horario_data):
    """Prueba la creación de un horario que se solapa con otro existente"""
    # Crear primer horario
    client.post("/api/v1/horarios", json=test_horario_data)
    
    # Intentar crear segundo horario que se solapa
    horario_solapado = test_horario_data.copy()
    horario_solapado["hora_inicio"] = "09:00"  # Se solapa con el horario existente
    response = client.post("/api/v1/horarios", json=horario_solapado)
    assert response.status_code == 400
    assert "solapamiento" in response.json()["detail"].lower()

def test_get_horario(client: TestClient, test_horario_data):
    """Prueba la obtención de un horario a través de la API"""
    # Crear horario
    create_response = client.post("/api/v1/horarios", json=test_horario_data)
    horario_id = create_response.json()["id"]
    
    # Obtener horario
    response = client.get(f"/api/v1/horarios/{horario_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == horario_id
    assert data["dia_semana"] == test_horario_data["dia_semana"]
    assert data["hora_inicio"] == test_horario_data["hora_inicio"]
    assert data["hora_fin"] == test_horario_data["hora_fin"]
    assert data["estado"] == EstadoHorario.ACTIVO

def test_get_horario_not_found(client: TestClient):
    """Prueba la obtención de un horario que no existe"""
    response = client.get("/api/v1/horarios/999")
    assert response.status_code == 404

def test_update_horario(client: TestClient, test_horario_data):
    """Prueba la actualización de un horario a través de la API"""
    # Crear horario
    create_response = client.post("/api/v1/horarios", json=test_horario_data)
    horario_id = create_response.json()["id"]
    
    # Actualizar horario
    update_data = {
        "dia_semana": 2,
        "hora_inicio": "10:00",
        "hora_fin": "18:00"
    }
    response = client.put(f"/api/v1/horarios/{horario_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["dia_semana"] == update_data["dia_semana"]
    assert data["hora_inicio"] == update_data["hora_inicio"]
    assert data["hora_fin"] == update_data["hora_fin"]
    assert data["estado"] == EstadoHorario.ACTIVO

def test_update_horario_not_found(client: TestClient):
    """Prueba la actualización de un horario que no existe"""
    update_data = {
        "dia_semana": 2,
        "hora_inicio": "10:00",
        "hora_fin": "18:00"
    }
    response = client.put("/api/v1/horarios/999", json=update_data)
    assert response.status_code == 404

def test_update_horario_solapado(client: TestClient, test_horario_data):
    """Prueba la actualización de un horario que se solapa con otro existente"""
    # Crear dos horarios
    horario1_response = client.post("/api/v1/horarios", json=test_horario_data)
    horario1_id = horario1_response.json()["id"]
    
    horario2_data = test_horario_data.copy()
    horario2_data["dia_semana"] = 2
    horario2_response = client.post("/api/v1/horarios", json=horario2_data)
    horario2_id = horario2_response.json()["id"]
    
    # Intentar actualizar el segundo horario para que se solape con el primero
    update_data = {"dia_semana": test_horario_data["dia_semana"]}
    response = client.put(f"/api/v1/horarios/{horario2_id}", json=update_data)
    assert response.status_code == 400
    assert "solapamiento" in response.json()["detail"].lower()

def test_delete_horario(client: TestClient, test_horario_data):
    """Prueba la eliminación de un horario a través de la API"""
    # Crear horario
    create_response = client.post("/api/v1/horarios", json=test_horario_data)
    horario_id = create_response.json()["id"]
    
    # Eliminar horario
    response = client.delete(f"/api/v1/horarios/{horario_id}")
    assert response.status_code == 204
    
    # Verificar que el horario fue eliminado
    get_response = client.get(f"/api/v1/horarios/{horario_id}")
    assert get_response.status_code == 404

def test_delete_horario_not_found(client: TestClient):
    """Prueba la eliminación de un horario que no existe"""
    response = client.delete("/api/v1/horarios/999")
    assert response.status_code == 404

def test_deactivate_horario(client: TestClient, test_horario_data):
    """Prueba la desactivación de un horario a través de la API"""
    # Crear horario
    create_response = client.post("/api/v1/horarios", json=test_horario_data)
    horario_id = create_response.json()["id"]
    
    # Desactivar horario
    response = client.put(f"/api/v1/horarios/{horario_id}/desactivar")
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == EstadoHorario.INACTIVO

def test_activate_horario(client: TestClient, test_horario_data):
    """Prueba la activación de un horario a través de la API"""
    # Crear horario
    create_response = client.post("/api/v1/horarios", json=test_horario_data)
    horario_id = create_response.json()["id"]
    
    # Desactivar horario
    client.put(f"/api/v1/horarios/{horario_id}/desactivar")
    
    # Activar horario
    response = client.put(f"/api/v1/horarios/{horario_id}/activar")
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == EstadoHorario.ACTIVO

def test_get_horarios(client: TestClient, test_horario_data):
    """Prueba la obtención de la lista de horarios a través de la API"""
    # Crear varios horarios
    for i in range(3):
        horario_data = test_horario_data.copy()
        horario_data["dia_semana"] = i + 1
        client.post("/api/v1/horarios", json=horario_data)
    
    # Obtener lista de horarios
    response = client.get("/api/v1/horarios")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 3
    assert all("id" in horario for horario in data)
    assert all("dia_semana" in horario for horario in data)
    assert all("hora_inicio" in horario for horario in data)
    assert all("hora_fin" in horario for horario in data)
    assert all("estado" in horario for horario in data)

def test_get_horarios_por_dia(client: TestClient, test_horario_data):
    """Prueba la obtención de horarios por día de la semana a través de la API"""
    # Crear horarios para diferentes días
    for dia in range(1, 4):
        horario_data = test_horario_data.copy()
        horario_data["dia_semana"] = dia
        client.post("/api/v1/horarios", json=horario_data)
    
    # Obtener horarios para un día específico
    dia_semana = 1
    response = client.get(f"/api/v1/horarios/dia/{dia_semana}")
    assert response.status_code == 200
    data = response.json()
    
    assert all(horario["dia_semana"] == dia_semana for horario in data)
    assert all("id" in horario for horario in data)
    assert all("hora_inicio" in horario for horario in data)
    assert all("hora_fin" in horario for horario in data)
    assert all("estado" in horario for horario in data) 