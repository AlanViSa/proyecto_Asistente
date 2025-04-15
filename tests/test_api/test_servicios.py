"""
Integration tests for the service endpoints.
"""
from fastapi.testclient import TestClient
from app.models.service import Service
from app.models.service_status import ServiceStatus

def test_create_service(client: TestClient, test_service_data):
    """Tests the creation of a service via the API."""
    response = client.post("/api/v1/services", json=test_service_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["nombre"] == test_servicio_data["nombre"]
    assert data["descripcion"] == test_servicio_data["descripcion"]
    assert data["duracion"] == test_servicio_data["duracion"]
    assert data["precio"] == test_servicio_data["precio"]
    assert data["estado"] == ServiceStatus.ACTIVE
    assert "id" in data

def test_create_service_duplicate_name(client: TestClient, test_service_data):
    """Tests the creation of a service with a duplicate name."""
    # Create the first service
    client.post("/api/v1/services", json=test_service_data)
    
    # Attempt to create a second service with the same name
    response = client.post("/api/v1/services", json=test_service_data)
    assert response.status_code == 400
    assert "name" in response.json()["detail"].lower()

def test_get_service(client: TestClient, test_service_data):
    """Tests retrieving a service via the API."""
    # Create a service
    create_response = client.post("/api/v1/services", json=test_service_data)
    service_id = create_response.json()["id"]
    
    # Retrieve the service
    response = client.get(f"/api/v1/services/{service_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == service_id
    assert data["nombre"] == test_servicio_data["nombre"]
    assert data["descripcion"] == test_servicio_data["descripcion"]
    assert data["duracion"] == test_servicio_data["duracion"]
    assert data["precio"] == test_servicio_data["precio"]
    assert data["estado"] == ServiceStatus.ACTIVE

def test_get_service_not_found(client: TestClient):
    """Tests retrieving a service that does not exist."""
    response = client.get("/api/v1/services/999")
    assert response.status_code == 404

def test_update_service(client: TestClient, test_service_data):
    """Tests updating a service via the API."""
    # Create a service
    create_response = client.post("/api/v1/services", json=test_service_data)
    service_id = create_response.json()["id"]
    
    # Update the service
    update_data = {        
        "name": "Updated Service",
        "description": "Updated description",
        "duration": 120,
        "price": 150.0
    }
    response = client.put(f"/api/v1/services/{service_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["duration"] == update_data["duration"]
    assert data["price"] == update_data["price"]
    assert data["estado"] == ServiceStatus.ACTIVE

def test_update_service_not_found(client: TestClient):
    """Tests updating a service that does not exist."""
    update_data = {
        "name": "Updated Service",
        "description": "Updated description",
        "duration": 120,
        "price": 150.0
    }
    response = client.put("/api/v1/services/999", json=update_data)
    assert response.status_code == 404

def test_update_service_duplicate_name(client: TestClient, test_service_data):
    """Tests updating a service with a duplicate name."""
    # Create two services
    service1_response = client.post("/api/v1/services", json=test_service_data)
    service1_id = service1_response.json()["id"]
    
    service2_data = test_service_data.copy()
    service2_data["name"] = "Another Service"
    service2_response = client.post("/api/v1/services", json=service2_data)
    service2_id = service2_response.json()["id"]
    
    # Attempt to update the second service with the name of the first one
    update_data = {"name": test_service_data["nombre"]}
    response = client.put(f"/api/v1/services/{service2_id}", json=update_data)
    assert response.status_code == 400
    assert "name" in response.json()["detail"].lower()

def test_delete_service(client: TestClient, test_service_data):
    """Tests deleting a service via the API."""
    # Create a service
    create_response = client.post("/api/v1/services", json=test_service_data)
    service_id = create_response.json()["id"]
    
    # Delete the service
    response = client.delete(f"/api/v1/services/{service_id}")
    assert response.status_code == 204
    
    # Verify that the service was deleted
    get_response = client.get(f"/api/v1/services/{service_id}")
    assert get_response.status_code == 404

def test_delete_service_not_found(client: TestClient):
    """Tests deleting a service that does not exist."""
    response = client.delete("/api/v1/services/999")
    assert response.status_code == 404

def test_get_services(client: TestClient, test_service_data):
    """Tests retrieving the list of services via the API."""
    # Create multiple services
    for i in range(3):
        service_data = test_service_data.copy()
        service_data["name"] = f"Service {i+1}"
        client.post("/api/v1/services", json=service_data)
    
    # Retrieve the list of services
    response = client.get("/api/v1/services")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 3
    assert all("id" in servicio for servicio in data)
    assert all("name" in service for service in data)
    assert all("descripcion" in servicio for servicio in data)
    assert all("duracion" in servicio for servicio in data)
    assert all("precio" in servicio for servicio in data)
    assert all("estado" in servicio for servicio in data)

def test_activar_servicio(client: TestClient, test_servicio_data):
    """Tests activating a service via the API."""
    # Create a service
    create_response = client.post("/api/v1/services", json=test_servicio_data)
    service_id = create_response.json()["id"]
    
    # Deactivate the service
    client.put(f"/api/v1/services/{service_id}/deactivate")
    
    # Activate the service
    response = client.put(f"/api/v1/services/{service_id}/activate")
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == ServiceStatus.ACTIVE

def test_desactivar_servicio(client: TestClient, test_servicio_data):
    """Tests deactivating a service via the API."""
    # Create a service
    create_response = client.post("/api/v1/services", json=test_service_data)
    service_id = create_response.json()["id"]
    
    # Deactivate the service
    response = client.put(f"/api/v1/services/{service_id}/deactivate")
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == ServiceStatus.INACTIVE

def test_activar_servicio_not_found(client: TestClient):
    """Tests activating a service that does not exist."""
    response = client.put("/api/v1/services/999/activate")
    assert response.status_code == 404

def test_desactivar_servicio_not_found(client: TestClient):
    """Tests deactivating a service that does not exist."""
    response = client.put("/api/v1/services/999/deactivate")
    assert response.status_code == 404 