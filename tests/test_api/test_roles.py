"""
Integration tests for the roles and permissions endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.models.role_user import RoleUser
from app.models.permission import Permission

def test_create_role(client: TestClient, test_role_data):
    """Tests the creation of a role via the API"""
    response = client.post("/api/v1/roles", json=test_role_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["nombre"] == test_rol_data["nombre"]
    assert data["descripcion"] == test_rol_data["descripcion"]
    assert data["permisos"] == test_rol_data["permisos"]
    assert "id" in data

def test_create_role_duplicate_name(client: TestClient, test_role_data):
    """Tests the creation of a role with a duplicate name"""
    # Create first role
    client.post("/api/v1/roles", json=test_role_data)
    
    # Attempt to create a second role with the same name
    response = client.post("/api/v1/roles", json=test_role_data)
    assert response.status_code == 400
    assert "nombre" in response.json()["detail"].lower()

def test_get_rol(client: TestClient, test_rol_data):
    """Prueba la obtención de un rol a través de la API"""
    # Create role
    create_response = client.post("/api/v1/roles", json=test_rol_data)
    rol_id = create_response.json()["id"]
    
    # Obtener rol
    response = client.get(f"/api/v1/roles/{rol_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == rol_id
    assert data["nombre"] == test_rol_data["nombre"]
    assert data["descripcion"] == test_rol_data["descripcion"]
    assert data["permisos"] == test_rol_data["permisos"]

def test_get_role_not_found(client: TestClient):
    """Tests getting a role that does not exist"""
    response = client.get("/api/v1/roles/999")
    assert response.status_code == 404

def test_update_rol(client: TestClient, test_rol_data):
    """Tests updating a role via the API"""
    # Create role
    create_response = client.post("/api/v1/roles", json=test_rol_data)
    rol_id = create_response.json()["id"]
    
    # Update role
    update_data = {
        "nombre": "Rol Actualizado",
        "descripcion": "Descripción actualizada",
        "permisos": [Permiso.ADMIN]
    }
    response = client.put(f"/api/v1/roles/{rol_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["nombre"] == update_data["nombre"]
    assert data["descripcion"] == update_data["descripcion"]
    assert data["permisos"] == update_data["permisos"]

def test_update_role_not_found(client: TestClient):
    """Tests updating a role that does not exist"""
    update_data = {
        "nombre": "Rol Actualizado",
        "descripcion": "Updated description",
        "permisos": [Permiso.ADMIN]
    }
    response = client.put("/api/v1/roles/999", json=update_data)
    assert response.status_code == 404

def test_update_rol_duplicate_name(client: TestClient, test_rol_data):
    """Prueba la actualización de un rol con nombre duplicado"""
    # Create two roles
    rol1_response = client.post("/api/v1/roles", json=test_rol_data)
    rol1_id = rol1_response.json()["id"]
    
    rol2_data = test_rol_data.copy()
    rol2_data["nombre"] = "Another Role"
    rol2_response = client.post("/api/v1/roles", json=rol2_data)
    rol2_id = rol2_response.json()["id"]
    
    # Attempt to update the second role with the name of the first
    update_data = {"nombre": test_rol_data["nombre"]}
    response = client.put(f"/api/v1/roles/{rol2_id}", json=update_data)
    assert response.status_code == 400
    assert "nombre" in response.json()["detail"].lower()

def test_delete_rol(client: TestClient, test_rol_data):
    """Prueba la eliminación de un rol a través de la API"""
    # Create role
    create_response = client.post("/api/v1/roles", json=test_rol_data)
    rol_id = create_response.json()["id"]
    
    # Delete role
    response = client.delete(f"/api/v1/roles/{rol_id}")
    assert response.status_code == 204
    
    # Verify that the role was deleted
    get_response = client.get(f"/api/v1/roles/{rol_id}")
    assert get_response.status_code == 404

def test_delete_rol_not_found(client: TestClient):
    """Prueba la eliminación de un rol que no existe"""
    response = client.delete("/api/v1/roles/999")
    assert response.status_code == 404

def test_get_roles(client: TestClient, test_rol_data):
    """Tests getting the list of roles via the API"""
    # Crear varios roles
    for i in range(3):
        rol_data = test_rol_data.copy()
        rol_data["nombre"] = f"Rol {i+1}"
        client.post("/api/v1/roles", json=rol_data)
    
    # Obtener lista de roles
    response = client.get("/api/v1/roles")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 3
    assert all("id" in rol for rol in data)
    assert all("nombre" in rol for rol in data)
    assert all("descripcion" in rol for rol in data)
    assert all("permisos" in rol for rol in data)

def test_assign_role_to_user(client: TestClient, test_user_data, test_role_data):
    """Tests assigning a role to a user via the API"""
    # Create user
    user_response = client.post("/api/v1/auth/register", json=test_user_data)
    user_id = user_response.json()["id"]
    
    # Create role
    rol_response = client.post("/api/v1/roles", json=test_rol_data)
    rol_id = rol_response.json()["id"]
    
    # Assign role to the user
    response = client.put(f"/api/v1/usuarios/{user_id}/rol/{rol_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["rol_id"] == rol_id
    assert data["usuario_id"] == user_id

def test_assign_role_to_user_not_found(client: TestClient, test_role_data):
    """Tests assigning a role to a user that does not exist"""
    # Create role
    rol_response = client.post("/api/v1/roles", json=test_rol_data)
    rol_id = rol_response.json()["id"]
    
    # Attempt to assign role to a non-existent user
    response = client.put(f"/api/v1/usuarios/999/rol/{rol_id}")
    assert response.status_code == 404
    assert "usuario" in response.json()["detail"].lower()

def test_asignar_rol_not_found(client: TestClient, test_user_data):
    """Prueba la asignación de un rol que no existe a un usuario"""
    # Crear usuario
    user_response1 = client.post("/api/v1/auth/register", json=test_user_data)
    user_id = user_response1.json()["id"]
    
    # Intentar asignar rol inexistente
    response = client.put(f"/api/v1/usuarios/{user_id}/rol/999")
    assert response.status_code == 404
    assert "rol" in response.json()["detail"].lower()

def test_verificar_permiso_usuario(client: TestClient, test_user_data, test_rol_data):
    """Tests verifying user permissions via the API"""
    # Create user
    user_response2 = client.post("/api/v1/auth/register", json=test_user_data)
    user_id = user_response2.json()["id"]
    
    # Create role with specific permissions
    rol_data = test_rol_data.copy()
    rol_data["permisos"] = [Permission.ADMIN]
    rol_response = client.post("/api/v1/roles", json=rol_data)
    rol_id = rol_response.json()["id"]
    
    # Assign role to the user
    client.put(f"/api/v1/usuarios/{user_id}/rol/{rol_id}")
    
    # Verify permission
    response = client.get(f"/api/v1/usuarios/{user_id}/permisos/{Permission.ADMIN}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["tiene_permiso"] is True
    assert data["permiso"] == Permission.ADMIN
    assert data["usuario_id"] == user_id

def test_verificar_permiso_usuario_sin_permiso(client: TestClient, test_user_data, test_rol_data):
    """Prueba la verificación de un permiso que el usuario no tiene"""
    # Crear usuario
    user_response = client.post("/api/v1/auth/register", json=test_user_data)
    user_id = user_response.json()["id"]
    
    # Crear rol sin permisos
    rol_data = test_rol_data.copy()
    rol_data["permisos"] = []
    rol_response = client.post("/api/v1/roles", json=rol_data)
    rol_id = rol_response.json()["id"]
    
    # Asignar rol al usuario
    client.put(f"/api/v1/usuarios/{user_id}/rol/{rol_id}")
    
    # Verificar permiso
    response = client.get(f"/api/v1/usuarios/{user_id}/permisos/{Permiso.ADMIN}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["tiene_permiso"] is False
    assert data["permiso"] == Permiso.ADMIN
    assert data["usuario_id"] == user_id 