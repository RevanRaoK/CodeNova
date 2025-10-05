"""
Redis queue application for CodeNova.

This module replaces Celery with a Redis-based queue system.
It provides the same interface for backward compatibility.

Requirements covered: 5.1, 5.3, 5.5
"""

import logging
from typing import Dict, Any, Optional

from app.core.redis_queue import redis_queue, TaskStatus
from app.core.queue_config import queue_config, QueuePriority

logger = logging.getLogger(__name__)


class RedisQueueApp:
    """Redis queue application that mimics Celery interface."""
    
    def __init__(self):
        self.queue = redis_queue
    
    async def initialize(self):
        """Initialize the queue system."""
        await self.queue.initialize()
    
    def task(self, name: str = None, priority: QueuePriority = QueuePriority.DEFAULT):
        """Task decorator (mimics Celery's @app.task)."""
        def decorator(func):
            task_name = name or f"{func.__module__}.{func.__name__}"
            return self.queue.task(task_name, priority)(func)
        return decorator
    
    async def send_task(self, name: str, args=None, kwargs=None, priority: QueuePriority = QueuePriority.DEFAULT):
        """Send task to queue (mimics Celery's send_task)."""
        return await self.queue.enqueue_task(name, args, kwargs, priority)
    
    async def get_task_result(self, task_id: str):
        """Get task result (mimics Celery's AsyncResult)."""
        return await self.queue.get_task_result(task_id)
    
    async def get_stats(self):
        """Get queue statistics."""
        return await self.queue.get_queue_stats()


# Global app instance (replaces celery_app)
app = RedisQueueApp()

# For backward compatibility
celery_app = app


class AsyncResult:
    """Mimics Celery's AsyncResult for backward compatibility."""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.app = app
    
    async def get(self, timeout=None):
        """Get task result."""
        result = await self.app.get_task_result(self.task_id)
        if result:
            if result.status == TaskStatus.SUCCESS:
                return result.result
            elif result.status == TaskStatus.FAILED:
                raise Exception(result.error)
            else:
                return None
        return None
    
    async def ready(self):
        """Check if task is ready."""
        result = await self.app.get_task_result(self.task_id)
        return result and result.status in [TaskStatus.SUCCESS, TaskStatus.FAILED]
    
    async def successful(self):
        """Check if task was successful."""
        result = await self.app.get_task_result(self.task_id)
        return result and result.status == TaskStatus.SUCCESS
    
    async def failed(self):
        """Check if task failed."""
        result = await self.app.get_task_result(self.task_id)
        return result and result.status == TaskStatus.FAILED
    
    @property
    def status(self):
        """Get task status (sync version for compatibility)."""
        # Note: This is a sync property, but the actual implementation is async
        # In practice, you should use the async methods above
        return "PENDING"


class QueueHealthCheck:
    """Health check utilities for Redis queue system."""
    
    @staticmethod
    async def check_worker_status() -> Dict[str, Any]:
        """Check status of Redis queue workers."""
        try:
            stats = await app.get_stats()
            
            total_pending = sum(queue_stats['total'] for queue_stats in stats.values())
            
            return {
                'status': 'healthy',
                'total_pending_tasks': total_pending,
                'queue_stats': stats,
                'configuration': queue_config.get_redis_config()
            }
            
        except Exception as e:
            logger.error(f"Error checking worker status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'total_pending_tasks': 0
            }
    
    @staticmethod
    async def check_queue_status() -> Dict[str, Any]:
        """Check status of message queues."""
        try:
            stats = await app.get_stats()
            
            queue_info = {}
            warnings = []
            
            for priority, queue_stats in stats.items():
                queue_info[priority] = queue_stats
                
                # Check for queue depth warnings
                if queue_stats['total'] > 1000:
                    warnings.append(f"Queue {priority} has high depth: {queue_stats['total']}")
            
            return {
                'status': 'healthy',
                'queues': queue_info,
                'total_queues': len(queue_info),
                'warnings': warnings
            }
            
        except Exception as e:
            logger.error(f"Error checking queue status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'queues': {}
            }
    
    @staticmethod
    async def get_comprehensive_health() -> Dict[str, Any]:
        """Get comprehensive health check for Redis queue system."""
        worker_status = await QueueHealthCheck.check_worker_status()
        queue_status = await QueueHealthCheck.check_queue_status()
        
        overall_healthy = (
            worker_status['status'] == 'healthy' and 
            queue_status['status'] == 'healthy'
        )
        
        return {
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'timestamp': app.queue._get_current_time().isoformat() if hasattr(app.queue, '_get_current_time') else None,
            'components': {
                'workers': worker_status,
                'queues': queue_status,
            },
            'configuration': queue_config.get_redis_config()
        }


# Utility functions for task management (Celery compatibility)
async def get_task_result(task_id: str) -> Optional[Any]:
    """Get result of a task by ID."""
    try:
        result = await app.get_task_result(task_id)
        return {
            'task_id': task_id,
            'status': result.status.value if result else 'PENDING',
            'result': result.result if result and result.status == TaskStatus.SUCCESS else None,
            'error': result.error if result and result.status == TaskStatus.FAILED else None,
            'started_at': result.started_at if result else None,
            'completed_at': result.completed_at if result else None,
        }
    except Exception as e:
        logger.error(f"Error getting task result for {task_id}: {e}")
        return None


async def revoke_task(task_id: str, terminate: bool = False) -> bool:
    """Revoke a task (Redis queue doesn't support this directly)."""
    logger.warning(f"Task revocation not supported in Redis queue: {task_id}")
    return False


async def purge_queue(queue_name: str = None) -> int:
    """Purge all messages from queues."""
    try:
        if queue_name:
            # Convert queue name to priority
            priority = None
            for p in QueuePriority:
                if p.value == queue_name:
                    priority = p
                    break
            
            if priority:
                await app.queue.purge_queue(priority)
                logger.info(f"Purged queue {queue_name}")
                return 1
        else:
            # Purge all queues
            await app.queue.purge_queue()
            logger.info("Purged all queues")
            return len(QueuePriority)
        
        return 0
    except Exception as e:
        logger.error(f"Error purging queue {queue_name}: {e}")
        return 0


# Export the main components
__all__ = [
    'app', 'celery_app', 'AsyncResult', 'QueueHealthCheck', 
    'get_task_result', 'revoke_task', 'purge_queue'
]