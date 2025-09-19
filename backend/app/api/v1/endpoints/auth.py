from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any

from app.core.database import get_db
from app.core.security import ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.users import User, UserRole
from app.schemas.user import (
    UserCreate, UserResponse, Token, UserLogin, 
    PasswordResetRequest, PasswordReset, UserRoleUpdate
)
from app.services.auth_service import AuthService

router = APIRouter()

def get_current_active_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Dependency to get the current active user from the token."""
    user = AuthService.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_current_active_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependency to check if the current user is an admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """Register a new user."""
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )
    
    # Create new user
    user = AuthService.create_user(db, user_in)
    return user

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login, get an access token for future requests."""
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = AuthService.create_user_tokens(db, user)
    return tokens

@router.post("/refresh-token", response_model=dict)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db),
) -> Any:
    """Refresh an access token using a refresh token."""
    tokens = AuthService.refresh_access_token(db, refresh_token)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return tokens

@router.post("/logout")
def logout(
    refresh_token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Revoke a refresh token (logout)."""
    success = AuthService.revoke_token(db, refresh_token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found",
        )
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get current user."""
    return current_user

@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
) -> Any:
    """Update a user's role (admin only)."""
    user = AuthService.update_user_role(db, user_id, role_update.role)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    return user

@router.post("/password-reset-request")
def password_reset_request(
    request: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> Any:
    """Request a password reset."""
    # In a real application, you would send an email with a reset token
    # For now, we'll just return a success message
    return {"message": "If your email is registered, you will receive a password reset link"}

@router.post("/password-reset")
def password_reset(
    reset_data: PasswordReset,
    db: Session = Depends(get_db),
) -> Any:
    """Reset a user's password with a valid reset token."""
    # In a real application, you would validate the reset token
    # and update the user's password
    return {"message": "Password has been reset successfully"}
