"""
Hybrid queue system: Redis for enqueueing -> RabbitMQ for processing.

This system provides:
- Fast Redis-based enqueueing for immediate response
- Reliable RabbitMQ processing with persistence and acknowledgments
- Automatic forwarding from Redis to RabbitMQ
- Monitoring and health checks for both systems

Requirements covered: 5.1, 5.3, 5.5
"""

import json
import uuid
import time
import logging
import asyncio
import aio_pika
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis

from app.core.queue_config import queue_config, QueuePriority
from app.core.redis_queue import redis_queue, Task, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class HybridQueueConfig:
    """Configuration for hybrid queue system."""
    
    # Redis configuration
    redis_url: str = queue_config.REDIS_URL
    redis_db_queue: int = queue_config.REDIS_DB_QUEUE
    
    # RabbitMQ configuration
    rabbitmq_url: str = queue_config.RABBITMQ_URL
    rabbitmq_exchange: str = "codenova.tasks"
    rabbitmq_queue_prefix: str = "codenova.queue."
    
    # Forwarding configuration
    forwarding_enabled: bool = True
    forwarding_batch_size: int = 10
    forwarding_interval: float = 1.0  # seconds
    
    # Reliability configuration
    rabbitmq_durable: bool = True
    rabbitmq_persistent: bool = True
    rabbitmq_confirm_delivery: bool = True
    
    # Health check configuration
    health_check_interval: float = 30.0  # seconds
    max_connection_retries: int = 5
    connection_retry_delay: float = 5.0  # seconds


class HybridQueueStatus(Enum):
    """Hybrid queue system status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class QueueMetrics:
    """Queue system metrics."""
    redis_tasks_enqueued: int = 0
    rabbitmq_tasks_processed: int = 0
    forwarding_rate: float = 0.0
    redis_queue_depth: int = 0
    rabbitmq_queue_depth: int = 0
    failed_forwards: int = 0
    last_health_check: Optional[datetime] = None
    status: HybridQueueStatus = HybridQueueStatus.HEALTHY


class HybridQueue:
    """
    Hybrid queue system combining Redis and RabbitMQ.
    
    Architecture:
    1. Tasks are enqueued to Redis for immediate response
    2. Background forwarder moves tasks from Redis to RabbitMQ
    3. Workers consume from RabbitMQ for reliable processing
    4. Results are stored back in Redis for fast retrieval
    """
    
    def __init__(self, config: HybridQueueConfig = None):
        self.config = config or HybridQueueConfig()
        self.redis_client = None
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        self.running = False
        self.metrics = QueueMetrics()
        self.task_registry: Dict[str, Callable] = {}
        
    async def initialize(self):
        """Initialize both Redis and RabbitMQ connections."""
        await self._initialize_redis()
        await self._initialize_rabbitmq()
        logger.info("Hybrid queue system initialized successfully")
    
    async def _initialize_redis(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.Redis.from_url(
                self.config.redis_url,
                db=self.config.redis_db_queue,
                decode_responses=False
            )
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    async def _initialize_rabbitmq(self):
        """Initialize RabbitMQ connection and setup exchanges/queues."""
        try:
            self.rabbitmq_connection = await aio_pika.connect_robust(
                self.config.rabbitmq_url,
                heartbeat=30
            )
            self.rabbitmq_channel = await self.rabbitmq_connection.channel()
            
            # Declare exchange
            self.exchange = await self.rabbitmq_channel.declare_exchange(
                self.config.rabbitmq_exchange,
                aio_pika.ExchangeType.DIRECT,
                durable=self.config.rabbitmq_durable
            )
            
            # Declare queues for each priority
            for priority in QueuePriority:
                queue_name = f"{self.config.rabbitmq_queue_prefix}{priority.value}"
                await self.rabbitmq_channel.declare_queue(
                    queue_name,
                    durable=self.config.rabbitmq_durable
                )
                
                # Bind queue to exchange
                queue = await self.rabbitmq_channel.get_queue(queue_name)
                await queue.bind(self.exchange, routing_key=priority.value)
            
            logger.info("RabbitMQ connection and queues established")
            
        except Exception as e:
            logger.error(f"Failed to initialize RabbitMQ: {e}")
            raise
    
    async def close(self):
        """Close all connections."""
        self.running = False
        
        if self.rabbitmq_connection:
            await self.rabbitmq_connection.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Hybrid queue connections closed")
    
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
        """
        Enqueue task to Redis for immediate response.
        Task will be forwarded to RabbitMQ by the forwarder process.
        """
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
        
        try:
            # Store in Redis for immediate response
            task_data = json.dumps(task.to_dict(), default=str)
            redis_queue_name = f"hybrid:redis:{priority.value}"
            
            if delay:
                # Schedule for later
                score = time.time() + delay
                await self.redis_client.zadd(f"{redis_queue_name}:delayed", {task_data: score})
            else:
                # Add to immediate queue
                await self.redis_client.lpush(redis_queue_name, task_data)
            
            # Store task result placeholder
            result_key = f"hybrid:result:{task_id}"
            await self.redis_client.hset(
                result_key,
                mapping={
                    'status': TaskStatus.PENDING.value,
                    'created_at': task.created_at.isoformat(),
                    'task_name': task_name
                }
            )
            await self.redis_client.expire(result_key, queue_config.RESULT_TTL)
            
            self.metrics.redis_tasks_enqueued += 1
            logger.info(f"Enqueued task {task_id} ({task_name}) to Redis queue")
            
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to enqueue task {task_name}: {e}")
            raise
    
    async def start_forwarder(self):
        """Start the Redis to RabbitMQ forwarder process."""
        self.running = True
        logger.info("Starting hybrid queue forwarder...")
        
        while self.running:
            try:
                # Process delayed tasks first
                await self._process_delayed_tasks()
                
                # Forward tasks from Redis to RabbitMQ
                await self._forward_tasks_batch()
                
                # Health check
                await self._perform_health_check()
                
                await asyncio.sleep(self.config.forwarding_interval)
                
            except Exception as e:
                logger.error(f"Error in forwarder loop: {e}")
                await asyncio.sleep(5)
    
    async def _process_delayed_tasks(self):
        """Move delayed tasks to immediate queues when ready."""
        current_time = time.time()
        
        for priority in QueuePriority:
            redis_queue_name = f"hybrid:redis:{priority.value}"
            delayed_queue = f"{redis_queue_name}:delayed"
            
            # Get ready tasks
            ready_tasks = await self.redis_client.zrangebyscore(
                delayed_queue, 0, current_time, withscores=True
            )
            
            for task_data, _ in ready_tasks:
                # Move to immediate queue
                await self.redis_client.lpush(redis_queue_name, task_data)
                await self.redis_client.zrem(delayed_queue, task_data)
    
    async def _forward_tasks_batch(self):
        """Forward a batch of tasks from Redis to RabbitMQ."""
        forwarded_count = 0
        
        for priority in [QueuePriority.HIGH, QueuePriority.MEDIUM, QueuePriority.LOW, QueuePriority.DEFAULT]:
            redis_queue_name = f"hybrid:redis:{priority.value}"
            
            # Get batch of tasks
            tasks = await self.redis_client.rpop(redis_queue_name, self.config.forwarding_batch_size)
            
            if not tasks:
                continue
            
            # Ensure tasks is a list
            if not isinstance(tasks, list):
                tasks = [tasks]
            
            for task_data in tasks:
                try:
                    await self._forward_single_task(task_data, priority)
                    forwarded_count += 1
                except Exception as e:
                    logger.error(f"Failed to forward task: {e}")
                    # Put task back in Redis queue for retry
                    await self.redis_client.lpush(redis_queue_name, task_data)
                    self.metrics.failed_forwards += 1
        
        if forwarded_count > 0:
            self.metrics.rabbitmq_tasks_processed += forwarded_count
            logger.debug(f"Forwarded {forwarded_count} tasks to RabbitMQ")
    
    async def _forward_single_task(self, task_data: bytes, priority: QueuePriority):
        """Forward a single task to RabbitMQ."""
        message = aio_pika.Message(
            task_data,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT if self.config.rabbitmq_persistent else aio_pika.DeliveryMode.NOT_PERSISTENT
        )
        
        await self.exchange.publish(
            message,
            routing_key=priority.value,
            mandatory=True
        )
    
    async def start_worker(self):
        """Start RabbitMQ consumer worker."""
        logger.info("Starting hybrid queue worker...")
        
        # Set up consumers for each priority queue
        for priority in QueuePriority:
            queue_name = f"{self.config.rabbitmq_queue_prefix}{priority.value}"
            queue = await self.rabbitmq_channel.get_queue(queue_name)
            
            # Set QoS to process one message at a time
            await self.rabbitmq_channel.set_qos(prefetch_count=1)
            
            # Start consuming
            await queue.consume(
                lambda message, p=priority: self._process_rabbitmq_message(message, p)
            )
        
        logger.info("Worker started, consuming from RabbitMQ queues")
    
    async def _process_rabbitmq_message(self, message: aio_pika.IncomingMessage, priority: QueuePriority):
        """Process a message from RabbitMQ."""
        async with message.process():
            try:
                # Parse task data
                task_dict = json.loads(message.body.decode())
                task = Task.from_dict(task_dict)
                
                # Check if task function is registered
                if task.name not in self.task_registry:
                    logger.error(f"Task function {task.name} not registered")
                    await self._mark_task_failed(task.id, f"Task function {task.name} not registered")
                    return
                
                # Mark as processing
                await self._mark_task_processing(task.id)
                
                # Execute task
                start_time = time.time()
                try:
                    func = self.task_registry[task.name]
                    result = await self._execute_task_function(func, task.args, task.kwargs)
                    
                    execution_time = time.time() - start_time
                    await self._mark_task_success(task.id, result, execution_time)
                    
                    logger.info(f"Task {task.id} ({task.name}) completed in {execution_time:.2f}s")
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    await self._mark_task_failed(task.id, str(e), execution_time)
                    logger.error(f"Task {task.id} failed: {e}")
                
            except Exception as e:
                logger.error(f"Failed to process RabbitMQ message: {e}")
                # Message will be rejected and potentially requeued
                raise
    
    async def _execute_task_function(self, func: Callable, args: List[Any], kwargs: Dict[str, Any]):
        """Execute task function (sync or async)."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    
    async def _mark_task_processing(self, task_id: str):
        """Mark task as processing in Redis."""
        result_key = f"hybrid:result:{task_id}"
        await self.redis_client.hset(
            result_key,
            mapping={
                'status': TaskStatus.PROCESSING.value,
                'started_at': datetime.utcnow().isoformat()
            }
        )
    
    async def _mark_task_success(self, task_id: str, result: Any, execution_time: float):
        """Mark task as successful in Redis."""
        result_key = f"hybrid:result:{task_id}"
        await self.redis_client.hset(
            result_key,
            mapping={
                'status': TaskStatus.SUCCESS.value,
                'result': json.dumps(result, default=str),
                'completed_at': datetime.utcnow().isoformat(),
                'execution_time': str(execution_time)
            }
        )
    
    async def _mark_task_failed(self, task_id: str, error: str, execution_time: float = 0):
        """Mark task as failed in Redis."""
        result_key = f"hybrid:result:{task_id}"
        await self.redis_client.hset(
            result_key,
            mapping={
                'status': TaskStatus.FAILED.value,
                'error': error,
                'completed_at': datetime.utcnow().isoformat(),
                'execution_time': str(execution_time)
            }
        )
    
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result from Redis."""
        result_key = f"hybrid:result:{task_id}"
        
        try:
            result_data = await self.redis_client.hgetall(result_key)
            if not result_data:
                return None
            
            # Decode bytes to strings
            decoded_data = {k.decode(): v.decode() for k, v in result_data.items()}
            
            # Parse result if it exists
            if 'result' in decoded_data:
                try:
                    decoded_data['result'] = json.loads(decoded_data['result'])
                except json.JSONDecodeError:
                    pass  # Keep as string if not valid JSON
            
            return TaskResult.from_dict(decoded_data)
            
        except Exception as e:
            logger.error(f"Failed to get task result {task_id}: {e}")
            return None
    
    async def _perform_health_check(self):
        """Perform health check on both Redis and RabbitMQ."""
        try:
            # Check Redis
            await self.redis_client.ping()
            
            # Check RabbitMQ
            if self.rabbitmq_connection.is_closed:
                raise Exception("RabbitMQ connection is closed")
            
            # Update metrics
            self.metrics.last_health_check = datetime.utcnow()
            
            # Calculate queue depths
            redis_depth = 0
            rabbitmq_depth = 0
            
            for priority in QueuePriority:
                redis_queue_name = f"hybrid:redis:{priority.value}"
                redis_depth += await self.redis_client.llen(redis_queue_name)
                
                rabbitmq_queue_name = f"{self.config.rabbitmq_queue_prefix}{priority.value}"
                queue = await self.rabbitmq_channel.get_queue(rabbitmq_queue_name)
                queue_info = await queue.declare(passive=True)
                rabbitmq_depth += queue_info.message_count
            
            self.metrics.redis_queue_depth = redis_depth
            self.metrics.rabbitmq_queue_depth = rabbitmq_depth
            
            # Calculate forwarding rate
            if self.metrics.redis_tasks_enqueued > 0:
                self.metrics.forwarding_rate = (
                    self.metrics.rabbitmq_tasks_processed / self.metrics.redis_tasks_enqueued
                )
            
            # Determine status
            if self.metrics.failed_forwards > 10:
                self.metrics.status = HybridQueueStatus.DEGRADED
            else:
                self.metrics.status = HybridQueueStatus.HEALTHY
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.metrics.status = HybridQueueStatus.FAILED
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current queue metrics."""
        return {
            'redis_tasks_enqueued': self.metrics.redis_tasks_enqueued,
            'rabbitmq_tasks_processed': self.metrics.rabbitmq_tasks_processed,
            'forwarding_rate': self.metrics.forwarding_rate,
            'redis_queue_depth': self.metrics.redis_queue_depth,
            'rabbitmq_queue_depth': self.metrics.rabbitmq_queue_depth,
            'failed_forwards': self.metrics.failed_forwards,
            'last_health_check': self.metrics.last_health_check.isoformat() if self.metrics.last_health_check else None,
            'status': self.metrics.status.value
        }
    
    async def purge_queues(self):
        """Purge all queues (Redis and RabbitMQ)."""
        # Purge Redis queues
        for priority in QueuePriority:
            redis_queue_name = f"hybrid:redis:{priority.value}"
            await self.redis_client.delete(redis_queue_name)
            await self.redis_client.delete(f"{redis_queue_name}:delayed")
        
        # Purge RabbitMQ queues
        for priority in QueuePriority:
            rabbitmq_queue_name = f"{self.config.rabbitmq_queue_prefix}{priority.value}"
            queue = await self.rabbitmq_channel.get_queue(rabbitmq_queue_name)
            await queue.purge()
        
        logger.info("All hybrid queues purged")


# Global hybrid queue instance
hybrid_queue = HybridQueue()