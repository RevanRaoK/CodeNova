"""
Analytics API endpoints for dashboard data retrieval and real-time updates.

This module provides:
- Analytics dashboard data endpoints
- Real-time analytics via WebSocket
- Data export functionality
- Performance metrics and health checks

Requirements covered: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import json
import asyncio
from datetime import datetime, timedelta
import redis
import logging

from app.api.deps import get_db, get_current_user, get_redis_client
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    AnalyticsRequest, AcceptanceRatesResponse, RejectionPatternsResponse,
    UsageStatisticsResponse, LearningProgressResponse, AnalyticsDashboardResponse,
    AnalyticsExportRequest, AnalyticsExportResponse, RealTimeAnalyticsUpdate,
    AnalyticsHealthCheck, TimeframeEnum
)
from app.models.users import User

logger = logging.getLogger(__name__)

router = APIRouter()


class WebSocketManager:
    """Manager for WebSocket connections for real-time analytics updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: Optional[int] = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
    
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting WebSocket message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            if connection in self.active_connections:
                self.active_connections.remove(connection)
    
    async def send_to_user(self, user_id: int, message: str):
        if user_id in self.user_connections:
            disconnected = []
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending user-specific WebSocket message: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                if connection in self.user_connections[user_id]:
                    self.user_connections[user_id].remove(connection)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


@router.get("/user-stats/{user_id}")
async def get_user_stats_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    Get user statistics for a specific user including total reviews, analyses, success rate, and recent activity.
    
    Requirements: 1.1, 1.3, 1.4, 1.5, 1.6
    """
    try:
        # Check if user is requesting their own data or has admin access
        if user_id != current_user.id:
            if not hasattr(current_user, 'role') or current_user.role != 'admin':
                raise HTTPException(status_code=403, detail="Access denied. Can only view your own statistics.")
        
        analytics_service = AnalyticsService(db, redis_client)
        result = await analytics_service.get_user_stats(user_id=user_id)
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user stats for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user statistics")


@router.get("/user-stats")
async def get_current_user_stats(
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    Get user statistics for the current user including total reviews, analyses, success rate, and recent activity.
    
    Requirements: 1.1, 1.3, 1.4, 1.5, 1.6
    """
    try:
        analytics_service = AnalyticsService(db, redis_client)
        result = await analytics_service.get_user_stats(user_id=current_user.id)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user statistics")


@router.get("/usage-trends")
async def get_usage_trends(
    timeframe: str = Query("30d", description="Time period for analysis (7d, 30d, 90d, 1y)"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    Get usage trends over time for the current user.
    
    Requirements: 1.3, 1.4, 1.5
    """
    try:
        analytics_service = AnalyticsService(db, redis_client)
        result = await analytics_service.get_usage_trends(
            user_id=current_user.id,
            timeframe=timeframe
        )
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error getting usage trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve usage trends")


@router.get("/feedback-distribution")
async def get_feedback_distribution(
    timeframe: str = Query("30d", description="Time period for analysis (7d, 30d, 90d, 1y)"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    Get feedback distribution by type for the current user.
    
    Requirements: 1.4, 1.5, 1.6
    """
    try:
        analytics_service = AnalyticsService(db, redis_client)
        result = await analytics_service.get_feedback_distribution(
            user_id=current_user.id,
            timeframe=timeframe
        )
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error getting feedback distribution: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback distribution")


@router.get("/issue-trends")
async def get_issue_trends(
    timeframe: str = Query("30d", description="Time period for analysis (7d, 30d, 90d)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (admin only)"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    Get issue trends over time showing errors, security issues, and warnings.
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    try:
        # Check admin access for other users' data
        if user_id and user_id != current_user.id:
            if not hasattr(current_user, 'role') or current_user.role != 'admin':
                raise HTTPException(status_code=403, detail="Admin access required to view other users' data")
        
        target_user_id = user_id if user_id and hasattr(current_user, 'role') and current_user.role == 'admin' else current_user.id
        
        analytics_service = AnalyticsService(db, redis_client)
        result = await analytics_service.get_issue_trends(
            user_id=target_user_id,
            timeframe=timeframe
        )
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error getting issue trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve issue trends")


@router.get("/criticality-distribution")
async def get_criticality_distribution(
    timeframe: str = Query("30d", description="Time period for analysis (7d, 30d, 90d)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (admin only)"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    Get criticality distribution showing severity breakdown of issues.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    try:
        # Check admin access for other users' data
        if user_id and user_id != current_user.id:
            if not hasattr(current_user, 'role') or current_user.role != 'admin':
                raise HTTPException(status_code=403, detail="Admin access required to view other users' data")
        
        target_user_id = user_id if user_id and hasattr(current_user, 'role') and current_user.role == 'admin' else current_user.id
        
        analytics_service = AnalyticsService(db, redis_client)
        result = await analytics_service.get_criticality_distribution(
            user_id=target_user_id,
            timeframe=timeframe
        )
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error getting criticality distribution: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve criticality distribution")


@router.get("/acceptance-rates", response_model=AcceptanceRatesResponse)
async def get_acceptance_rates(
    timeframe: TimeframeEnum = Query(TimeframeEnum.THIRTY_DAYS, description="Time period for analysis"),
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (admin only)"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    Get acceptance rates for AI suggestions.
    
    Requirements: 2.1, 2.2
    """
    try:
        # Check if user is requesting data for another user (admin only)
        if user_id and user_id != current_user.id:
            if not hasattr(current_user, 'role') or current_user.role != 'admin':
                raise HTTPException(status_code=403, detail="Admin access required to view other users' data")
        
        # Use current user ID if not specified or not admin
        target_user_id = user_id if user_id and hasattr(current_user, 'role') and current_user.role == 'admin' else current_user.id
        
        analytics_service = AnalyticsService(db, redis_client)
        result = await analytics_service.get_acceptance_rates(
            user_id=target_user_id,
            timeframe=timeframe.value,
            pattern_type=pattern_type
        )
        
        return AcceptanceRatesResponse(**result)
    
    except Exception as e:
        logger.error(f"Error getting acceptance rates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve acceptance rates")


@router.get("/rejection-patterns", response_model=RejectionPatternsResponse)
async def get_rejection_patterns(
    timeframe: TimeframeEnum = Query(TimeframeEnum.THIRTY_DAYS, description="Time period for analysis"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (admin only)"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    Get rejection patterns and reasons analysis.
    
    Requirements: 2.2, 2.3
    """
    try:
        # Check admin access for other users' data
        if user_id and user_id != current_user.id:
            if not hasattr(current_user, 'role') or current_user.role != 'admin':
                raise HTTPException(status_code=403, detail="Admin access required to view other users' data")
        
        target_user_id = user_id if user_id and hasattr(current_user, 'role') and current_user.role == 'admin' else current_user.id
        
        analytics_service = AnalyticsService(db, redis_client)
        result = await analytics_service.get_rejection_patterns(
            user_id=target_user_id,
            timeframe=timeframe.value
        )
        
        return RejectionPatternsResponse(**result)
    
    except Exception as e:
        logger.error(f"Error getting rejection patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rejection patterns")


@router.get("/usage-statistics", response_model=UsageStatisticsResponse)
async def get_usage_statistics(
    timeframe: TimeframeEnum = Query(TimeframeEnum.THIRTY_DAYS, description="Time period for analysis"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (admin only)"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    Get usage statistics and activity metrics.
    
    Requirements: 2.3, 2.4
    """
    try:
        # Check admin access for other users' data
        if user_id and user_id != current_user.id:
            if not hasattr(current_user, 'role') or current_user.role != 'admin':
                raise HTTPException(status_code=403, detail="Admin access required to view other users' data")
        
        target_user_id = user_id if user_id and hasattr(current_user, 'role') and current_user.role == 'admin' else current_user.id
        
        analytics_service = AnalyticsService(db, redis_client)
        result = await analytics_service.get_usage_statistics(
            user_id=target_user_id,
            timeframe=timeframe.value
        )
        
        return UsageStatisticsResponse(**result)
    
    except Exception as e:
        logger.error(f"Error getting usage statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve usage statistics")


@router.get("/learning-progress", response_model=LearningProgressResponse)
async def get_learning_progress(
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI model learning progress indicators.
    
    Requirements: 2.4, 2.5
    """
    try:
        analytics_service = AnalyticsService(db, redis_client)
        result = await analytics_service.get_learning_progress()
        
        return LearningProgressResponse(**result)
    
    except Exception as e:
        logger.error(f"Error getting learning progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve learning progress")


@router.get("/dashboard-data")
async def get_dashboard_data(
    timeframe: str = Query("30d", description="Time period for analysis (7d, 30d, 90d, 1y)"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive dashboard data for the current user.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
    """
    try:
        analytics_service = AnalyticsService(db, redis_client)
        result = await analytics_service.get_dashboard_data(
            user_id=current_user.id,
            timeframe=timeframe
        )
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def get_analytics_dashboard(
    timeframe: TimeframeEnum = Query(TimeframeEnum.THIRTY_DAYS, description="Time period for analysis"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (admin only)"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive analytics dashboard data (admin endpoint).
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """
    try:
        # Check admin access for other users' data
        if user_id and user_id != current_user.id:
            if not hasattr(current_user, 'role') or current_user.role != 'admin':
                raise HTTPException(status_code=403, detail="Admin access required to view other users' data")
        
        target_user_id = user_id if user_id and hasattr(current_user, 'role') and current_user.role == 'admin' else current_user.id
        
        analytics_service = AnalyticsService(db, redis_client)
        result = await analytics_service.get_analytics_dashboard_data(
            user_id=target_user_id,
            timeframe=timeframe.value
        )
        
        return AnalyticsDashboardResponse(**result)
    
    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics dashboard")


class DateRange:
    """Simple date range class for export functionality."""
    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date


@router.post("/export", response_model=AnalyticsExportResponse)
async def export_analytics_data(
    export_request: AnalyticsExportRequest,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    Export analytics data in specified format.
    
    Requirements: 2.5
    """
    try:
        # Create date range if provided
        date_range = None
        if export_request.start_date and export_request.end_date:
            date_range = DateRange(
                start_date=export_request.start_date,
                end_date=export_request.end_date
            )
        
        # Check admin access for other users' data
        target_user_id = export_request.user_id
        if target_user_id and target_user_id != current_user.id:
            if not hasattr(current_user, 'role') or current_user.role != 'admin':
                raise HTTPException(status_code=403, detail="Admin access required to export other users' data")
        
        analytics_service = AnalyticsService(db, redis_client)
        result = await analytics_service.export_analytics_data(
            export_format=export_request.export_format.value,
            date_range=date_range,
            user_id=target_user_id
        )
        
        return AnalyticsExportResponse(**result)
    
    except Exception as e:
        logger.error(f"Error exporting analytics data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export analytics data")


@router.websocket("/ws/real-time")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    WebSocket endpoint for real-time analytics updates.
    
    Requirements: 2.4, 2.5
    """
    await websocket_manager.connect(websocket, user_id)
    
    try:
        analytics_service = AnalyticsService(db, redis_client)
        
        # Send initial analytics data
        initial_data = await analytics_service.get_analytics_dashboard_data(user_id=user_id)
        update = RealTimeAnalyticsUpdate(
            update_type="dashboard_refresh",
            data=initial_data,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id
        )
        await websocket_manager.send_personal_message(update.model_dump_json(), websocket)
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for client message or timeout
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle client requests for specific data
                try:
                    request_data = json.loads(message)
                    request_type = request_data.get("type")
                    
                    if request_type == "get_acceptance_rates":
                        timeframe = request_data.get("timeframe", "30d")
                        data = await analytics_service.get_acceptance_rates(user_id=user_id, timeframe=timeframe)
                        update = RealTimeAnalyticsUpdate(
                            update_type="acceptance_rate",
                            data=data,
                            timestamp=datetime.utcnow().isoformat(),
                            user_id=user_id
                        )
                        await websocket_manager.send_personal_message(update.model_dump_json(), websocket)
                    
                    elif request_type == "get_usage_stats":
                        timeframe = request_data.get("timeframe", "30d")
                        data = await analytics_service.get_usage_statistics(user_id=user_id, timeframe=timeframe)
                        update = RealTimeAnalyticsUpdate(
                            update_type="usage_stats",
                            data=data,
                            timestamp=datetime.utcnow().isoformat(),
                            user_id=user_id
                        )
                        await websocket_manager.send_personal_message(update.model_dump_json(), websocket)
                
                except json.JSONDecodeError:
                    # Invalid JSON, ignore
                    pass
            
            except asyncio.TimeoutError:
                # Send periodic heartbeat/update
                try:
                    # Get fresh analytics data every 30 seconds
                    fresh_data = await analytics_service.get_analytics_dashboard_data(user_id=user_id)
                    update = RealTimeAnalyticsUpdate(
                        update_type="dashboard_refresh",
                        data=fresh_data,
                        timestamp=datetime.utcnow().isoformat(),
                        user_id=user_id
                    )
                    await websocket_manager.send_personal_message(update.model_dump_json(), websocket)
                except Exception as e:
                    logger.error(f"Error sending periodic update: {e}")
                    break
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket, user_id)


@router.get("/health", response_model=AnalyticsHealthCheck)
async def analytics_health_check(
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Health check endpoint for analytics service.
    
    Requirements: 2.5
    """
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Check cache connection
    try:
        if redis_client:
            redis_client.ping()
            cache_status = "healthy"
        else:
            cache_status = "unavailable"
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        cache_status = "unhealthy"
    
    # Determine overall status
    if db_status == "healthy" and cache_status == "healthy":
        overall_status = "healthy"
    elif db_status == "healthy" and cache_status == "unavailable":
        overall_status = "degraded"  # Can work without cache
    elif db_status == "healthy" or cache_status == "healthy":
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    # Mock performance metrics (in real implementation, these would be actual metrics)
    metrics = {
        "query_time_ms": 150.5,
        "cache_hit": redis_client is not None,
        "data_freshness_minutes": 2.5,
        "total_records_processed": 1250
    }
    
    return AnalyticsHealthCheck(
        status=overall_status,
        cache_status=cache_status,
        database_status=db_status,
        last_update=datetime.utcnow().isoformat(),
        metrics=metrics
    )


@router.get("/config")
async def get_analytics_config(
    current_user: User = Depends(get_current_user)
):
    """
    Get analytics configuration summary (admin only).
    
    Requirements: 2.5
    """
    # Check admin access
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from app.core.analytics_config import analytics_config
    
    return {
        "config_summary": analytics_config.get_config_summary(),
        "validation_results": analytics_config.validate_config(),
        "retrieved_at": datetime.utcnow().isoformat()
    }


@router.post("/invalidate-cache")
async def invalidate_analytics_cache(
    pattern: str = Query("*", description="Cache key pattern to invalidate"),
    redis_client: redis.Redis = Depends(get_redis_client),
    current_user: User = Depends(get_current_user)
):
    """
    Invalidate analytics cache (admin only).
    
    Requirements: 2.5
    """
    # Check admin access
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        analytics_service = AnalyticsService(None, redis_client)
        analytics_service.invalidate_cache(pattern)
        
        return {"message": f"Cache invalidated for pattern: {pattern}"}
    
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")


# Function to broadcast analytics updates to all connected clients
async def broadcast_analytics_update(update_type: str, data: dict, user_id: Optional[int] = None):
    """
    Broadcast analytics updates to WebSocket clients.
    
    Args:
        update_type: Type of update
        data: Update data
        user_id: Optional user ID for user-specific updates
    """
    update = RealTimeAnalyticsUpdate(
        update_type=update_type,
        data=data,
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id
    )
    
    if user_id:
        await websocket_manager.send_to_user(user_id, update.model_dump_json())
    else:
        await websocket_manager.broadcast(update.model_dump_json())


# Export the broadcast function for use in other modules
__all__ = ["broadcast_analytics_update", "websocket_manager"]