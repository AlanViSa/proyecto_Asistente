"""
Configuración de pruebas para middleware
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

@pytest.fixture
def test_app():
    """Create a test FastAPI application"""
    app = FastAPI(
        title="Test App",
        version="0.1.0"
    )
    app.version = "0.1.0"  # Explicitly set version
    return app

@pytest.fixture
def client(test_app):
    """Create a test client"""
    return TestClient(test_app) 