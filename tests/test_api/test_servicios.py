"""
Pruebas de integración para los endpoints de servicios
"""
import pytest
from fastapi.testclient import TestClient
from app.models.servicio import Servicio
from app.models.estado_servicio import EstadoServicio

def test_create_servicio(client: TestClient, test_servicio_data):
    """Prueba la creación de un servicio a través de la API"""
    response = client.post("/api/v1/servicios", json=test_servicio_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["nombre"] == test_servicio_data["nombre"]
    assert data["descripcion"] == test_servicio_data["descripcion"]
    assert data["duracion"] == test_servicio_data["duracion"]
    assert data["precio"] == test_servicio_data["precio"]
    assert data["estado"] == EstadoServicio.ACTIVO
    assert "id" in data

def test_create_servicio_duplicate_name(client: TestClient, test_servicio_data):
    """Prueba la creación de un servicio con nombre duplicado"""
    # Crear primer servicio
    client.post("/api/v1/servicios", json=test_servicio_data)
    
    # Intentar crear segundo servicio con el mismo nombre
    response = client.post("/api/v1/servicios", json=test_servicio_data)
    assert response.status_code == 400
    assert "nombre" in response.json()["detail"].lower()

def test_get_servicio(client: TestClient, test_servicio_data):
    """Prueba la obtención de un servicio a través de la API"""
    # Crear servicio
    create_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = create_response.json()["id"]
    
    # Obtener servicio
    response = client.get(f"/api/v1/servicios/{servicio_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == servicio_id
    assert data["nombre"] == test_servicio_data["nombre"]
    assert data["descripcion"] == test_servicio_data["descripcion"]
    assert data["duracion"] == test_servicio_data["duracion"]
    assert data["precio"] == test_servicio_data["precio"]
    assert data["estado"] == EstadoServicio.ACTIVO

def test_get_servicio_not_found(client: TestClient):
    """Prueba la obtención de un servicio que no existe"""
    response = client.get("/api/v1/servicios/999")
    assert response.status_code == 404

def test_update_servicio(client: TestClient, test_servicio_data):
    """Prueba la actualización de un servicio a través de la API"""
    # Crear servicio
    create_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = create_response.json()["id"]
    
    # Actualizar servicio
    update_data = {
        "nombre": "Servicio Actualizado",
        "descripcion": "Descripción actualizada",
        "duracion": 120,
        "precio": 150.0
    }
    response = client.put(f"/api/v1/servicios/{servicio_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["nombre"] == update_data["nombre"]
    assert data["descripcion"] == update_data["descripcion"]
    assert data["duracion"] == update_data["duracion"]
    assert data["precio"] == update_data["precio"]
    assert data["estado"] == EstadoServicio.ACTIVO

def test_update_servicio_not_found(client: TestClient):
    """Prueba la actualización de un servicio que no existe"""
    update_data = {
        "nombre": "Servicio Actualizado",
        "descripcion": "Descripción actualizada",
        "duracion": 120,
        "precio": 150.0
    }
    response = client.put("/api/v1/servicios/999", json=update_data)
    assert response.status_code == 404

def test_update_servicio_duplicate_name(client: TestClient, test_servicio_data):
    """Prueba la actualización de un servicio con nombre duplicado"""
    # Crear dos servicios
    servicio1_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio1_id = servicio1_response.json()["id"]
    
    servicio2_data = test_servicio_data.copy()
    servicio2_data["nombre"] = "Otro Servicio"
    servicio2_response = client.post("/api/v1/servicios", json=servicio2_data)
    servicio2_id = servicio2_response.json()["id"]
    
    # Intentar actualizar el segundo servicio con el nombre del primero
    update_data = {"nombre": test_servicio_data["nombre"]}
    response = client.put(f"/api/v1/servicios/{servicio2_id}", json=update_data)
    assert response.status_code == 400
    assert "nombre" in response.json()["detail"].lower()

def test_delete_servicio(client: TestClient, test_servicio_data):
    """Prueba la eliminación de un servicio a través de la API"""
    # Crear servicio
    create_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = create_response.json()["id"]
    
    # Eliminar servicio
    response = client.delete(f"/api/v1/servicios/{servicio_id}")
    assert response.status_code == 204
    
    # Verificar que el servicio fue eliminado
    get_response = client.get(f"/api/v1/servicios/{servicio_id}")
    assert get_response.status_code == 404

def test_delete_servicio_not_found(client: TestClient):
    """Prueba la eliminación de un servicio que no existe"""
    response = client.delete("/api/v1/servicios/999")
    assert response.status_code == 404

def test_get_servicios(client: TestClient, test_servicio_data):
    """Prueba la obtención de la lista de servicios a través de la API"""
    # Crear varios servicios
    for i in range(3):
        servicio_data = test_servicio_data.copy()
        servicio_data["nombre"] = f"Servicio {i+1}"
        client.post("/api/v1/servicios", json=servicio_data)
    
    # Obtener lista de servicios
    response = client.get("/api/v1/servicios")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 3
    assert all("id" in servicio for servicio in data)
    assert all("nombre" in servicio for servicio in data)
    assert all("descripcion" in servicio for servicio in data)
    assert all("duracion" in servicio for servicio in data)
    assert all("precio" in servicio for servicio in data)
    assert all("estado" in servicio for servicio in data)

def test_activar_servicio(client: TestClient, test_servicio_data):
    """Prueba la activación de un servicio a través de la API"""
    # Crear servicio
    create_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = create_response.json()["id"]
    
    # Desactivar servicio
    client.put(f"/api/v1/servicios/{servicio_id}/desactivar")
    
    # Activar servicio
    response = client.put(f"/api/v1/servicios/{servicio_id}/activar")
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == EstadoServicio.ACTIVO

def test_desactivar_servicio(client: TestClient, test_servicio_data):
    """Prueba la desactivación de un servicio a través de la API"""
    # Crear servicio
    create_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = create_response.json()["id"]
    
    # Desactivar servicio
    response = client.put(f"/api/v1/servicios/{servicio_id}/desactivar")
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == EstadoServicio.INACTIVO

def test_activar_servicio_not_found(client: TestClient):
    """Prueba la activación de un servicio que no existe"""
    response = client.put("/api/v1/servicios/999/activar")
    assert response.status_code == 404

def test_desactivar_servicio_not_found(client: TestClient):
    """Prueba la desactivación de un servicio que no existe"""
    response = client.put("/api/v1/servicios/999/desactivar")
    assert response.status_code == 404 