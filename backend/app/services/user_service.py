from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from fastapi import UploadFile
import json
import os
import uuid

from app.models.users import User
from app.schemas.users import UserProfileUpdate, UserPreferences, NotificationPreferences, PasswordChange, UserProfile
from app.core.security import get_password_hash, verify_password


class UserService:
    """Service for managing user operations including profile, preferences, and settings."""
    
    async def get_user_profile(self, db: Session, user_id: str) -> Optional[UserProfile]:
        """Get user profile information."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Convert user model to profile schema
        profile = UserProfile(
            firstName=getattr(user, 'first_name', None),
            lastName=getattr(user, 'last_name', None),
            email=user.email,
            jobTitle=getattr(user, 'job_title', None),
            bio=getattr(user, 'bio', None),
            programmingLanguages=json.loads(getattr(user, 'programming_languages', '[]')) if getattr(user, 'programming_languages', None) else [],
            profilePictureUrl=getattr(user, 'profile_picture_url', None)
        )
        return profile
    
    async def update_user_profile(self, db: Session, user_id: str, profile_data: UserProfileUpdate) -> Optional[UserProfile]:
        """Update user profile information."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Update user fields
        if profile_data.firstName is not None:
            user.first_name = profile_data.firstName
        if profile_data.lastName is not None:
            user.last_name = profile_data.lastName
        if profile_data.email is not None:
            user.email = profile_data.email
        if profile_data.jobTitle is not None:
            user.job_title = profile_data.jobTitle
        if profile_data.bio is not None:
            user.bio = profile_data.bio
        if profile_data.programmingLanguages is not None:
            user.programming_languages = json.dumps(profile_data.programmingLanguages)
        
        user.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            db.refresh(user)
            return await self.get_user_profile(db, user_id)
        except IntegrityError:
            db.rollback()
            raise
    
    async def get_user_preferences(self, db: Session, user_id: str) -> Dict[str, Any]:
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
    
    async def update_user_preferences(self, db: Session, user_id: str, preferences: UserPreferences) -> Dict[str, Any]:
        """Update user preferences."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Get current preferences
        current_prefs = await self.get_user_preferences(db, user_id)
        
        # Update user preferences
        current_prefs["userPreferences"] = preferences.dict()
        
        # Save to database
        user.preferences = json.dumps(current_prefs)
        user.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            return current_prefs
        except IntegrityError:
            db.rollback()
            raise
    
    async def update_notification_preferences(self, db: Session, user_id: str, notifications: NotificationPreferences) -> Dict[str, Any]:
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
    
    async def change_password(self, db: Session, user_id: str, password_data: PasswordChange) -> bool:
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
    
    async def upload_profile_picture(self, db: Session, user_id: str, file: UploadFile) -> str:
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