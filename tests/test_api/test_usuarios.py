"""
Integration tests for user endpoints
"""
from fastapi.testclient import TestClient


def test_create_user(client: TestClient, test_user_data):
    """Tests the creation of a user through the API"""
    response = client.post("/api/v1/users", json=test_user_data)
    assert response.status_code == 200
    data = response.json()

    assert data["email"] == test_user_data["email"]
    assert data["name"] == test_user_data["name"]
    assert data["surname"] == test_user_data["surname"]
    assert data["phone"] == test_user_data["phone"]
    assert "id" in data
    assert "password" not in data


def test_create_user_duplicate_email(client: TestClient, test_user_data):
    """Tests the creation of a user with a duplicate email"""
    # Create the first user
    client.post("/api/v1/users", json=test_user_data)

    # Attempt to create a second user with the same email
    response = client.post("/api/v1/users", json=test_user_data)
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_get_user(client: TestClient, test_user_data):
    """Tests retrieving a user through the API"""
    # Create a user
    create_response = client.post("/api/v1/users", json=test_user_data)
    user_id = create_response.json()["id"]

    # Retrieve the user
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == user_id
    assert data["email"] == test_user_data["email"]
    assert data["name"] == test_user_data["name"]
    assert data["surname"] == test_user_data["surname"]
    assert data["phone"] == test_user_data["phone"]
    assert "password" not in data


def test_get_user_not_found(client: TestClient):
    """Tests retrieving a user that does not exist"""
    response = client.get("/api/v1/users/999")
    assert response.status_code == 404


def test_update_user(client: TestClient, test_user_data):
    """Tests updating a user through the API"""
    # Create a user
    create_response = client.post("/api/v1/users", json=test_user_data)
    user_id = create_response.json()["id"]

    # Update the user
    update_data = {
        "name": "Updated Name",
        "surname": "Updated Surname",
        "phone": "1234567890"
    }
    response = client.put(f"/api/v1/users/{user_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == update_data["name"]
    assert data["surname"] == update_data["surname"]
    assert data["phone"] == update_data["phone"]
    assert data["email"] == test_user_data["email"]
    assert "password" not in data


def test_update_user_not_found(client: TestClient):
    """Tests updating a user that does not exist"""
    update_data = {
        "name": "Updated Name",
        "surname": "Updated Surname",
        "phone": "1234567890"
    }
    response = client.put("/api/v1/users/999", json=update_data)
    assert response.status_code == 404


def test_update_user_duplicate_email(client: TestClient, test_user_data):
    """Tests updating a user with a duplicate email"""
    # Create two users
    user1_response = client.post("/api/v1/users", json=test_user_data)
    user1_id = user1_response.json()["id"]

    user2_data = test_user_data.copy()
    user2_data["email"] = "otro@email.com"
    user2_response = client.post("/api/v1/users", json=user2_data)
    user2_id = user2_response.json()["id"]

    # Attempt to update the second user with the first user's email
    update_data = {"email": test_user_data["email"]}
    response = client.put(f"/api/v1/users/{user2_id}", json=update_data)
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_delete_user(client: TestClient, test_user_data):
    """Tests deleting a user through the API"""
    # Create a user
    create_response = client.post("/api/v1/users", json=test_user_data)
    user_id = create_response.json()["id"]

    # Delete the user
    response = client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 204

    # Verify that the user was deleted
    get_response = client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 404


def test_delete_user_not_found(client: TestClient):
    """Tests deleting a user that does not exist"""
    response = client.delete("/api/v1/users/999")
    assert response.status_code == 404


def test_get_users(client: TestClient, test_user_data):
    """Tests retrieving the list of users through the API"""
    # Create several users
    for i in range(3):
        user_data = test_user_data.copy()
        user_data["email"] = f"user{i+1}@email.com"
        client.post("/api/v1/users", json=user_data)

    # Retrieve the list of users
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    data = response.json()

    assert len(data) >= 3
    assert all("id" in user for user in data)
    assert all("email" in user for user in data)
    assert all("name" in user for user in data)
    assert all("surname" in user for user in data)
    assert all("phone" in user for user in data)
    assert all("password" not in user for user in data)

