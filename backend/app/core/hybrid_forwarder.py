#!/usr/bin/env python3
"""
Hybrid queue forwarder script.

This script runs the forwarder process that moves tasks from Redis
to RabbitMQ for reliable processing.

Usage:
    python -m app.core.hybrid_forwarder
    
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


class HybridForwarder:
    """Hybrid queue forwarder manager."""
    
    def __init__(self):
        self.running = False
        self.tasks_forwarded = 0
        
    async def start(self):
        """Start the hybrid forwarder."""
        logger.info("Starting hybrid queue forwarder...")
        
        try:
            # Initialize hybrid queue
            await hybrid_queue.initialize()
            
            # Start forwarder
            self.running = True
            await hybrid_queue.start_forwarder()
            
            logger.info("Hybrid forwarder started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start hybrid forwarder: {e}")
            raise
        finally:
            await hybrid_queue.close()
    
    def stop(self):
        """Stop the forwarder."""
        logger.info("Stopping hybrid forwarder...")
        self.running = False
        hybrid_queue.running = False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get forwarder statistics."""
        metrics = await hybrid_queue.get_metrics()
        return {
            'forwarder_stats': {
                'tasks_forwarded': self.tasks_forwarded,
                'running': self.running,
            },
            'queue_metrics': metrics
        }


async def main():
    """Main forwarder function."""
    forwarder = HybridForwarder()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        forwarder.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await forwarder.start()
    except KeyboardInterrupt:
        logger.info("Forwarder interrupted by user")
    except Exception as e:
        logger.error(f"Forwarder failed: {e}")
        sys.exit(1)
    finally:
        logger.info("Forwarder shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())