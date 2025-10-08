from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.users import User
from app.schemas.users import UserProfile, UserProfileUpdate, UserPreferences, NotificationPreferences, PasswordChange, ThemePreference
from app.services.user_service import UserService
from app.services.notification_service import NotificationService
from pydantic import BaseModel, validator
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
user_service = UserService()
notification_service = NotificationService()

class ProfileUpdateResponse(BaseModel):
    profile: UserProfile
    message: str = "Profile updated successfully"
    
class PreferencesUpdateResponse(BaseModel):
    preferences: Dict[str, Any]
    message: str = "Preferences updated successfully"

@router.get("/{user_id}/profile", response_model=UserProfile)
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile information"""
    try:
        # Check if user can access this profile (self or admin)
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        profile = await user_service.get_user_profile(db, user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return profile
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )

@router.put("/{user_id}/profile", response_model=ProfileUpdateResponse)
async def update_user_profile(
    user_id: str,
    profile_data: UserProfileUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile information with real-time notifications"""
    try:
        # Check if user can update this profile (self or admin)
        if str(current_user.id) != str(user_id) and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        # Validate profile data
        if profile_data.email and profile_data.email != current_user.email:
            # Check if email is already taken
            existing_user = await user_service.get_user_by_email(db, profile_data.email)
            if existing_user and existing_user.id != int(user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        updated_profile = await user_service.update_user_profile(db, int(user_id), profile_data)
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Send real-time notification for profile update
        background_tasks.add_task(
            notification_service.send_profile_update_notification,
            user_id=int(user_id),
            updated_fields=profile_data.dict(exclude_unset=True)
        )
        
        return ProfileUpdateResponse(
            profile=updated_profile,
            message="Profile updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )

@router.get("/{user_id}/preferences")
async def get_user_preferences(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user preferences"""
    try:
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        preferences = await user_service.get_user_preferences(db, user_id)
        return preferences
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user preferences"
        )

@router.put("/{user_id}/preferences", response_model=PreferencesUpdateResponse)
async def update_user_preferences(
    user_id: str,
    preferences: UserPreferences,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences with real-time notifications"""
    try:
        if str(current_user.id) != str(user_id) and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        updated_preferences = await user_service.update_user_preferences(db, int(user_id), preferences)
        
        # Send real-time notification for preferences update
        background_tasks.add_task(
            notification_service.send_preferences_update_notification,
            user_id=int(user_id),
            updated_preferences=preferences.dict()
        )
        
        return PreferencesUpdateResponse(
            preferences=updated_preferences,
            message="Preferences updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user preferences"
        )

@router.put("/{user_id}/notifications")
async def update_notification_preferences(
    user_id: str,
    notifications: NotificationPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notification preferences"""
    try:
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        updated_notifications = await user_service.update_notification_preferences(db, user_id, notifications)
        return updated_notifications
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )

@router.put("/{user_id}/password")
async def change_password(
    user_id: str,
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        success = await user_service.change_password(db, user_id, password_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid current password"
            )
        
        return {"message": "Password changed successfully"}
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.post("/{user_id}/profile-picture")
async def upload_profile_picture(
    user_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile picture"""
    try:
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Validate file size (5MB limit)
        if file.size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 5MB"
            )
        
        url = await user_service.upload_profile_picture(db, user_id, file)
        return {"url": url}
    except Exception as e:
        logger.error(f"Error uploading profile picture: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile picture"
        )

@router.delete("/{user_id}/profile-picture")
async def delete_profile_picture(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete profile picture"""
    try:
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        success = await user_service.delete_profile_picture(db, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile picture not found"
            )
        
        return {"message": "Profile picture deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting profile picture: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete profile picture"
        )

@router.get("/{user_id}/theme")
async def get_theme_preference(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user theme preference"""
    try:
        if str(current_user.id) != str(user_id) and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        theme = await user_service.get_theme_preference(db, int(user_id))
        return {"theme": theme}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting theme preference: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get theme preference"
        )

@router.put("/{user_id}/theme")
async def update_theme_preference(
    user_id: str,
    theme_data: ThemePreference,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user theme preference"""
    try:
        if str(current_user.id) != str(user_id) and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        updated_preferences = await user_service.update_theme_preference(db, int(user_id), theme_data.theme)
        
        # Send real-time notification for theme update
        background_tasks.add_task(
            notification_service.send_theme_update_notification,
            user_id=int(user_id),
            theme=theme_data.theme
        )
        
        return {
            "theme": theme_data.theme,
            "message": "Theme preference updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating theme preference: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update theme preference"
        )

@router.get("/{user_id}/settings")
async def get_user_settings(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive user settings including preferences and notifications"""
    try:
        if str(current_user.id) != str(user_id) and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        settings = await user_service.get_user_settings(db, int(user_id))
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user settings"
        )

@router.put("/{user_id}/settings")
async def update_user_settings(
    user_id: str,
    settings: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update comprehensive user settings"""
    try:
        if str(current_user.id) != str(user_id) and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        updated_settings = await user_service.update_user_settings(db, int(user_id), settings)
        
        # Send real-time notification for settings update
        background_tasks.add_task(
            notification_service.send_settings_update_notification,
            user_id=int(user_id),
            updated_settings=settings
        )
        
        return {
            "settings": updated_settings,
            "message": "Settings updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user settings"
        )