import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User
from app.core.security import create_access_token
import jwt
from datetime import datetime, timedelta
import re

# Configuración de la base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_security.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Fixtures
@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

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

@pytest.fixture(scope="function")
def test_token(test_user):
    return create_access_token(data={"sub": test_user.email})

# Tests de autenticación
def test_password_hashing(client, test_user):
    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    
    # Verificar que el token es un JWT válido
    token = response.json()["access_token"]
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert "sub" in decoded
        assert "exp" in decoded
    except jwt.InvalidTokenError:
        pytest.fail("Token no es un JWT válido")

def test_token_expiration(client, test_user):
    # Crear un token expirado
    expired_token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(seconds=-1)
    )
    
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401

def test_invalid_token(client):
    response = client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

# Tests de autorización
def test_admin_access(client, test_user):
    # Intentar acceder a una ruta de admin como usuario normal
    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 403

def test_user_data_isolation(client, test_user, db):
    # Crear otro usuario
    other_user = User(
        email="other@example.com",
        hashed_password="hashed_password",
        full_name="Other User",
        is_active=True,
        is_superuser=False
    )
    db.add(other_user)
    db.commit()
    
    # Intentar acceder a los datos del otro usuario
    response = client.get(
        f"/api/users/{other_user.id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 403

# Tests de validación de entrada
def test_sql_injection_prevention(client, test_token):
    malicious_input = "' OR '1'='1"
    response = client.post(
        "/api/users/",
        headers={"Authorization": f"Bearer {test_token}"},
        json={
            "email": malicious_input,
            "password": "testpassword",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 422

def test_xss_prevention(client, test_token):
    malicious_input = "<script>alert('xss')</script>"
    response = client.post(
        "/api/users/",
        headers={"Authorization": f"Bearer {test_token}"},
        json={
            "email": "test@example.com",
            "password": "testpassword",
            "full_name": malicious_input
        }
    )
    assert response.status_code == 422

# Tests de headers de seguridad
def test_security_headers(client):
    response = client.get("/")
    headers = response.headers
    
    # Verificar headers de seguridad
    assert "X-Frame-Options" in headers
    assert "X-XSS-Protection" in headers
    assert "X-Content-Type-Options" in headers
    assert "Strict-Transport-Security" in headers
    assert "Content-Security-Policy" in headers

# Tests de rate limiting
def test_rate_limiting(client, test_token):
    responses = []
    for _ in range(20):  # Intentar 20 peticiones rápidas
        response = client.get(
            "/api/appointments/",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        responses.append(response.status_code)
    
    # Verificar que algunas peticiones fueron limitadas
    assert 429 in responses

# Tests de validación de contraseña
def test_password_validation(client, test_token):
    weak_passwords = [
        "123456",  # Demasiado corta
        "abcdefgh",  # Sin números
        "12345678",  # Sin letras
        "password",  # Palabra común
        "qwerty123"  # Patrón de teclado
    ]
    
    for password in weak_passwords:
        response = client.post(
            "/api/users/",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "email": "new@example.com",
                "password": password,
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422

# Tests de validación de email
def test_email_validation(client, test_token):
    invalid_emails = [
        "invalid-email",
        "test@",
        "@example.com",
        "test@.com",
        "test@example.",
        "test@example.com."  # Punto al final
    ]
    
    for email in invalid_emails:
        response = client.post(
            "/api/users/",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "email": email,
                "password": "StrongP@ss123",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422

# Tests de sanitización de datos
def test_input_sanitization(client, test_token):
    # Crear un usuario con caracteres especiales
    response = client.post(
        "/api/users/",
        headers={"Authorization": f"Bearer {test_token}"},
        json={
            "email": "test@example.com",
            "password": "StrongP@ss123",
            "full_name": "Test User<script>alert('xss')</script>"
        }
    )
    assert response.status_code == 422

# Tests de manejo de sesiones
def test_session_management(client, test_user):
    # Login
    login_response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Logout
    logout_response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_response.status_code == 200
    
    # Intentar usar el token después del logout
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401 