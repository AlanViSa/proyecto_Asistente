"""
Integration tests for schedule endpoints.
"""
from fastapi.testclient import TestClient

from app.models.schedule_state import ScheduleState

def test_create_horario(client: TestClient, test_horario_data):
    """Tests the creation of a schedule via the API."""
    response = client.post("/api/v1/schedules", json=test_horario_data)
    assert response.status_code == 200
    response_data = response.json()
    
    assert response_data["day_of_week"] == test_horario_data["day_of_week"]
    assert response_data["start_time"] == test_horario_data["start_time"]
    assert response_data["end_time"] == test_horario_data["end_time"]
    assert response_data["state"] == ScheduleState.ACTIVE
    assert "id" in response_data

def test_create_horario_solapado(client: TestClient, test_horario_data):
    """Tests the creation of a schedule that overlaps with an existing one."""
    # Create first schedule
    client.post("/api/v1/schedules", json=test_horario_data)
    
    # Attempt to create a second overlapping schedule
    overlapping_schedule = test_horario_data.copy()
    overlapping_schedule["start_time"] = "09:00"  # Overlaps with the existing schedule
    response = client.post("/api/v1/schedules", json=overlapping_schedule)
    assert response.status_code == 400
    assert "overlap" in response.json()["detail"].lower()

def test_get_horario(client: TestClient, test_horario_data):
    """Tests retrieving a schedule via the API."""
    # Create a schedule
    create_response = client.post("/api/v1/schedules", json=test_horario_data)
    schedule_id = create_response.json()["id"]
    
    # Get schedule
    response = client.get(f"/api/v1/schedules/{schedule_id}")
    assert response.status_code == 200
    response_data = response.json()
    
    assert response_data["id"] == schedule_id
    assert response_data["day_of_week"] == test_horario_data["day_of_week"]
    assert response_data["start_time"] == test_horario_data["start_time"]
    assert response_data["end_time"] == test_horario_data["end_time"]
    assert response_data["state"] == ScheduleState.ACTIVE

def test_get_horario_not_found(client: TestClient):
    """Tests retrieving a schedule that does not exist."""
    response = client.get("/api/v1/schedules/999")
    assert response.status_code == 404

def test_update_horario(client: TestClient, test_horario_data):
    """Tests updating a schedule via the API."""
    # Create schedule
    create_response = client.post("/api/v1/schedules", json=test_horario_data)
    schedule_id = create_response.json()["id"]
    
    # Update schedule
    schedule_update_data = {
        "day_of_week": 2,
        "start_time": "10:00",
        "end_time": "18:00"
    }
    response = client.put(f"/api/v1/schedules/{schedule_id}", json=schedule_update_data)
    assert response.status_code == 200
    response_data = response.json()
    
    assert response_data["day_of_week"] == schedule_update_data["day_of_week"]
    assert response_data["start_time"] == schedule_update_data["start_time"]
    assert response_data["end_time"] == schedule_update_data["end_time"]
    assert response_data["state"] == ScheduleState.ACTIVE

def test_update_horario_not_found(client: TestClient):
    """Tests updating a schedule that does not exist."""
    schedule_update_data = {
        "day_of_week": 2,
        "start_time": "10:00",
        "end_time": "18:00"
    }
    response = client.put("/api/v1/schedules/999", json=schedule_update_data)
    assert response.status_code == 404

def test_update_horario_solapado(client: TestClient, test_horario_data):
    """Tests updating a schedule that overlaps with an existing one."""
    # Create two schedules
    schedule1_response = client.post("/api/v1/schedules", json=test_horario_data)
    schedule1_id = schedule1_response.json()["id"]
    
    schedule2_data = test_horario_data.copy()
    schedule2_data["day_of_week"] = 2
    schedule2_response = client.post("/api/v1/schedules", json=schedule2_data)
    schedule2_id = schedule2_response.json()["id"]
    
    # Attempt to update the second schedule to overlap with the first
    schedule_update_data = {"day_of_week": test_horario_data["day_of_week"]}
    response = client.put(f"/api/v1/schedules/{schedule2_id}", json=schedule_update_data)
    assert response.status_code == 400
    assert "overlap" in response.json()["detail"].lower()

def test_delete_horario(client: TestClient, test_horario_data):
    """Tests deleting a schedule via the API."""
    # Create schedule
    create_response = client.post("/api/v1/schedules", json=test_horario_data)
    schedule_id = create_response.json()["id"]
    
    # Delete schedule
    response = client.delete(f"/api/v1/schedules/{schedule_id}")
    assert response.status_code == 204
    
    # Verify that the schedule was deleted
    get_response = client.get(f"/api/v1/schedules/{schedule_id}")
    assert get_response.status_code == 404

def test_delete_horario_not_found(client: TestClient):
    """Tests deleting a schedule that does not exist."""
    response = client.delete("/api/v1/schedules/999")
    assert response.status_code == 404

def test_deactivate_horario(client: TestClient, test_horario_data):
    """Tests deactivating a schedule via the API."""
    # Create schedule
    create_response = client.post("/api/v1/schedules", json=test_horario_data)
    schedule_id = create_response.json()["id"]
    
    # Deactivate schedule
    response = client.put(f"/api/v1/schedules/{schedule_id}/deactivate")
    assert response.status_code == 200
    response_data = response.json()
    
    assert response_data["state"] == ScheduleState.INACTIVE

def test_activate_horario(client: TestClient, test_horario_data):
    """Tests activating a schedule via the API."""
    # Create schedule
    create_response = client.post("/api/v1/schedules", json=test_horario_data)
    schedule_id = create_response.json()["id"]
    
    # Deactivate schedule
    client.put(f"/api/v1/schedules/{schedule_id}/deactivate")
    
    # Activate schedule
    response = client.put(f"/api/v1/schedules/{schedule_id}/activate")
    assert response.status_code == 200
    response_data = response.json()
    
    assert response_data["state"] == ScheduleState.ACTIVE

def test_get_horarios(client: TestClient, test_horario_data):
    """Tests retrieving the list of schedules via the API."""
    # Create multiple schedules
    for i in range(3):
        schedule_data = test_horario_data.copy()
        schedule_data["day_of_week"] = i + 1
        client.post("/api/v1/schedules", json=schedule_data)
    
    # Get list of schedules
    response = client.get("/api/v1/schedules")
    assert response.status_code == 200
    response_data = response.json()
    
    assert len(response_data) >= 3
    assert all("id" in schedule for schedule in response_data)
    assert all("day_of_week" in schedule for schedule in response_data)
    assert all("start_time" in schedule for schedule in response_data)
    assert all("end_time" in schedule for schedule in response_data)
    assert all("state" in schedule for schedule in response_data)

def test_get_horarios_por_dia(client: TestClient, test_horario_data):
    """Tests retrieving schedules by day of the week via the API."""
    # Create schedules for different days
    for day in range(1, 4):
        schedule_data = test_horario_data.copy()
        schedule_data["day_of_week"] = day
        client.post("/api/v1/schedules", json=schedule_data)
    
    # Get schedules for a specific day
    day_of_week = 1
    response = client.get(f"/api/v1/schedules/day/{day_of_week}")
    assert response.status_code == 200
    response_data = response.json()
    
    assert all(schedule["day_of_week"] == day_of_week for schedule in response_data)
    assert all("id" in schedule for schedule in response_data)
    assert all("start_time" in schedule for schedule in response_data)
    assert all("end_time" in schedule for schedule in response_data)
    assert all("state" in schedule for schedule in response_data)