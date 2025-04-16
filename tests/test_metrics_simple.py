"""
Simple script to test the metrics middleware
"""
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.metrics import setup_metrics

def main():
    """Main test function"""
    # Create a test app
    app = FastAPI(
        title="Test App",
        version="0.1.0"
    )
    app.version = "0.1.0"
    
    # Setup metrics
    setup_metrics(app)
    
    # Add test endpoints
    @app.get("/test")
    def test_endpoint():
        return {"message": "This is a test"}
        
    @app.get("/error")
    def error_endpoint():
        raise ValueError("Test error")
    
    # Create a test client
    client = TestClient(app)
    
    # Test metrics endpoint
    print("Testing metrics endpoint...")
    response = client.get("/metrics")
    if response.status_code != 200:
        print("FAIL: Metrics endpoint returned status code", response.status_code)
        return False
    if "text/plain" not in response.headers.get("content-type", ""):
        print("FAIL: Metrics endpoint returned wrong content type:", 
              response.headers.get("content-type", ""))
        return False
    print("PASS: Metrics endpoint works")
    
    # Test request counting
    print("\nTesting request counting...")
    for _ in range(3):
        client.get("/test")
    
    response = client.get("/metrics")
    metrics_text = response.text
    if 'http_requests_total{app_version="0.1.0",method="GET",path="/test"}' not in metrics_text:
        print("FAIL: Request counter not found in metrics")
        return False
    print("PASS: Request counter works")
    
    # Test exception tracking
    print("\nTesting exception tracking...")
    try:
        client.get("/error")
    except:
        pass  # Catch the exception raised by TestClient
    
    response = client.get("/metrics")
    metrics_text = response.text
    if 'http_exceptions_total{exception_type="ValueError",method="GET",path="/error"}' not in metrics_text:
        print("FAIL: Exception tracker not found in metrics")
        return False
    print("PASS: Exception tracking works")
    
    # Test in-progress tracking
    print("\nTesting in-progress request tracking...")
    client.get("/test")
    
    response = client.get("/metrics")
    metrics_text = response.text
    if 'http_requests_in_progress{method="GET",path="/test"} 0.0' not in metrics_text:
        print("FAIL: In-progress tracker not correctly decremented")
        return False
    print("PASS: In-progress tracking works")
    
    print("\nAll tests passed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)