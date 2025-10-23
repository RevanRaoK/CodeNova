from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from fastapi import UploadFile, HTTPException
import json
import os
import uuid
import logging
import re

from ..models import User
from ..schemas.user import UserCreate, UserUpdate, UserProfile, UserProfileUpdate, NotificationPreferences, PasswordChange, UserPreferences
from ..core.security import get_password_hash, verify_password
from ..core.encryption import encrypt_api_key, decrypt_api_key, mask_api_key

logger = logging.getLogger(__name__)


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
            # Validate first name
            if profile_data.firstName is not None:
                first_name = profile_data.firstName.strip()
                if not first_name:
                    raise HTTPException(status_code=400, detail="First name cannot be empty")
                if len(first_name) > 100:
                    raise HTTPException(status_code=400, detail="First name must be 100 characters or less")
                if not re.match(r'^[a-zA-Z\s\-\'\.]+$', first_name):
                    raise HTTPException(status_code=400, detail="First name contains invalid characters")
                user.first_name = first_name
            
            # Validate last name
            if profile_data.lastName is not None:
                last_name = profile_data.lastName.strip()
                if not last_name:
                    raise HTTPException(status_code=400, detail="Last name cannot be empty")
                if len(last_name) > 100:
                    raise HTTPException(status_code=400, detail="Last name must be 100 characters or less")
                if not re.match(r'^[a-zA-Z\s\-\'\.]+$', last_name):
                    raise HTTPException(status_code=400, detail="Last name contains invalid characters")
                user.last_name = last_name
            
            # Validate email
            if profile_data.email is not None:
                email = profile_data.email.strip().lower()
                # Basic email validation
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                    raise HTTPException(status_code=400, detail="Invalid email format")
                
                # Check if email is already taken by another user
                existing_user = db.query(User).filter(
                    User.email == email,
                    User.id != user_id
                ).first()
                if existing_user:
                    raise HTTPException(status_code=400, detail="Email already registered")
                user.email = email
            
            # Validate job title
            if profile_data.jobTitle is not None:
                job_title = profile_data.jobTitle.strip() if profile_data.jobTitle else None
                if job_title and len(job_title) > 200:
                    raise HTTPException(status_code=400, detail="Job title must be 200 characters or less")
                user.job_title = job_title
            
            # Validate bio
            if profile_data.bio is not None:
                bio = profile_data.bio.strip() if profile_data.bio else None
                if bio and len(bio) > 1000:
                    raise HTTPException(status_code=400, detail="Bio must be 1000 characters or less")
                user.bio = bio
            
            # Validate programming languages
            if profile_data.programmingLanguages is not None:
                # Validate and clean programming languages
                clean_languages = [lang.strip() for lang in profile_data.programmingLanguages if lang.strip()]
                if len(clean_languages) > 20:
                    raise HTTPException(status_code=400, detail="Maximum 20 programming languages allowed")
                for lang in clean_languages:
                    if len(lang) > 50:
                        raise HTTPException(status_code=400, detail="Programming language name must be 50 characters or less")
                user.programming_languages = json.dumps(clean_languages)
            
            # Update full_name for backward compatibility
            if user.first_name and user.last_name:
                user.full_name = f"{user.first_name} {user.last_name}"
            elif user.first_name:
                user.full_name = user.first_name
            elif user.last_name:
                user.full_name = user.last_name
            
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Successfully updated profile for user {user_id}")
            return await self.get_user_profile(db, user_id)
            
        except HTTPException:
            db.rollback()
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error updating profile for user {user_id}: {e}")
            if "email" in str(e).lower():
                raise HTTPException(status_code=400, detail="Email already registered")
            raise HTTPException(status_code=500, detail="Failed to update profile due to database constraint")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error updating profile for user {user_id}: {e}")
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
            preferences_dict = preferences.dict(exclude_none=True)
            
            # Validate theme
            if preferences.theme is not None:
                allowed_themes = ['light', 'dark', 'auto']
                if preferences.theme not in allowed_themes:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid theme. Must be one of: {', '.join(allowed_themes)}"
                    )
            
            # Validate language
            if preferences.language is not None:
                if len(preferences.language) > 10:
                    raise HTTPException(status_code=400, detail="Language code must be 10 characters or less")
            
            # Validate timezone
            if preferences.timezone is not None:
                if len(preferences.timezone) > 50:
                    raise HTTPException(status_code=400, detail="Timezone must be 50 characters or less")
            
            # Validate defaultProgrammingLanguage
            if preferences.defaultProgrammingLanguage is not None:
                if len(preferences.defaultProgrammingLanguage) > 50:
                    raise HTTPException(status_code=400, detail="Programming language must be 50 characters or less")
            
            # Validate aiModel
            if preferences.aiModel is not None:
                allowed_models = ['gemini-pro', 'gemini-1.5-pro', 'gemini-1.5-flash']
                if preferences.aiModel not in allowed_models:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid AI model. Must be one of: {', '.join(allowed_models)}"
                    )
            
            # Validate codeEditorTheme
            if preferences.codeEditorTheme is not None:
                allowed_editor_themes = ['vs-light', 'vs-dark', 'hc-black', 'hc-light']
                if preferences.codeEditorTheme not in allowed_editor_themes:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid editor theme. Must be one of: {', '.join(allowed_editor_themes)}"
                    )
            
            # Update user preferences (merge with existing)
            current_prefs["userPreferences"].update(preferences_dict)
            
            # Save to database
            user.preferences = json.dumps(current_prefs)
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Successfully updated preferences for user {user_id}")
            return current_prefs
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update user preferences for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update preferences")
    
    async def update_notification_preferences(self, db: Session, user_id: int, notifications: NotificationPreferences) -> Dict[str, Any]:
        """Update notification preferences with validation and error handling."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            # Get current preferences
            current_prefs = await self.get_user_preferences(db, user_id)
            
            # Validate notification preferences (Pydantic already validates types)
            notifications_dict = notifications.dict()
            
            # Validate frequency
            allowed_frequencies = ['immediate', 'daily', 'weekly']
            if notifications.frequency not in allowed_frequencies:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid frequency. Must be one of: {', '.join(allowed_frequencies)}"
                )
            
            # Update notification preferences
            current_prefs["notifications"] = notifications_dict
            
            # Save to database
            user.preferences = json.dumps(current_prefs)
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Successfully updated notification preferences for user {user_id}")
            return current_prefs
            
        except HTTPException:
            db.rollback()
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error updating notification preferences for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update notification preferences due to database constraint")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update notification preferences for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update notification preferences")
    
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
        """Change user password with validation and error handling."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            # Verify current password
            if not user.hashed_password:
                raise HTTPException(status_code=400, detail="Password not set for this account")
            
            if not verify_password(password_data.current_password, user.hashed_password):
                raise HTTPException(status_code=400, detail="Current password is incorrect")
            
            # Validate new password is different from current
            if verify_password(password_data.new_password, user.hashed_password):
                raise HTTPException(status_code=400, detail="New password must be different from current password")
            
            # Update password
            user.hashed_password = get_password_hash(password_data.new_password)
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Successfully changed password for user {user_id}")
            return True
            
        except HTTPException:
            db.rollback()
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error changing password for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to change password due to database constraint")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to change password for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to change password")
    
    async def upload_profile_picture(self, db: Session, user_id: int, file: UploadFile) -> str:
        """Upload profile picture with validation and return URL."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            # Validate file type
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
            
            if not file_extension or file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
                )
            
            # Validate content type
            allowed_content_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if file.content_type not in allowed_content_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid content type. Must be an image file."
                )
            
            # Read file content
            content = await file.read()
            
            # Validate file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            if len(content) > max_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size is 5MB."
                )
            
            # Validate minimum file size (at least 1KB to avoid empty files)
            if len(content) < 1024:
                raise HTTPException(
                    status_code=400,
                    detail="File too small. Minimum size is 1KB."
                )
            
            # Create uploads directory if it doesn't exist
            upload_dir = "uploads/profile_pictures"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Delete old profile picture if exists
            if user.profile_picture_url and user.profile_picture_url.startswith('/uploads/'):
                old_file_path = user.profile_picture_url[1:]  # Remove leading slash
                if os.path.exists(old_file_path):
                    try:
                        os.remove(old_file_path)
                        logger.info(f"Deleted old profile picture for user {user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to delete old profile picture for user {user_id}: {e}")
            
            # Generate unique filename
            filename = f"{user_id}_{uuid.uuid4().hex}.{file_extension}"
            file_path = os.path.join(upload_dir, filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            # Update user profile picture URL
            profile_picture_url = f"/uploads/profile_pictures/{filename}"
            user.profile_picture_url = profile_picture_url
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Successfully uploaded profile picture for user {user_id}")
            return profile_picture_url
            
        except HTTPException:
            db.rollback()
            raise
        except IntegrityError as e:
            db.rollback()
            # Clean up uploaded file
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f"Integrity error uploading profile picture for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload profile picture due to database constraint")
        except Exception as e:
            db.rollback()
            # Clean up uploaded file
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f"Failed to upload profile picture for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload profile picture")
    
    async def delete_profile_picture(self, db: Session, user_id: int) -> bool:
        """Delete profile picture with error handling."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.profile_picture_url:
            raise HTTPException(status_code=400, detail="No profile picture to delete")
        
        try:
            # Delete file if it exists
            if user.profile_picture_url.startswith('/uploads/'):
                file_path = user.profile_picture_url[1:]  # Remove leading slash
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted profile picture file for user {user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to delete profile picture file for user {user_id}: {e}")
            
            # Update user
            user.profile_picture_url = None
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Successfully deleted profile picture for user {user_id}")
            return True
            
        except HTTPException:
            db.rollback()
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error deleting profile picture for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete profile picture due to database constraint")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete profile picture for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete profile picture")
    
    async def get_api_key_status(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Check if user has an API key configured.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dictionary with hasKey and keyPreview
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        has_key = bool(user.gemini_api_key)
        key_preview = None
        
        if has_key:
            try:
                # Decrypt and mask the key for preview
                decrypted_key = decrypt_api_key(user.gemini_api_key)
                key_preview = mask_api_key(decrypted_key)
            except Exception as e:
                logger.error(f"Failed to decrypt API key for user {user_id}: {e}")
                key_preview = "****"
        
        return {
            "hasKey": has_key,
            "keyPreview": key_preview
        }
    
    async def save_api_key(self, db: Session, user_id: int, api_key: str) -> Dict[str, Any]:
        """
        Save encrypted API key for user with comprehensive validation.
        
        Args:
            db: Database session
            user_id: User ID
            api_key: Plain text API key to encrypt and save
            
        Returns:
            Success status and message
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            # Validate API key format using validation method
            validation_result = await self.validate_api_key(api_key)
            if not validation_result["valid"]:
                raise HTTPException(
                    status_code=400,
                    detail=validation_result["error"]
                )
            
            api_key = api_key.strip()
            
            # Encrypt the API key
            encrypted_key = encrypt_api_key(api_key)
            
            # Save to database
            user.gemini_api_key = encrypted_key
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Successfully saved API key for user {user_id}")
            
            return {
                "success": True,
                "message": "API key saved successfully",
                "keyPreview": mask_api_key(api_key)
            }
            
        except HTTPException:
            db.rollback()
            raise
        except ValueError as e:
            db.rollback()
            logger.error(f"Encryption error saving API key for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to encrypt API key")
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error saving API key for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to save API key due to database constraint")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save API key for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to save API key")
    
    async def delete_api_key(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Delete user's Gemini API key.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Success status and message
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.gemini_api_key:
            raise HTTPException(status_code=400, detail="No API key to delete")
        
        try:
            # Delete the API key
            user.gemini_api_key = None
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Successfully deleted API key for user {user_id}")
            
            return {
                "success": True,
                "message": "API key deleted successfully"
            }
            
        except HTTPException:
            db.rollback()
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error deleting API key for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete API key due to database constraint")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete API key for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete API key")
    
    async def get_decrypted_api_key(self, db: Session, user_id: int) -> Optional[str]:
        """
        Get user's decrypted Gemini API key for internal use by AI service.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Decrypted API key or None if not set
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.gemini_api_key:
            return None
        
        try:
            decrypted_key = decrypt_api_key(user.gemini_api_key)
            return decrypted_key
        except Exception as e:
            logger.error(f"Failed to decrypt API key for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to decrypt API key")
    
    async def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Validate Gemini API key format and basic structure.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Dictionary with validation result and details
        """
        try:
            # Basic format validation
            if not api_key or not isinstance(api_key, str):
                return {
                    "valid": False,
                    "error": "API key must be a non-empty string"
                }
            
            api_key = api_key.strip()
            
            # Length validation
            if len(api_key) < 10:
                return {
                    "valid": False,
                    "error": "API key must be at least 10 characters long"
                }
            
            if len(api_key) > 200:
                return {
                    "valid": False,
                    "error": "API key is too long (maximum 200 characters)"
                }
            
            # Format validation for Gemini API keys
            if not api_key.startswith('AIza'):
                return {
                    "valid": False,
                    "error": "Invalid API key format. Gemini API keys should start with 'AIza'"
                }
            
            # Character validation - should only contain alphanumeric characters and some special chars
            import re
            if not re.match(r'^[A-Za-z0-9_-]+$', api_key):
                return {
                    "valid": False,
                    "error": "API key contains invalid characters. Only alphanumeric characters, underscores, and hyphens are allowed"
                }
            
            return {
                "valid": True,
                "message": "API key format is valid"
            }
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return {
                "valid": False,
                "error": "Failed to validate API key"
            }
    

            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error deleting API key for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete API key due to database constraint")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete API key for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete API key")
    
    async def get_decrypted_api_key(self, db: Session, user_id: int) -> Optional[str]:
        """
        Get decrypted API key for user (for internal use by AI service).
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Decrypted API key or None if not set
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.gemini_api_key:
            return None
        
        try:
            return decrypt_api_key(user.gemini_api_key)
        except Exception as e:
            logger.error(f"Failed to decrypt API key for user {user_id}: {e}")
            return None

    async def get_security_settings(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Get user's security settings.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Security settings dictionary
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            # Get current preferences
            preferences = await self.get_user_preferences(db, user_id)
            
            # Extract security settings or use defaults
            security_settings = preferences.get("securitySettings", {
                "twoFactorEnabled": False,
                "dataCollection": True,
                "sessionTimeout": 30
            })
            
            return security_settings
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get security settings for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get security settings")
    
    async def update_security_settings(self, db: Session, user_id: int, security_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user's security settings with validation.
        
        Args:
            db: Database session
            user_id: User ID
            security_settings: Security settings to update
            
        Returns:
            Updated security settings
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            # Get current preferences
            current_prefs = await self.get_user_preferences(db, user_id)
            
            # Validate security settings
            if "sessionTimeout" in security_settings:
                allowed_timeouts = [15, 30, 60, 120, 240, 480]
                if security_settings["sessionTimeout"] not in allowed_timeouts:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid session timeout. Must be one of: {', '.join(map(str, allowed_timeouts))} minutes"
                    )
            
            if "twoFactorEnabled" in security_settings:
                if not isinstance(security_settings["twoFactorEnabled"], bool):
                    raise HTTPException(status_code=400, detail="twoFactorEnabled must be a boolean")
            
            if "dataCollection" in security_settings:
                if not isinstance(security_settings["dataCollection"], bool):
                    raise HTTPException(status_code=400, detail="dataCollection must be a boolean")
            
            # Update security settings in preferences
            current_prefs["securitySettings"] = {
                **current_prefs.get("securitySettings", {}),
                **security_settings
            }
            
            # Save to database
            user.preferences = json.dumps(current_prefs)
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Successfully updated security settings for user {user_id}")
            return current_prefs["securitySettings"]
            
        except HTTPException:
            db.rollback()
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error updating security settings for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update security settings due to database constraint")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update security settings for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update security settings")


    
    async def update_security_settings(self, db: Session, user_id: int, security_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user's security settings with validation.
        
        Args:
            db: Database session
            user_id: User ID
            security_settings: Security settings to update
            
        Returns:
            Updated security settings
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            # Get current preferences
            current_prefs = await self.get_user_preferences(db, user_id)
            
            # Validate security settings
            if "sessionTimeout" in security_settings:
                allowed_timeouts = [15, 30, 60, 120, 240, 480]
                if security_settings["sessionTimeout"] not in allowed_timeouts:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid session timeout. Must be one of: {', '.join(map(str, allowed_timeouts))} minutes"
                    )
            
            if "twoFactorEnabled" in security_settings:
                if not isinstance(security_settings["twoFactorEnabled"], bool):
                    raise HTTPException(status_code=400, detail="twoFactorEnabled must be a boolean")
            
            if "dataCollection" in security_settings:
                if not isinstance(security_settings["dataCollection"], bool):
                    raise HTTPException(status_code=400, detail="dataCollection must be a boolean")
            
            # Update security settings
            current_security = current_prefs.get("securitySettings", {})
            current_security.update(security_settings)
            current_prefs["securitySettings"] = current_security
            
            # Save to database
            user.preferences = json.dumps(current_prefs)
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Successfully updated security settings for user {user_id}")
            return current_security
            
        except HTTPException:
            db.rollback()
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error updating security settings for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update security settings due to database constraint")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update security settings for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update security settings")
    
    async def get_notification_preferences(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Get user's notification preferences.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dictionary with notification preferences
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            # Get current preferences
            preferences = await self.get_user_preferences(db, user_id)
            return preferences.get("notifications", {
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
            })
        except Exception as e:
            logger.error(f"Failed to get notification preferences for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get notification preferences")
    
    async def update_integration_settings(self, db: Session, user_id: int, integration_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user's integration settings.
        
        Args:
            db: Database session
            user_id: User ID
            integration_settings: Integration settings to update
            
        Returns:
            Updated integration settings
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            # Get current preferences
            current_prefs = await self.get_user_preferences(db, user_id)
            
            # Update integration settings
            if "integrations" not in current_prefs:
                current_prefs["integrations"] = {}
            
            current_prefs["integrations"].update(integration_settings)
            
            # Save to database
            user.preferences = json.dumps(current_prefs)
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Successfully updated integration settings for user {user_id}")
            return current_prefs["integrations"]
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update integration settings for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update integration settings")
    
    async def update_team_settings(self, db: Session, user_id: int, team_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user's team settings.
        
        Args:
            db: Database session
            user_id: User ID
            team_settings: Team settings to update
            
        Returns:
            Updated team settings
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            # Get current preferences
            current_prefs = await self.get_user_preferences(db, user_id)
            
            # Update team settings
            if "team" not in current_prefs:
                current_prefs["team"] = {}
            
            current_prefs["team"].update(team_settings)
            
            # Also update team_id in user model if provided
            if "teamId" in team_settings:
                user.team_id = team_settings["teamId"]
            
            # Save to database
            user.preferences = json.dumps(current_prefs)
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Successfully updated team settings for user {user_id}")
            return current_prefs["team"]
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update team settings for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update team settings")
    
    async def update_api_access_settings(self, db: Session, user_id: int, api_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user's API access settings.
        
        Args:
            db: Database session
            user_id: User ID
            api_settings: API access settings to update
            
        Returns:
            Updated API access settings
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            # Get current preferences
            current_prefs = await self.get_user_preferences(db, user_id)
            
            # Update API access settings
            if "apiAccess" not in current_prefs:
                current_prefs["apiAccess"] = {}
            
            current_prefs["apiAccess"].update(api_settings)
            
            # Save to database
            user.preferences = json.dumps(current_prefs)
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Successfully updated API access settings for user {user_id}")
            return current_prefs["apiAccess"]
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update API access settings for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update API access settings")