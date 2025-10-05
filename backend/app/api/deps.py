from app.core.database import SessionLocal
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
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

