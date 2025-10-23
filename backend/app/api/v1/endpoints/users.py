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
        if str(current_user.id) != str(user_id) and current_user.role.value != "admin":
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
    except HTTPException:
        raise
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
        if str(current_user.id) != str(user_id) and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        preferences = await user_service.get_user_preferences(db, int(user_id))
        return preferences
    except HTTPException:
        raise
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
        if str(current_user.id) != str(user_id) and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        updated_notifications = await user_service.update_notification_preferences(db, user_id, notifications)
        return updated_notifications
    except HTTPException:
        raise
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
        if str(current_user.id) != str(user_id) and current_user.role.value != "admin":
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
        if str(current_user.id) != str(user_id) and current_user.role.value != "admin":
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


# API Key Management Endpoints

class ApiKeyRequest(BaseModel):
    """Request model for API key operations."""
    apiKey: str
    
    @validator('apiKey')
    def validate_api_key(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('API key must be at least 10 characters')
        return v.strip()


@router.get("/api-key")
async def get_api_key_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if user has a Gemini API key configured.
    Returns hasKey boolean and masked key preview if available.
    
    Requirements: 4.8, 6.6
    """
    try:
        status = await user_service.get_api_key_status(db, current_user.id)
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting API key status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get API key status"
        )


@router.put("/api-key")
async def save_api_key(
    api_key_data: ApiKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save encrypted Gemini API key for the current user.
    The key will be used for AI analysis requests instead of the default key.
    
    Requirements: 4.8, 4.9, 6.7, 6.8
    """
    try:
        result = await user_service.save_api_key(db, current_user.id, api_key_data.apiKey)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save API key"
        )


@router.delete("/api-key")
async def delete_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete user's Gemini API key.
    After deletion, the default API key will be used for analysis.
    
    Requirements: 4.8, 6.8
    """
    try:
        result = await user_service.delete_api_key(db, current_user.id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key"
        )


@router.post("/api-key/validate")
async def validate_api_key(
    api_key_data: ApiKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate Gemini API key format without saving it.
    Useful for real-time validation in the frontend.
    
    Requirements: 4.9, 6.7
    """
    try:
        result = await user_service.validate_api_key(api_key_data.apiKey)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate API key"
        )


# Current user convenience endpoints (without user_id in path)

@router.get("/profile", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile information.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.5
    """
    try:
        profile = await user_service.get_user_profile(db, str(current_user.id))
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.put("/profile", response_model=ProfileUpdateResponse)
async def update_current_user_profile(
    profile_data: UserProfileUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.8, 6.5
    """
    try:
        # Validate email if changed
        if profile_data.email and profile_data.email != current_user.email:
            existing_user = await user_service.get_user_by_email(db, profile_data.email)
            if existing_user and existing_user.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        updated_profile = await user_service.update_user_profile(db, current_user.id, profile_data)
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Send real-time notification
        background_tasks.add_task(
            notification_service.send_profile_update_notification,
            user_id=current_user.id,
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


@router.get("/preferences")
async def get_current_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's preferences.
    
    Requirements: 4.2, 4.3, 6.4
    """
    try:
        preferences = await user_service.get_user_preferences(db, str(current_user.id))
        return preferences
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user preferences"
        )


@router.put("/preferences", response_model=PreferencesUpdateResponse)
async def update_current_user_preferences(
    preferences: UserPreferences,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's preferences.
    
    Requirements: 4.2, 4.3, 6.4
    """
    try:
        updated_preferences = await user_service.update_user_preferences(db, current_user.id, preferences)
        
        # Send real-time notification
        background_tasks.add_task(
            notification_service.send_preferences_update_notification,
            user_id=current_user.id,
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


@router.get("/notifications")
async def get_current_user_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's notification preferences.
    
    Requirements: 4.4, 6.4
    """
    try:
        notifications = await user_service.get_notification_preferences(db, str(current_user.id))
        return notifications
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification preferences"
        )


@router.put("/notifications")
async def update_current_user_notifications(
    notifications: NotificationPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's notification preferences.
    
    Requirements: 4.4, 6.4
    """
    try:
        updated_notifications = await user_service.update_notification_preferences(
            db, str(current_user.id), notifications
        )
        return {
            "notifications": updated_notifications,
            "message": "Notification preferences updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )


class SecuritySettings(BaseModel):
    """Security settings model."""
    twoFactorEnabled: bool = False
    dataCollection: bool = True
    sessionTimeout: int = 30
    
    @validator('sessionTimeout')
    def validate_session_timeout(cls, v):
        if v not in [15, 30, 60, 120, 240, 480]:
            raise ValueError('Session timeout must be one of: 15, 30, 60, 120, 240, 480 minutes')
        return v


@router.get("/{user_id}/security")
async def get_security_settings(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's security settings.
    
    Requirements: 4.5, 6.4
    """
    try:
        if str(current_user.id) != str(user_id) and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        security_settings = await user_service.get_security_settings(db, int(user_id))
        return security_settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting security settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security settings"
        )


@router.put("/{user_id}/security")
async def update_security_settings(
    user_id: str,
    security_settings: SecuritySettings,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's security settings.
    
    Requirements: 4.5, 4.10, 4.11, 6.4
    """
    try:
        if str(current_user.id) != str(user_id) and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
        
        updated_settings = await user_service.update_security_settings(
            db, int(user_id), security_settings.dict()
        )
        
        # Send real-time notification for security settings update
        background_tasks.add_task(
            notification_service.send_security_update_notification,
            user_id=int(user_id),
            updated_settings=security_settings.dict()
        )
        
        return {
            "securitySettings": updated_settings,
            "message": "Security settings updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating security settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update security settings"
        )


@router.post("/profile-picture")
async def upload_current_user_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload profile picture for current user.
    
    Requirements: 5.7, 9.1
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Validate file size (5MB limit)
        if file.size and file.size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 5MB"
            )
        
        url = await user_service.upload_profile_picture(db, str(current_user.id), file)
        return {
            "success": True,
            "profilePictureUrl": url,
            "message": "Profile picture uploaded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading profile picture: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile picture"
        )