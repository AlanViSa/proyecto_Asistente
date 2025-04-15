"""
Security utilities for handling authentication and authorization.
"""
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.client import Client
from app.core.config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password for storing.
    """
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str) -> Optional[Union[User, Client]]:
    """
    Authenticate a user by email and password.
    Tries both User and Client models.
    """
    # First try to authenticate as User (staff)
    user = db.query(User).filter(User.email == email).first()
    if user and verify_password(password, user.hashed_password):
        return user
    
    # Then try to authenticate as Client
    client = db.query(Client).filter(Client.email == email).first()
    if client and verify_password(password, client.hashed_password):
        return client
    
    return None


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Union[User, Client]:
    """
    Validate token and return current user (either User or Client).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
        
    # Try to get User first
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user
    
    # If not a User, try Client
    client = db.query(Client).filter(Client.id == user_id).first()
    if client:
        return client
    
    raise credentials_exception


def get_current_active_user(
    current_user: Union[User, Client] = Depends(get_current_user),
) -> Union[User, Client]:
    """
    Get current user and verify that user is active.
    Works for both User and Client models.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_admin(
    current_user: Union[User, Client] = Depends(get_current_user),
) -> Union[User, Client]:
    """
    Get current user and verify that user is an active admin.
    Works for both User and Client models.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user 