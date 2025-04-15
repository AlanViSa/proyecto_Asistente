"""
Concurrency and simultaneous access tests
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
    """Auxiliary function to create an appointment asynchronously"""
    appointment_data = {
        "client_id": cliente_id,
        "service_id": servicio_id,
        "date": (datetime.now() + timedelta(days=1)).date().isoformat(),
        "time": hora,
        "notes": "Test appointment"
    }
    return client.post("/api/v1/appointments", json=appointment_data)

async def actualizar_cita_concurrente(client: TestClient, cita_id: int, notas: str):
    """Auxiliary function to update an appointment asynchronously"""
    update_data = {"notes": notas}
    return client.put(f"/api/v1/appointments/{cita_id}", json=update_data)

async def actualizar_cliente_concurrente(client: TestClient, cliente_id: int, telefono: str):
    """Auxiliary function to update a client asynchronously"""
    update_data = {"phone": telefono}
    return client.put(f"/api/v1/clients/{cliente_id}", json=update_data)

def test_crear_citas_concurrentes(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests concurrent appointment creation"""
    # Create client
    client_response = client.post("/api/v1/clients", json=test_cliente_data)
    client_id = client_response.json()["id"]
    
    # Create service
    service_response = client.post("/api/v1/services", json=test_servicio_data)
    service_id = service_response.json()["id"]
    
    # Create appointments concurrently
    times = ["10:00", "11:00", "12:00", "13:00", "14:00"]
    tasks = [
        crear_cita_concurrente(client, client_id, service_id, time)
        for time in times
    ]
    
    # Execute tasks concurrently
    responses = asyncio.run(asyncio.gather(*tasks))
    
    # Verify that all appointments were created successfully
    assert all(r.status_code == 200 for r in responses)
    
    # Verify that appointments have different IDs
    appointment_ids = [r.json()["id"] for r in responses]
    assert len(set(appointment_ids)) == len(appointment_ids)
    
    # Verify that appointments have different times
    appointment_times = [r.json()["time"] for r in responses]
    assert len(set(appointment_times)) == len(appointment_times)

def test_actualizar_cita_concurrente(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests concurrent update of an appointment"""
    # Create client
    client_response = client.post("/api/v1/clients", json=test_cliente_data)
    client_id = client_response.json()["id"]
    
    # Create service
    service_response = client.post("/api/v1/services", json=test_servicio_data)
    service_id = service_response.json()["id"]
    
    # Create appointment
    appointment_data = {
        "client_id": client_id,
        "service_id": service_id,
        "date": (datetime.now() + timedelta(days=1)).date().isoformat(),
        "time": "10:00",
        "notes": "Initial appointment"
    }
    appointment_response = client.post("/api/v1/appointments", json=appointment_data)
    appointment_id = appointment_response.json()["id"]
    
    # Update appointment concurrently
    notes = ["Note 1", "Note 2", "Note 3", "Note 4", "Note 5"]
    tasks = [
        actualizar_cita_concurrente(client, appointment_id, note)
        for note in notes
    ]
    
    # Execute tasks concurrently
    responses = asyncio.run(asyncio.gather(*tasks))
    
    # Verify that all updates were successful
    assert all(r.status_code == 200 for r in responses)
    
    # Get the updated appointment
    appointment_response = client.get(f"/api/v1/appointments/{appointment_id}")
    assert appointment_response.status_code == 200
    updated_appointment = appointment_response.json()
    
    # Verify that the last update was applied correctly
    assert updated_appointment["notes"] in notes

def test_actualizar_cliente_concurrente(client: TestClient, test_cliente_data):
    """Tests concurrent update of a client"""
    # Create client
    client_response = client.post("/api/v1/clients", json=test_cliente_data)
    client_id = client_response.json()["id"]
    
    # Update client concurrently
    phones = ["111-111-1111", "222-222-2222", "333-333-3333", "444-444-4444", "555-555-5555"]
    tasks = [
        actualizar_cliente_concurrente(client, client_id, phone)
        for phone in phones
    ]
    
    # Execute tasks concurrently
    responses = asyncio.run(asyncio.gather(*tasks))
    
    # Verify that all updates were successful
    assert all(r.status_code == 200 for r in responses)
    
    # Get the updated client
    client_response = client.get(f"/api/v1/clients/{client_id}")
    assert client_response.status_code == 200
    updated_client = client_response.json()
    
    # Verify that the last update was applied correctly
    assert updated_client["phone"] in phones

def test_crear_notificaciones_concurrentes(client: TestClient, test_cliente_data):
    """Tests concurrent creation of notifications"""
    # Create client
    client_response = client.post("/api/v1/clients", json=test_cliente_data)
    client_id = client_response.json()["id"]
    
    # Create notifications concurrently
    messages = [f"Message {i+1}" for i in range(5)]
    tasks = []
    
    for message in messages:
        notification_data = {
            "client_id": client_id,
            "type": TipoNotificacion.CITA_PROGRAMADA,
            "message": message,
            "channel": "EMAIL"
        }
        tasks.append(client.post("/api/v1/notifications", json=notification_data))
    
    # Execute tasks concurrently
    responses = asyncio.run(asyncio.gather(*tasks))
    
    # Verify that all notifications were created successfully
    assert all(r.status_code == 200 for r in responses)
    
    # Verify that notifications have different IDs
    notification_ids = [r.json()["id"] for r in responses]
    assert len(set(notification_ids)) == len(notification_ids)
    
    # Verify that notifications have different messages
    notification_messages = [r.json()["message"] for r in responses]
    assert len(set(notification_messages)) == len(notification_messages)

def test_crear_recordatorios_concurrentes(client: TestClient, test_cliente_data):
    """Tests concurrent creation of reminders"""
    # Create client
    client_response = client.post("/api/v1/clients", json=test_cliente_data)
    client_id = client_response.json()["id"]
    
    # Create reminders concurrently
    titles = [f"Reminder {i+1}" for i in range(5)]
    tasks = []
    
    for title in titles:
        reminder_data = {
            "client_id": client_id,
            "type": TipoRecordatorio.CITA,
            "title": title,
            "message": f"Message for {title}",
            "reminder_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "frequency": None
        }
        tasks.append(client.post("/api/v1/reminders", json=reminder_data))
    
    # Execute tasks concurrently
    responses = asyncio.run(asyncio.gather(*tasks))
    
    # Verify that all reminders were created successfully
    assert all(r.status_code == 200 for r in responses)
    
    # Verify that reminders have different IDs
    reminder_ids = [r.json()["id"] for r in responses]
    assert len(set(reminder_ids)) == len(reminder_ids)
    
    # Verify that reminders have different titles
    reminder_titles = [r.json()["title"] for r in responses]
    assert len(set(reminder_titles)) == len(reminder_titles)