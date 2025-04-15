"""
Integration tests for the notifications endpoints.
"""
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.models.appointment_status import AppointmentStatus
from app.services.notification import NotificationChannel

def test_get_pending_notifications(client: TestClient, test_user_data, test_appointment_data):
    """Tests retrieving pending notifications through the API."""
    # Create client and appointment
    client_response = client.post("/api/v1/clients", json=test_user_data)
    client_id = client_response.json()["id"]
    
    # Create appointment for 24 hours from now
    datetime_value = datetime.now() + timedelta(hours=24)
    appointment_data = test_appointment_data.copy()
    appointment_data["client_id"] = client_id
    appointment_data["date_time"] = datetime_value.isoformat()
    appointment_data["status"] = AppointmentStatus.CONFIRMED
    appointment_response = client.post("/api/v1/appointments", json=appointment_data)
    appointment_id = appointment_response.json()["id"]
    
    # Get pending notifications
    response = client.get("/api/v1/notifications/pending")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) > 0
    assert any(notification["appointment_id"] == appointment_id for notification in data)
    assert all("id" in notificacion for notificacion in data)
    assert all("appointment_id" in notification for notification in data)
    assert all("type" in notification for notification in data)
    assert all("channel" in notification for notification in data)
    assert all("status" in notification for notification in data)

def test_get_appointment_notifications(client: TestClient, test_user_data, test_appointment_data):
    """Tests retrieving notifications for an appointment through the API."""
    # Create client and appointment
    client_response = client.post("/api/v1/clients", json=test_user_data)
    client_id = client_response.json()["id"]
    
    appointment_data = test_appointment_data.copy()
    appointment_data["client_id"] = client_id
    appointment_response = client.post("/api/v1/appointments", json=appointment_data)
    appointment_id = appointment_response.json()["id"]
    
    # Get appointment notifications
    response = client.get(f"/api/v1/appointments/{appointment_id}/notifications")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 2  # Should have at least the 24h and 2h notifications
    assert all(notification["appointment_id"] == appointment_id for notification in data)
    assert all("id" in notificacion for notificacion in data)
    assert all("type" in notification for notification in data)
    assert all("channel" in notification for notification in data)
    assert all("status" in notification for notification in data)

def test_get_appointment_notifications_not_found(client: TestClient):
    """Tests retrieving notifications for an appointment that does not exist."""
    response = client.get("/api/v1/appointments/999/notifications")
    assert response.status_code == 404

def test_mark_notification_sent(client: TestClient, test_user_data, test_appointment_data):
    """Tests marking a notification as sent through the API."""
    # Create client and appointment
    client_response = client.post("/api/v1/clients", json=test_user_data)
    client_id = client_response.json()["id"]
    
    appointment_data = test_appointment_data.copy()
    appointment_data["client_id"] = client_id
    appointment_response = client.post("/api/v1/appointments", json=appointment_data)
    appointment_id = appointment_response.json()["id"]
    
    # Get appointment notifications
    notifications_response = client.get(f"/api/v1/appointments/{appointment_id}/notifications")
    notifications = notifications_response.json()
    
    # Mark the first notification as sent
    notification_id = notifications[0]["id"]
    response = client.put(f"/api/v1/notifications/{notification_id}/sent")
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "SENT"
    assert data["sent_date"] is not None

def test_mark_notification_sent_not_found(client: TestClient):
    """Tests marking a notification that does not exist as sent."""
    response = client.put("/api/v1/notifications/999/sent")
    assert response.status_code == 404

def test_mark_notification_failed(client: TestClient, test_user_data, test_appointment_data):
    """Tests marking a notification as failed through the API."""
    # Create client and appointment
    client_response = client.post("/api/v1/clients", json=test_user_data)
    client_id = client_response.json()["id"]
    
    appointment_data = test_appointment_data.copy()
    appointment_data["client_id"] = client_id
    appointment_response = client.post("/api/v1/appointments", json=appointment_data)
    appointment_id = appointment_response.json()["id"]
    
    # Get appointment notifications
    notifications_response = client.get(f"/api/v1/appointments/{appointment_id}/notifications")
    notifications = notifications_response.json()
    
    # Mark the first notification as failed
    notification_id = notifications[0]["id"]
    error_message = "Connection error"
    response = client.put(
        f"/api/v1/notifications/{notification_id}/failed",
        json={"error": error_message}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "FAILED"
    assert data["error"] == error_message
    assert data["attempt_date"] is not None

def test_mark_notification_failed_not_found(client: TestClient):
    """Tests marking a notification that does not exist as failed."""
    response = client.put(
        "/api/v1/notifications/999/failed",
        json={"error": "Test error"}
    )
    assert response.status_code == 404

def test_get_notification_statistics(client: TestClient, test_user_data, test_appointment_data):
    """Tests retrieving notification statistics through the API."""
    # Create client and appointment
    client_response = client.post("/api/v1/clients", json=test_user_data)
    client_id = client_response.json()["id"]
    
    appointment_data = test_appointment_data.copy()
    appointment_data["client_id"] = client_id
    appointment_response = client.post("/api/v1/appointments", json=appointment_data)
    appointment_id = appointment_response.json()["id"]
    
    # Get appointment notifications
    notifications_response = client.get(f"/api/v1/appointments/{appointment_id}/notifications")
    notifications = notifications_response.json()
    
    # Mark some notifications as sent and failed
    for i, notification in enumerate(notifications[:2]):
        if i == 0:
            client.put(f"/api/v1/notifications/{notification['id']}/sent")
        else:
            client.put(
                f"/api/v1/notifications/{notification['id']}/failed",
                json={"error": "Test error"}
            )
    
    # Get statistics
    start = (datetime.now() - timedelta(hours=1)).isoformat()
    end = (datetime.now() + timedelta(hours=1)).isoformat()
    response = client.get(f"/api/v1/notifications/statistics?start={start}&end={end}")
    assert response.status_code == 200
    data = response.json()
    
    assert "total_sent" in data
    assert "successful" in data
    assert "failed" in data
    assert "by_type" in data
    assert "by_channel" in data
    assert data["successful"] >= 1
    assert data["failed"] >= 1

def test_get_notifications_by_channel(client: TestClient, test_user_data, test_appointment_data):
    """Tests retrieving notifications by channel through the API."""
    # Create client and appointment
    client_response = client.post("/api/v1/clients", json=test_user_data)
    client_id = client_response.json()["id"]
    
    appointment_data = test_appointment_data.copy()
    appointment_data["client_id"] = client_id
    appointment_response = client.post("/api/v1/appointments", json=appointment_data)
    appointment_id = appointment_response.json()["id"]
    
    # Get notifications by channel
    for canal in NotificationChannel:
        response = client.get(f"/api/v1/notifications/channel/{canal.value}")
        assert response.status_code == 200
        data = response.json()
        
        assert all(notification["channel"] == canal.value for notification in data)
        assert all("id" in notificacion for notificacion in data)
        assert all("appointment_id" in notification for notification in data)
        assert all("type" in notification for notification in data)
        assert all("status" in notification for notification in data)