"""
Pruebas de integración para los endpoints de autenticación y autorización
"""
import pytest
from fastapi.testclient import TestClient
from app.models.rol_usuario import RolUsuario
from app.core.security import create_access_token

def test_register_user(client: TestClient, test_user_data):
    """Prueba el registro de un nuevo usuario a través de la API"""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["email"] == test_user_data["email"]
    assert data["nombre"] == test_user_data["nombre"]
    assert data["rol"] == RolUsuario.ADMIN
    assert "id" in data
    assert "password" not in data  # Verificar que la contraseña no se devuelve

def test_register_user_duplicate_email(client: TestClient, test_user_data):
    """Prueba el registro de un usuario con email duplicado"""
    # Registrar primer usuario
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Intentar registrar segundo usuario con el mismo email
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()

def test_login_user(client: TestClient, test_user_data):
    """Prueba el inicio de sesión de un usuario a través de la API"""
    # Registrar usuario
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Iniciar sesión
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["rol"] == RolUsuario.ADMIN

def test_login_user_invalid_credentials(client: TestClient, test_user_data):
    """Prueba el inicio de sesión con credenciales inválidas"""
    # Registrar usuario
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Intentar iniciar sesión con contraseña incorrecta
    login_data = {
        "username": test_user_data["email"],
        "password": "contraseña_incorrecta"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()

def test_login_user_not_found(client: TestClient):
    """Prueba el inicio de sesión de un usuario que no existe"""
    login_data = {
        "username": "usuario_no_existente@example.com",
        "password": "contraseña"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()

def test_get_current_user(client: TestClient, test_user_data):
    """Prueba la obtención del usuario actual a través de la API"""
    # Registrar usuario
    register_response = client.post("/api/v1/auth/register", json=test_user_data)
    user_id = register_response.json()["id"]
    
    # Iniciar sesión
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Obtener usuario actual
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == user_id
    assert data["email"] == test_user_data["email"]
    assert data["nombre"] == test_user_data["nombre"]
    assert data["rol"] == RolUsuario.ADMIN

def test_get_current_user_invalid_token(client: TestClient):
    """Prueba la obtención del usuario actual con token inválido"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer token_invalido"}
    )
    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()

def test_get_current_user_no_token(client: TestClient):
    """Prueba la obtención del usuario actual sin token"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()

def test_change_password(client: TestClient, test_user_data):
    """Prueba el cambio de contraseña a través de la API"""
    # Registrar usuario
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Iniciar sesión
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Cambiar contraseña
    password_data = {
        "current_password": test_user_data["password"],
        "new_password": "nueva_contraseña123"
    }
    response = client.put(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json=password_data
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Contraseña actualizada exitosamente"
    
    # Verificar que se puede iniciar sesión con la nueva contraseña
    new_login_data = {
        "username": test_user_data["email"],
        "password": "nueva_contraseña123"
    }
    login_response = client.post("/api/v1/auth/login", data=new_login_data)
    assert login_response.status_code == 200

def test_change_password_invalid_current(client: TestClient, test_user_data):
    """Prueba el cambio de contraseña con contraseña actual incorrecta"""
    # Registrar usuario
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Iniciar sesión
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Intentar cambiar contraseña con contraseña actual incorrecta
    password_data = {
        "current_password": "contraseña_incorrecta",
        "new_password": "nueva_contraseña123"
    }
    response = client.put(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json=password_data
    )
    assert response.status_code == 400
    assert "current_password" in response.json()["detail"].lower()

def test_reset_password_request(client: TestClient, test_user_data):
    """Prueba la solicitud de recuperación de contraseña a través de la API"""
    # Registrar usuario
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Solicitar recuperación de contraseña
    reset_data = {"email": test_user_data["email"]}
    response = client.post("/api/v1/auth/reset-password-request", json=reset_data)
    assert response.status_code == 200
    assert "message" in response.json()

def test_reset_password_request_user_not_found(client: TestClient):
    """Prueba la solicitud de recuperación de contraseña para un usuario que no existe"""
    reset_data = {"email": "usuario_no_existente@example.com"}
    response = client.post("/api/v1/auth/reset-password-request", json=reset_data)
    assert response.status_code == 404
    assert "email" in response.json()["detail"].lower()

def test_reset_password(client: TestClient, test_user_data):
    """Prueba la recuperación de contraseña a través de la API"""
    # Registrar usuario
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Generar token de recuperación
    token = create_access_token({"sub": test_user_data["email"]})
    
    # Recuperar contraseña
    reset_data = {
        "token": token,
        "new_password": "nueva_contraseña123"
    }
    response = client.post("/api/v1/auth/reset-password", json=reset_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Contraseña actualizada exitosamente"
    
    # Verificar que se puede iniciar sesión con la nueva contraseña
    login_data = {
        "username": test_user_data["email"],
        "password": "nueva_contraseña123"
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200

def test_reset_password_invalid_token(client: TestClient):
    """Prueba la recuperación de contraseña con token inválido"""
    reset_data = {
        "token": "token_invalido",
        "new_password": "nueva_contraseña123"
    }
    response = client.post("/api/v1/auth/reset-password", json=reset_data)
    assert response.status_code == 400
    assert "token" in response.json()["detail"].lower()

def test_verify_token(client: TestClient, test_user_data):
    """Prueba la verificación de token a través de la API"""
    # Registrar usuario
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Iniciar sesión
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Verificar token
    response = client.get(
        "/api/v1/auth/verify-token",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["valid"] is True
    assert data["email"] == test_user_data["email"]
    assert data["rol"] == RolUsuario.ADMIN

def test_verify_token_invalid(client: TestClient):
    """Prueba la verificación de token inválido"""
    response = client.get(
        "/api/v1/auth/verify-token",
        headers={"Authorization": "Bearer token_invalido"}
    )
    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower() 