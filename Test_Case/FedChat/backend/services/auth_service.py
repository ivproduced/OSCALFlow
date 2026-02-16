"""
Authentication and Authorization Service
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from models import User, APIKey
from core.config import settings

logger = structlog.get_logger()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication and authorization service"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.error("jwt_decode_error", error=str(e))
            return None
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str,
        ip_address: str = "unknown"
    ) -> Optional[User]:
        """Authenticate user by username/email and password"""
        from services.account_service import AccountService
        
        # Try username first
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        # Try email if username not found
        if not user:
            result = await db.execute(
                select(User).where(User.email == username)
            )
            user = result.scalar_one_or_none()
        
        if not user:
            logger.info("auth_failed_user_not_found", username=username)
            return None
        
        # Check if account is locked
        if user.account_status == "locked":
            if user.account_locked_until and user.account_locked_until > datetime.utcnow():
                logger.info("auth_failed_account_locked", user_id=str(user.id))
                return None
            else:
                # Unlock account if lock period expired
                user.account_status = "active"
                user.account_locked_until = None
                user.failed_login_attempts = 0
        
        if not user.is_active or user.account_status == "disabled":
            logger.info("auth_failed_user_inactive", user_id=str(user.id))
            return None
        
        if not AuthService.verify_password(password, user.password_hash):
            logger.info("auth_failed_invalid_password", user_id=str(user.id))
            
            # Record failed login attempt (AC-7)
            await AccountService.record_failed_login(db, str(user.id), ip_address)
            return None
        
        # Successful authentication
        # Reset failed login attempts
        await AccountService.reset_failed_login_attempts(db, str(user.id))
        
        # Update last login and last activity
        user.last_login = datetime.utcnow()
        await AccountService.update_last_activity(db, str(user.id))
        
        logger.info("auth_success", user_id=str(user.id), username=user.username)
        return user
    
    @staticmethod
    async def get_current_user(db: AsyncSession, token: str) -> Optional[User]:
        """Get current user from JWT token"""
        payload = AuthService.decode_token(token)
        
        if not payload:
            return None
        
        user_id: str = payload.get("sub")
        if not user_id:
            return None
        
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            return None
        
        return user
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None,
        role: str = "user"
    ) -> User:
        """Create a new user"""
        password_hash = AuthService.hash_password(password)
        
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info("user_created", user_id=str(user.id), username=username)
        return user
    
    @staticmethod
    async def validate_api_key(db: AsyncSession, api_key: str) -> Optional[User]:
        """Validate API key and return associated user"""
        import hashlib
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        result = await db.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            )
        )
        api_key_obj = result.scalar_one_or_none()
        
        if not api_key_obj:
            return None
        
        # Check expiration
        if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
            logger.info("api_key_expired", api_key_id=str(api_key_obj.id))
            return None
        
        # Update last used
        api_key_obj.last_used_at = datetime.utcnow()
        await db.commit()
        
        # Get user
        result = await db.execute(
            select(User).where(User.id == api_key_obj.user_id)
        )
        user = result.scalar_one_or_none()
        
        if user and user.is_active:
            return user
        
        return None
