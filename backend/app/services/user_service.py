from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError

from app.models.users import User, UserRole, Token
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserRoleUpdate
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import ValidationError, NotFoundError, ConflictError
from app.core.config import settings


class UserService:
    """Service for managing user operations including CRUD, authentication, and role management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with hashed password."""
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ConflictError("User with this email already exists")
        
        # Hash the password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user instance
        db_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=UserRole.USER,
            is_active=True,
            is_verified=False,
            preferences={}
        )
        
        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("User with this email already exists")
    
    def create_oauth_user(self, email: str, full_name: str, oauth_provider: str, 
                         oauth_id: str, profile_picture_url: Optional[str] = None) -> User:
        """Create a new user from OAuth authentication."""
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            or_(
                User.email == email,
                and_(User.oauth_provider == oauth_provider, User.oauth_id == oauth_id)
            )
        ).first()
        
        if existing_user:
            # Update OAuth info if user exists but doesn't have OAuth data
            if not existing_user.oauth_provider:
                existing_user.oauth_provider = oauth_provider
                existing_user.oauth_id = oauth_id
                existing_user.oauth_email_verified = True
                if profile_picture_url:
                    existing_user.profile_picture_url = profile_picture_url
                self.db.commit()
                self.db.refresh(existing_user)
            return existing_user
        
        # Create new OAuth user
        db_user = User(
            email=email,
            full_name=full_name,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
            oauth_email_verified=True,
            profile_picture_url=profile_picture_url,
            role=UserRole.USER,
            is_active=True,
            is_verified=True,  # OAuth users are considered verified
            preferences={}
        )
        
        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("User with this email already exists")
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not user.hashed_password:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_oauth(self, oauth_provider: str, oauth_id: str) -> Optional[User]:
        """Get user by OAuth provider and ID."""
        return self.db.query(User).filter(
            and_(User.oauth_provider == oauth_provider, User.oauth_id == oauth_id)
        ).first()
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user information."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Check email uniqueness if email is being updated
        if user_data.email and user_data.email != user.email:
            existing_user = self.get_user_by_email(user_data.email)
            if existing_user:
                raise ConflictError("User with this email already exists")
        
        # Update fields
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.password is not None:
            user.hashed_password = get_password_hash(user_data.password)
        
        user.updated_at = datetime.utcnow()
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("User with this email already exists")
    
    def update_user_role(self, user_id: int, role_data: UserRoleUpdate) -> User:
        """Update user role (admin only operation)."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        user.role = role_data.role
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> User:
        """Update user preferences."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Merge with existing preferences
        current_prefs = user.preferences or {}
        current_prefs.update(preferences)
        user.preferences = current_prefs
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def deactivate_user(self, user_id: int) -> User:
        """Deactivate a user account."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def activate_user(self, user_id: int) -> User:
        """Activate a user account."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def verify_user_email(self, user_id: int) -> User:
        """Mark user email as verified."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        user.is_verified = True
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_users_by_role(self, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role with pagination."""
        return self.db.query(User).filter(User.role == role).offset(skip).limit(limit).all()
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users with pagination."""
        return self.db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
    
    def search_users(self, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users by email or full name."""
        search_filter = or_(
            User.email.ilike(f"%{query}%"),
            User.full_name.ilike(f"%{query}%")
        )
        return self.db.query(User).filter(search_filter).offset(skip).limit(limit).all()
    
    def get_user_count(self) -> int:
        """Get total number of users."""
        return self.db.query(User).count()
    
    def get_active_user_count(self) -> int:
        """Get number of active users."""
        return self.db.query(User).filter(User.is_active == True).count()
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user (hard delete - use with caution)."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Delete related tokens first
        self.db.query(Token).filter(Token.user_id == user_id).delete()
        
        # Delete user
        self.db.delete(user)
        self.db.commit()
        return True
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> User:
        """Change user password with current password verification."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Verify current password
        if not user.hashed_password or not verify_password(current_password, user.hashed_password):
            raise ValidationError("Current password is incorrect")
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def reset_password(self, user_id: int, new_password: str) -> User:
        """Reset user password (admin operation or after token verification)."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_last_login(self, user_id: int) -> User:
        """Update user's last login timestamp."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        user.last_login = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_users_by_team(self, team_id: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by team ID."""
        return self.db.query(User).filter(User.team_id == team_id).offset(skip).limit(limit).all()
    
    def assign_user_to_team(self, user_id: int, team_id: str) -> User:
        """Assign user to a team."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        user.team_id = team_id
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def remove_user_from_team(self, user_id: int) -> User:
        """Remove user from their current team."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        user.team_id = None
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        return user