"""
Endpoints for service management.
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_active_admin, get_current_active_user
from app.models.service import Service
from app.models.user import User
from app.schemas.service import ServiceCreate, ServiceResponse, ServiceUpdate

router = APIRouter()


@router.get(
    "/",
    response_model=List[ServiceResponse],
    summary="List Services",
    description="Retrieve list of available services with pagination."
)
async def read_services(
    skip: int = 0,
    limit: int = Query(default=100, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve services.
    """
    services = db.query(Service).filter(Service.is_active == True).offset(skip).limit(limit).all()
    return services


@router.post(
    "/",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Service",
    description="Create a new service (admin only)."
)
async def create_service(
    *,
    db: Session = Depends(get_db),
    service_in: ServiceCreate,
    _: User = Depends(get_current_active_admin),
) -> Any:
    """
    Create new service.
    """
    service = Service(
        name=service_in.name,
        description=service_in.description,
        price=service_in.price,
        duration=service_in.duration,
        is_active=True,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Get Service Details",
    description="Get details of a specific service by ID."
)
async def read_service(
    service_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Any:
    """
    Get service by ID.
    """
    service = db.query(Service).filter(Service.id == service_id, Service.is_active == True).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.put(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Update Service",
    description="Update an existing service (admin only)."
)
async def update_service(
    *,
    db: Session = Depends(get_db),
    service_id: int,
    service_in: ServiceUpdate,
    _: User = Depends(get_current_active_admin),
) -> Any:
    """
    Update a service.
    """
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    update_data = service_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)
    
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.delete(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Delete Service",
    description="Deactivate a service (admin only)."
)
async def delete_service(
    *,
    db: Session = Depends(get_db),
    service_id: int,
    _: User = Depends(get_current_active_admin),
) -> Any:
    """
    Deactivate a service.
    """
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service.is_active = False
    db.add(service)
    db.commit()
    db.refresh(service)
    return service 