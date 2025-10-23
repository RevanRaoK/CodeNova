#!/usr/bin/env python3
"""
Hybrid queue worker script.

This script runs the RabbitMQ consumer worker that processes tasks
forwarded from Redis by the forwarder process.

Usage:
    python -m app.core.hybrid_worker
    
Requirements covered: 5.1, 5.3, 5.5
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any

from app.core.hybrid_queue import hybrid_queue, HybridQueueConfig
from app.core.queue_config import monitoring_config

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


class HybridWorker:
    """Hybrid queue worker manager."""
    
    def __init__(self):
        self.running = False
        self.tasks_processed = 0
        
    async def start(self):
        """Start the hybrid worker."""
        logger.info("Starting hybrid queue worker...")
        
        try:
            # Initialize hybrid queue
            await hybrid_queue.initialize()
            
            # Register task modules
            await self._register_task_modules()
            
            # Start worker
            self.running = True
            await hybrid_queue.start_worker()
            
            logger.info("Hybrid worker started successfully")
            
            # Keep running until stopped
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Failed to start hybrid worker: {e}")
            raise
        finally:
            await hybrid_queue.close()
    
    async def _register_task_modules(self):
        """Register all task modules with the hybrid queue."""
        task_modules = [
            'app.tasks.file_analysis_tasks',
            'app.tasks.github_webhook_tasks', 
            'app.tasks.feedback_tasks',
            'app.tasks.analytics_tasks',
            'app.tasks.cache_tasks',
        ]
        
        for module_name in task_modules:
            try:
                # Import module to register tasks
                __import__(module_name)
                logger.info(f"Registered tasks from {module_name}")
            except ImportError as e:
                logger.warning(f"Could not import task module {module_name}: {e}")
            except Exception as e:
                logger.error(f"Error registering tasks from {module_name}: {e}")
    
    def stop(self):
        """Stop the worker."""
        logger.info("Stopping hybrid worker...")
        self.running = False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        metrics = await hybrid_queue.get_metrics()
        return {
            'worker_stats': {
                'tasks_processed': self.tasks_processed,
                'running': self.running,
            },
            'queue_metrics': metrics
        }


async def main():
    """Main worker function."""
    worker = HybridWorker()
    shutdown_event = asyncio.Event()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        worker.stop()
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start worker in a task so we can cancel it
        worker_task = asyncio.create_task(worker.start())
        
        # Wait for either completion or shutdown signal
        done, pending = await asyncio.wait(
            [worker_task, asyncio.create_task(shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
                
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)
    finally:
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())