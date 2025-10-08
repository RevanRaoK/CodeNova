"""
Background Job Worker for processing queued jobs.

This worker integrates with the Redis queue system to process background jobs
with proper error handling, progress tracking, and result caching.

Requirements covered: 2.1, 2.2, 2.3
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any, Callable
from datetime import datetime

from app.services.background_job_service import (
    background_job_service,
    BackgroundJob,
    JobStatus
)
from app.core.redis_queue import redis_queue
from app.core.hybrid_queue import hybrid_queue
from app.core.config import settings

logger = logging.getLogger(__name__)


class BackgroundJobWorker:
    """
    Worker for processing background jobs from the queue system.
    
    Features:
    - Processes jobs from both Redis and hybrid queues
    - Handles job execution with proper error handling
    - Updates job progress and status
    - Supports graceful shutdown
    """
    
    def __init__(self):
        self.running = False
        self.job_handlers: Dict[str, Callable] = {}
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self):
        """Initialize the worker and queue systems."""
        try:
            # Initialize background job service
            await background_job_service.initialize()
            
            # Register job handlers from background job service
            self.job_handlers = background_job_service.job_handlers.copy()
            
            # Register background job processor with queue systems
            redis_queue.register_task("background_job", self._process_background_job)
            hybrid_queue.register_task("background_job", self._process_background_job)
            
            logger.info("Background job worker initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize background job worker: {e}")
            raise
    
    async def start(self):
        """Start the worker to process jobs."""
        self.running = True
        logger.info("Starting background job worker...")
        
        # Set up signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        try:
            # Start queue processing tasks
            tasks = [
                asyncio.create_task(self._run_redis_worker()),
                asyncio.create_task(self._run_hybrid_worker()),
                asyncio.create_task(self._monitor_worker_health())
            ]
            
            # Wait for shutdown signal or task completion
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error in worker main loop: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown the worker."""
        if not self.running:
            return
        
        logger.info("Shutting down background job worker...")
        self.running = False
        self._shutdown_event.set()
        
        try:
            # Close background job service
            await background_job_service.close()
            
            logger.info("Background job worker shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during worker shutdown: {e}")
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _run_redis_worker(self):
        """Run Redis queue worker."""
        logger.info("Starting Redis queue worker...")
        
        try:
            await redis_queue.process_queues()
        except Exception as e:
            logger.error(f"Redis worker error: {e}")
            if self.running:
                # Restart after delay
                await asyncio.sleep(5)
                if self.running:
                    await self._run_redis_worker()
    
    async def _run_hybrid_worker(self):
        """Run hybrid queue worker."""
        logger.info("Starting hybrid queue worker...")
        
        try:
            # Start forwarder and worker
            await asyncio.gather(
                hybrid_queue.start_forwarder(),
                hybrid_queue.start_worker()
            )
        except Exception as e:
            logger.error(f"Hybrid worker error: {e}")
            if self.running:
                # Restart after delay
                await asyncio.sleep(5)
                if self.running:
                    await self._run_hybrid_worker()
    
    async def _monitor_worker_health(self):
        """Monitor worker health and performance."""
        logger.info("Starting worker health monitor...")
        
        while self.running:
            try:
                # Check queue statistics
                stats = await background_job_service.get_queue_statistics()
                
                # Log health information
                total_jobs = stats.get('total_jobs', 0)
                if total_jobs > 0:
                    logger.debug(f"Queue health: {total_jobs} total jobs in queues")
                
                # Cleanup old jobs periodically (every hour)
                current_time = datetime.utcnow()
                if current_time.minute == 0:  # Top of the hour
                    await background_job_service.cleanup_completed_jobs(older_than_hours=24)
                
                # Wait before next health check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(60)
    
    async def _process_background_job(self, job_id: str):
        """
        Process a background job by ID.
        
        Args:
            job_id: ID of the job to process
        """
        try:
            # Get job details
            job = await background_job_service.get_job_status(job_id)
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            if job.status != JobStatus.QUEUED:
                logger.warning(f"Job {job_id} is not in queued status: {job.status}")
                return
            
            # Mark job as processing
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            await background_job_service._save_job(job)
            
            logger.info(f"Processing job {job_id} ({job.name})")
            
            # Find and execute job handler
            handler_name = job.name
            if handler_name not in self.job_handlers:
                error_msg = f"No handler found for job type: {handler_name}"
                logger.error(error_msg)
                await background_job_service.fail_job(job_id, error_msg)
                return
            
            handler = self.job_handlers[handler_name]
            
            # Execute job handler with timeout
            try:
                # Pass job_id as first argument, then job args
                handler_args = [job_id] + job.args
                
                if asyncio.iscoroutinefunction(handler):
                    await asyncio.wait_for(
                        handler(*handler_args, **job.kwargs),
                        timeout=job.timeout
                    )
                else:
                    # Run sync function in thread pool
                    loop = asyncio.get_event_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: handler(*handler_args, **job.kwargs)),
                        timeout=job.timeout
                    )
                
                logger.info(f"Job {job_id} completed successfully")
                
            except asyncio.TimeoutError:
                error_msg = f"Job timed out after {job.timeout} seconds"
                logger.error(f"Job {job_id} timed out")
                await background_job_service.fail_job(job_id, error_msg)
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Job {job_id} failed: {error_msg}")
                await background_job_service.fail_job(job_id, error_msg)
        
        except Exception as e:
            logger.error(f"Error processing background job {job_id}: {e}")
            try:
                await background_job_service.fail_job(job_id, str(e))
            except Exception as save_error:
                logger.error(f"Failed to save job failure status: {save_error}")


# Global worker instance
background_job_worker = BackgroundJobWorker()


async def main():
    """Main entry point for the background job worker."""
    try:
        # Initialize and start worker
        await background_job_worker.initialize()
        await background_job_worker.start()
        
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run worker
    asyncio.run(main())