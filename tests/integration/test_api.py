import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User, Appointment, Service
from app.core.security import create_access_token
from datetime import datetime, timedelta

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Fixture para la base de datos
@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# Fixture para el cliente de prueba
@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

# Fixture to create a test user
@pytest.fixture(scope="function")
def test_user(db):
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True,
        is_superuser=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Fixture to create an access token
@pytest.fixture(scope="function")
def test_token(test_user):
    return create_access_token(data={"sub": test_user.email})

# Authentication tests
def test_login(client, test_user):
    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_incorrect_password(client, test_user):
    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401

# User tests
def test_create_user(client, test_token):
    response = client.post(
        "/api/users/",
        headers={"Authorization": f"Bearer {test_token}"},
        json={
            "email": "new@example.com",
            "password": "newpassword",
            "full_name": "New User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data

def test_get_current_user(client, test_token, test_user):
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name

# Appointment tests
def test_create_appointment(client, test_token, test_user):
    response = client.post(
        "/api/appointments/",
        headers={"Authorization": f"Bearer {test_token}"},
        json={
            "service_id": 1,
            "appointment_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "notes": "Test appointment"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_user.id
    assert data["service_id"] == 1
    assert "appointment_date" in data

def test_get_user_appointments(client, test_token, test_user):
    response = client.get(
        "/api/appointments/",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Service tests
def test_get_services(client):
    response = client.get("/api/services/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_service(client, test_token):
    response = client.post(
        "/api/services/",
        headers={"Authorization": f"Bearer {test_token}"},
        json={
            "name": "Test Service",
            "description": "Test service description",
            "duration": 60,
            "price": 50.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Service"
    assert data["price"] == 50.0

# Validation tests
def test_create_appointment_invalid_date(client, test_token):
    response = client.post(
        "/api/appointments/",
        headers={"Authorization": f"Bearer {test_token}"},
        json={
            "service_id": 1,
            "appointment_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "notes": "Test appointment"
        }
    )
    assert response.status_code == 422

def test_create_user_invalid_email(client, test_token):
    response = client.post(
        "/api/users/",
        headers={"Authorization": f"Bearer {test_token}"},
        json={
            "email": "invalid-email",
            "password": "newpassword",
            "full_name": "New User"
        }
    )
    assert response.status_code == 422

# Permission tests
def test_access_protected_route_without_token(client):
    response = client.get("/api/users/me")
    assert response.status_code == 401

def test_access_admin_route_as_user(client, test_token):
    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 403 