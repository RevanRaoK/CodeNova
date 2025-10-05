"""
API endpoints for queue monitoring and management.

This module provides endpoints for:
- Queue health monitoring
- Worker status checking
- Performance metrics retrieval
- Queue management operations

Requirements covered: 5.5
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from app.api.deps import get_current_user, require_admin
from app.models.users import User
from app.services.queue_monitoring_service import queue_monitoring_service
from app.services.cache_service import cache_service
from app.core.celery_app import QueueHealthCheck

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def get_queue_health(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive queue health status.
    
    Returns:
        Queue health information including alerts and recommendations
    """
    try:
        health_data = await queue_monitoring_service.check_queue_health()
        return {
            "status": "success",
            "data": health_data
        }
        
    except Exception as exc:
        logger.error(f"Error getting queue health: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue health: {str(exc)}"
        )


@router.get("/statistics")
async def get_queue_statistics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed queue statistics from RabbitMQ.
    
    Returns:
        Queue statistics including message counts and consumer information
    """
    try:
        stats = await queue_monitoring_service.get_queue_statistics()
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as exc:
        logger.error(f"Error getting queue statistics: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue statistics: {str(exc)}"
        )


@router.get("/workers")
async def get_worker_statistics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get Celery worker statistics and health information.
    
    Returns:
        Worker statistics including active tasks and resource usage
    """
    try:
        stats = await queue_monitoring_service.get_worker_statistics()
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as exc:
        logger.error(f"Error getting worker statistics: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get worker statistics: {str(exc)}"
        )


@router.get("/performance")
async def get_performance_metrics(
    hours: int = Query(default=24, ge=1, le=168, description="Hours to look back (1-168)"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get performance metrics over specified time range.
    
    Args:
        hours: Number of hours to look back (1-168 hours)
        
    Returns:
        Performance metrics and trends
    """
    try:
        metrics = await queue_monitoring_service.get_performance_metrics(hours)
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as exc:
        logger.error(f"Error getting performance metrics: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance metrics: {str(exc)}"
        )


@router.get("/dashboard")
async def get_monitoring_dashboard(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive monitoring dashboard data.
    
    Returns:
        All monitoring data for dashboard display
    """
    try:
        dashboard_data = await queue_monitoring_service.get_monitoring_dashboard_data()
        return {
            "status": "success",
            "data": dashboard_data
        }
        
    except Exception as exc:
        logger.error(f"Error getting dashboard data: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard data: {str(exc)}"
        )


@router.post("/purge/{queue_name}")
async def purge_queue(
    queue_name: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Purge all messages from a specific queue.
    
    Args:
        queue_name: Name of the queue to purge
        
    Returns:
        Purge operation results
        
    Requires:
        Admin privileges
    """
    try:
        # Validate queue name
        valid_queues = [
            'file_analysis',
            'github_webhooks', 
            'feedback_processing',
            'analytics',
            'cache_management',
            'default'
        ]
        
        if queue_name not in valid_queues:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid queue name. Valid queues: {', '.join(valid_queues)}"
            )
        
        result = await queue_monitoring_service.purge_queue(queue_name)
        
        if result['status'] == 'success':
            return {
                "status": "success",
                "message": f"Queue {queue_name} purged successfully",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Unknown error occurred')
            )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error purging queue {queue_name}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to purge queue: {str(exc)}"
        )


@router.get("/celery/health")
async def get_celery_health(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get Celery-specific health check information.
    
    Returns:
        Celery health status and configuration
    """
    try:
        health_data = await QueueHealthCheck.get_comprehensive_health()
        return {
            "status": "success",
            "data": health_data
        }
        
    except Exception as exc:
        logger.error(f"Error getting Celery health: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Celery health: {str(exc)}"
        )


@router.get("/cache/health")
async def get_cache_health(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get cache (Redis) health check information.
    
    Returns:
        Cache health status and metrics
    """
    try:
        health_data = await cache_service.health_check()
        return {
            "status": "success",
            "data": health_data
        }
        
    except Exception as exc:
        logger.error(f"Error getting cache health: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache health: {str(exc)}"
        )


@router.get("/cache/info")
async def get_cache_info(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed cache information and statistics.
    
    Returns:
        Cache information including hit rates and performance metrics
    """
    try:
        cache_info = await cache_service.get_cache_info()
        return {
            "status": "success",
            "data": cache_info
        }
        
    except Exception as exc:
        logger.error(f"Error getting cache info: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache info: {str(exc)}"
        )


@router.post("/cache/warm")
async def warm_cache(
    cache_type: str = Query(default="all", description="Type of cache to warm (all, user, file, analytics)"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Trigger cache warming operation.
    
    Args:
        cache_type: Type of cache to warm
        
    Returns:
        Cache warming operation results
        
    Requires:
        Admin privileges
    """
    try:
        from app.tasks.cache_tasks import warm_cache_data
        
        # Queue cache warming task
        task = warm_cache_data.delay(cache_type, 100)
        
        return {
            "status": "success",
            "message": f"Cache warming task queued for {cache_type}",
            "task_id": task.id
        }
        
    except Exception as exc:
        logger.error(f"Error warming cache: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to warm cache: {str(exc)}"
        )


@router.post("/cache/cleanup")
async def cleanup_cache(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Trigger cache cleanup operation.
    
    Returns:
        Cache cleanup operation results
        
    Requires:
        Admin privileges
    """
    try:
        from app.tasks.cache_tasks import cleanup_expired_cache
        
        # Queue cache cleanup task
        task = cleanup_expired_cache.delay()
        
        return {
            "status": "success",
            "message": "Cache cleanup task queued",
            "task_id": task.id
        }
        
    except Exception as exc:
        logger.error(f"Error cleaning up cache: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup cache: {str(exc)}"
        )


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get status of a specific Celery task.
    
    Args:
        task_id: ID of the task to check
        
    Returns:
        Task status and result information
    """
    try:
        from app.core.celery_app import get_task_result
        
        task_result = get_task_result(task_id)
        
        if task_result:
            return {
                "status": "success",
                "data": task_result
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error getting task status for {task_id}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(exc)}"
        )


@router.post("/tasks/{task_id}/revoke")
async def revoke_task(
    task_id: str,
    terminate: bool = Query(default=False, description="Whether to terminate the task"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Revoke a specific Celery task.
    
    Args:
        task_id: ID of the task to revoke
        terminate: Whether to terminate the task if it's running
        
    Returns:
        Task revocation results
        
    Requires:
        Admin privileges
    """
    try:
        from app.core.celery_app import revoke_task as revoke_celery_task
        
        success = revoke_celery_task(task_id, terminate)
        
        if success:
            return {
                "status": "success",
                "message": f"Task {task_id} revoked successfully",
                "task_id": task_id,
                "terminated": terminate
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to revoke task {task_id}"
            )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error revoking task {task_id}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to revoke task: {str(exc)}"
        )


@router.get("/alerts")
async def get_queue_alerts(
    severity: Optional[str] = Query(default=None, description="Filter by severity (critical, warning, info)"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of alerts to return"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get recent queue monitoring alerts.
    
    Args:
        severity: Filter alerts by severity level
        limit: Maximum number of alerts to return
        
    Returns:
        List of recent alerts
    """
    try:
        # Get recent health check data which includes alerts
        health_data = await queue_monitoring_service.check_queue_health()
        
        alerts = health_data.get('alerts', [])
        
        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert.get('severity') == severity]
        
        # Limit results
        alerts = alerts[:limit]
        
        return {
            "status": "success",
            "data": {
                "alerts": alerts,
                "total_count": len(alerts),
                "filtered_by_severity": severity,
                "generated_at": health_data.get('timestamp')
            }
        }
        
    except Exception as exc:
        logger.error(f"Error getting queue alerts: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue alerts: {str(exc)}"
        )