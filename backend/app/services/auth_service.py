from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.models.users import User, Token, UserRole
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin, TokenPayload

class AuthService:
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user with hashed password."""
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            name=user_data.name,
            hashed_password=hashed_password,
            role=UserRole.GUEST,
            is_active=True,
            is_verified=False
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    @staticmethod
    def create_user_tokens(db: Session, user: User) -> Dict[str, str]:
        """Create access and refresh tokens for a user."""
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_refresh_token(
            {"sub": str(user.id), "email": user.email}
        )
        
        # Store the refresh token in the database
        expires = datetime.utcnow() + timedelta(days=7)  # 7 days expiration for refresh token
        db_token = Token(
            token=refresh_token,
            expires=expires,
            user_id=user.id
        )
        db.add(db_token)
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh an access token using a valid refresh token."""
        # Verify the refresh token
        payload = verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
            
        # Check if the token exists in the database and is not expired
        token = db.query(Token).filter(
            Token.token == refresh_token,
            Token.expires > datetime.utcnow()
        ).first()
        
        if not token:
            return None
            
        # Get the user
        user = db.query(User).filter(User.id == token.user_id).first()
        if not user or not user.is_active:
            return None
            
        # Create new access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {"access_token": access_token, "token_type": "bearer"}

    @staticmethod
    def revoke_token(db: Session, token: str) -> bool:
        """Revoke a refresh token."""
        db_token = db.query(Token).filter(Token.token == token).first()
        if not db_token:
            return False
        db.delete(db_token)
        db.commit()
        return True

    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[User]:
        """Get the current user from a JWT token."""
        payload = verify_token(token)
        if not payload or payload.get("type") != "access":
            return None
            
        user_id = payload.get("sub")
        if not user_id:
            return None
            
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            return None
            
        return user

    @staticmethod
    def update_user_role(db: Session, user_id: int, role: UserRole) -> Optional[User]:
        """Update a user's role (admin only)."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
            
        user.role = role
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user_status(db: Session, user_id: int, is_active: bool) -> Optional[User]:
        """Update a user's active status (admin only)."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
            
        user.is_active = is_active
        db.commit()
        db.refresh(user)
        return user
