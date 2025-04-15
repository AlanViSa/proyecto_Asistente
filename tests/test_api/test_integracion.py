"""
Integration tests between different modules of the system.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.models.estado_cita import EstadoCita
from app.models.estado_notificacion import EstadoNotificacion
from app.models.estado_recordatorio import EstadoRecordatorio
from app.models.tipo_notificacion import TipoNotificacion
from app.models.tipo_recordatorio import TipoRecordatorio

def test_creacion_cita_genera_notificaciones_y_recordatorios(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests that creating an appointment generates the corresponding notifications and reminders."""
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
        "notes": "Test appointment"
    }
    appointment_response = client.post("/api/v1/appointments", json=appointment_data)
    appointment_id = appointment_response.json()["id"]
    
    # Verify that the notification was created
    notifications_response = client.get(f"/api/v1/clients/{client_id}/notifications")
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()
    
    appointment_notification = next(
        (n for n in notifications if n["type"] == TipoNotificacion.CITA_PROGRAMADA),
        None
    )
    assert appointment_notification is not None
    assert appointment_notification["status"] == EstadoNotificacion.PENDIENTE
    assert appointment_notification["appointment_id"] == appointment_id
    
    # Verify that the reminder was created
    reminders_response = client.get(f"/api/v1/clients/{client_id}/reminders")
    assert reminders_response.status_code == 200
    reminders = reminders_response.json()
    
    appointment_reminder = next(
        (r for r in reminders if r["type"] == TipoRecordatorio.CITA),
        None
    )
    assert appointment_reminder is not None
    assert appointment_reminder["status"] == EstadoRecordatorio.PENDIENTE
    assert appointment_reminder["appointment_id"] == appointment_id

def test_appointment_cancellation_updates_notifications(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests that canceling an appointment updates the corresponding notifications."""
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
        "notes": "Test appointment"
    }
    appointment_response = client.post("/api/v1/appointments", json=appointment_data)
    appointment_id = appointment_response.json()["id"]
    
    # Cancel appointment
    client.put(f"/api/v1/appointments/{appointment_id}/cancel")
    
    # Verify that the notification was updated
    notifications_response = client.get(f"/api/v1/clients/{client_id}/notifications")
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()
    
    appointment_notification = next(
        (n for n in notifications if n["type"] == TipoNotificacion.CITA_CANCELADA),
        None
    )
    assert appointment_notification is not None
    assert appointment_notification["status"] == EstadoNotificacion.PENDIENTE
    assert appointment_notification["appointment_id"] == appointment_id

def test_complete_appointment_updates_reminders(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests that completing an appointment updates the corresponding reminders."""
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
        "notes": "Test appointment"
    }
    appointment_response = client.post("/api/v1/appointments", json=appointment_data)
    appointment_id = appointment_response.json()["id"]
    
    # Complete appointment
    client.put(f"/api/v1/appointments/{appointment_id}/complete")
    
    # Verify that the reminder was updated
    reminders_response = client.get(f"/api/v1/clients/{client_id}/reminders")
    assert reminders_response.status_code == 200
    reminders = reminders_response.json()
    
    appointment_reminder = next(
        (r for r in reminders if r["type"] == TipoRecordatorio.CITA),
        None
    )
    assert appointment_reminder is not None
    assert appointment_reminder["status"] == EstadoRecordatorio.COMPLETADO
    assert appointment_reminder["appointment_id"] == appointment_id

def test_update_notification_preferences_affects_notifications(client: TestClient, test_cliente_data):
    """Tests that updating notification preferences affects future notifications."""
    # Create client
    client_response = client.post("/api/v1/clients", json=test_cliente_data)
    client_id = client_response.json()["id"]
    
    # Create notification preference
    preference_data = {
        "client_id": client_id,
        "notification_type": TipoNotificacion.CITA_PROGRAMADA,
        "channels": ["EMAIL", "SMS"],
        "start_time": "09:00",
        "end_time": "18:00",
        "week_days": ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
    }
    preference_response = client.post("/api/v1/notification-preferences", json=preference_data)
    preference_id = preference_response.json()["id"]
    
    # Update preference
    update_data = {
        "channels": ["EMAIL"],
        "start_time": "10:00",
        "end_time": "19:00"
    }
    client.put(f"/api/v1/notification-preferences/{preference_id}", json=update_data)
    
    # Verify that the preference was updated
    preference_response = client.get(f"/api/v1/notification-preferences/{preference_id}")
    assert preference_response.status_code == 200
    preference = preference_response.json()
    
    assert preference["channels"] == ["EMAIL"]
    assert preference["start_time"] == "10:00"
    assert preference["end_time"] == "19:00"

def test_activate_deactivate_client_affects_appointments(client: TestClient, test_cliente_data, test_servicio_data):
    """Tests that activating/deactivating a client affects their appointments."""
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
        "notes": "Test appointment"
    }
    appointment_response = client.post("/api/v1/appointments", json=appointment_data)
    appointment_id = appointment_response.json()["id"]
    
    # Deactivate client
    client.put(f"/api/v1/clients/{client_id}/deactivate")
    
    # Verify that new appointments cannot be created
    new_appointment_data = {
        "client_id": client_id,
        "service_id": service_id,
        "date": (datetime.now() + timedelta(days=2)).date().isoformat(),
        "time": "11:00",
        "notes": "New appointment"
    }
    new_appointment_response = client.post("/api/v1/appointments", json=new_appointment_data)
    assert new_appointment_response.status_code == 400
    assert "inactive client" in new_appointment_response.json()["detail"].lower()
    
    # Activate client
    client.put(f"/api/v1/clients/{client_id}/activate")
    
    # Verify that new appointments can be created
    new_appointment_response = client.post("/api/v1/appointments", json=new_appointment_data)
    assert new_appointment_response.status_code == 200