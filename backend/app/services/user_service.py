from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from fastapi import UploadFile, HTTPException
import json
import os
import uuid

from ..models import User
from ..schemas.user import UserCreate, UserUpdate, UserProfile, UserProfileUpdate, NotificationPreferences, PasswordChange, UserPreferences
from ..core.security import get_password_hash, verify_password


class UserService:
    """Service for managing user operations including profile, preferences, and settings."""
    
    async def get_user_profile(self, db: Session, user_id: int) -> Optional[UserProfile]:
        """Get user profile information."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Convert user model to profile schema
        profile = UserProfile(
            firstName=user.first_name,
            lastName=user.last_name,
            email=user.email,
            jobTitle=user.job_title,
            bio=user.bio,
            programmingLanguages=json.loads(user.programming_languages) if user.programming_languages else [],
            profilePictureUrl=user.profile_picture_url
        )
        return profile
    
    async def update_user_profile(self, db: Session, user_id: int, profile_data: UserProfileUpdate) -> Optional[UserProfile]:
        """Update user profile information with comprehensive validation."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate and update user fields
        try:
            if profile_data.firstName is not None:
                if not profile_data.firstName.strip():
                    raise HTTPException(status_code=400, detail="First name cannot be empty")
                user.first_name = profile_data.firstName.strip()
            
            if profile_data.lastName is not None:
                if not profile_data.lastName.strip():
                    raise HTTPException(status_code=400, detail="Last name cannot be empty")
                user.last_name = profile_data.lastName.strip()
            
            if profile_data.email is not None:
                # Check if email is already taken by another user
                existing_user = db.query(User).filter(
                    User.email == profile_data.email,
                    User.id != user_id
                ).first()
                if existing_user:
                    raise HTTPException(status_code=400, detail="Email already registered")
                user.email = profile_data.email
            
            if profile_data.jobTitle is not None:
                user.job_title = profile_data.jobTitle.strip() if profile_data.jobTitle else None
            
            if profile_data.bio is not None:
                user.bio = profile_data.bio.strip() if profile_data.bio else None
            
            if profile_data.programmingLanguages is not None:
                # Validate and clean programming languages
                clean_languages = [lang.strip() for lang in profile_data.programmingLanguages if lang.strip()]
                user.programming_languages = json.dumps(clean_languages)
            
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            return await self.get_user_profile(db, user_id)
            
        except HTTPException:
            db.rollback()
            raise
        except IntegrityError as e:
            db.rollback()
            if "email" in str(e).lower():
                raise HTTPException(status_code=400, detail="Email already registered")
            raise HTTPException(status_code=500, detail="Failed to update profile")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error updating profile: {e}")
            raise HTTPException(status_code=500, detail="Failed to update profile")
    
    async def get_user_preferences(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get user preferences."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Get preferences from user model or return defaults
        preferences_json = getattr(user, 'preferences', '{}')
        if isinstance(preferences_json, str):
            preferences = json.loads(preferences_json) if preferences_json else {}
        else:
            preferences = preferences_json or {}
        
        # Return structured preferences
        return {
            "notifications": preferences.get("notifications", {
                "emailNotifications": {
                    "reviewCompleted": True,
                    "newPattern": True,
                    "securityAlert": True,
                    "weeklyDigest": False,
                    "marketingEmails": False
                },
                "pushNotifications": {
                    "reviewCompleted": True,
                    "newPattern": False,
                    "securityAlert": True
                },
                "frequency": "immediate"
            }),
            "userPreferences": preferences.get("userPreferences", {
                "theme": "light",
                "language": "en",
                "timezone": "UTC",
                "defaultProgrammingLanguage": "javascript",
                "aiModel": "gemini-pro",
                "codeEditorTheme": "vs-light",
                "autoSave": True,
                "showLineNumbers": True
            })
        }
    
    async def update_user_preferences(self, db: Session, user_id: int, preferences: UserPreferences) -> Dict[str, Any]:
        """Update user preferences with validation."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            # Get current preferences
            current_prefs = await self.get_user_preferences(db, user_id)
            
            # Validate preferences (Pydantic validation already done, but add extra checks)
            preferences_dict = preferences.dict()
            
            # Update user preferences
            current_prefs["userPreferences"] = preferences_dict
            
            # Save to database
            user.preferences = json.dumps(current_prefs)
            user.updated_at = datetime.utcnow()
            
            db.commit()
            return current_prefs
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update user preferences: {e}")
            raise HTTPException(status_code=500, detail="Failed to update preferences")
    
    async def update_notification_preferences(self, db: Session, user_id: int, notifications: NotificationPreferences) -> Dict[str, Any]:
        """Update notification preferences."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Get current preferences
        current_prefs = await self.get_user_preferences(db, user_id)
        
        # Update notification preferences
        current_prefs["notifications"] = notifications.dict()
        
        # Save to database
        user.preferences = json.dumps(current_prefs)
        user.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            return current_prefs
        except IntegrityError:
            db.rollback()
            raise
    
    async def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email address."""
        return db.query(User).filter(User.email == email).first()
    
    async def get_theme_preference(self, db: Session, user_id: int) -> str:
        """Get user theme preference."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return "light"  # Default theme
        
        preferences = await self.get_user_preferences(db, user_id)
        return preferences.get("userPreferences", {}).get("theme", "light")
    
    async def update_theme_preference(self, db: Session, user_id: int, theme: str) -> Dict[str, Any]:
        """Update user theme preference."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate theme
        allowed_themes = ['light', 'dark', 'auto']
        if theme not in allowed_themes:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid theme. Must be one of: {', '.join(allowed_themes)}"
            )
        
        # Get current preferences
        current_prefs = await self.get_user_preferences(db, user_id)
        
        # Update theme preference
        current_prefs["userPreferences"]["theme"] = theme
        
        # Save to database
        user.preferences = json.dumps(current_prefs)
        user.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            return current_prefs
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update theme preference")
    
    async def get_user_settings(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user settings."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        preferences = await self.get_user_preferences(db, user_id)
        profile = await self.get_user_profile(db, user_id)
        
        return {
            "profile": profile.dict() if profile else {},
            "preferences": preferences.get("userPreferences", {}),
            "notifications": preferences.get("notifications", {}),
            "theme": preferences.get("userPreferences", {}).get("theme", "light"),
            "lastUpdated": user.updated_at.isoformat() if user.updated_at else None
        }
    
    async def update_user_settings(self, db: Session, user_id: int, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update comprehensive user settings."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get current preferences
        current_prefs = await self.get_user_preferences(db, user_id)
        
        # Update preferences if provided
        if "preferences" in settings:
            current_prefs["userPreferences"].update(settings["preferences"])
        
        # Update notifications if provided
        if "notifications" in settings:
            current_prefs["notifications"].update(settings["notifications"])
        
        # Update theme if provided
        if "theme" in settings:
            theme = settings["theme"]
            allowed_themes = ['light', 'dark', 'auto']
            if theme not in allowed_themes:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid theme. Must be one of: {', '.join(allowed_themes)}"
                )
            current_prefs["userPreferences"]["theme"] = theme
        
        # Save to database
        user.preferences = json.dumps(current_prefs)
        user.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            return await self.get_user_settings(db, user_id)
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update user settings")
    
    async def change_password(self, db: Session, user_id: int, password_data: PasswordChange) -> bool:
        """Change user password."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Verify current password
        if not verify_password(password_data.currentPassword, user.hashed_password):
            return False
        
        # Update password
        user.hashed_password = get_password_hash(password_data.newPassword)
        user.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            return True
        except IntegrityError:
            db.rollback()
            return False
    
    async def upload_profile_picture(self, db: Session, user_id: int, file: UploadFile) -> str:
        """Upload profile picture and return URL."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/profile_pictures"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{user_id}_{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Update user profile picture URL
        profile_picture_url = f"/uploads/profile_pictures/{filename}"
        user.profile_picture_url = profile_picture_url
        user.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            return profile_picture_url
        except IntegrityError:
            db.rollback()
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise
    
    async def delete_profile_picture(self, db: Session, user_id: str) -> bool:
        """Delete profile picture."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.profile_picture_url:
            return False
        
        # Delete file if it exists
        if user.profile_picture_url.startswith('/uploads/'):
            file_path = user.profile_picture_url[1:]  # Remove leading slash
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Update user
        user.profile_picture_url = None
        user.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            return True
        except IntegrityError:
            db.rollback()
            return False