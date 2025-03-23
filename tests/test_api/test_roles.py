"""
Pruebas de integración para los endpoints de roles y permisos
"""
import pytest
from fastapi.testclient import TestClient
from app.models.rol_usuario import RolUsuario
from app.models.permiso import Permiso

def test_create_rol(client: TestClient, test_rol_data):
    """Prueba la creación de un rol a través de la API"""
    response = client.post("/api/v1/roles", json=test_rol_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["nombre"] == test_rol_data["nombre"]
    assert data["descripcion"] == test_rol_data["descripcion"]
    assert data["permisos"] == test_rol_data["permisos"]
    assert "id" in data

def test_create_rol_duplicate_name(client: TestClient, test_rol_data):
    """Prueba la creación de un rol con nombre duplicado"""
    # Crear primer rol
    client.post("/api/v1/roles", json=test_rol_data)
    
    # Intentar crear segundo rol con el mismo nombre
    response = client.post("/api/v1/roles", json=test_rol_data)
    assert response.status_code == 400
    assert "nombre" in response.json()["detail"].lower()

def test_get_rol(client: TestClient, test_rol_data):
    """Prueba la obtención de un rol a través de la API"""
    # Crear rol
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

def test_get_rol_not_found(client: TestClient):
    """Prueba la obtención de un rol que no existe"""
    response = client.get("/api/v1/roles/999")
    assert response.status_code == 404

def test_update_rol(client: TestClient, test_rol_data):
    """Prueba la actualización de un rol a través de la API"""
    # Crear rol
    create_response = client.post("/api/v1/roles", json=test_rol_data)
    rol_id = create_response.json()["id"]
    
    # Actualizar rol
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

def test_update_rol_not_found(client: TestClient):
    """Prueba la actualización de un rol que no existe"""
    update_data = {
        "nombre": "Rol Actualizado",
        "descripcion": "Descripción actualizada",
        "permisos": [Permiso.ADMIN]
    }
    response = client.put("/api/v1/roles/999", json=update_data)
    assert response.status_code == 404

def test_update_rol_duplicate_name(client: TestClient, test_rol_data):
    """Prueba la actualización de un rol con nombre duplicado"""
    # Crear dos roles
    rol1_response = client.post("/api/v1/roles", json=test_rol_data)
    rol1_id = rol1_response.json()["id"]
    
    rol2_data = test_rol_data.copy()
    rol2_data["nombre"] = "Otro Rol"
    rol2_response = client.post("/api/v1/roles", json=rol2_data)
    rol2_id = rol2_response.json()["id"]
    
    # Intentar actualizar el segundo rol con el nombre del primero
    update_data = {"nombre": test_rol_data["nombre"]}
    response = client.put(f"/api/v1/roles/{rol2_id}", json=update_data)
    assert response.status_code == 400
    assert "nombre" in response.json()["detail"].lower()

def test_delete_rol(client: TestClient, test_rol_data):
    """Prueba la eliminación de un rol a través de la API"""
    # Crear rol
    create_response = client.post("/api/v1/roles", json=test_rol_data)
    rol_id = create_response.json()["id"]
    
    # Eliminar rol
    response = client.delete(f"/api/v1/roles/{rol_id}")
    assert response.status_code == 204
    
    # Verificar que el rol fue eliminado
    get_response = client.get(f"/api/v1/roles/{rol_id}")
    assert get_response.status_code == 404

def test_delete_rol_not_found(client: TestClient):
    """Prueba la eliminación de un rol que no existe"""
    response = client.delete("/api/v1/roles/999")
    assert response.status_code == 404

def test_get_roles(client: TestClient, test_rol_data):
    """Prueba la obtención de la lista de roles a través de la API"""
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

def test_asignar_rol_usuario(client: TestClient, test_user_data, test_rol_data):
    """Prueba la asignación de un rol a un usuario a través de la API"""
    # Crear usuario
    user_response = client.post("/api/v1/auth/register", json=test_user_data)
    user_id = user_response.json()["id"]
    
    # Crear rol
    rol_response = client.post("/api/v1/roles", json=test_rol_data)
    rol_id = rol_response.json()["id"]
    
    # Asignar rol al usuario
    response = client.put(f"/api/v1/usuarios/{user_id}/rol/{rol_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["rol_id"] == rol_id
    assert data["usuario_id"] == user_id

def test_asignar_rol_usuario_not_found(client: TestClient, test_rol_data):
    """Prueba la asignación de un rol a un usuario que no existe"""
    # Crear rol
    rol_response = client.post("/api/v1/roles", json=test_rol_data)
    rol_id = rol_response.json()["id"]
    
    # Intentar asignar rol a usuario inexistente
    response = client.put(f"/api/v1/usuarios/999/rol/{rol_id}")
    assert response.status_code == 404
    assert "usuario" in response.json()["detail"].lower()

def test_asignar_rol_not_found(client: TestClient, test_user_data):
    """Prueba la asignación de un rol que no existe a un usuario"""
    # Crear usuario
    user_response = client.post("/api/v1/auth/register", json=test_user_data)
    user_id = user_response.json()["id"]
    
    # Intentar asignar rol inexistente
    response = client.put(f"/api/v1/usuarios/{user_id}/rol/999")
    assert response.status_code == 404
    assert "rol" in response.json()["detail"].lower()

def test_verificar_permiso_usuario(client: TestClient, test_user_data, test_rol_data):
    """Prueba la verificación de permisos de un usuario a través de la API"""
    # Crear usuario
    user_response = client.post("/api/v1/auth/register", json=test_user_data)
    user_id = user_response.json()["id"]
    
    # Crear rol con permisos específicos
    rol_data = test_rol_data.copy()
    rol_data["permisos"] = [Permiso.ADMIN]
    rol_response = client.post("/api/v1/roles", json=rol_data)
    rol_id = rol_response.json()["id"]
    
    # Asignar rol al usuario
    client.put(f"/api/v1/usuarios/{user_id}/rol/{rol_id}")
    
    # Verificar permiso
    response = client.get(f"/api/v1/usuarios/{user_id}/permisos/{Permiso.ADMIN}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["tiene_permiso"] is True
    assert data["permiso"] == Permiso.ADMIN
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