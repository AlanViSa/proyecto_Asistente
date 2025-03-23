"""
Pruebas de concurrencia y acceso simultáneo
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.models.estado_cita import EstadoCita
from app.models.estado_notificacion import EstadoNotificacion
from app.models.estado_recordatorio import EstadoRecordatorio
from app.models.tipo_notificacion import TipoNotificacion
from app.models.tipo_recordatorio import TipoRecordatorio

async def crear_cita_concurrente(client: TestClient, cliente_id: int, servicio_id: int, hora: str):
    """Función auxiliar para crear una cita de forma asíncrona"""
    cita_data = {
        "cliente_id": cliente_id,
        "servicio_id": servicio_id,
        "fecha": (datetime.now() + timedelta(days=1)).date().isoformat(),
        "hora": hora,
        "notas": "Cita de prueba"
    }
    return client.post("/api/v1/citas", json=cita_data)

async def actualizar_cita_concurrente(client: TestClient, cita_id: int, notas: str):
    """Función auxiliar para actualizar una cita de forma asíncrona"""
    update_data = {"notas": notas}
    return client.put(f"/api/v1/citas/{cita_id}", json=update_data)

async def actualizar_cliente_concurrente(client: TestClient, cliente_id: int, telefono: str):
    """Función auxiliar para actualizar un cliente de forma asíncrona"""
    update_data = {"telefono": telefono}
    return client.put(f"/api/v1/clientes/{cliente_id}", json=update_data)

def test_crear_citas_concurrentes(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba la creación concurrente de citas"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear servicio
    servicio_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = servicio_response.json()["id"]
    
    # Crear citas de forma concurrente
    horas = ["10:00", "11:00", "12:00", "13:00", "14:00"]
    tareas = [
        crear_cita_concurrente(client, cliente_id, servicio_id, hora)
        for hora in horas
    ]
    
    # Ejecutar tareas de forma concurrente
    respuestas = asyncio.run(asyncio.gather(*tareas))
    
    # Verificar que todas las citas se crearon correctamente
    assert all(r.status_code == 200 for r in respuestas)
    
    # Verificar que las citas tienen diferentes IDs
    cita_ids = [r.json()["id"] for r in respuestas]
    assert len(set(cita_ids)) == len(cita_ids)
    
    # Verificar que las citas tienen diferentes horas
    citas_horas = [r.json()["hora"] for r in respuestas]
    assert len(set(citas_horas)) == len(citas_horas)

def test_actualizar_cita_concurrente(client: TestClient, test_cliente_data, test_servicio_data):
    """Prueba la actualización concurrente de una cita"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear servicio
    servicio_response = client.post("/api/v1/servicios", json=test_servicio_data)
    servicio_id = servicio_response.json()["id"]
    
    # Crear cita
    cita_data = {
        "cliente_id": cliente_id,
        "servicio_id": servicio_id,
        "fecha": (datetime.now() + timedelta(days=1)).date().isoformat(),
        "hora": "10:00",
        "notas": "Cita inicial"
    }
    cita_response = client.post("/api/v1/citas", json=cita_data)
    cita_id = cita_response.json()["id"]
    
    # Actualizar cita de forma concurrente
    notas = ["Nota 1", "Nota 2", "Nota 3", "Nota 4", "Nota 5"]
    tareas = [
        actualizar_cita_concurrente(client, cita_id, nota)
        for nota in notas
    ]
    
    # Ejecutar tareas de forma concurrente
    respuestas = asyncio.run(asyncio.gather(*tareas))
    
    # Verificar que todas las actualizaciones fueron exitosas
    assert all(r.status_code == 200 for r in respuestas)
    
    # Obtener la cita actualizada
    cita_response = client.get(f"/api/v1/citas/{cita_id}")
    assert cita_response.status_code == 200
    cita_actual = cita_response.json()
    
    # Verificar que la última actualización se aplicó correctamente
    assert cita_actual["notas"] in notas

def test_actualizar_cliente_concurrente(client: TestClient, test_cliente_data):
    """Prueba la actualización concurrente de un cliente"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Actualizar cliente de forma concurrente
    telefonos = ["111-111-1111", "222-222-2222", "333-333-3333", "444-444-4444", "555-555-5555"]
    tareas = [
        actualizar_cliente_concurrente(client, cliente_id, telefono)
        for telefono in telefonos
    ]
    
    # Ejecutar tareas de forma concurrente
    respuestas = asyncio.run(asyncio.gather(*tareas))
    
    # Verificar que todas las actualizaciones fueron exitosas
    assert all(r.status_code == 200 for r in respuestas)
    
    # Obtener el cliente actualizado
    cliente_response = client.get(f"/api/v1/clientes/{cliente_id}")
    assert cliente_response.status_code == 200
    cliente_actual = cliente_response.json()
    
    # Verificar que la última actualización se aplicó correctamente
    assert cliente_actual["telefono"] in telefonos

def test_crear_notificaciones_concurrentes(client: TestClient, test_cliente_data):
    """Prueba la creación concurrente de notificaciones"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear notificaciones de forma concurrente
    mensajes = [f"Mensaje {i+1}" for i in range(5)]
    tareas = []
    
    for mensaje in mensajes:
        notificacion_data = {
            "cliente_id": cliente_id,
            "tipo": TipoNotificacion.CITA_PROGRAMADA,
            "mensaje": mensaje,
            "canal": "EMAIL"
        }
        tareas.append(client.post("/api/v1/notificaciones", json=notificacion_data))
    
    # Ejecutar tareas de forma concurrente
    respuestas = asyncio.run(asyncio.gather(*tareas))
    
    # Verificar que todas las notificaciones se crearon correctamente
    assert all(r.status_code == 200 for r in respuestas)
    
    # Verificar que las notificaciones tienen diferentes IDs
    notificacion_ids = [r.json()["id"] for r in respuestas]
    assert len(set(notificacion_ids)) == len(notificacion_ids)
    
    # Verificar que las notificaciones tienen diferentes mensajes
    notificaciones_mensajes = [r.json()["mensaje"] for r in respuestas]
    assert len(set(notificaciones_mensajes)) == len(notificaciones_mensajes)

def test_crear_recordatorios_concurrentes(client: TestClient, test_cliente_data):
    """Prueba la creación concurrente de recordatorios"""
    # Crear cliente
    cliente_response = client.post("/api/v1/clientes", json=test_cliente_data)
    cliente_id = cliente_response.json()["id"]
    
    # Crear recordatorios de forma concurrente
    titulos = [f"Recordatorio {i+1}" for i in range(5)]
    tareas = []
    
    for titulo in titulos:
        recordatorio_data = {
            "cliente_id": cliente_id,
            "tipo": TipoRecordatorio.CITA,
            "titulo": titulo,
            "mensaje": f"Mensaje para {titulo}",
            "fecha_recordatorio": (datetime.now() + timedelta(days=1)).isoformat(),
            "frecuencia": None
        }
        tareas.append(client.post("/api/v1/recordatorios", json=recordatorio_data))
    
    # Ejecutar tareas de forma concurrente
    respuestas = asyncio.run(asyncio.gather(*tareas))
    
    # Verificar que todos los recordatorios se crearon correctamente
    assert all(r.status_code == 200 for r in respuestas)
    
    # Verificar que los recordatorios tienen diferentes IDs
    recordatorio_ids = [r.json()["id"] for r in respuestas]
    assert len(set(recordatorio_ids)) == len(recordatorio_ids)
    
    # Verificar que los recordatorios tienen diferentes títulos
    recordatorios_titulos = [r.json()["titulo"] for r in respuestas]
    assert len(set(recordatorios_titulos)) == len(recordatorios_titulos) 