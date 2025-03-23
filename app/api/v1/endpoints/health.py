"""
Endpoint para verificar el estado de la aplicación
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.health import HealthStatus

router = APIRouter()

@router.get("/health", response_model=HealthStatus)
def health_check(db: Session = Depends(get_db)):
    """
    Verifica el estado de la aplicación y sus dependencias
    """
    try:
        # Verificar conexión a la base de datos
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return HealthStatus(
        status="healthy" if db_status == "healthy" else "unhealthy",
        database=db_status,
        version="1.0.0"
    ) 