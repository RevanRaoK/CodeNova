"""
Analysis Notification Service for real-time progress tracking.

This service provides:
- Real-time notifications for analysis progress
- WebSocket connections for live updates
- Email notifications for completed analyses
- Integration with notification service

Requirements covered: 2.1, 2.6
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.services.notification_service import NotificationService
from app.services.background_code_analysis_service import (
    background_code_analysis_service,
    AnalysisStatus,
    AnalysisResult
)

logger = logging.getLogger(__name__)


@dataclass
class AnalysisNotification:
    """Analysis notification data structure."""
    analysis_id: str
    user_id: str
    notification_type: str  # 'progress', 'completed', 'failed', 'cancelled'
    message: str
    progress_percentage: float = 0.0
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {
            'analysis_id': self.analysis_id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'message': self.message,
            'progress_percentage': self.progress_percentage,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class AnalysisNotificationService:
    """
    Service for managing analysis notifications and real-time updates.
    
    Features:
    - Real-time progress notifications
    - WebSocket integration for live updates
    - Email notifications for completion
    - Batch analysis progress tracking
    - User preference management
    """
    
    def __init__(self):
        self._websocket_connections: Dict[str, Set] = {}  # user_id -> set of websockets
        self._notification_preferences: Dict[str, Dict[str, bool]] = {}  # user_id -> preferences
        self._active_subscriptions: Dict[str, Set[str]] = {}  # user_id -> set of analysis_ids
        self._notification_history: Dict[str, List[AnalysisNotification]] = {}  # analysis_id -> notifications
    
    async def initialize(self):
        """Initialize the notification service."""
        try:
            # Initialize the notification service
            self._notification_service = NotificationService()
            
            # Register progress callbacks with background analysis service
            self._setup_analysis_callbacks()
            
            logger.info("Analysis notification service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize analysis notification service: {e}")
            raise
    
    def _setup_analysis_callbacks(self):
        """Set up callbacks with the background analysis service."""
        # This would be called when analyses are queued to register callbacks
        pass
    
    async def subscribe_to_analysis(self, user_id: str, analysis_id: str, websocket=None):
        """
        Subscribe a user to notifications for a specific analysis.
        
        Args:
            user_id: User ID to subscribe
            analysis_id: Analysis ID to subscribe to
            websocket: Optional WebSocket connection for real-time updates
        """
        try:
            # Add to active subscriptions
            if user_id not in self._active_subscriptions:
                self._active_subscriptions[user_id] = set()
            self._active_subscriptions[user_id].add(analysis_id)
            
            # Add WebSocket connection if provided
            if websocket:
                if user_id not in self._websocket_connections:
                    self._websocket_connections[user_id] = set()
                self._websocket_connections[user_id].add(websocket)
            
            # Register progress callback with analysis service
            background_code_analysis_service.add_progress_callback(
                analysis_id,
                lambda aid, msg, pct: asyncio.create_task(
                    self._handle_progress_update(aid, user_id, msg, pct)
                )
            )
            
            logger.info(f"User {user_id} subscribed to analysis {analysis_id}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe user {user_id} to analysis {analysis_id}: {e}")
    
    async def unsubscribe_from_analysis(self, user_id: str, analysis_id: str, websocket=None):
        """
        Unsubscribe a user from notifications for a specific analysis.
        
        Args:
            user_id: User ID to unsubscribe
            analysis_id: Analysis ID to unsubscribe from
            websocket: Optional WebSocket connection to remove
        """
        try:
            # Remove from active subscriptions
            if user_id in self._active_subscriptions:
                self._active_subscriptions[user_id].discard(analysis_id)
                if not self._active_subscriptions[user_id]:
                    del self._active_subscriptions[user_id]
            
            # Remove WebSocket connection if provided
            if websocket and user_id in self._websocket_connections:
                self._websocket_connections[user_id].discard(websocket)
                if not self._websocket_connections[user_id]:
                    del self._websocket_connections[user_id]
            
            logger.info(f"User {user_id} unsubscribed from analysis {analysis_id}")
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe user {user_id} from analysis {analysis_id}: {e}")
    
    async def _handle_progress_update(
        self, 
        analysis_id: str, 
        user_id: str, 
        message: str, 
        progress_percentage: float
    ):
        """
        Handle progress updates from the analysis service.
        
        Args:
            analysis_id: Analysis ID
            user_id: User ID
            message: Progress message
            progress_percentage: Progress percentage (0-100)
        """
        try:
            # Create notification
            notification = AnalysisNotification(
                analysis_id=analysis_id,
                user_id=user_id,
                notification_type='progress',
                message=message,
                progress_percentage=progress_percentage,
                metadata={'source': 'progress_update'}
            )
            
            # Store in history
            if analysis_id not in self._notification_history:
                self._notification_history[analysis_id] = []
            self._notification_history[analysis_id].append(notification)
            
            # Send real-time notifications
            await self._send_realtime_notification(notification)
            
            # Send completion notifications if analysis is done
            if progress_percentage >= 100.0:
                await self._handle_analysis_completion(analysis_id, user_id)
            
        except Exception as e:
            logger.error(f"Failed to handle progress update for analysis {analysis_id}: {e}")
    
    async def _handle_analysis_completion(self, analysis_id: str, user_id: str):
        """
        Handle analysis completion notifications.
        
        Args:
            analysis_id: Analysis ID
            user_id: User ID
        """
        try:
            # Get analysis result
            result = await background_code_analysis_service.get_analysis_status(analysis_id)
            
            if not result:
                logger.warning(f"Analysis {analysis_id} not found for completion notification")
                return
            
            # Determine notification type based on status
            if result.status == AnalysisStatus.COMPLETED:
                notification_type = 'completed'
                message = f"Analysis completed successfully with {len(result.issues)} issues found"
            elif result.status == AnalysisStatus.FAILED:
                notification_type = 'failed'
                message = f"Analysis failed: {result.error or 'Unknown error'}"
            elif result.status == AnalysisStatus.CANCELLED:
                notification_type = 'cancelled'
                message = "Analysis was cancelled"
            else:
                return  # Not a completion state
            
            # Create completion notification
            notification = AnalysisNotification(
                analysis_id=analysis_id,
                user_id=user_id,
                notification_type=notification_type,
                message=message,
                progress_percentage=100.0 if result.status == AnalysisStatus.COMPLETED else 0.0,
                metadata={
                    'issues_count': len(result.issues) if result.issues else 0,
                    'suggestions_count': len(result.suggestions) if result.suggestions else 0,
                    'processing_time': result.processing_time,
                    'analysis_type': result.request.analysis_type.value,
                    'language': result.request.language
                }
            )
            
            # Store in history
            if analysis_id not in self._notification_history:
                self._notification_history[analysis_id] = []
            self._notification_history[analysis_id].append(notification)
            
            # Send real-time notification
            await self._send_realtime_notification(notification)
            
            # Send email notification if enabled
            await self._send_email_notification(notification, result)
            
            # Clean up subscriptions
            await self.unsubscribe_from_analysis(user_id, analysis_id)
            
        except Exception as e:
            logger.error(f"Failed to handle analysis completion for {analysis_id}: {e}")
    
    async def _send_realtime_notification(self, notification: AnalysisNotification):
        """
        Send real-time notification via WebSocket.
        
        Args:
            notification: Notification to send
        """
        try:
            user_id = notification.user_id
            
            # Check if user has active WebSocket connections
            if user_id not in self._websocket_connections:
                return
            
            # Prepare notification data
            notification_data = {
                'type': 'analysis_notification',
                'data': notification.to_dict()
            }
            
            # Send to all user's WebSocket connections
            disconnected_websockets = set()
            
            for websocket in self._websocket_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(notification_data))
                except Exception as ws_error:
                    logger.warning(f"Failed to send WebSocket notification: {ws_error}")
                    disconnected_websockets.add(websocket)
            
            # Clean up disconnected WebSockets
            for websocket in disconnected_websockets:
                self._websocket_connections[user_id].discard(websocket)
            
            if not self._websocket_connections[user_id]:
                del self._websocket_connections[user_id]
            
        except Exception as e:
            logger.error(f"Failed to send real-time notification: {e}")
    
    async def _send_email_notification(self, notification: AnalysisNotification, result: AnalysisResult):
        """
        Send email notification for analysis completion.
        
        Args:
            notification: Notification data
            result: Analysis result
        """
        try:
            # Check user preferences for email notifications
            user_id = notification.user_id
            preferences = self._notification_preferences.get(user_id, {})
            
            if not preferences.get('email_notifications', True):
                return  # User has disabled email notifications
            
            # Only send email for completion, not progress
            if notification.notification_type not in ['completed', 'failed']:
                return
            
            # Prepare email content
            if notification.notification_type == 'completed':
                subject = f"Code Analysis Completed - {result.request.language}"
                
                # Create summary
                issues_count = len(result.issues) if result.issues else 0
                suggestions_count = len(result.suggestions) if result.suggestions else 0
                
                body = f"""
Your code analysis has been completed successfully!

Analysis Details:
- Language: {result.request.language}
- Analysis Type: {result.request.analysis_type.value}
- Processing Time: {result.processing_time:.2f} seconds

Results Summary:
- Issues Found: {issues_count}
- Suggestions: {suggestions_count}
- Quality Score: {result.summary.get('quality_score', 'N/A')}

You can view the detailed results in your dashboard.
"""
            
            elif notification.notification_type == 'failed':
                subject = f"Code Analysis Failed - {result.request.language}"
                body = f"""
Unfortunately, your code analysis has failed.

Error: {result.error or 'Unknown error occurred'}

Please try submitting your analysis again or contact support if the issue persists.
"""
            
            # Send email via notification service (simplified for now)
            # In a real implementation, this would integrate with an email service
            logger.info(f"Email notification would be sent to user {user_id}: {subject}")
            logger.info(f"Email body: {body[:100]}...")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    async def get_notification_history(self, analysis_id: str) -> List[Dict[str, Any]]:
        """
        Get notification history for an analysis.
        
        Args:
            analysis_id: Analysis ID to query
            
        Returns:
            List of notifications for the analysis
        """
        try:
            notifications = self._notification_history.get(analysis_id, [])
            return [notification.to_dict() for notification in notifications]
            
        except Exception as e:
            logger.error(f"Failed to get notification history for {analysis_id}: {e}")
            return []
    
    async def set_user_preferences(self, user_id: str, preferences: Dict[str, bool]):
        """
        Set notification preferences for a user.
        
        Args:
            user_id: User ID
            preferences: Notification preferences dictionary
        """
        try:
            self._notification_preferences[user_id] = preferences
            logger.info(f"Updated notification preferences for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to set notification preferences for user {user_id}: {e}")
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, bool]:
        """
        Get notification preferences for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            User's notification preferences
        """
        return self._notification_preferences.get(user_id, {
            'email_notifications': True,
            'realtime_notifications': True,
            'progress_notifications': True,
            'completion_notifications': True
        })
    
    async def notify_batch_progress(self, batch_id: str, user_id: str):
        """
        Send notifications for batch analysis progress.
        
        Args:
            batch_id: Batch ID
            user_id: User ID
        """
        try:
            batch_status = await background_code_analysis_service.get_batch_status(batch_id)
            
            if not batch_status:
                return
            
            total_analyses = batch_status['total_count']
            completed_analyses = batch_status['completed_count']
            failed_analyses = batch_status['failed_count']
            
            progress_percentage = (
                (completed_analyses + failed_analyses) / total_analyses * 100
                if total_analyses > 0 else 0
            )
            
            message = f"Batch analysis progress: {completed_analyses + failed_analyses}/{total_analyses} completed"
            
            # Create batch notification
            notification = AnalysisNotification(
                analysis_id=batch_id,
                user_id=user_id,
                notification_type='batch_progress',
                message=message,
                progress_percentage=progress_percentage,
                metadata={
                    'batch_id': batch_id,
                    'total_analyses': total_analyses,
                    'completed_analyses': completed_analyses,
                    'failed_analyses': failed_analyses
                }
            )
            
            # Send real-time notification
            await self._send_realtime_notification(notification)
            
        except Exception as e:
            logger.error(f"Failed to notify batch progress for {batch_id}: {e}")
    
    async def cleanup_old_notifications(self, older_than_hours: int = 24):
        """
        Clean up old notification history.
        
        Args:
            older_than_hours: Remove notifications older than this many hours
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            cleaned_count = 0
            
            for analysis_id in list(self._notification_history.keys()):
                notifications = self._notification_history[analysis_id]
                
                # Filter out old notifications
                recent_notifications = [
                    n for n in notifications
                    if n.timestamp > cutoff_time
                ]
                
                if len(recent_notifications) != len(notifications):
                    if recent_notifications:
                        self._notification_history[analysis_id] = recent_notifications
                    else:
                        del self._notification_history[analysis_id]
                    
                    cleaned_count += len(notifications) - len(recent_notifications)
            
            logger.info(f"Cleaned up {cleaned_count} old notifications")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old notifications: {e}")


# Global analysis notification service instance
analysis_notification_service = AnalysisNotificationService()


# Utility functions
async def subscribe_to_analysis_notifications(user_id: str, analysis_id: str, websocket=None):
    """Subscribe to analysis notifications."""
    await analysis_notification_service.subscribe_to_analysis(user_id, analysis_id, websocket)


async def unsubscribe_from_analysis_notifications(user_id: str, analysis_id: str, websocket=None):
    """Unsubscribe from analysis notifications."""
    await analysis_notification_service.unsubscribe_from_analysis(user_id, analysis_id, websocket)


async def get_analysis_notification_history(analysis_id: str) -> List[Dict[str, Any]]:
    """Get notification history for an analysis."""
    return await analysis_notification_service.get_notification_history(analysis_id)


async def initialize_analysis_notification_service():
    """Initialize the analysis notification service."""
    await analysis_notification_service.initialize()