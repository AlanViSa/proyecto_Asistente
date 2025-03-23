"""
Pruebas de integración para los endpoints de clientes
"""
import pytest
from fastapi.testclient import TestClient
from app.models.estado_cliente import EstadoCliente

def test_create_cliente(client: TestClient, test_cliente_data):
    """Prueba la creación de un cliente a través de la API"""
    response = client.post("/api/v1/clientes", json=test_cliente_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["email"] == test_cliente_data["email"]
    assert data["nombre"] == test_cliente_data["nombre"]
    assert data["apellido"] == test_cliente_data["apellido"]
    assert data["telefono"] == test_cliente_data["telefono"]
    assert data["direccion"] == test_cliente_data["direccion"]
    assert data["estado"] == EstadoCliente.ACTIVO
    assert "id" in data
    assert "fecha_creacion" in data
    assert "fecha_actualizacion" in data

def test_create_cliente_duplicate_email(client: TestClient, test_cliente_data):
    """Prueba la creación de un cliente con email duplicado"""
    # Crear primer cliente
    client.post("/api/v1/clientes", json=test_cliente_data)
    
    # Intentar crear segundo cliente con el mismo email
    response = client.post("/api/v1/clientes", json=test_cliente_data)
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()

def test_get_cliente(client: TestClient, test_cliente_data):
    """Prueba la obtención de un cliente a través de la API"""
    # Crear cliente
    create_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = create_response.json()["id"]
    
    # Obtener cliente
    response = client.get(f"/api/v1/clientes/{cliente_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == cliente_id
    assert data["email"] == test_cliente_data["email"]
    assert data["nombre"] == test_cliente_data["nombre"]
    assert data["apellido"] == test_cliente_data["apellido"]
    assert data["telefono"] == test_cliente_data["telefono"]
    assert data["direccion"] == test_cliente_data["direccion"]
    assert data["estado"] == EstadoCliente.ACTIVO
    assert "fecha_creacion" in data
    assert "fecha_actualizacion" in data

def test_get_cliente_not_found(client: TestClient):
    """Prueba la obtención de un cliente que no existe"""
    response = client.get("/api/v1/clientes/999")
    assert response.status_code == 404

def test_update_cliente(client: TestClient, test_cliente_data):
    """Prueba la actualización de un cliente a través de la API"""
    # Crear cliente
    create_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = create_response.json()["id"]
    
    # Actualizar cliente
    update_data = {
        "nombre": "Nombre Actualizado",
        "apellido": "Apellido Actualizado",
        "telefono": "1234567890",
        "direccion": "Nueva dirección"
    }
    response = client.put(f"/api/v1/clientes/{cliente_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["nombre"] == update_data["nombre"]
    assert data["apellido"] == update_data["apellido"]
    assert data["telefono"] == update_data["telefono"]
    assert data["direccion"] == update_data["direccion"]
    assert data["email"] == test_cliente_data["email"]
    assert data["estado"] == EstadoCliente.ACTIVO
    assert "fecha_actualizacion" in data

def test_update_cliente_not_found(client: TestClient):
    """Prueba la actualización de un cliente que no existe"""
    update_data = {
        "nombre": "Nombre Actualizado",
        "apellido": "Apellido Actualizado",
        "telefono": "1234567890",
        "direccion": "Nueva dirección"
    }
    response = client.put("/api/v1/clientes/999", json=update_data)
    assert response.status_code == 404

def test_update_cliente_duplicate_email(client: TestClient, test_cliente_data):
    """Prueba la actualización de un cliente con email duplicado"""
    # Crear dos clientes
    cliente1_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente1_id = cliente1_response.json()["id"]
    
    cliente2_data = test_cliente_data.copy()
    cliente2_data["email"] = "otro@email.com"
    cliente2_response = client.post("/api/v1/clientes", json=cliente2_data)
    cliente2_id = cliente2_response.json()["id"]
    
    # Intentar actualizar el segundo cliente con el email del primero
    update_data = {"email": test_cliente_data["email"]}
    response = client.put(f"/api/v1/clientes/{cliente2_id}", json=update_data)
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()

def test_delete_cliente(client: TestClient, test_cliente_data):
    """Prueba la eliminación de un cliente a través de la API"""
    # Crear cliente
    create_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = create_response.json()["id"]
    
    # Eliminar cliente
    response = client.delete(f"/api/v1/clientes/{cliente_id}")
    assert response.status_code == 204
    
    # Verificar que el cliente fue eliminado
    get_response = client.get(f"/api/v1/clientes/{cliente_id}")
    assert get_response.status_code == 404

def test_delete_cliente_not_found(client: TestClient):
    """Prueba la eliminación de un cliente que no existe"""
    response = client.delete("/api/v1/clientes/999")
    assert response.status_code == 404

def test_get_clientes(client: TestClient, test_cliente_data):
    """Prueba la obtención de la lista de clientes a través de la API"""
    # Crear varios clientes
    for i in range(3):
        cliente_data = test_cliente_data.copy()
        cliente_data["email"] = f"cliente{i+1}@email.com"
        client.post("/api/v1/clientes", json=cliente_data)
    
    # Obtener lista de clientes
    response = client.get("/api/v1/clientes")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 3
    assert all("id" in cliente for cliente in data)
    assert all("email" in cliente for cliente in data)
    assert all("nombre" in cliente for cliente in data)
    assert all("apellido" in cliente for cliente in data)
    assert all("telefono" in cliente for cliente in data)
    assert all("direccion" in cliente for cliente in data)
    assert all("estado" in cliente for cliente in data)
    assert all("fecha_creacion" in cliente for cliente in data)
    assert all("fecha_actualizacion" in cliente for cliente in data)

def test_activar_cliente(client: TestClient, test_cliente_data):
    """Prueba la activación de un cliente a través de la API"""
    # Crear cliente
    create_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = create_response.json()["id"]
    
    # Desactivar cliente
    client.put(f"/api/v1/clientes/{cliente_id}/desactivar")
    
    # Activar cliente
    response = client.put(f"/api/v1/clientes/{cliente_id}/activar")
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == EstadoCliente.ACTIVO

def test_desactivar_cliente(client: TestClient, test_cliente_data):
    """Prueba la desactivación de un cliente a través de la API"""
    # Crear cliente
    create_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = create_response.json()["id"]
    
    # Desactivar cliente
    response = client.put(f"/api/v1/clientes/{cliente_id}/desactivar")
    assert response.status_code == 200
    data = response.json()
    
    assert data["estado"] == EstadoCliente.INACTIVO

def test_activar_cliente_not_found(client: TestClient):
    """Prueba la activación de un cliente que no existe"""
    response = client.put("/api/v1/clientes/999/activar")
    assert response.status_code == 404

def test_desactivar_cliente_not_found(client: TestClient):
    """Prueba la desactivación de un cliente que no existe"""
    response = client.put("/api/v1/clientes/999/desactivar")
    assert response.status_code == 404

def test_buscar_clientes(client: TestClient, test_cliente_data):
    """Prueba la búsqueda de clientes a través de la API"""
    # Crear varios clientes
    for i in range(3):
        cliente_data = test_cliente_data.copy()
        cliente_data["email"] = f"cliente{i+1}@email.com"
        cliente_data["nombre"] = f"Nombre{i+1}"
        cliente_data["apellido"] = f"Apellido{i+1}"
        client.post("/api/v1/clientes", json=cliente_data)
    
    # Buscar clientes por nombre
    response = client.get("/api/v1/clientes/buscar?nombre=Nombre1")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) > 0
    assert all("nombre" in cliente for cliente in data)
    assert any(cliente["nombre"] == "Nombre1" for cliente in data)
    
    # Buscar clientes por apellido
    response = client.get("/api/v1/clientes/buscar?apellido=Apellido2")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) > 0
    assert all("apellido" in cliente for cliente in data)
    assert any(cliente["apellido"] == "Apellido2" for cliente in data)
    
    # Buscar clientes por email
    response = client.get("/api/v1/clientes/buscar?email=cliente3@email.com")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) > 0
    assert all("email" in cliente for cliente in data)
    assert any(cliente["email"] == "cliente3@email.com" for cliente in data) 