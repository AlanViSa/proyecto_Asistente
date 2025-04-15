"""
API endpoints for client authentication

This module provides endpoints for:
- Client login
- Registration of new clients
- JWT token verification
"""
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.config import settings
from app.core.security import authenticate_user, create_access_token, get_current_user, verify_password
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientResponse
from app.schemas.token import Token
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()

@router.post(
    "/login",
    response_model=Token,
    summary="Login",
    description="""
    Endpoint to authenticate a client and obtain a JWT token.
    
    Parameters:
    - **username**: Client email
    - **password**: Client password
    
    Response:
    - **access_token**: JWT token for authentication
    - **token_type**: Token type (always "bearer")
    """,
    responses={
        200: {
            "description": "Successful login",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "Incorrect credentials",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Incorrect email or password"
                    }
                }
            }
        },
        400: {
            "description": "Inactive client",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Inactive client"
                    }
                }
            }
        }
    }
)
async def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # Find the user with the given email
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # If user doesn't exist or password is incorrect, raise an exception
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # If user is not active, raise an exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    # Create access token with expiry as configured in settings
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Client",
    description="""
    Endpoint to register a new client in the system.
    
    Parameters:
    - **email**: Client email (unique)
    - **password**: Client password
    - **full_name**: Client's full name
    - **phone**: Client's phone number in format +1-XXX-XXX-XXXX (unique)
    
    Response:
    - Registered client data
    """,
    responses={
        201: {
            "description": "Client successfully registered",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "client@example.com",
                        "full_name": "John Doe",
                        "phone": "+1-555-123-4567",
                        "is_active": True
                    }
                }
            }
        },
        400: {
            "description": "Email or phone already registered",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email already registered"
                    }
                }
            }
        }
    }
)
async def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user.
    """
    # Check if a user with the same email already exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    
    # Create a new user with the provided data
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone=user_in.phone,
        is_active=True,
        is_admin=False,
    )
    
    # Add the user to the database and commit the changes
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.post(
    "/test-token",
    response_model=ClientResponse,
    summary="Test Token",
    description="""
    Endpoint to verify the validity of a JWT token.
    
    Headers:
    - **Authorization**: Bearer JWT token
    
    Response:
    - Authenticated client data
    """,
    responses={
        200: {
            "description": "Valid token",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "client@example.com",
                        "full_name": "John Doe",
                        "phone": "+1-555-123-4567",
                        "is_active": True
                    }
                }
            }
        },
        401: {
            "description": "Invalid or expired token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Could not validate credentials"
                    }
                }
            }
        }
    }
)
async def test_token(
    current_user: Client = Depends(get_current_user)
) -> Any:
    """
    Endpoint to test JWT token
    """
    return current_user 