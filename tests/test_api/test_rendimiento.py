"""
Pruebas de rendimiento y carga
"""
import pytest
import time
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.models.estado_cita import EstadoCita
from app.models.estado_notificacion import EstadoNotificacion
from app.models.estado_recordatorio import EstadoRecordatorio
from app.models.tipo_notificacion import TipoNotificacion
from app.models.tipo_recordatorio import TipoRecordatorio

def test_crear_multiples_clientes_rendimiento(client: TestClient):
    """Prueba el rendimiento al crear múltiples clientes"""
    # Medir tiempo de inicio
    inicio = time.time()
    
    # Crear 100 clientes
    for i in range(100):
        cliente_data = {
            "email": f"cliente{i}@email.com",
            "nombre": f"Nombre{i}",
            "apellido": f"Apellido{i}",
            "telefono": f"123-456-{i:04d}",
            "direccion": f"Dirección {i}"
        }
        response = client.post("/api/v1/clientes", json=cliente_data)
        assert response.status_code == 200
    
    # Medir tiempo de fin
    fin = time.time()
    tiempo_total = fin - inicio
    
    # Verificar que el tiempo total sea razonable (menos de 10 segundos)
    assert tiempo_total < 10

def test_obtener_multiples_clientes_rendimiento(client: TestClient):
    """Prueba el rendimiento al obtener múltiples clientes"""
    # Crear 100 clientes
    for i in range(100):
        cliente_data = {
            "email": f"cliente{i}@email.com",
            "nombre": f"Nombre{i}",
            "apellido": f"Apellido{i}",
            "telefono": f"123-456-{i:04d}",
            "direccion": f"Dirección {i}"
        }
        client.post("/api/v1/clientes", json=cliente_data)
    
    # Medir tiempo de inicio
    inicio = time.time()
    
    # Obtener todos los clientes
    response = client.get("/api/v1/clientes")
    assert response.status_code == 200
    clientes = response.json()
    
    # Medir tiempo de fin
    fin = time.time()
    tiempo_total = fin - inicio
    
    # Verificar que el tiempo total sea razonable (menos de 2 segundos)
    assert tiempo_total < 2
    assert len(clientes) >= 100

def test_crear_multiples_citas_rendimiento(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba el rendimiento al crear múltiples citas"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear servicio
    servicio_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = servicio_response.json()["id"]
    
    # Medir tiempo de inicio
    inicio = time.time()
    
    # Crear 50 citas
    for i in range(50):
        cita_data = {
            "cliente_id": cliente_id,
            "servicio_id": servicio_id,
            "fecha": (datetime.now() + timedelta(days=i+1)).date().isoformat(),
            "hora": f"{10 + i}:00",
            "notas": f"Cita {i}"
        }
        response = client.post("/api/v1/citas", json=cita_data)
        assert response.status_code == 200
    
    # Medir tiempo de fin
    fin = time.time()
    tiempo_total = fin - inicio
    
    # Verificar que el tiempo total sea razonable (menos de 5 segundos)
    assert tiempo_total < 5

def test_obtener_citas_cliente_rendimiento(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba el rendimiento al obtener las citas de un cliente"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear servicio
    servicio_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = servicio_response.json()["id"]
    
    # Crear 50 citas
    for i in range(50):
        cita_data = {
            "cliente_id": cliente_id,
            "servicio_id": servicio_id,
            "fecha": (datetime.now() + timedelta(days=i+1)).date().isoformat(),
            "hora": f"{10 + i}:00",
            "notas": f"Cita {i}"
        }
        client.post("/api/v1/citas", json=cita_data)
    
    # Medir tiempo de inicio
    inicio = time.time()
    
    # Obtener citas del cliente
    response = client.get(f"/api/v1/clientes/{cliente_id}/citas")
    assert response.status_code == 200
    citas = response.json()
    
    # Medir tiempo de fin
    fin = time.time()
    tiempo_total = fin - inicio
    
    # Verificar que el tiempo total sea razonable (menos de 1 segundo)
    assert tiempo_total < 1
    assert len(citas) >= 50

def test_crear_multiples_notificaciones_rendimiento(client: TestClient, test_cliente_data):
    """Prueba el rendimiento al crear múltiples notificaciones"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Medir tiempo de inicio
    inicio = time.time()
    
    # Crear 100 notificaciones
    for i in range(100):
        notificacion_data = {
            "cliente_id": cliente_id,
            "tipo": TipoNotificacion.CITA_PROGRAMADA,
            "mensaje": f"Notificación {i}",
            "canal": "EMAIL"
        }
        response = client.post("/api/v1/notificaciones", json=notificacion_data)
        assert response.status_code == 200
    
    # Medir tiempo de fin
    fin = time.time()
    tiempo_total = fin - inicio
    
    # Verificar que el tiempo total sea razonable (menos de 5 segundos)
    assert tiempo_total < 5

def test_obtener_notificaciones_cliente_rendimiento(client: TestClient, test_cliente_data):
    """Prueba el rendimiento al obtener las notificaciones de un cliente"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear 100 notificaciones
    for i in range(100):
        notificacion_data = {
            "cliente_id": cliente_id,
            "tipo": TipoNotificacion.CITA_PROGRAMADA,
            "mensaje": f"Notificación {i}",
            "canal": "EMAIL"
        }
        client.post("/api/v1/notificaciones", json=notificacion_data)
    
    # Medir tiempo de inicio
    inicio = time.time()
    
    # Obtener notificaciones del cliente
    response = client.get(f"/api/v1/clientes/{cliente_id}/notificaciones")
    assert response.status_code == 200
    notificaciones = response.json()
    
    # Medir tiempo de fin
    fin = time.time()
    tiempo_total = fin - inicio
    
    # Verificar que el tiempo total sea razonable (menos de 1 segundo)
    assert tiempo_total < 1
    assert len(notificaciones) >= 100

def test_crear_multiples_recordatorios_rendimiento(client: TestClient, test_cliente_data):
    """Prueba el rendimiento al crear múltiples recordatorios"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Medir tiempo de inicio
    inicio = time.time()
    
    # Crear 100 recordatorios
    for i in range(100):
        recordatorio_data = {
            "cliente_id": cliente_id,
            "tipo": TipoRecordatorio.CITA,
            "titulo": f"Recordatorio {i}",
            "mensaje": f"Mensaje {i}",
            "fecha_recordatorio": (datetime.now() + timedelta(days=i+1)).isoformat(),
            "frecuencia": None
        }
        response = client.post("/api/v1/recordatorios", json=recordatorio_data)
        assert response.status_code == 200
    
    # Medir tiempo de fin
    fin = time.time()
    tiempo_total = fin - inicio
    
    # Verificar que el tiempo total sea razonable (menos de 5 segundos)
    assert tiempo_total < 5

def test_obtener_recordatorios_cliente_rendimiento(client: TestClient, test_cliente_data):
    """Prueba el rendimiento al obtener los recordatorios de un cliente"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear 100 recordatorios
    for i in range(100):
        recordatorio_data = {
            "cliente_id": cliente_id,
            "tipo": TipoRecordatorio.CITA,
            "titulo": f"Recordatorio {i}",
            "mensaje": f"Mensaje {i}",
            "fecha_recordatorio": (datetime.now() + timedelta(days=i+1)).isoformat(),
            "frecuencia": None
        }
        client.post("/api/v1/recordatorios", json=recordatorio_data)
    
    # Medir tiempo de inicio
    inicio = time.time()
    
    # Obtener recordatorios del cliente
    response = client.get(f"/api/v1/clientes/{cliente_id}/recordatorios")
    assert response.status_code == 200
    recordatorios = response.json()
    
    # Medir tiempo de fin
    fin = time.time()
    tiempo_total = fin - inicio
    
    # Verificar que el tiempo total sea razonable (menos de 1 segundo)
    assert tiempo_total < 1
    assert len(recordatorios) >= 100

def test_busqueda_clientes_rendimiento(client: TestClient):
    """Prueba el rendimiento de la búsqueda de clientes"""
    # Crear 100 clientes
    for i in range(100):
        cliente_data = {
            "email": f"cliente{i}@email.com",
            "nombre": f"Nombre{i}",
            "apellido": f"Apellido{i}",
            "telefono": f"123-456-{i:04d}",
            "direccion": f"Dirección {i}"
        }
        client.post("/api/v1/clientes", json=cliente_data)
    
    # Medir tiempo de inicio
    inicio = time.time()
    
    # Realizar búsqueda
    response = client.get("/api/v1/clientes/buscar?nombre=Nombre")
    assert response.status_code == 200
    resultados = response.json()
    
    # Medir tiempo de fin
    fin = time.time()
    tiempo_total = fin - inicio
    
    # Verificar que el tiempo total sea razonable (menos de 1 segundo)
    assert tiempo_total < 1
    assert len(resultados) > 0 