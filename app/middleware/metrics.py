"""
Prometheus metrics middleware for FastAPI.
"""
import time
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST

# Define metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total count of requests by method and path.", ["method", "path", "app_version"]
)
REQUEST_TIME = Histogram(
    "http_request_duration_seconds", "Histogram of request duration by path (in seconds)", ["method", "path"]
)
REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress", "Gauge of requests by method and path currently being processed", ["method", "path"]
)
EXCEPTIONS = Counter(
    "http_exceptions_total", "Total count of exceptions raised by path and exception type", ["method", "path", "exception_type"]
)
DB_CONNECTION_ERRORS = Counter(
    "db_connection_errors_total", "Total count of database connection errors", []
)

APP_INFO = Info('app_info', 'Application information')

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware that collects Prometheus metrics for FastAPI.
    """
    
    def __init__(self, app: FastAPI, app_version: str = "unknown"):
        """
        Initialize the Prometheus middleware.
        
        Args:
            app: The application
            app_version: The application version
        """
        super().__init__(app)
        self.app = app
        self.app_version = app_version
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request and collect metrics.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response from the next handler
        """
        method = request.method
        path = request.url.path
        
        if path.endswith("/metrics") or path.endswith("/docs") or path.endswith("/redoc"):
            # Skip metrics for Prometheus endpoint and docs
            return await call_next(request)
        
        # Track in-progress requests
        REQUESTS_IN_PROGRESS.labels(method=method, path=path).inc()
        
        # Time the request
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Don't track 404s in histogram (they skew the data)
            if status_code != 404:
                REQUEST_TIME.labels(method=method, path=path).observe(time.time() - start_time)
            
            # Use the app version stored in the middleware instance
            REQUEST_COUNT.labels(method=method, path=path, app_version=self.app_version).inc()
            
            return response
            
        except Exception as e:
            # Record exceptions as 500 errors
            EXCEPTIONS.labels(method=method, path=path, exception_type=type(e).__name__).inc()
            raise e
            
        finally:
            # Calculate and record request duration
            duration = time.time() - start_time
            REQUEST_TIME.labels(method=method, path=path).observe(duration)
            
            # Decrement in-progress counter
            REQUESTS_IN_PROGRESS.labels(method=method, path=path).dec()

def setup_metrics(app: FastAPI):
    """
    Set up Prometheus metrics for a FastAPI application.
    
    Args:
        app: The FastAPI application
    """
    # Get app version - first try version attribute, then info dict if available
    app_version = "unknown"
    if hasattr(app, "version"):
        app_version = app.version
    elif hasattr(app, "info") and isinstance(app.info, dict) and "version" in app.info:
        app_version = app.info["version"]
    elif hasattr(app, "title") and app.title:
        # Get version from FastAPI info
        for route in app.routes:
            if route.path == "/openapi.json":
                app_version = getattr(app, "version", "unknown")
                break
    
    # Update app info
    APP_INFO.info({'version': app_version})
    
    # Add middleware with app_version
    app.add_middleware(PrometheusMiddleware, app_version=app_version)
    
    # Add metrics endpoint
    from prometheus_client import make_asgi_app
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    # Log setup completion
    import logging
    logger = logging.getLogger("app.metrics")
    logger.info(f"Prometheus metrics initialized with app version: {app_version}") 