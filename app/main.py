"""
Main FastAPI application entry point
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk
from prometheus_client import make_asgi_app

from app.api.v1.api import api_router
from app.core.config import settings
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.tasks.scheduler import scheduler
from app.db.database import check_db_connection

# Configure logging
logging.basicConfig(
    level=settings.LOGGING_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app.main")

# Configure Sentry if DSN is provided
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
    )
    logger.info("Sentry integration enabled")

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for a salon appointment management system",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    RateLimitMiddleware, 
    redis_url=settings.REDIS_URL,
    rate_limit_per_minute=settings.RATE_LIMIT
)

# Add Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Execute tasks on application startup."""
    logger.info(f"Starting {settings.PROJECT_NAME} API")
    
    # Check database connection
    is_connected = await check_db_connection()
    if not is_connected:
        logger.error("Failed to connect to the database")
    else:
        logger.info("Successfully connected to the database")
    
    # Start the scheduler
    scheduler.start()
    logger.info("Task scheduler started")
    
    logger.info(f"{settings.PROJECT_NAME} API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Execute tasks on application shutdown."""
    logger.info(f"Shutting down {settings.PROJECT_NAME} API")
    
    # Shutdown the scheduler
    scheduler.shutdown()
    logger.info("Task scheduler stopped")

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint that redirects to docs."""
    return {"message": f"Welcome to {settings.PROJECT_NAME} API", "docs": f"{settings.API_V1_STR}/docs"}

@app.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint for monitoring."""
    # Check database connection
    db_connected = await check_db_connection()
    
    if not db_connected:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": "Database connection failed"}
        )
    
    return {"status": "ok", "version": "1.0.0"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    
    # Send exception to Sentry if configured
    if settings.SENTRY_DSN:
        sentry_sdk.capture_exception(exc)
    
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    ) 