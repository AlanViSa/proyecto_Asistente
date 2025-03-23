import pytest
import time
import concurrent.futures
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User, Appointment, Service
from app.core.security import create_access_token
from datetime import datetime, timedelta
import statistics

# Configuración de la base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_perf.db"
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

# Tests de rendimiento de la API
def test_login_performance(client, test_user):
    times = []
    for _ in range(100):
        start_time = time.time()
        response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "testpassword"}
        )
        end_time = time.time()
        times.append(end_time - start_time)
        assert response.status_code == 200
    
    avg_time = statistics.mean(times)
    p95_time = statistics.quantiles(times, n=20)[-1]
    assert avg_time < 0.1  # Promedio menor a 100ms
    assert p95_time < 0.2  # 95% de las peticiones menor a 200ms

def test_concurrent_appointments(client, test_token, test_user):
    def create_appointment():
        return client.post(
            "/api/appointments/",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "service_id": 1,
                "appointment_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "notes": "Test appointment"
            }
        )
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_appointment) for _ in range(50)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    end_time = time.time()
    
    total_time = end_time - start_time
    assert total_time < 5  # Menos de 5 segundos para 50 peticiones concurrentes
    assert all(r.status_code == 200 for r in results)

def test_database_query_performance(client, test_token, db):
    # Crear 1000 servicios
    services = [
        Service(
            name=f"Service {i}",
            description=f"Description {i}",
            duration=60,
            price=50.0
        )
        for i in range(1000)
    ]
    db.bulk_save_objects(services)
    db.commit()
    
    # Medir tiempo de consulta
    start_time = time.time()
    response = client.get("/api/services/")
    end_time = time.time()
    
    assert response.status_code == 200
    assert end_time - start_time < 0.5  # Menos de 500ms para obtener 1000 servicios

def test_memory_usage(client, test_token, db):
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Crear 1000 citas
    appointments = [
        Appointment(
            user_id=1,
            service_id=1,
            appointment_date=datetime.now() + timedelta(days=i),
            notes=f"Test appointment {i}"
        )
        for i in range(1000)
    ]
    db.bulk_save_objects(appointments)
    db.commit()
    
    # Obtener todas las citas
    response = client.get(
        "/api/appointments/",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    assert response.status_code == 200
    assert memory_increase < 50 * 1024 * 1024  # Menos de 50MB de aumento de memoria

def test_cache_performance(client, test_token):
    # Primera petición (sin caché)
    start_time = time.time()
    response1 = client.get(
        "/api/services/",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    first_request_time = time.time() - start_time
    
    # Segunda petición (con caché)
    start_time = time.time()
    response2 = client.get(
        "/api/services/",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    second_request_time = time.time() - start_time
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert second_request_time < first_request_time * 0.5  # La segunda petición debe ser al menos 2 veces más rápida

def test_rate_limiting(client, test_token):
    times = []
    for _ in range(20):  # Intentar 20 peticiones rápidas
        start_time = time.time()
        response = client.get(
            "/api/appointments/",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        end_time = time.time()
        times.append(end_time - start_time)
    
    # Verificar que algunas peticiones fueron limitadas
    assert any(response.status_code == 429 for response in responses)
    
    # Verificar que el tiempo promedio de respuesta es razonable
    avg_time = statistics.mean(times)
    assert avg_time < 0.1  # Promedio menor a 100ms para peticiones no limitadas 