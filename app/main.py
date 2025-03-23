"""
Punto de entrada principal de la aplicación

Este módulo configura y ejecuta la aplicación FastAPI, incluyendo:
- Configuración de middleware (CORS, rate limiting, logging)
- Endpoints de health check
- Configuración de monitoreo
- Documentación de la API
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import logging.handlers
import os
from datetime import datetime
import time

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.database import database, DatabaseError
from app.core.monitoring import setup_monitoring
from app.core.logging import setup_logging

# Crear directorio de logs si no existe
log_dir = os.path.dirname(settings.LOG_FILE)
if log_dir:
    os.makedirs(log_dir, exist_ok=True)

# Configuración de logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Middleware de Rate Limiting
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests = {}

    async def dispatch(self, request: Request, call_next):
        # Obtener IP del cliente
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Limpiar registros antiguos (más de 1 minuto)
        self.requests = {
            ip: times for ip, times in self.requests.items()
            if current_time - times[-1] < 60
        }

        # Verificar límite de rate
        if client_ip in self.requests:
            times = self.requests[client_ip]
            if len(times) >= settings.RATE_LIMIT_PER_MINUTE:
                if current_time - times[0] < 60:  # Menos de 1 minuto
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": "Too many requests",
                            "retry_after": 60 - (current_time - times[0])
                        }
                    )
                times.pop(0)  # Eliminar la solicitud más antigua
            times.append(current_time)
        else:
            self.requests[client_ip] = [current_time]

        return await call_next(request)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application...")
    try:
        await database.connect()
        async with database.session() as session:
            await session.execute("SELECT 1")  # Test de conexión
            logger.info("Database connection successful")
    except DatabaseError as e:
        logger.error(f"Database connection failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await database.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    API para el sistema de gestión de citas de un salón de belleza.
    
    ## Características
    * Gestión de clientes y usuarios
    * Gestión de citas y servicios
    * Sistema de notificaciones
    * Gestión de roles y permisos
    * Monitoreo y logging
    
    ## Autenticación
    La API utiliza autenticación JWT. Para obtener un token:
    1. Registra un nuevo usuario en `/api/v1/auth/registro`
    2. Inicia sesión en `/api/v1/auth/login`
    3. Usa el token recibido en el header `Authorization: Bearer <token>`
    
    ## Rate Limiting
    La API implementa rate limiting de {settings.RATE_LIMIT_PER_MINUTE} solicitudes por minuto por IP.
    
    ## Documentación
    * Swagger UI: `/api/v1/docs`
    * ReDoc: `/api/v1/redoc`
    * OpenAPI JSON: `/api/v1/openapi.json`
    """,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Middleware de Rate Limiting
app.add_middleware(RateLimitMiddleware)

# Middleware de CORS
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Middleware de Host Confiable
if settings.SERVER_HOST:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[str(settings.SERVER_HOST)]
    )

# Middleware de Logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()
    
    # Log request
    logger.info(f"Incoming {request.method} request to {request.url.path}")
    
    try:
        response = await call_next(request)
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Log response
        logger.info(
            f"Path: {request.url.path} "
            f"Method: {request.method} "
            f"Status: {response.status_code} "
            f"Duration: {duration:.3f}s"
        )
        
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        raise

# Health check endpoints
@app.get(
    "/health",
    response_model=dict,
    summary="Health Check",
    description="""
    Endpoint para verificar el estado general de la aplicación.
    
    ## Respuesta
    * `status`: Estado de la aplicación ("healthy" o "unhealthy")
    * `timestamp`: Fecha y hora de la verificación
    * `version`: Versión actual de la API
    * `environment`: Ambiente de ejecución (development, testing, production)
    """
)
async def health_check():
    """
    Endpoint para verificar el estado general de la aplicación
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get(
    "/health/db",
    response_model=dict,
    summary="Database Health Check",
    description="""
    Endpoint para verificar el estado de la conexión a la base de datos.
    
    ## Respuesta
    * `status`: Estado de la base de datos ("healthy" o "unhealthy")
    * `database`: Estado de la conexión ("connected" o "disconnected")
    * `timestamp`: Fecha y hora de la verificación
    * `error`: Mensaje de error (si aplica)
    """
)
async def db_health_check():
    """
    Endpoint para verificar el estado de la conexión a la base de datos
    """
    try:
        async with database.session() as session:
            await session.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow()
        }
    except DatabaseError as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

# Configurar monitoreo
setup_monitoring(app)

# Incluir rutas API
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get(
    "/",
    response_model=dict,
    summary="API Root",
    description="""
    Endpoint raíz que muestra información básica de la API.
    
    ## Respuesta
    * `app_name`: Nombre de la aplicación
    * `version`: Versión actual de la API
    * `docs_url`: URL de la documentación Swagger
    * `openapi_url`: URL del esquema OpenAPI
    """
)
async def root():
    """
    Endpoint raíz que muestra información básica de la API
    """
    return {
        "app_name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs_url": f"{settings.API_V1_STR}/docs",
        "openapi_url": f"{settings.API_V1_STR}/openapi.json"
    }

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...") 