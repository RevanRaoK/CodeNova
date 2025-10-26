from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for handling real-time notifications for user profile and settings updates."""
    
    def __init__(self):
        self.notification_channels = []
    
    async def send_profile_update_notification(self, user_id: int, updated_fields: Dict[str, Any]):
        """Send real-time notification for profile updates."""
        try:
            notification_data = {
                "type": "profile_update",
                "user_id": user_id,
                "updated_fields": updated_fields,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Profile updated successfully"
            }
            
            # Log the notification for now (can be extended to WebSocket/SSE later)
            logger.info(f"Profile update notification for user {user_id}: {json.dumps(notification_data)}")
            
            # Here you would typically send to WebSocket connections, SSE, or message queue
            await self._broadcast_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Failed to send profile update notification: {e}")
    
    async def send_preferences_update_notification(self, user_id: int, updated_preferences: Dict[str, Any]):
        """Send real-time notification for preferences updates."""
        try:
            notification_data = {
                "type": "preferences_update",
                "user_id": user_id,
                "updated_preferences": updated_preferences,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Preferences updated successfully"
            }
            
            logger.info(f"Preferences update notification for user {user_id}: {json.dumps(notification_data)}")
            await self._broadcast_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Failed to send preferences update notification: {e}")
    
    async def send_theme_update_notification(self, user_id: int, theme: str):
        """Send real-time notification for theme updates."""
        try:
            notification_data = {
                "type": "theme_update",
                "user_id": user_id,
                "theme": theme,
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Theme changed to {theme}"
            }
            
            logger.info(f"Theme update notification for user {user_id}: {json.dumps(notification_data)}")
            await self._broadcast_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Failed to send theme update notification: {e}")
    
    async def send_settings_update_notification(self, user_id: int, updated_settings: Dict[str, Any]):
        """Send real-time notification for comprehensive settings updates."""
        try:
            notification_data = {
                "type": "settings_update",
                "user_id": user_id,
                "updated_settings": updated_settings,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Settings updated successfully"
            }
            
            logger.info(f"Settings update notification for user {user_id}: {json.dumps(notification_data)}")
            await self._broadcast_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Failed to send settings update notification: {e}")
    
    async def _broadcast_notification(self, notification_data: Dict[str, Any]):
        """Broadcast notification to all registered channels."""
        # This is a placeholder for actual notification broadcasting
        # In a real implementation, this would:
        # 1. Send to WebSocket connections for the specific user
        # 2. Send to Server-Sent Events (SSE) streams
        # 3. Push to message queues (Redis, RabbitMQ, etc.)
        # 4. Send push notifications to mobile devices
        
        # For now, we'll just log the notification
        logger.info(f"Broadcasting notification: {json.dumps(notification_data)}")
        
        # Example WebSocket broadcasting (would need WebSocket manager):
        # await websocket_manager.send_to_user(notification_data["user_id"], notification_data)
        
        # Example Redis pub/sub (would need Redis client):
        # await redis_client.publish(f"user:{notification_data['user_id']}", json.dumps(notification_data))
    
    def register_notification_channel(self, channel_type: str, channel_config: Dict[str, Any]):
        """Register a notification channel (WebSocket, SSE, etc.)."""
        self.notification_channels.append({
            "type": channel_type,
            "config": channel_config,
            "registered_at": datetime.utcnow()
        })
        logger.info(f"Registered notification channel: {channel_type}")
    
    def get_notification_channels(self) -> list:
        """Get all registered notification channels."""
        return self.notification_channels    

    async def send_settings_update_notification(self, user_id: int, updated_fields: list):
        """Send real-time notification for settings updates."""
        try:
            notification_data = {
                "type": "settings_update",
                "user_id": user_id,
                "updated_fields": updated_fields,
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Settings updated: {', '.join(updated_fields)}"
            }
            
            logger.info(f"Settings update notification for user {user_id}: {json.dumps(notification_data)}")
            await self._broadcast_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Failed to send settings update notification: {e}")
    
    async def send_theme_update_notification(self, user_id: int, theme: str):
        """Send real-time notification for theme updates."""
        try:
            notification_data = {
                "type": "theme_update",
                "user_id": user_id,
                "theme": theme,
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Theme changed to {theme}"
            }
            
            logger.info(f"Theme update notification for user {user_id}: {json.dumps(notification_data)}")
            await self._broadcast_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Failed to send theme update notification: {e}")
    
    async def send_security_update_notification(self, user_id: int, updated_settings: dict):
        """Send real-time notification for security settings updates."""
        try:
            notification_data = {
                "type": "security_update",
                "user_id": user_id,
                "updated_settings": updated_settings,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Security settings updated"
            }
            
            logger.info(f"Security update notification for user {user_id}: {json.dumps(notification_data)}")
            await self._broadcast_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Failed to send security update notification: {e}")
    
    async def send_upload_completion_notification(
        self, 
        user_id: int, 
        batch_id: str, 
        uploaded_files: int, 
        total_files: int, 
        failed_files: int = 0
    ):
        """Send real-time notification for file upload completion."""
        try:
            # Create appropriate message based on upload results
            if failed_files == 0:
                message = f"Successfully uploaded {uploaded_files} file{'s' if uploaded_files != 1 else ''}"
                notification_type = "upload_success"
            elif uploaded_files > 0:
                message = f"Uploaded {uploaded_files} of {total_files} files ({failed_files} failed)"
                notification_type = "upload_partial"
            else:
                message = f"Upload failed for all {total_files} files"
                notification_type = "upload_failed"
            
            notification_data = {
                "type": notification_type,
                "user_id": user_id,
                "batch_id": batch_id,
                "uploaded_files": uploaded_files,
                "total_files": total_files,
                "failed_files": failed_files,
                "timestamp": datetime.utcnow().isoformat(),
                "message": message
            }
            
            logger.info(f"Upload completion notification for user {user_id}: {json.dumps(notification_data)}")
            await self._broadcast_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Failed to send upload completion notification: {e}")

    async def _broadcast_notification(self, notification_data: dict):
        """Broadcast notification to all channels."""
        # This is a placeholder for actual notification broadcasting
        # In a real implementation, this would send to WebSocket connections,
        # Server-Sent Events, or a message queue
        logger.debug(f"Broadcasting notification: {notification_data}")
        pass