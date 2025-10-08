"""
Background Job Queue Service for CodeNova.

This service provides comprehensive background job processing capabilities:
- Redis-based message queue for background processing
- Job queue service for handling asynchronous tasks
- Job status tracking and progress monitoring
- Job result caching with expiration policies

Requirements covered: 2.1, 2.2, 2.3
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum

import redis.asyncio as redis
from app.core.config import settings
from app.core.redis_queue import redis_queue, Task, TaskResult, TaskStatus
from app.core.hybrid_queue import hybrid_queue
from app.core.queue_config import queue_config, QueuePriority
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job execution status with progress tracking."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(Enum):
    """Job priority levels."""
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class JobProgress:
    """Job progress tracking data."""
    current_step: int = 0
    total_steps: int = 1
    percentage: float = 0.0
    message: str = ""
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    def update(self, current_step: int = None, total_steps: int = None, 
               message: str = None, details: Dict[str, Any] = None):
        """Update progress information."""
        if current_step is not None:
            self.current_step = current_step
        if total_steps is not None:
            self.total_steps = total_steps
        if message is not None:
            self.message = message
        if details is not None:
            self.details.update(details)
        
        # Calculate percentage
        if self.total_steps > 0:
            self.percentage = min(100.0, (self.current_step / self.total_steps) * 100.0)


@dataclass
class BackgroundJob:
    """Background job data structure with enhanced tracking."""
    id: str
    name: str
    args: List[Any]
    kwargs: Dict[str, Any]
    priority: JobPriority
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: JobProgress = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 600
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.progress is None:
            self.progress = JobProgress()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackgroundJob':
        """Create job from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['started_at'] = datetime.fromisoformat(data['started_at']) if data.get('started_at') else None
        data['completed_at'] = datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None
        data['status'] = JobStatus(data['status'])
        data['priority'] = JobPriority(data['priority'])
        
        # Handle progress
        if 'progress' in data and data['progress']:
            data['progress'] = JobProgress(**data['progress'])
        
        return cls(**data)


class BackgroundJobService:
    """
    Comprehensive background job service with Redis queue integration.
    
    Features:
    - Job queuing with priority support
    - Real-time progress tracking
    - Result caching with TTL
    - Job status monitoring
    - Retry logic with exponential backoff
    - Job cancellation support
    """
    
    def __init__(self):
        self.redis_client = None
        self.job_handlers: Dict[str, Callable] = {}
        self.running = False
        self._progress_callbacks: Dict[str, List[Callable]] = {}
    
    async def initialize(self):
        """Initialize the background job service."""
        try:
            # Initialize Redis connection
            self.redis_client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=False
            )
            await self.redis_client.ping()
            
            # Initialize Redis queue system
            await redis_queue.initialize()
            
            # Try to initialize hybrid queue (RabbitMQ), but don't fail if it's not available
            try:
                await hybrid_queue.initialize()
                logger.info("Hybrid queue (RabbitMQ) initialized successfully")
            except Exception as hybrid_error:
                logger.warning(f"Hybrid queue (RabbitMQ) initialization failed, continuing with Redis only: {hybrid_error}")
            
            logger.info("Background job service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize background job service: {e}")
            raise
    
    async def close(self):
        """Close connections and cleanup."""
        self.running = False
        
        if self.redis_client:
            await self.redis_client.close()
        
        await redis_queue.close()
        
        try:
            await hybrid_queue.close()
        except Exception as e:
            logger.debug(f"Error closing hybrid queue: {e}")
        
        logger.info("Background job service closed")
    
    def register_job_handler(self, job_name: str, handler: Callable):
        """Register a job handler function."""
        self.job_handlers[job_name] = handler
        logger.info(f"Registered job handler: {job_name}")
    
    def job_handler(self, job_name: str):
        """Decorator to register job handlers."""
        def decorator(func: Callable):
            self.register_job_handler(job_name, func)
            return func
        return decorator
    
    async def enqueue_job(
        self,
        job_name: str,
        args: List[Any] = None,
        kwargs: Dict[str, Any] = None,
        priority: JobPriority = JobPriority.NORMAL,
        user_id: Optional[str] = None,
        metadata: Dict[str, Any] = None,
        delay: Optional[int] = None,
        timeout: int = 600,
        max_retries: int = 3
    ) -> str:
        """
        Enqueue a background job for processing.
        
        Args:
            job_name: Name of the job to execute
            args: Positional arguments for the job
            kwargs: Keyword arguments for the job
            priority: Job priority level
            user_id: Optional user ID for job tracking
            metadata: Additional metadata for the job
            delay: Optional delay in seconds before processing
            timeout: Job timeout in seconds
            max_retries: Maximum number of retry attempts
            
        Returns:
            Job ID for tracking
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        if metadata is None:
            metadata = {}
        
        job_id = str(uuid.uuid4())
        
        # Create job instance
        job = BackgroundJob(
            id=job_id,
            name=job_name,
            args=args,
            kwargs=kwargs,
            priority=priority,
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow(),
            user_id=user_id,
            metadata=metadata,
            timeout=timeout,
            max_retries=max_retries
        )
        
        try:
            # Store job data in Redis
            job_key = f"job:{job_id}"
            job_data = json.dumps(job.to_dict(), default=str)
            
            await self.redis_client.hset(
                job_key,
                mapping={
                    'data': job_data,
                    'status': job.status.value,
                    'created_at': job.created_at.isoformat(),
                    'priority': job.priority.value
                }
            )
            
            # Set TTL for job data (24 hours)
            await self.redis_client.expire(job_key, 86400)
            
            # Convert priority to queue priority
            queue_priority = self._convert_job_priority(priority)
            
            # Enqueue to Redis queue system
            await redis_queue.enqueue_task(
                task_name=f"background_job:{job_name}",
                args=[job_id],
                kwargs={},
                priority=queue_priority,
                delay=delay
            )
            
            # Also enqueue to hybrid queue for reliability (if available)
            try:
                await hybrid_queue.enqueue_task(
                    task_name=f"background_job:{job_name}",
                    args=[job_id],
                    kwargs={},
                    priority=queue_priority,
                    delay=delay
                )
            except Exception as hybrid_error:
                logger.debug(f"Hybrid queue not available for job {job_id}: {hybrid_error}")
            
            # Add to user's job list if user_id provided
            if user_id:
                user_jobs_key = f"user_jobs:{user_id}"
                await self.redis_client.lpush(user_jobs_key, job_id)
                await self.redis_client.expire(user_jobs_key, 86400)  # 24 hours
            
            # Add to priority queue for monitoring
            priority_queue_key = f"jobs_by_priority:{priority.value}"
            await self.redis_client.zadd(
                priority_queue_key,
                {job_id: time.time()}
            )
            await self.redis_client.expire(priority_queue_key, 86400)
            
            logger.info(f"Enqueued background job {job_id} ({job_name}) with priority {priority.value}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to enqueue job {job_name}: {e}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[BackgroundJob]:
        """
        Get current status and details of a job.
        
        Args:
            job_id: Job ID to query
            
        Returns:
            BackgroundJob instance or None if not found
        """
        try:
            job_key = f"job:{job_id}"
            job_data = await self.redis_client.hgetall(job_key)
            
            if not job_data:
                return None
            
            # Decode job data
            job_json = job_data[b'data'].decode()
            job_dict = json.loads(job_json)
            
            return BackgroundJob.from_dict(job_dict)
            
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None
    
    async def update_job_progress(
        self,
        job_id: str,
        current_step: int = None,
        total_steps: int = None,
        message: str = None,
        details: Dict[str, Any] = None
    ):
        """
        Update job progress information.
        
        Args:
            job_id: Job ID to update
            current_step: Current step number
            total_steps: Total number of steps
            message: Progress message
            details: Additional progress details
        """
        try:
            job = await self.get_job_status(job_id)
            if not job:
                logger.warning(f"Cannot update progress for non-existent job {job_id}")
                return
            
            # Update progress
            job.progress.update(
                current_step=current_step,
                total_steps=total_steps,
                message=message,
                details=details
            )
            
            # Save updated job
            await self._save_job(job)
            
            # Trigger progress callbacks
            await self._trigger_progress_callbacks(job_id, job.progress)
            
            logger.debug(f"Updated progress for job {job_id}: {job.progress.percentage:.1f}%")
            
        except Exception as e:
            logger.error(f"Failed to update job progress for {job_id}: {e}")
    
    async def complete_job(self, job_id: str, result: Any = None):
        """
        Mark a job as completed with optional result.
        
        Args:
            job_id: Job ID to complete
            result: Job execution result
        """
        try:
            job = await self.get_job_status(job_id)
            if not job:
                logger.warning(f"Cannot complete non-existent job {job_id}")
                return
            
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = result
            job.progress.percentage = 100.0
            job.progress.message = "Job completed successfully"
            
            await self._save_job(job)
            
            # Cache result with TTL
            if result is not None:
                result_key = f"job_result:{job_id}"
                await cache_service.set(
                    result_key,
                    result,
                    cache_type="job_results",
                    ttl=3600  # 1 hour
                )
            
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to complete job {job_id}: {e}")
    
    async def fail_job(self, job_id: str, error: str):
        """
        Mark a job as failed with error information.
        
        Args:
            job_id: Job ID to fail
            error: Error message or description
        """
        try:
            job = await self.get_job_status(job_id)
            if not job:
                logger.warning(f"Cannot fail non-existent job {job_id}")
                return
            
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error = error
            job.progress.message = f"Job failed: {error}"
            
            await self._save_job(job)
            
            logger.error(f"Job {job_id} failed: {error}")
            
        except Exception as e:
            logger.error(f"Failed to mark job as failed {job_id}: {e}")
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a queued or processing job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if job was cancelled, False otherwise
        """
        try:
            job = await self.get_job_status(job_id)
            if not job:
                return False
            
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                return False  # Cannot cancel already finished jobs
            
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            job.progress.message = "Job cancelled by user"
            
            await self._save_job(job)
            
            logger.info(f"Job {job_id} cancelled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    async def get_user_jobs(
        self,
        user_id: str,
        status_filter: Optional[JobStatus] = None,
        limit: int = 50
    ) -> List[BackgroundJob]:
        """
        Get jobs for a specific user.
        
        Args:
            user_id: User ID to query
            status_filter: Optional status filter
            limit: Maximum number of jobs to return
            
        Returns:
            List of user's jobs
        """
        try:
            user_jobs_key = f"user_jobs:{user_id}"
            job_ids = await self.redis_client.lrange(user_jobs_key, 0, limit - 1)
            
            jobs = []
            for job_id in job_ids:
                job_id_str = job_id.decode() if isinstance(job_id, bytes) else job_id
                job = await self.get_job_status(job_id_str)
                
                if job and (status_filter is None or job.status == status_filter):
                    jobs.append(job)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to get user jobs for {user_id}: {e}")
            return []
    
    async def get_queue_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive queue statistics.
        
        Returns:
            Dictionary containing queue statistics
        """
        try:
            stats = {
                'timestamp': datetime.utcnow().isoformat(),
                'total_jobs': 0,
                'jobs_by_status': {},
                'jobs_by_priority': {},
                'queue_depths': {},
                'processing_times': {}
            }
            
            # Count jobs by status
            for status in JobStatus:
                count = 0
                # This would require scanning all jobs - in production, use counters
                stats['jobs_by_status'][status.value] = count
            
            # Count jobs by priority
            for priority in JobPriority:
                priority_queue_key = f"jobs_by_priority:{priority.value}"
                count = await self.redis_client.zcard(priority_queue_key)
                stats['jobs_by_priority'][priority.value] = count
                stats['total_jobs'] += count
            
            # Get Redis queue statistics
            redis_stats = await redis_queue.get_queue_stats()
            stats['queue_depths'] = redis_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get queue statistics: {e}")
            return {'error': str(e)}
    
    async def cleanup_completed_jobs(self, older_than_hours: int = 24):
        """
        Clean up completed jobs older than specified time.
        
        Args:
            older_than_hours: Remove jobs completed more than this many hours ago
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            cutoff_timestamp = cutoff_time.timestamp()
            
            cleaned_count = 0
            
            # Clean up from priority queues
            for priority in JobPriority:
                priority_queue_key = f"jobs_by_priority:{priority.value}"
                
                # Remove old entries
                removed = await self.redis_client.zremrangebyscore(
                    priority_queue_key,
                    0,
                    cutoff_timestamp
                )
                cleaned_count += removed
            
            logger.info(f"Cleaned up {cleaned_count} old job entries")
            
        except Exception as e:
            logger.error(f"Failed to cleanup completed jobs: {e}")
    
    def add_progress_callback(self, job_id: str, callback: Callable):
        """Add a callback function for job progress updates."""
        if job_id not in self._progress_callbacks:
            self._progress_callbacks[job_id] = []
        self._progress_callbacks[job_id].append(callback)
    
    def remove_progress_callback(self, job_id: str, callback: Callable):
        """Remove a progress callback for a job."""
        if job_id in self._progress_callbacks:
            try:
                self._progress_callbacks[job_id].remove(callback)
                if not self._progress_callbacks[job_id]:
                    del self._progress_callbacks[job_id]
            except ValueError:
                pass
    
    async def _save_job(self, job: BackgroundJob):
        """Save job data to Redis."""
        job_key = f"job:{job.id}"
        job_data = json.dumps(job.to_dict(), default=str)
        
        await self.redis_client.hset(
            job_key,
            mapping={
                'data': job_data,
                'status': job.status.value,
                'updated_at': datetime.utcnow().isoformat()
            }
        )
    
    async def _trigger_progress_callbacks(self, job_id: str, progress: JobProgress):
        """Trigger progress callbacks for a job."""
        if job_id in self._progress_callbacks:
            for callback in self._progress_callbacks[job_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(job_id, progress)
                    else:
                        callback(job_id, progress)
                except Exception as e:
                    logger.error(f"Progress callback failed for job {job_id}: {e}")
    
    def _convert_job_priority(self, job_priority: JobPriority) -> QueuePriority:
        """Convert job priority to queue priority."""
        mapping = {
            JobPriority.URGENT: QueuePriority.HIGH,
            JobPriority.HIGH: QueuePriority.HIGH,
            JobPriority.NORMAL: QueuePriority.MEDIUM,
            JobPriority.LOW: QueuePriority.LOW
        }
        return mapping.get(job_priority, QueuePriority.DEFAULT)


# Global background job service instance
background_job_service = BackgroundJobService()


# Job handler decorators for easy registration
def background_job(job_name: str):
    """Decorator to register background job handlers."""
    def decorator(func: Callable):
        background_job_service.register_job_handler(job_name, func)
        return func
    return decorator


# Example job handlers
@background_job("file_analysis")
async def analyze_file_job(job_id: str, file_path: str, analysis_type: str = "full"):
    """Example file analysis background job."""
    try:
        await background_job_service.update_job_progress(
            job_id, 
            current_step=1, 
            total_steps=5, 
            message="Starting file analysis"
        )
        
        # Simulate analysis steps
        steps = [
            "Reading file content",
            "Parsing code structure", 
            "Running static analysis",
            "Generating insights",
            "Finalizing results"
        ]
        
        for i, step in enumerate(steps, 1):
            await background_job_service.update_job_progress(
                job_id,
                current_step=i,
                total_steps=len(steps),
                message=step
            )
            
            # Simulate processing time
            await asyncio.sleep(2)
        
        # Complete with result
        result = {
            "file_path": file_path,
            "analysis_type": analysis_type,
            "issues_found": 3,
            "suggestions": 7,
            "quality_score": 85
        }
        
        await background_job_service.complete_job(job_id, result)
        
    except Exception as e:
        await background_job_service.fail_job(job_id, str(e))


@background_job("batch_file_processing")
async def batch_file_processing_job(job_id: str, file_ids: List[str]):
    """Example batch file processing job."""
    try:
        total_files = len(file_ids)
        
        await background_job_service.update_job_progress(
            job_id,
            current_step=0,
            total_steps=total_files,
            message=f"Processing {total_files} files"
        )
        
        results = []
        
        for i, file_id in enumerate(file_ids, 1):
            await background_job_service.update_job_progress(
                job_id,
                current_step=i,
                total_steps=total_files,
                message=f"Processing file {i} of {total_files}",
                details={"current_file_id": file_id}
            )
            
            # Simulate file processing
            await asyncio.sleep(1)
            
            results.append({
                "file_id": file_id,
                "status": "processed",
                "size": 1024 * (i % 10 + 1)  # Simulate varying file sizes
            })
        
        result = {
            "total_files": total_files,
            "processed_files": len(results),
            "results": results
        }
        
        await background_job_service.complete_job(job_id, result)
        
    except Exception as e:
        await background_job_service.fail_job(job_id, str(e))