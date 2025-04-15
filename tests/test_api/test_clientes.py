"""
Integration tests for the client endpoints
"""
from fastapi.testclient import TestClient

from app.models.client import ClientStatus


def test_create_client(client: TestClient, test_client_data):
    """Tests the creation of a client through the API"""
    response = client.post("/api/v1/clients", json=test_client_data)
    assert response.status_code == 200
    data = response.json()

    assert data["email"] == test_client_data["email"]
    assert data["name"] == test_client_data["name"]
    assert data["surname"] == test_client_data["surname"]
    assert data["phone"] == test_client_data["phone"]
    assert data["address"] == test_client_data["address"]
    assert data["status"] == ClientStatus.ACTIVE
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_client_duplicate_email(client: TestClient, test_client_data):
    """Tests the creation of a client with a duplicate email"""
    # Create first client
    client.post("/api/v1/clients", json=test_client_data)

    # Attempt to create a second client with the same email
    response = client.post("/api/v1/clients", json=test_client_data)
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_get_client(client: TestClient, test_client_data):
    """Tests retrieving a client through the API"""
    # Create client
    create_response = client.post("/api/v1/clients", json=test_client_data)
    client_id = create_response.json()["id"]

    # Get client
    response = client.get(f"/api/v1/clients/{client_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == client_id
    assert data["email"] == test_client_data["email"]
    assert data["name"] == test_client_data["name"]
    assert data["surname"] == test_client_data["surname"]
    assert data["phone"] == test_client_data["phone"]
    assert data["address"] == test_client_data["address"]
    assert data["status"] == ClientStatus.ACTIVE
    assert "created_at" in data
    assert "updated_at" in data


def test_get_client_not_found(client: TestClient):
    """Tests retrieving a client that does not exist"""
    response = client.get("/api/v1/clients/999")
    assert response.status_code == 404


def test_update_client(client: TestClient, test_client_data):
    """Tests updating a client through the API"""
    # Create client
    create_response = client.post("/api/v1/clients", json=test_client_data)
    client_id = create_response.json()["id"]

    # Update client
    update_data = {
        "name": "Updated Name",
        "surname": "Updated Surname",
        "phone": "1234567890",
        "address": "New address",
    }
    response = client.put(f"/api/v1/clients/{client_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == update_data["name"]
    assert data["surname"] == update_data["surname"]
    assert data["phone"] == update_data["phone"]
    assert data["address"] == update_data["address"]
    assert data["email"] == test_client_data["email"]
    assert data["status"] == ClientStatus.ACTIVE
    assert "updated_at" in data


def test_update_client_not_found(client: TestClient):
    """Tests updating a client that does not exist"""
    update_data = {
        "name": "Updated Name",
        "surname": "Updated Surname",
        "phone": "1234567890",
        "address": "New address",
    }
    response = client.put("/api/v1/clients/999", json=update_data)
    assert response.status_code == 404


def test_update_client_duplicate_email(client: TestClient, test_client_data):
    """Tests updating a client with a duplicate email"""
    # Create two clients
    client1_response = client.post("/api/v1/clients", json=test_client_data)
    client1_id = client1_response.json()["id"]

    client2_data = test_client_data.copy()
    client2_data["email"] = "another@email.com"
    client2_response = client.post("/api/v1/clients", json=client2_data)
    client2_id = client2_response.json()["id"]

    # Attempt to update the second client with the email of the first
    update_data = {"email": test_client_data["email"]}
    response = client.put(f"/api/v1/clients/{client2_id}", json=update_data)
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_delete_client(client: TestClient, test_client_data):
    """Tests deleting a client through the API"""
    # Create client
    create_response = client.post("/api/v1/clients", json=test_client_data)
    client_id = create_response.json()["id"]

    # Delete client
    response = client.delete(f"/api/v1/clients/{client_id}")
    assert response.status_code == 204

    # Verify that the client was deleted
    get_response = client.get(f"/api/v1/clients/{client_id}")
    assert get_response.status_code == 404


def test_delete_client_not_found(client: TestClient):
    """Tests deleting a client that does not exist"""
    response = client.delete("/api/v1/clients/999")
    assert response.status_code == 404


def test_get_clients(client: TestClient, test_client_data):
    """Tests retrieving the list of clients through the API"""
    # Create multiple clients
    for i in range(3):
        client_data = test_client_data.copy()
        client_data["email"] = f"client{i+1}@email.com"
        client.post("/api/v1/clients", json=client_data)

    # Get list of clients
    response = client.get("/api/v1/clients")
    assert response.status_code == 200
    data = response.json()

    assert len(data) >= 3
    assert all("id" in client_data for client_data in data)
    assert all("email" in client_data for client_data in data)
    assert all("name" in client_data for client_data in data)
    assert all("surname" in client_data for client_data in data)
    assert all("phone" in client_data for client_data in data)
    assert all("address" in client_data for client_data in data)
    assert all("status" in client_data for client_data in data)
    assert all("created_at" in client_data for client_data in data)
    assert all("updated_at" in client_data for client_data in data)


def test_activate_client(client: TestClient, test_client_data):
    """Tests activating a client through the API"""
    # Create client
    create_response = client.post("/api/v1/clients", json=test_client_data)
    client_id = create_response.json()["id"]

    # Deactivate client
    client.put(f"/api/v1/clients/{client_id}/deactivate")

    # Activate client
    response = client.put(f"/api/v1/clients/{client_id}/activate")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == ClientStatus.ACTIVE


def test_deactivate_client(client: TestClient, test_client_data):
    """Tests deactivating a client through the API"""
    # Create client
    create_response = client.post("/api/v1/clients", json=test_client_data)
    client_id = create_response.json()["id"]

    # Deactivate client
    response = client.put(f"/api/v1/clients/{client_id}/deactivate")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == ClientStatus.INACTIVE


def test_activate_client_not_found(client: TestClient):
    """Tests activating a client that does not exist"""
    response = client.put("/api/v1/clients/999/activate")
    assert response.status_code == 404


def test_deactivate_client_not_found(client: TestClient):
    """Tests deactivating a client that does not exist"""
    response = client.put("/api/v1/clients/999/deactivate")
    assert response.status_code == 404


def test_search_clients(client: TestClient, test_client_data):
    """Tests searching for clients through the API"""
    # Create multiple clients
    for i in range(3):
        client_data = test_client_data.copy()
        client_data["email"] = f"client{i+1}@email.com"
        client_data["name"] = f"Name{i+1}"
        client_data["surname"] = f"Surname{i+1}"
        client.post("/api/v1/clients", json=client_data)

    # Search clients by name
    response = client.get("/api/v1/clients/search?name=Name1")
    assert response.status_code == 200
    data = response.json()

    assert len(data) > 0
    assert all("name" in client_data for client_data in data)
    assert any(client_data["name"] == "Name1" for client_data in data)

    # Search clients by surname
    response = client.get("/api/v1/clients/search?surname=Surname2")
    assert response.status_code == 200
    data = response.json()

    assert len(data) > 0
    assert all("surname" in client_data for client_data in data)
    assert any(client_data["surname"] == "Surname2" for client_data in data)

    # Search clients by email
    response = client.get("/api/v1/clients/search?email=client3@email.com")
    assert response.status_code == 200
    data = response.json()

    assert len(data) > 0
    assert all("email" in client_data for client_data in data)
    assert any(client_data["email"] == "client3@email.com" for client_data in data)