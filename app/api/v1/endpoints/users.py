"""
API endpoints for user management

This module provides endpoints for:
- User listing, creation, update, and deletion (admin operations)
- User profile management
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_user, get_current_active_admin, get_password_hash
from app.models.user import User
from app.models.client import Client
from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter()

@router.get(
    "/users/",
    response_model=List[UserResponse],
    summary="Get all users",
    description="""
    Get all users.
    
    - **Superuser only**: This endpoint is restricted to superusers
    """,
    responses={
        200: {
            "description": "List of users",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "email": "admin@example.com",
                            "full_name": "Admin User",
                            "phone": "+1-555-123-4567",
                            "is_active": True,
                            "is_admin": True,
                            "is_superuser": True
                        }
                    ]
                }
            }
        },
        403: {
            "description": "Not enough permissions",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not enough permissions"
                    }
                }
            }
        }
    }
)
async def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """
    Get all users (superusers only).
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users = db.query(User).all()
    return users

@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="""
    Get a specific user by ID.
    
    - **Admin users**: Can get details of any user
    - **Regular users**: Can only get their own details
    
    Parameters:
    - **user_id**: The ID of the user to retrieve
    """,
    responses={
        200: {
            "description": "User details",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "admin@example.com",
                        "full_name": "Admin User",
                        "phone": "+1-555-123-4567",
                        "is_active": True,
                        "is_admin": True,
                        "is_superuser": True
                    }
                }
            }
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User not found"
                    }
                }
            }
        },
        403: {
            "description": "Not enough permissions",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not enough permissions"
                    }
                }
            }
        }
    }
)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific user by ID.
    
    - **Admin users**: Can get details of any user
    - **Regular users**: Can only get their own details
    
    Parameters:
    - **user_id**: The ID of the user to retrieve
    """
    # Check permissions
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.post(
    "/users/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="""
    Create a new user.
    
    - **Superuser only**: This endpoint is restricted to superusers
    
    Parameters:
    - **user_data**: User information
    """,
    responses={
        201: {
            "description": "User created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "admin@example.com",
                        "full_name": "Admin User",
                        "phone": "+1-555-123-4567",
                        "is_active": True,
                        "is_admin": True,
                        "is_superuser": True
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email already registered"
                    }
                }
            }
        },
        403: {
            "description": "Not enough permissions",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not enough permissions"
                    }
                }
            }
        }
    }
)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """
    Create a new user.
    
    - **Superuser only**: This endpoint is restricted to superusers
    
    Parameters:
    - **user_data**: User information
    """
    # Check permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if email already exists in users or clients
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    existing_client = db.query(Client).filter(Client.email == user_data.email).first()
    
    if existing_user or existing_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=user_data.is_admin,
        is_superuser=user_data.is_superuser
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="""
    Update a user's information.
    
    - **Superuser**: Can update any user and change admin/superuser status
    - **Admin users**: Can update their own information but not admin/superuser status
    
    Parameters:
    - **user_id**: The ID of the user to update
    - **user_data**: Updated user information
    """,
    responses={
        200: {
            "description": "User updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "updated.email@example.com",
                        "full_name": "Updated User",
                        "phone": "+1-555-987-6543",
                        "is_active": True,
                        "is_admin": True,
                        "is_superuser": True
                    }
                }
            }
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User not found"
                    }
                }
            }
        },
        403: {
            "description": "Not enough permissions",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not enough permissions"
                    }
                }
            }
        }
    }
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a user's information.
    
    - **Superuser**: Can update any user and change admin/superuser status
    - **Admin users**: Can update their own information but not admin/superuser status
    
    Parameters:
    - **user_id**: The ID of the user to update
    - **user_data**: Updated user information
    """
    # Get the user to update
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update other users"
        )
    
    # Regular admin users can't change admin or superuser status
    if not current_user.is_superuser:
        if user_data.is_admin is not None or user_data.is_superuser is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to change admin or superuser status"
            )
    
    # Update user data
    update_data = user_data.dict(exclude_unset=True)
    
    # Hash password if provided
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # Apply updates to user model
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="""
    Delete a user.
    
    - **Superuser only**: This endpoint is restricted to superusers
    
    Parameters:
    - **user_id**: The ID of the user to delete
    """,
    responses={
        204: {
            "description": "User deleted successfully"
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User not found"
                    }
                }
            }
        },
        403: {
            "description": "Not enough permissions",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not enough permissions"
                    }
                }
            }
        }
    }
)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """
    Delete a user.
    
    - **Superuser only**: This endpoint is restricted to superusers
    
    Parameters:
    - **user_id**: The ID of the user to delete
    """
    # Check permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Prevent deletion of own account
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own user account"
        )
    
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete the user
    db.delete(user)
    db.commit()
    
    return None 