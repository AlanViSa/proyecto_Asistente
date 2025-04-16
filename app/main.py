"""
Minimal FastAPI application for testing
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import metrics middleware
from app.middleware.metrics import setup_metrics

# Configure logging
logging.basicConfig(
    level="INFO",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app.main")

# Define app version
APP_VERSION = "1.0.0"

# Create FastAPI application
app = FastAPI(
    title="Salon Assistant",
    description="API for a salon appointment management system",
    version=APP_VERSION,
)

# Make version accessible as an attribute
app.version = APP_VERSION

# Setup metrics middleware first
setup_metrics(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Salon Assistant API"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": APP_VERSION}

@app.get("/api/services")
async def list_services():
    """List available services."""
    return [
        {"id": 1, "name": "Haircut", "description": "Standard haircut", "price": 25.0, "duration_minutes": 30},
        {"id": 2, "name": "Hair Coloring", "description": "Full hair coloring", "price": 60.0, "duration_minutes": 90},
        {"id": 3, "name": "Manicure", "description": "Basic manicure", "price": 20.0, "duration_minutes": 45},
    ] 