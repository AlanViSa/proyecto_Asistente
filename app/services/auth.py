"""
Servicio para la gestión de autenticación y tokens
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import DatabaseError
from app.models.cliente import Cliente
from app.schemas.token import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Servicio para operaciones de autenticación"""

    @staticmethod
    def create_access_token(*, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crea un token JWT de acceso
        
        Args:
            data: Datos a incluir en el token
            expires_delta: Tiempo de expiración opcional
            
        Returns:
            str: Token JWT generado
            
        Raises:
            JWTError: Si hay un error al crear el token
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
            raise DatabaseError(f"Error al crear token de acceso: {str(e)}")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifica si una contraseña coincide con su hash
        
        Args:
            plain_password: Contraseña en texto plano
            hashed_password: Hash de la contraseña
            
        Returns:
            bool: True si la contraseña coincide, False en caso contrario
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Genera un hash para una contraseña
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            str: Hash de la contraseña
        """
        return pwd_context.hash(password)

    @staticmethod
    def decode_token(token: str) -> Optional[TokenPayload]:
        """
        Decodifica un token JWT
        
        Args:
            token: Token JWT a decodificar
            
        Returns:
            Optional[TokenPayload]: Datos del token decodificado o None si es inválido
            
        Raises:
            JWTError: Si hay un error al decodificar el token
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
            raise DatabaseError(f"Error al decodificar token: {str(e)}")

    @staticmethod
    async def authenticate_cliente(
        db: AsyncSession, 
        email: str, 
        password: str
    ) -> Optional[Cliente]:
        """
        Autentica un cliente por email y contraseña
        
        Args:
            db: Sesión de base de datos
            email: Email del cliente
            password: Contraseña del cliente
            
        Returns:
            Optional[Cliente]: Cliente autenticado o None si las credenciales son inválidas
        """
        from app.services.cliente import ClienteService
        
        try:
            cliente = await ClienteService.get_by_email(db, email)
            if not cliente:
                return None
            if not AuthService.verify_password(password, cliente.hashed_password):
                return None
            return cliente
        except Exception as e:
            raise DatabaseError(f"Error al autenticar cliente: {str(e)}")

    @staticmethod
    def is_token_expired(token: str) -> bool:
        """
        Verifica si un token JWT ha expirado
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            bool: True si el token ha expirado, False en caso contrario
        """
        try:
            token_data = AuthService.decode_token(token)
            if not token_data:
                return True
            return datetime.fromtimestamp(token_data.exp) < datetime.utcnow()
        except JWTError:
            return True 