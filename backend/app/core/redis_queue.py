"""
Redis-based queue system for CodeNova.

This module provides a simple, efficient queue system using Redis as the backend.
It replaces Celery with a lightweight, custom implementation.

Requirements covered: 5.1, 5.3, 5.5
"""

import json
import uuid
import time
import logging
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
import pickle
import gzip

from app.core.queue_config import queue_config, QueuePriority, task_routing

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class Task:
    """Task data structure."""
    id: str
    name: str
    args: List[Any]
    kwargs: Dict[str, Any]
    priority: QueuePriority
    created_at: datetime
    max_retries: int = 3
    retry_count: int = 0
    timeout: int = 600
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['priority'] = QueuePriority(data['priority'])
        return cls(**data)


@dataclass
class TaskResult:
    """Task result data structure."""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskResult':
        """Create result from dictionary."""
        data['status'] = TaskStatus(data['status'])
        if data.get('started_at'):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)


class RedisQueue:
    """Redis-based queue implementation."""
    
    def __init__(self):
        self.redis_pool = None
        self.task_registry: Dict[str, Callable] = {}
        self.running = False
        
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_pool = redis.ConnectionPool.from_url(
                queue_config.REDIS_URL,
                decode_responses=False,
                max_connections=20
            )
            # Test connection
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            await redis_client.ping()
            logger.info("Redis queue initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis queue: {e}")
            raise
    
    async def close(self):
        """Close Redis connections."""
        if self.redis_pool:
            await self.redis_pool.disconnect()
    
    def register_task(self, name: str, func: Callable):
        """Register a task function."""
        self.task_registry[name] = func
        logger.info(f"Registered task: {name}")
    
    def task(self, name: str, priority: QueuePriority = QueuePriority.DEFAULT):
        """Decorator to register task functions."""
        def decorator(func: Callable):
            self.register_task(name, func)
            
            async def enqueue(*args, **kwargs):
                return await self.enqueue_task(name, args, kwargs, priority)
            
            func.delay = enqueue
            func.apply_async = enqueue
            return func
        return decorator
    
    async def enqueue_task(
        self, 
        task_name: str, 
        args: List[Any] = None, 
        kwargs: Dict[str, Any] = None,
        priority: QueuePriority = QueuePriority.DEFAULT,
        delay: Optional[int] = None
    ) -> str:
        """Enqueue a task for execution."""
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
            
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=task_name,
            args=args,
            kwargs=kwargs,
            priority=priority,
            created_at=datetime.utcnow(),
            max_retries=queue_config.TASK_MAX_RETRIES,
            timeout=queue_config.TASK_TIMEOUT
        )
        
        redis_client = redis.Redis(connection_pool=self.redis_pool)
        
        try:
            # Serialize task
            task_data = self._serialize_data(task.to_dict())
            
            # Add to queue
            queue_name = queue_config.get_queue_name(priority)
            
            if delay:
                # Schedule for later execution
                score = time.time() + delay
                await redis_client.zadd(f"{queue_name}:delayed", {task_data: score})
            else:
                # Add to immediate queue
                await redis_client.lpush(queue_name, task_data)
            
            # Store task metadata
            await redis_client.hset(
                queue_config.get_result_key(task_id),
                mapping={
                    'status': TaskStatus.PENDING.value,
                    'created_at': task.created_at.isoformat(),
                    'task_name': task_name
                }
            )
            await redis_client.expire(
                queue_config.get_result_key(task_id),
                queue_config.RESULT_TTL
            )
            
            logger.info(f"Enqueued task {task_id} ({task_name}) to {queue_name}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to enqueue task {task_name}: {e}")
            raise
    
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result by ID."""
        redis_client = redis.Redis(connection_pool=self.redis_pool)
        
        try:
            result_data = await redis_client.hgetall(queue_config.get_result_key(task_id))
            if not result_data:
                return None
            
            # Decode bytes to strings
            decoded_data = {k.decode(): v.decode() for k, v in result_data.items()}
            
            # Handle result field if it exists
            if 'result' in decoded_data:
                decoded_data['result'] = self._deserialize_data(decoded_data['result'])
            
            return TaskResult.from_dict(decoded_data)
            
        except Exception as e:
            logger.error(f"Failed to get task result {task_id}: {e}")
            return None
    
    async def process_queues(self):
        """Main worker loop to process tasks from queues."""
        self.running = True
        redis_client = redis.Redis(connection_pool=self.redis_pool)
        
        logger.info("Starting queue processing...")
        
        while self.running:
            try:
                # Process delayed tasks first
                await self._process_delayed_tasks(redis_client)
                
                # Process tasks from all queues (high priority first)
                for priority in [QueuePriority.HIGH, QueuePriority.MEDIUM, QueuePriority.LOW, QueuePriority.DEFAULT]:
                    queue_name = queue_config.get_queue_name(priority)
                    
                    # Get task from queue (blocking with timeout)
                    task_data = await redis_client.brpop(queue_name, timeout=1)
                    
                    if task_data:
                        _, serialized_task = task_data
                        await self._process_task(redis_client, serialized_task)
                        break  # Process one task at a time
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(queue_config.WORKER_POLL_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in queue processing: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _process_delayed_tasks(self, redis_client):
        """Move delayed tasks to immediate queues when ready."""
        current_time = time.time()
        
        for priority in QueuePriority:
            queue_name = queue_config.get_queue_name(priority)
            delayed_queue = f"{queue_name}:delayed"
            
            # Get tasks ready for execution
            ready_tasks = await redis_client.zrangebyscore(
                delayed_queue, 0, current_time, withscores=True
            )
            
            for task_data, _ in ready_tasks:
                # Move to immediate queue
                await redis_client.lpush(queue_name, task_data)
                await redis_client.zrem(delayed_queue, task_data)
    
    async def _process_task(self, redis_client, serialized_task: bytes):
        """Process a single task."""
        try:
            # Deserialize task
            task_dict = self._deserialize_data(serialized_task)
            task = Task.from_dict(task_dict)
            
            # Check if task function is registered
            if task.name not in self.task_registry:
                logger.error(f"Task function {task.name} not registered")
                await self._mark_task_failed(redis_client, task.id, f"Task function {task.name} not registered")
                return
            
            # Mark task as processing
            await self._mark_task_processing(redis_client, task.id)
            
            # Execute task
            start_time = time.time()
            try:
                func = self.task_registry[task.name]
                
                # Execute task with timeout
                result = await asyncio.wait_for(
                    self._execute_task_function(func, task.args, task.kwargs),
                    timeout=task.timeout
                )
                
                execution_time = time.time() - start_time
                await self._mark_task_success(redis_client, task.id, result, execution_time)
                
                logger.info(f"Task {task.id} ({task.name}) completed successfully in {execution_time:.2f}s")
                
            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                error_msg = f"Task timed out after {task.timeout} seconds"
                await self._handle_task_failure(redis_client, task, error_msg, execution_time)
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = str(e)
                await self._handle_task_failure(redis_client, task, error_msg, execution_time)
                
        except Exception as e:
            logger.error(f"Failed to process task: {e}")
    
    async def _execute_task_function(self, func: Callable, args: List[Any], kwargs: Dict[str, Any]):
        """Execute task function (sync or async)."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    
    async def _mark_task_processing(self, redis_client, task_id: str):
        """Mark task as processing."""
        await redis_client.hset(
            queue_config.get_result_key(task_id),
            mapping={
                'status': TaskStatus.PROCESSING.value,
                'started_at': datetime.utcnow().isoformat()
            }
        )
    
    async def _mark_task_success(self, redis_client, task_id: str, result: Any, execution_time: float):
        """Mark task as successful."""
        await redis_client.hset(
            queue_config.get_result_key(task_id),
            mapping={
                'status': TaskStatus.SUCCESS.value,
                'result': self._serialize_data(result),
                'completed_at': datetime.utcnow().isoformat(),
                'execution_time': str(execution_time)
            }
        )
    
    async def _mark_task_failed(self, redis_client, task_id: str, error: str, execution_time: float = 0):
        """Mark task as failed."""
        await redis_client.hset(
            queue_config.get_result_key(task_id),
            mapping={
                'status': TaskStatus.FAILED.value,
                'error': error,
                'completed_at': datetime.utcnow().isoformat(),
                'execution_time': str(execution_time)
            }
        )
    
    async def _handle_task_failure(self, redis_client, task: Task, error: str, execution_time: float):
        """Handle task failure with retry logic."""
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            # Retry task
            logger.warning(f"Task {task.id} failed, retrying ({task.retry_count}/{task.max_retries}): {error}")
            
            # Add delay before retry
            delay = queue_config.TASK_RETRY_DELAY * (2 ** (task.retry_count - 1))  # Exponential backoff
            
            # Re-enqueue with delay
            task_data = self._serialize_data(task.to_dict())
            queue_name = queue_config.get_queue_name(task.priority)
            score = time.time() + delay
            await redis_client.zadd(f"{queue_name}:delayed", {task_data: score})
            
            # Update status
            await redis_client.hset(
                queue_config.get_result_key(task.id),
                mapping={
                    'status': TaskStatus.RETRY.value,
                    'error': error,
                    'retry_count': str(task.retry_count),
                    'next_retry_at': (datetime.utcnow() + timedelta(seconds=delay)).isoformat()
                }
            )
        else:
            # Max retries exceeded
            logger.error(f"Task {task.id} failed permanently after {task.retry_count} retries: {error}")
            await self._mark_task_failed(redis_client, task.id, error, execution_time)
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data for Redis storage."""
        if queue_config.ENABLE_COMPRESSION:
            return gzip.compress(pickle.dumps(data))
        else:
            return pickle.dumps(data)
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data from Redis storage."""
        if queue_config.ENABLE_COMPRESSION:
            return pickle.loads(gzip.decompress(data))
        else:
            return pickle.loads(data)
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        redis_client = redis.Redis(connection_pool=self.redis_pool)
        stats = {}
        
        for priority in QueuePriority:
            queue_name = queue_config.get_queue_name(priority)
            queue_length = await redis_client.llen(queue_name)
            delayed_length = await redis_client.zcard(f"{queue_name}:delayed")
            
            stats[priority.value] = {
                'pending': queue_length,
                'delayed': delayed_length,
                'total': queue_length + delayed_length
            }
        
        return stats
    
    async def purge_queue(self, priority: QueuePriority = None):
        """Purge queue(s)."""
        redis_client = redis.Redis(connection_pool=self.redis_pool)
        
        priorities = [priority] if priority else list(QueuePriority)
        
        for p in priorities:
            queue_name = queue_config.get_queue_name(p)
            await redis_client.delete(queue_name)
            await redis_client.delete(f"{queue_name}:delayed")
            logger.info(f"Purged queue: {queue_name}")
    
    def stop(self):
        """Stop queue processing."""
        self.running = False
        logger.info("Queue processing stopped")


# Global queue instance
redis_queue = RedisQueue()