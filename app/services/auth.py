"""
Authentication and token management service
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import DatabaseError
from app.models.client import Client
from app.schemas.token import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Service for authentication operations"""

    @staticmethod
    def create_access_token(*, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Creates a JWT access token
        
        Args:
            data: Data to include in the token
            expires_delta: Optional expiration time
            
        Returns:
            str: Generated JWT token
            
        Raises:
            JWTError: If there is an error creating the token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        try:
            encoded_jwt = jwt.encode(
                to_encode, 
                settings.SECRET_KEY, 
                algorithm=settings.ALGORITHM
            )
            return encoded_jwt
        except JWTError as e:
            raise DatabaseError(f"Error creating access token: {str(e)}")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifies if a password matches its hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Password hash
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Generates a hash for a password
        
        Args:
            password: Plain text password
            
        Returns:
            str: Password hash
        """
        return pwd_context.hash(password)

    @staticmethod
    def decode_token(token: str) -> Optional[TokenPayload]:
        """
        Decodes a JWT token
        
        Args:
            token: JWT token to decode
            
        Returns:
            Optional[TokenPayload]: Decoded token data or None if invalid
            
        Raises:
            JWTError: If there is an error decoding the token
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
            return token_data
        except JWTError as e:
            raise DatabaseError(f"Error decoding token: {str(e)}")

    @staticmethod
    async def authenticate_client(
        db: AsyncSession, 
        email: str, 
        password: str
    ) -> Optional[Client]:
        """
        Authenticates a client by email and password
        
        Args:
            db: Database session
            email: Client email
            password: Client password
            
        Returns:
            Optional[Client]: Authenticated client or None if credentials are invalid
        """
        from app.services.client_service import ClientService
        
        try:
            client = await ClientService.get_by_email(db, email)
            if not client:
                return None
            if not AuthService.verify_password(password, client.hashed_password):
                return None
            return client
        except Exception as e:
            raise DatabaseError(f"Error authenticating client: {str(e)}")

    @staticmethod
    def is_token_expired(token: str) -> bool:
        """
        Checks if a JWT token has expired
        
        Args:
            token: JWT token to check
            
        Returns:
            bool: True if token has expired, False otherwise
        """
        try:
            token_data = AuthService.decode_token(token)
            if not token_data:
                return True
            return datetime.fromtimestamp(token_data.exp) < datetime.utcnow()
        except JWTError:
            return True 