"""
Settings API endpoints for comprehensive user settings management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.users import User
from app.schemas.settings import (
    ComprehensiveSettings,
    SettingsUpdateRequest,
    SettingsUpdateResponse,
    GeneralSettings,
    NotificationSettings,
    SecuritySettings,
    IntegrationSettings,
    TeamSettings,
    APIAccessSettings,
    SettingsValidationError,
    SettingsErrorResponse
)
from app.services.user_service import UserService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter()
user_service = UserService()
notification_service = NotificationService()


@router.get("/", response_model=ComprehensiveSettings)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive user settings.
    
    Requirements: 4.2, 4.3, 6.4
    """
    try:
        settings = await user_service.get_user_settings(db, current_user.id)
        
        # Convert to comprehensive settings format
        comprehensive_settings = ComprehensiveSettings(
            general=GeneralSettings(
                theme=settings.get("preferences", {}).get("theme", "light"),
                language=settings.get("preferences", {}).get("language", "en"),
                timezone=settings.get("preferences", {}).get("timezone", "UTC"),
                defaultProgrammingLanguage=settings.get("preferences", {}).get("defaultProgrammingLanguage", "javascript"),
                aiModel=settings.get("preferences", {}).get("aiModel", "gemini-pro"),
                codeEditorTheme=settings.get("preferences", {}).get("codeEditorTheme", "vs-light"),
                autoSave=settings.get("preferences", {}).get("autoSave", True),
                showLineNumbers=settings.get("preferences", {}).get("showLineNumbers", True)
            ),
            notifications=NotificationSettings(
                emailNotifications=settings.get("notifications", {}).get("emailNotifications", {}),
                pushNotifications=settings.get("notifications", {}).get("pushNotifications", {}),
                frequency=settings.get("notifications", {}).get("frequency", "immediate")
            ),
            security=SecuritySettings(
                twoFactorEnabled=settings.get("security", {}).get("twoFactorEnabled", False),
                dataCollection=settings.get("security", {}).get("dataCollection", True),
                sessionTimeout=settings.get("security", {}).get("sessionTimeout", 30)
            ),
            integrations=IntegrationSettings(
                githubConnected=settings.get("integrations", {}).get("githubConnected", False),
                gitlabConnected=settings.get("integrations", {}).get("gitlabConnected", False),
                slackConnected=settings.get("integrations", {}).get("slackConnected", False),
                discordConnected=settings.get("integrations", {}).get("discordConnected", False),
                githubWebhooksEnabled=settings.get("integrations", {}).get("githubWebhooksEnabled", False),
                autoSyncRepositories=settings.get("integrations", {}).get("autoSyncRepositories", True),
                notifyOnPullRequests=settings.get("integrations", {}).get("notifyOnPullRequests", True)
            ),
            team=TeamSettings(
                teamId=settings.get("team", {}).get("teamId"),
                teamRole=settings.get("team", {}).get("teamRole", "member"),
                allowTeamInvitations=settings.get("team", {}).get("allowTeamInvitations", True),
                shareAnalyticsWithTeam=settings.get("team", {}).get("shareAnalyticsWithTeam", False),
                autoJoinTeamProjects=settings.get("team", {}).get("autoJoinTeamProjects", True)
            ),
            apiAccess=APIAccessSettings(
                hasPersonalApiKey=bool(current_user.gemini_api_key),
                apiKeyPreview=None,  # Will be populated by service
                usePersonalApiKey=settings.get("apiAccess", {}).get("usePersonalApiKey", False),
                apiRateLimit=settings.get("apiAccess", {}).get("apiRateLimit", 1000),
                allowApiKeySharing=settings.get("apiAccess", {}).get("allowApiKeySharing", False)
            )
        )
        
        return comprehensive_settings
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user settings"
        )


@router.put("/", response_model=SettingsUpdateResponse)
async def update_user_settings(
    settings_update: SettingsUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update comprehensive user settings with validation.
    
    Requirements: 4.1, 4.2, 4.3, 4.10, 4.11, 6.4
    """
    try:
        updated_fields = []
        validation_errors = []
        
        # Get current settings
        current_settings = await user_service.get_user_settings(db, current_user.id)
        
        # Update general settings
        if settings_update.general:
            try:
                general_dict = settings_update.general.dict()
                await user_service.update_user_preferences(db, current_user.id, general_dict)
                updated_fields.append("general")
            except ValueError as e:
                validation_errors.append(SettingsValidationError(
                    field="general",
                    message=str(e),
                    value=settings_update.general.dict()
                ))
        
        # Update notification settings
        if settings_update.notifications:
            try:
                notifications_dict = settings_update.notifications.dict()
                await user_service.update_notification_preferences(db, current_user.id, notifications_dict)
                updated_fields.append("notifications")
            except ValueError as e:
                validation_errors.append(SettingsValidationError(
                    field="notifications",
                    message=str(e),
                    value=settings_update.notifications.dict()
                ))
        
        # Update security settings
        if settings_update.security:
            try:
                security_dict = settings_update.security.dict()
                await user_service.update_security_settings(db, current_user.id, security_dict)
                updated_fields.append("security")
            except ValueError as e:
                validation_errors.append(SettingsValidationError(
                    field="security",
                    message=str(e),
                    value=settings_update.security.dict()
                ))
        
        # Update integration settings
        if settings_update.integrations:
            try:
                integrations_dict = settings_update.integrations.dict()
                await user_service.update_integration_settings(db, current_user.id, integrations_dict)
                updated_fields.append("integrations")
            except ValueError as e:
                validation_errors.append(SettingsValidationError(
                    field="integrations",
                    message=str(e),
                    value=settings_update.integrations.dict()
                ))
        
        # Update team settings
        if settings_update.team:
            try:
                team_dict = settings_update.team.dict()
                await user_service.update_team_settings(db, current_user.id, team_dict)
                updated_fields.append("team")
            except ValueError as e:
                validation_errors.append(SettingsValidationError(
                    field="team",
                    message=str(e),
                    value=settings_update.team.dict()
                ))
        
        # Update API access settings
        if settings_update.apiAccess:
            try:
                api_dict = settings_update.apiAccess.dict()
                await user_service.update_api_access_settings(db, current_user.id, api_dict)
                updated_fields.append("apiAccess")
            except ValueError as e:
                validation_errors.append(SettingsValidationError(
                    field="apiAccess",
                    message=str(e),
                    value=settings_update.apiAccess.dict()
                ))
        
        # If there are validation errors, return them
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Validation failed",
                    "details": [error.dict() for error in validation_errors],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Get updated settings
        updated_settings = await get_user_settings(current_user, db)
        
        # Send notification
        background_tasks.add_task(
            notification_service.send_settings_update_notification,
            user_id=current_user.id,
            updated_fields=updated_fields
        )
        
        return SettingsUpdateResponse(
            settings=updated_settings,
            message="Settings updated successfully",
            updatedFields=updated_fields,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user settings"
        )


@router.get("/general", response_model=GeneralSettings)
async def get_general_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get general settings.
    
    Requirements: 4.1, 4.2, 4.3
    """
    try:
        preferences = await user_service.get_user_preferences(db, current_user.id)
        user_prefs = preferences.get("userPreferences", {})
        
        return GeneralSettings(
            theme=user_prefs.get("theme", "light"),
            language=user_prefs.get("language", "en"),
            timezone=user_prefs.get("timezone", "UTC"),
            defaultProgrammingLanguage=user_prefs.get("defaultProgrammingLanguage", "javascript"),
            aiModel=user_prefs.get("aiModel", "gemini-pro"),
            codeEditorTheme=user_prefs.get("codeEditorTheme", "vs-light"),
            autoSave=user_prefs.get("autoSave", True),
            showLineNumbers=user_prefs.get("showLineNumbers", True)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting general settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get general settings"
        )


@router.put("/general")
async def update_general_settings(
    general_settings: GeneralSettings,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update general settings.
    
    Requirements: 4.1, 4.2, 4.3, 4.10, 4.11
    """
    try:
        # Convert to preferences format
        preferences_dict = general_settings.dict()
        
        # Update preferences
        await user_service.update_user_preferences(db, current_user.id, preferences_dict)
        
        # Send notification
        background_tasks.add_task(
            notification_service.send_settings_update_notification,
            user_id=current_user.id,
            updated_fields=["general"]
        )
        
        return {
            "message": "General settings updated successfully",
            "settings": general_settings,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating general settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update general settings"
        )


@router.get("/notifications", response_model=NotificationSettings)
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notification settings.
    
    Requirements: 4.4, 6.4
    """
    try:
        notifications = await user_service.get_notification_preferences(db, current_user.id)
        
        return NotificationSettings(
            emailNotifications=notifications.get("emailNotifications", {}),
            pushNotifications=notifications.get("pushNotifications", {}),
            frequency=notifications.get("frequency", "immediate")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification settings"
        )


@router.put("/notifications")
async def update_notification_settings(
    notification_settings: NotificationSettings,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update notification settings.
    
    Requirements: 4.4, 4.10, 4.11, 6.4
    """
    try:
        # Update notification preferences
        notifications_dict = notification_settings.dict()
        await user_service.update_notification_preferences(db, current_user.id, notifications_dict)
        
        # Send notification
        background_tasks.add_task(
            notification_service.send_settings_update_notification,
            user_id=current_user.id,
            updated_fields=["notifications"]
        )
        
        return {
            "message": "Notification settings updated successfully",
            "settings": notification_settings,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification settings"
        )


@router.get("/security", response_model=SecuritySettings)
async def get_security_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get security settings.
    
    Requirements: 4.5, 6.4
    """
    try:
        security = await user_service.get_security_settings(db, current_user.id)
        
        return SecuritySettings(
            twoFactorEnabled=security.get("twoFactorEnabled", False),
            dataCollection=security.get("dataCollection", True),
            sessionTimeout=security.get("sessionTimeout", 30)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting security settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security settings"
        )


@router.put("/security")
async def update_security_settings(
    security_settings: SecuritySettings,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update security settings.
    
    Requirements: 4.5, 4.10, 4.11, 6.4
    """
    try:
        # Update security settings
        security_dict = security_settings.dict()
        await user_service.update_security_settings(db, current_user.id, security_dict)
        
        # Send notification
        background_tasks.add_task(
            notification_service.send_settings_update_notification,
            user_id=current_user.id,
            updated_fields=["security"]
        )
        
        return {
            "message": "Security settings updated successfully",
            "settings": security_settings,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating security settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update security settings"
        )