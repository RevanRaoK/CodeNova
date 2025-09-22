from datetime import timedelta
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Any

from app.core.database import get_db
from app.core.security import ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.users import User, UserRole
from app.schemas.user import (
    UserCreate, UserResponse, UserLogin, 
    PasswordResetRequest, PasswordReset, UserRoleUpdate
)
from app.services.auth_service import AuthService
from app.services.oauth_service import google_oauth_service

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """Register a new user."""
    try:
        # Check if user already exists
        db_user = db.query(User).filter(User.email == user_in.email).first()
        if db_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered",
            )
        
        # Create new user
        user = AuthService.create_user(db, user_in)
        
        # Create tokens for the new user
        tokens = AuthService.create_user_tokens(db, user)
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/login", response_model=dict)
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
    
    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": tokens["token_type"],
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }
    }

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

@router.get("/google")
def google_oauth_login() -> Any:
    """Initiate Google OAuth flow"""
    try:
        # Generate state parameter for CSRF protection
        state = "oauth_state_" + str(hash(str(datetime.datetime.utcnow())))
        
        # Get authorization URL
        auth_url = google_oauth_service.get_authorization_url(state)
        
        return {
            "authorization_url": auth_url,
            "state": state
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate OAuth flow: {str(e)}"
        )

@router.get("/google/callback")
async def google_oauth_callback(
    code: str,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db)
) -> Any:
    """Handle Google OAuth callback"""
    try:
        # Check for OAuth errors
        if error:
            raise HTTPException(
                status_code=400,
                detail=f"OAuth error: {error}"
            )
        
        if not code:
            raise HTTPException(
                status_code=400,
                detail="Authorization code not provided"
            )
        
        # Authenticate with Google
        result = await google_oauth_service.authenticate_with_google(db, code)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OAuth authentication failed: {str(e)}"
        )

@router.post("/google/token")
async def google_token_login(
    google_token: dict,
    db: Session = Depends(get_db)
) -> Any:
    """Authenticate with Google ID token (for frontend-initiated OAuth)"""
    try:
        id_token_str = google_token.get("credential") or google_token.get("id_token")
        
        if not id_token_str:
            raise HTTPException(
                status_code=400,
                detail="Google ID token not provided"
            )
        
        # Verify ID token and get user info
        user_info = google_oauth_service.verify_id_token(id_token_str)
        
        # Create or update user
        user = google_oauth_service.create_or_update_user(db, user_info)
        
        # Generate JWT tokens for our application
        tokens = AuthService.create_user_tokens(db, user)
        
        return {
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role.value,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'profile_picture_url': user.profile_picture_url,
                'oauth_provider': user.oauth_provider,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            },
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'token_type': tokens['token_type']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Google token authentication failed: {str(e)}"
        )
