"""
Pruebas de integración para los endpoints de usuarios
"""
import pytest
from fastapi.testclient import TestClient
from app.models.rol_usuario import RolUsuario
from app.models.permiso import Permiso

def test_create_usuario(client: TestClient, test_user_data):
    """Prueba la creación de un usuario a través de la API"""
    response = client.post("/api/v1/usuarios", json=test_user_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["email"] == test_user_data["email"]
    assert data["nombre"] == test_user_data["nombre"]
    assert data["apellido"] == test_user_data["apellido"]
    assert data["telefono"] == test_user_data["telefono"]
    assert "id" in data
    assert "password" not in data

def test_create_usuario_duplicate_email(client: TestClient, test_user_data):
    """Prueba la creación de un usuario con email duplicado"""
    # Crear primer usuario
    client.post("/api/v1/usuarios", json=test_user_data)
    
    # Intentar crear segundo usuario con el mismo email
    response = client.post("/api/v1/usuarios", json=test_user_data)
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()

def test_get_usuario(client: TestClient, test_user_data):
    """Prueba la obtención de un usuario a través de la API"""
    # Crear usuario
    create_response = client.post("/api/v1/usuarios", json=test_user_data)
    user_id = create_response.json()["id"]
    
    # Obtener usuario
    response = client.get(f"/api/v1/usuarios/{user_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == user_id
    assert data["email"] == test_user_data["email"]
    assert data["nombre"] == test_user_data["nombre"]
    assert data["apellido"] == test_user_data["apellido"]
    assert data["telefono"] == test_user_data["telefono"]
    assert "password" not in data

def test_get_usuario_not_found(client: TestClient):
    """Prueba la obtención de un usuario que no existe"""
    response = client.get("/api/v1/usuarios/999")
    assert response.status_code == 404

def test_update_usuario(client: TestClient, test_user_data):
    """Prueba la actualización de un usuario a través de la API"""
    # Crear usuario
    create_response = client.post("/api/v1/usuarios", json=test_user_data)
    user_id = create_response.json()["id"]
    
    # Actualizar usuario
    update_data = {
        "nombre": "Nombre Actualizado",
        "apellido": "Apellido Actualizado",
        "telefono": "1234567890"
    }
    response = client.put(f"/api/v1/usuarios/{user_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["nombre"] == update_data["nombre"]
    assert data["apellido"] == update_data["apellido"]
    assert data["telefono"] == update_data["telefono"]
    assert data["email"] == test_user_data["email"]
    assert "password" not in data

def test_update_usuario_not_found(client: TestClient):
    """Prueba la actualización de un usuario que no existe"""
    update_data = {
        "nombre": "Nombre Actualizado",
        "apellido": "Apellido Actualizado",
        "telefono": "1234567890"
    }
    response = client.put("/api/v1/usuarios/999", json=update_data)
    assert response.status_code == 404

def test_update_usuario_duplicate_email(client: TestClient, test_user_data):
    """Prueba la actualización de un usuario con email duplicado"""
    # Crear dos usuarios
    user1_response = client.post("/api/v1/usuarios", json=test_user_data)
    user1_id = user1_response.json()["id"]
    
    user2_data = test_user_data.copy()
    user2_data["email"] = "otro@email.com"
    user2_response = client.post("/api/v1/usuarios", json=user2_data)
    user2_id = user2_response.json()["id"]
    
    # Intentar actualizar el segundo usuario con el email del primero
    update_data = {"email": test_user_data["email"]}
    response = client.put(f"/api/v1/usuarios/{user2_id}", json=update_data)
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()

def test_delete_usuario(client: TestClient, test_user_data):
    """Prueba la eliminación de un usuario a través de la API"""
    # Crear usuario
    create_response = client.post("/api/v1/usuarios", json=test_user_data)
    user_id = create_response.json()["id"]
    
    # Eliminar usuario
    response = client.delete(f"/api/v1/usuarios/{user_id}")
    assert response.status_code == 204
    
    # Verificar que el usuario fue eliminado
    get_response = client.get(f"/api/v1/usuarios/{user_id}")
    assert get_response.status_code == 404

def test_delete_usuario_not_found(client: TestClient):
    """Prueba la eliminación de un usuario que no existe"""
    response = client.delete("/api/v1/usuarios/999")
    assert response.status_code == 404

def test_get_usuarios(client: TestClient, test_user_data):
    """Prueba la obtención de la lista de usuarios a través de la API"""
    # Crear varios usuarios
    for i in range(3):
        user_data = test_user_data.copy()
        user_data["email"] = f"usuario{i+1}@email.com"
        client.post("/api/v1/usuarios", json=user_data)
    
    # Obtener lista de usuarios
    response = client.get("/api/v1/usuarios")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 3
    assert all("id" in user for user in data)
    assert all("email" in user for user in data)
    assert all("nombre" in user for user in data)
    assert all("apellido" in user for user in data)
    assert all("telefono" in user for user in data)
    assert all("password" not in user for user in data)

def test_get_usuarios_por_rol(client: TestClient, test_user_data, test_rol_data):
    """Prueba la obtención de usuarios por rol a través de la API"""
    # Crear rol
    rol_response = client.post("/api/v1/roles", json=test_rol_data)
    rol_id = rol_response.json()["id"]
    
    # Crear varios usuarios y asignarles el rol
    for i in range(3):
        user_data = test_user_data.copy()
        user_data["email"] = f"usuario{i+1}@email.com"
        user_response = client.post("/api/v1/usuarios", json=user_data)
        user_id = user_response.json()["id"]
        client.put(f"/api/v1/usuarios/{user_id}/rol/{rol_id}")
    
    # Obtener usuarios por rol
    response = client.get(f"/api/v1/roles/{rol_id}/usuarios")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 3
    assert all("id" in user for user in data)
    assert all("email" in user for user in data)
    assert all("nombre" in user for user in data)
    assert all("apellido" in user for user in data)
    assert all("telefono" in user for user in data)
    assert all("password" not in user for user in data)

def test_get_usuarios_por_rol_not_found(client: TestClient):
    """Prueba la obtención de usuarios por un rol que no existe"""
    response = client.get("/api/v1/roles/999/usuarios")
    assert response.status_code == 404

def test_activar_usuario(client: TestClient, test_user_data):
    """Prueba la activación de un usuario a través de la API"""
    # Crear usuario
    create_response = client.post("/api/v1/usuarios", json=test_user_data)
    user_id = create_response.json()["id"]
    
    # Desactivar usuario
    client.put(f"/api/v1/usuarios/{user_id}/desactivar")
    
    # Activar usuario
    response = client.put(f"/api/v1/usuarios/{user_id}/activar")
    assert response.status_code == 200
    data = response.json()
    
    assert data["activo"] is True

def test_desactivar_usuario(client: TestClient, test_user_data):
    """Prueba la desactivación de un usuario a través de la API"""
    # Crear usuario
    create_response = client.post("/api/v1/usuarios", json=test_user_data)
    user_id = create_response.json()["id"]
    
    # Desactivar usuario
    response = client.put(f"/api/v1/usuarios/{user_id}/desactivar")
    assert response.status_code == 200
    data = response.json()
    
    assert data["activo"] is False

def test_activar_usuario_not_found(client: TestClient):
    """Prueba la activación de un usuario que no existe"""
    response = client.put("/api/v1/usuarios/999/activar")
    assert response.status_code == 404

def test_desactivar_usuario_not_found(client: TestClient):
    """Prueba la desactivación de un usuario que no existe"""
    response = client.put("/api/v1/usuarios/999/desactivar")
    assert response.status_code == 404 