from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os

# Obtener límite de rate desde variables de entorno
RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))

# Crear limiter
limiter = Limiter(key_func=get_remote_address)

def setup_rate_limit(app):
    """Configura el rate limiting para la aplicación"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware, limiter=limiter)

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Maneja las excepciones de rate limit"""
    raise HTTPException(
        status_code=429,
        detail={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.retry_after
        }
    )

def get_rate_limit():
    """Retorna el límite de rate configurado"""
    return RATE_LIMIT_PER_MINUTE 