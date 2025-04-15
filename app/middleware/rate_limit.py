"""
Rate limiting middleware for FastAPI.
"""
import time
import logging
from typing import Callable, Dict, Optional
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import redis
import os

# Configure logger
logger = logging.getLogger("app.middleware.rate_limit")

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests by client IP.
    """
    
    def __init__(
        self, 
        app,
        redis_url: Optional[str] = None,
        rate_limit_per_minute: int = 60,
        excluded_paths: Optional[list] = None
    ):
        """
        Initialize the rate limit middleware.
        
        Args:
            app: The FastAPI application
            redis_url: Redis URL for storing rate limit data
            rate_limit_per_minute: Maximum requests allowed per minute
            excluded_paths: List of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.rate_limit = rate_limit_per_minute
        self.excluded_paths = excluded_paths or ["/docs", "/redoc", "/openapi.json", "/metrics"]
        
        # Initialize Redis client
        try:
            self.redis = redis.from_url(self.redis_url)
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.redis = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request, apply rate limiting and pass to the next middleware or route handler.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response: The response from the next middleware or route handler
        """
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Skip if Redis is not available
        if not self.redis:
            logger.warning("Rate limiting disabled: Redis not available")
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Create Redis key
        redis_key = f"rate_limit:{client_ip}:{int(time.time() / 60)}"  # Key expires every minute
        
        try:
            # Increment request count
            current_count = self.redis.incr(redis_key)
            
            # Set expiry if this is the first request in the window
            if current_count == 1:
                self.redis.expire(redis_key, 60)  # Expire after 60 seconds
            
            # Check if rate limit exceeded
            if current_count > self.rate_limit:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                
                # Return rate limit error
                return Response(
                    content={"detail": "Too many requests. Please try again later."},
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json"
                )
            
            # Process the request if within rate limit
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Error in rate limiting: {str(e)}")
            # Continue processing if rate limiting fails
            return await call_next(request) 