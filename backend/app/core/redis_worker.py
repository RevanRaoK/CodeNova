"""
Redis queue worker for CodeNova.

This script runs the Redis queue worker to process background tasks.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from app.core.redis_queue import redis_queue
from app.core.queue_config import queue_config, monitoring_config

# Import all task modules to register them
from app.tasks import (
    file_analysis_tasks,
    github_webhook_tasks,
    feedback_tasks,
    analytics_tasks,
    cache_tasks
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, monitoring_config.LOG_LEVEL),
    format=monitoring_config.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(monitoring_config.LOG_FILE) if monitoring_config.LOG_FILE else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


class RedisWorker:
    """Redis queue worker manager."""
    
    def __init__(self):
        self.running = False
        self.tasks: list = []
    
    async def start(self):
        """Start the worker."""
        logger.info("Starting Redis queue worker...")
        
        try:
            # Initialize Redis queue
            await redis_queue.initialize()
            
            # Start processing
            self.running = True
            
            # Create multiple worker tasks for concurrency
            for i in range(queue_config.WORKER_CONCURRENCY):
                task = asyncio.create_task(
                    self._worker_loop(f"worker-{i}")
                )
                self.tasks.append(task)
            
            logger.info(f"Started {queue_config.WORKER_CONCURRENCY} worker processes")
            
            # Wait for all tasks
            await asyncio.gather(*self.tasks)
            
        except Exception as e:
            logger.error(f"Worker startup failed: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def _worker_loop(self, worker_name: str):
        """Individual worker loop."""
        logger.info(f"Worker {worker_name} started")
        
        while self.running:
            try:
                await redis_queue.process_queues()
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def stop(self):
        """Stop the worker."""
        logger.info("Stopping Redis queue worker...")
        self.running = False
        redis_queue.stop()
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
    
    async def cleanup(self):
        """Cleanup resources."""
        await redis_queue.close()
        logger.info("Worker cleanup completed")


# Global worker instance
worker = RedisWorker()


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    asyncio.create_task(worker.stop())


async def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())