from app.core.database import SessionLocal, get_async_db
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User
from app.services.auth_service import AuthService
import redis
import os
from typing import Optional

# Security scheme for JWT tokens
security = HTTPBearer()

def get_db():
  # Dependency to get a database session for API requests.
  db=SessionLocal()
  try: 
    yield db
  finally:
    db.close()

# Export the async version from database module
# This is used by endpoints that need async database access
get_db_async = get_async_db

def get_redis_client() -> redis.Redis:
    """Dependency to get Redis client for caching."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        client = redis.from_url(redis_url, decode_responses=True)
        # Test connection
        client.ping()
        return client
    except Exception as e:
        # Return None if Redis is not available (graceful degradation)
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user."""
    try:
        user = await AuthService.get_current_user(credentials.credentials, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Optional security scheme
optional_security = HTTPBearer(auto_error=False)

async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency to get current authenticated user (optional)."""
    if not credentials:
        return None
    
    try:
        user = await AuthService.get_current_user(credentials.credentials, db)
        return user
    except Exception:
        return None


# Async version for endpoints that need AsyncSession
from app.core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession

async def get_current_user_async(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """Dependency to get current authenticated user with async session."""
    try:
        # Convert async session to sync for AuthService
        # This is a temporary solution - ideally AuthService should support async
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            user = await AuthService.get_current_user(credentials.credentials, sync_db)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user
        finally:
            sync_db.close()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional_async(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: AsyncSession = Depends(get_async_db)
) -> Optional[User]:
    """Dependency to get current authenticated user (optional) with async session."""
    if not credentials:
        return None
    
    try:
        # Convert async session to sync for AuthService
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            user = await AuthService.get_current_user(credentials.credentials, sync_db)
            return user
        finally:
            sync_db.close()
    except Exception:
        return None


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to require admin role."""
    from app.models.users import UserRole
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

