#!/usr/bin/env python3
"""
Hybrid queue management script.

This script provides easy management of the hybrid queue system,
allowing you to start forwarder, worker, or both processes.

Usage:
    python start_hybrid_queue.py --mode forwarder    # Start only forwarder
    python start_hybrid_queue.py --mode worker       # Start only worker  
    python start_hybrid_queue.py --mode both         # Start both (default)
    python start_hybrid_queue.py --mode status       # Check status
    
Requirements covered: 5.1, 5.3, 5.5
"""

import asyncio
import argparse
import logging
import signal
import sys
from typing import Optional

from app.core.hybrid_forwarder import HybridForwarder
from app.core.hybrid_worker import HybridWorker
from app.core.hybrid_queue import hybrid_queue
from app.core.queue_config import monitoring_config, validate_queue_config

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


class HybridQueueManager:
    """Manager for hybrid queue processes."""
    
    def __init__(self):
        self.forwarder: Optional[HybridForwarder] = None
        self.worker: Optional[HybridWorker] = None
        self.running = False
        
    async def start_forwarder(self):
        """Start the forwarder process."""
        logger.info("Starting hybrid queue forwarder...")
        self.forwarder = HybridForwarder()
        await self.forwarder.start()
    
    async def start_worker(self):
        """Start the worker process.""" 
        logger.info("Starting hybrid queue worker...")
        self.worker = HybridWorker()
        await self.worker.start()
    
    async def start_both(self):
        """Start both forwarder and worker processes."""
        logger.info("Starting hybrid queue system (forwarder + worker)...")
        
        # Start forwarder and worker concurrently
        tasks = []
        
        self.forwarder = HybridForwarder()
        tasks.append(asyncio.create_task(self.forwarder.start()))
        
        self.worker = HybridWorker()
        tasks.append(asyncio.create_task(self.worker.start()))
        
        self.running = True
        
        try:
            # Wait for both tasks
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error running hybrid queue system: {e}")
            raise
    
    async def check_status(self):
        """Check the status of the hybrid queue system."""
        logger.info("Checking hybrid queue system status...")
        
        try:
            # Initialize connection to check status
            await hybrid_queue.initialize()
            
            # Get metrics
            metrics = await hybrid_queue.get_metrics()
            
            print("\n=== Hybrid Queue System Status ===")
            print(f"Status: {metrics['status']}")
            print(f"Redis Queue Depth: {metrics['redis_queue_depth']}")
            print(f"RabbitMQ Queue Depth: {metrics['rabbitmq_queue_depth']}")
            print(f"Tasks Enqueued (Redis): {metrics['redis_tasks_enqueued']}")
            print(f"Tasks Processed (RabbitMQ): {metrics['rabbitmq_tasks_processed']}")
            print(f"Forwarding Rate: {metrics['forwarding_rate']:.2%}")
            print(f"Failed Forwards: {metrics['failed_forwards']}")
            print(f"Last Health Check: {metrics['last_health_check']}")
            
            # Validate configuration
            config_validation = validate_queue_config()
            print(f"\n=== Configuration Status ===")
            print(f"Valid: {config_validation['valid']}")
            
            if config_validation['issues']:
                print("Issues:")
                for issue in config_validation['issues']:
                    print(f"  - {issue}")
            
            if config_validation['warnings']:
                print("Warnings:")
                for warning in config_validation['warnings']:
                    print(f"  - {warning}")
            
            await hybrid_queue.close()
            
        except Exception as e:
            logger.error(f"Failed to check status: {e}")
            print(f"Error: {e}")
    
    def stop(self):
        """Stop all processes."""
        logger.info("Stopping hybrid queue system...")
        self.running = False
        
        if self.forwarder:
            self.forwarder.stop()
        
        if self.worker:
            self.worker.stop()


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Hybrid Queue Management")
    parser.add_argument(
        '--mode',
        choices=['forwarder', 'worker', 'both', 'status'],
        default='both',
        help='Mode to run (default: both)'
    )
    parser.add_argument(
        '--validate-config',
        action='store_true',
        help='Validate configuration before starting'
    )
    
    args = parser.parse_args()
    
    # Validate configuration if requested
    if args.validate_config or args.mode != 'status':
        logger.info("Validating queue configuration...")
        config_validation = validate_queue_config()
        
        if not config_validation['valid']:
            logger.error("Configuration validation failed:")
            for issue in config_validation['issues']:
                logger.error(f"  - {issue}")
            sys.exit(1)
        
        if config_validation['warnings']:
            logger.warning("Configuration warnings:")
            for warning in config_validation['warnings']:
                logger.warning(f"  - {warning}")
    
    manager = HybridQueueManager()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        manager.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.mode == 'forwarder':
            await manager.start_forwarder()
        elif args.mode == 'worker':
            await manager.start_worker()
        elif args.mode == 'both':
            await manager.start_both()
        elif args.mode == 'status':
            await manager.check_status()
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Process failed: {e}")
        sys.exit(1)
    finally:
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())