"""
Monitoring endpoints for queue system health and metrics.

This module provides API endpoints for monitoring the health and performance
of both Redis and hybrid queue systems.

Requirements covered: 5.5
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from app.core.redis_queue import redis_queue
from app.core.hybrid_queue import hybrid_queue
from app.core.queue_config import validate_queue_config, get_queue_status_summary
from app.api.deps import get_current_user
from app.models.users import User

router = APIRouter()


@router.get("/queue/health")
async def get_queue_health():
    """
    Get overall queue system health status.
    
    Returns health information for both Redis and hybrid queue systems.
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "systems": {}
        }
        
        # Check Redis queue health
        try:
            redis_stats = await redis_queue.get_queue_stats()
            health_status["systems"]["redis_queue"] = {
                "status": "healthy",
                "stats": redis_stats
            }
        except Exception as e:
            health_status["systems"]["redis_queue"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check hybrid queue health
        try:
            hybrid_metrics = await hybrid_queue.get_metrics()
            health_status["systems"]["hybrid_queue"] = {
                "status": hybrid_metrics["status"],
                "metrics": hybrid_metrics
            }
            
            if hybrid_metrics["status"] != "healthy":
                health_status["status"] = "degraded"
                
        except Exception as e:
            health_status["systems"]["hybrid_queue"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue health: {str(e)}"
        )


@router.get("/queue/stats")
async def get_queue_stats():
    """
    Get detailed queue statistics and metrics.
    
    Returns comprehensive statistics for monitoring and alerting.
    """
    try:
        stats = {
            "redis_queue": {},
            "hybrid_queue": {},
            "configuration": {}
        }
        
        # Get Redis queue stats
        try:
            stats["redis_queue"] = await redis_queue.get_queue_stats()
        except Exception as e:
            stats["redis_queue"] = {"error": str(e)}
        
        # Get hybrid queue metrics
        try:
            stats["hybrid_queue"] = await hybrid_queue.get_metrics()
        except Exception as e:
            stats["hybrid_queue"] = {"error": str(e)}
        
        # Get configuration summary
        stats["configuration"] = get_queue_status_summary()
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue stats: {str(e)}"
        )


@router.get("/queue/config/validate")
async def validate_configuration():
    """
    Validate queue system configuration.
    
    Returns configuration validation results and recommendations.
    """
    try:
        validation_result = validate_queue_config()
        return validation_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate configuration: {str(e)}"
        )


@router.get("/workers/status")
async def get_worker_status():
    """
    Get status of queue workers.
    
    Returns information about active workers and their performance.
    """
    try:
        # This would typically connect to worker management system
        # For now, return basic status based on queue metrics
        
        redis_stats = await redis_queue.get_queue_stats()
        hybrid_metrics = await hybrid_queue.get_metrics()
        
        worker_status = {
            "redis_workers": {
                "active": True,  # Assume active if we can get stats
                "queue_depths": redis_stats
            },
            "hybrid_workers": {
                "forwarder_active": hybrid_metrics.get("status") == "healthy",
                "worker_active": hybrid_metrics.get("rabbitmq_tasks_processed", 0) > 0,
                "metrics": hybrid_metrics
            }
        }
        
        return worker_status
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get worker status: {str(e)}"
        )


@router.get("/workers/performance")
async def get_worker_performance():
    """
    Get worker performance metrics.
    
    Returns detailed performance data for optimization.
    """
    try:
        performance_data = {
            "redis_queue": {
                "throughput": "N/A",  # Would need historical data
                "latency": "N/A",
                "error_rate": "N/A"
            },
            "hybrid_queue": {},
            "recommendations": []
        }
        
        # Get hybrid queue metrics
        hybrid_metrics = await hybrid_queue.get_metrics()
        performance_data["hybrid_queue"] = {
            "forwarding_rate": hybrid_metrics.get("forwarding_rate", 0),
            "failed_forwards": hybrid_metrics.get("failed_forwards", 0),
            "queue_depths": {
                "redis": hybrid_metrics.get("redis_queue_depth", 0),
                "rabbitmq": hybrid_metrics.get("rabbitmq_queue_depth", 0)
            }
        }
        
        # Generate recommendations
        recommendations = []
        
        if hybrid_metrics.get("forwarding_rate", 0) < 0.8:
            recommendations.append("Consider increasing forwarder batch size or frequency")
        
        if hybrid_metrics.get("failed_forwards", 0) > 5:
            recommendations.append("High number of failed forwards - check RabbitMQ connectivity")
        
        if hybrid_metrics.get("redis_queue_depth", 0) > 1000:
            recommendations.append("High Redis queue depth - consider scaling workers")
        
        performance_data["recommendations"] = recommendations
        
        return performance_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get worker performance: {str(e)}"
        )


@router.get("/cache/performance")
async def get_cache_performance():
    """
    Get cache system performance metrics.
    
    Returns cache hit rates, response times, and optimization suggestions.
    """
    try:
        # This would typically connect to Redis cache monitoring
        # For now, return basic cache information
        
        cache_performance = {
            "hit_rate": "N/A",  # Would need Redis INFO stats
            "miss_rate": "N/A",
            "response_time_avg": "N/A",
            "memory_usage": "N/A",
            "evictions": "N/A",
            "recommendations": [
                "Enable cache monitoring to get detailed metrics",
                "Consider implementing cache warming for frequently accessed data"
            ]
        }
        
        return cache_performance
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache performance: {str(e)}"
        )


@router.post("/queue/purge")
async def purge_queues(
    queue_type: str = "all",
    current_user: User = Depends(get_current_user)
):
    """
    Purge queue contents (admin only).
    
    Args:
        queue_type: Type of queue to purge ("redis", "hybrid", or "all")
        current_user: Current authenticated user (must be admin)
    """
    # Check admin permissions
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        purged_queues = []
        
        if queue_type in ["redis", "all"]:
            await redis_queue.purge_queue()
            purged_queues.append("redis")
        
        if queue_type in ["hybrid", "all"]:
            await hybrid_queue.purge_queues()
            purged_queues.append("hybrid")
        
        return {
            "message": "Queues purged successfully",
            "purged_queues": purged_queues,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purge queues: {str(e)}"
        )


@router.get("/system/overview")
async def get_system_overview():
    """
    Get comprehensive system overview.
    
    Returns high-level status and metrics for the entire queue system.
    """
    try:
        overview = {
            "system_status": "healthy",
            "components": {},
            "summary": {},
            "alerts": []
        }
        
        # Get component statuses
        try:
            redis_stats = await redis_queue.get_queue_stats()
            overview["components"]["redis_queue"] = {
                "status": "healthy",
                "total_pending": sum(queue["total"] for queue in redis_stats.values())
            }
        except Exception:
            overview["components"]["redis_queue"] = {"status": "unhealthy"}
            overview["system_status"] = "degraded"
        
        try:
            hybrid_metrics = await hybrid_queue.get_metrics()
            overview["components"]["hybrid_queue"] = {
                "status": hybrid_metrics["status"],
                "total_pending": hybrid_metrics["redis_queue_depth"] + hybrid_metrics["rabbitmq_queue_depth"]
            }
            
            if hybrid_metrics["status"] != "healthy":
                overview["system_status"] = "degraded"
                
        except Exception:
            overview["components"]["hybrid_queue"] = {"status": "unhealthy"}
            overview["system_status"] = "degraded"
        
        # Generate summary
        total_pending = 0
        for component in overview["components"].values():
            if "total_pending" in component:
                total_pending += component["total_pending"]
        
        overview["summary"] = {
            "total_pending_tasks": total_pending,
            "active_components": len([c for c in overview["components"].values() if c["status"] == "healthy"]),
            "total_components": len(overview["components"])
        }
        
        # Generate alerts
        alerts = []
        if total_pending > 1000:
            alerts.append({
                "level": "warning",
                "message": f"High number of pending tasks: {total_pending}"
            })
        
        if overview["system_status"] != "healthy":
            alerts.append({
                "level": "error", 
                "message": "One or more queue components are unhealthy"
            })
        
        overview["alerts"] = alerts
        
        return overview
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system overview: {str(e)}"
        )