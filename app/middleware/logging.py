"""
Logging middleware for FastAPI.
"""
import time
import logging
from uuid import uuid4
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logger
logger = logging.getLogger("app.middleware.logging")

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request, log details and pass to the next middleware or route handler.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response: The response from the next middleware or route handler
        """
        # Generate request ID for tracking
        request_id = str(uuid4())
        
        # Extract request details
        client_host = request.client.host if request.client else "unknown"
        request_path = request.url.path
        request_method = request.method
        
        # Log request start
        logger.info(
            f"Request started | ID: {request_id} | {request_method} {request_path} | "
            f"Client: {client_host}"
        )
        
        # Record start time
        start_time = time.time()
        
        # Process request and get response
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log request completion
            logger.info(
                f"Request completed | ID: {request_id} | {request_method} {request_path} | "
                f"Status: {response.status_code} | Time: {process_time:.4f}s | "
                f"Client: {client_host}"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log exception
            logger.error(
                f"Request failed | ID: {request_id} | {request_method} {request_path} | "
                f"Error: {str(e)} | Time: {process_time:.4f}s | Client: {client_host}"
            )
            
            # Re-raise the exception
            raise 