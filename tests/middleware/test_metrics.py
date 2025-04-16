"""
Tests for the Prometheus metrics middleware
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.metrics import setup_metrics

def create_test_app():
    """Create a test FastAPI application"""
    app = FastAPI(
        title="Test App",
        version="0.1.0"
    )
    app.version = "0.1.0"  # Explicitly set version
    return app

def test_metrics_setup():
    """Test that the metrics middleware can be set up correctly"""
    app = create_test_app()
    setup_metrics(app)
    
    # Add a test endpoint
    @app.get("/test")
    def test_endpoint():
        return {"message": "This is a test"}
    
    # Create a client
    client = TestClient(app)
    
    # Test the metrics endpoint
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")

def test_request_count_incremented():
    """Test that the request counter is incremented"""
    app = create_test_app()
    setup_metrics(app)
    
    # Add a test endpoint
    @app.get("/test")
    def test_endpoint():
        return {"message": "This is a test"}
    
    # Create a client
    client = TestClient(app)
    
    # Make multiple requests
    for _ in range(3):
        client.get("/test")
    
    # Get metrics
    response = client.get("/metrics")
    metrics_text = response.text
    
    # Check if counter increased
    assert 'http_requests_total{app_version="0.1.0",method="GET",path="/test"}' in metrics_text

def test_exceptions_tracked():
    """Test that exceptions are tracked"""
    app = create_test_app()
    setup_metrics(app)
    
    # Add endpoints
    @app.get("/test")
    def test_endpoint():
        return {"message": "This is a test"}
        
    @app.get("/error")
    def error_endpoint():
        raise ValueError("Test error")
    
    # Create a client
    client = TestClient(app)
    
    # Try to access an endpoint that raises an error
    try:
        client.get("/error")
    except:
        pass  # Catch the exception raised by TestClient
    
    # Get metrics
    response = client.get("/metrics")
    metrics_text = response.text
    
    # Check if exceptions counter increased
    assert 'http_exceptions_total{exception_type="ValueError",method="GET",path="/error"}' in metrics_text

def test_in_progress_requests():
    """Test that in-progress requests are tracked and decremented properly"""
    app = create_test_app()
    setup_metrics(app)
    
    # Add a test endpoint
    @app.get("/test")
    def test_endpoint():
        return {"message": "This is a test"}
    
    # Create a client
    client = TestClient(app)
    
    # Make a request
    client.get("/test")
    
    # Get metrics
    response = client.get("/metrics")
    metrics_text = response.text
    
    # Check that in-progress requests are properly decremented
    assert 'http_requests_in_progress{method="GET",path="/test"} 0.0' in metrics_text