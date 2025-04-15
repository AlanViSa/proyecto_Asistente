"""
Minimal test app for debugging the API
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List, Optional
from datetime import datetime

# Create FastAPI app
app = FastAPI(
    title="Salon Assistant Test App",
    description="Testing API for salon appointment system",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define some models for testing
class Service(BaseModel):
    id: int
    name: str
    description: str
    price: float
    duration_minutes: int

class ServiceResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    duration_minutes: int

# Define some test data
SERVICES = [
    {
        "id": 1,
        "name": "Haircut",
        "description": "Standard haircut service",
        "price": 25.0,
        "duration_minutes": 30
    },
    {
        "id": 2,
        "name": "Hair Coloring",
        "description": "Full hair coloring service",
        "price": 60.0,
        "duration_minutes": 90
    },
    {
        "id": 3,
        "name": "Manicure",
        "description": "Basic manicure service",
        "price": 20.0,
        "duration_minutes": 45
    }
]

# Define routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Salon Assistant Test API"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}

@app.get("/services", response_model=List[ServiceResponse])
async def get_services():
    """Get all services."""
    return SERVICES

@app.get("/services/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: int):
    """Get a specific service by ID."""
    for service in SERVICES:
        if service["id"] == service_id:
            return service
    raise HTTPException(status_code=404, detail="Service not found")

# Run the app if executed directly
if __name__ == "__main__":
    print("Starting Salon Assistant Test API on http://0.0.0.0:8000")
    uvicorn.run("app.test_app:app", host="0.0.0.0", port=8000, reload=True) 