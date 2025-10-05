#!/usr/bin/env python3
"""
Example usage of the hybrid queue system.

This script demonstrates how to use the hybrid queue system for various tasks
including file analysis, feedback processing, and analytics.

Usage:
    python example_hybrid_queue_usage.py
    
Requirements covered: 5.1, 5.3, 5.5
"""

import asyncio
import logging
from typing import Dict, Any

from app.core.hybrid_queue import hybrid_queue
from app.core.queue_config import QueuePriority

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_usage():
    """Example of basic hybrid queue usage."""
    logger.info("=== Basic Hybrid Queue Usage ===")
    
    try:
        # Initialize the hybrid queue
        await hybrid_queue.initialize()
        
        # Example 1: Enqueue a file analysis task
        logger.info("1. Enqueueing file analysis task...")
        file_task_id = await hybrid_queue.enqueue_task(
            "analyze_file",
            args=["file_123", "/path/to/example.py", "full"],
            priority=QueuePriority.MEDIUM
        )
        logger.info(f"   Task ID: {file_task_id}")
        
        # Example 2: Enqueue a feedback processing task
        logger.info("2. Enqueueing feedback processing task...")
        feedback_task_id = await hybrid_queue.enqueue_task(
            "process_feedback",
            args=[{
                "feedback_id": "feedback_456",
                "type": "accept",
                "suggestion_id": "suggestion_789",
                "accepted": True,
                "category": "code_optimization"
            }],
            priority=QueuePriority.HIGH
        )
        logger.info(f"   Task ID: {feedback_task_id}")
        
        # Example 3: Enqueue a delayed analytics task
        logger.info("3. Enqueueing delayed analytics task...")
        analytics_task_id = await hybrid_queue.enqueue_task(
            "generate_usage_report",
            args=["week"],
            kwargs={"user_id": "user_123"},
            priority=QueuePriority.LOW,
            delay=5  # Process in 5 seconds
        )
        logger.info(f"   Task ID: {analytics_task_id}")
        
        # Check task results
        logger.info("4. Checking task results...")
        for task_id, task_name in [
            (file_task_id, "File Analysis"),
            (feedback_task_id, "Feedback Processing"),
            (analytics_task_id, "Analytics Report")
        ]:
            result = await hybrid_queue.get_task_result(task_id)
            if result:
                logger.info(f"   {task_name}: {result.status.value}")
            else:
                logger.info(f"   {task_name}: No result found")
        
        # Get queue metrics
        logger.info("5. Getting queue metrics...")
        metrics = await hybrid_queue.get_metrics()
        logger.info(f"   Status: {metrics['status']}")
        logger.info(f"   Redis Queue Depth: {metrics['redis_queue_depth']}")
        logger.info(f"   RabbitMQ Queue Depth: {metrics['rabbitmq_queue_depth']}")
        logger.info(f"   Tasks Enqueued: {metrics['redis_tasks_enqueued']}")
        
    except Exception as e:
        logger.error(f"Error in basic usage example: {e}")
    
    finally:
        await hybrid_queue.close()


async def example_batch_processing():
    """Example of batch task processing."""
    logger.info("\n=== Batch Processing Example ===")
    
    try:
        await hybrid_queue.initialize()
        
        # Enqueue multiple file analysis tasks
        logger.info("Enqueueing batch of file analysis tasks...")
        file_ids = [f"file_{i}" for i in range(1, 6)]
        
        batch_task_id = await hybrid_queue.enqueue_task(
            "batch_analyze_files",
            args=[file_ids, "quick"],
            priority=QueuePriority.MEDIUM
        )
        
        logger.info(f"Batch task ID: {batch_task_id}")
        
        # Enqueue cache warming task
        logger.info("Enqueueing cache warming task...")
        cache_keys = [f"user:{i}:profile" for i in range(1, 11)]
        
        cache_task_id = await hybrid_queue.enqueue_task(
            "warm_cache",
            args=[cache_keys, "user"],
            priority=QueuePriority.LOW
        )
        
        logger.info(f"Cache warming task ID: {cache_task_id}")
        
        # Check results
        await asyncio.sleep(1)  # Give tasks time to be enqueued
        
        batch_result = await hybrid_queue.get_task_result(batch_task_id)
        cache_result = await hybrid_queue.get_task_result(cache_task_id)
        
        logger.info(f"Batch analysis status: {batch_result.status.value if batch_result else 'None'}")
        logger.info(f"Cache warming status: {cache_result.status.value if cache_result else 'None'}")
        
    except Exception as e:
        logger.error(f"Error in batch processing example: {e}")
    
    finally:
        await hybrid_queue.close()


async def example_custom_task():
    """Example of registering and using custom tasks."""
    logger.info("\n=== Custom Task Example ===")
    
    try:
        await hybrid_queue.initialize()
        
        # Register a custom task
        @hybrid_queue.task("custom_calculation", priority=QueuePriority.MEDIUM)
        async def custom_calculation(numbers: list, operation: str) -> Dict[str, Any]:
            """Custom task that performs calculations on a list of numbers."""
            await asyncio.sleep(0.5)  # Simulate processing
            
            if operation == "sum":
                result = sum(numbers)
            elif operation == "average":
                result = sum(numbers) / len(numbers) if numbers else 0
            elif operation == "max":
                result = max(numbers) if numbers else 0
            else:
                result = 0
            
            return {
                "operation": operation,
                "input": numbers,
                "result": result,
                "count": len(numbers)
            }
        
        # Use the custom task
        logger.info("Using custom calculation task...")
        
        calc_task_id = await hybrid_queue.enqueue_task(
            "custom_calculation",
            args=[[1, 2, 3, 4, 5], "average"],
            priority=QueuePriority.MEDIUM
        )
        
        logger.info(f"Custom calculation task ID: {calc_task_id}")
        
        # Check result
        result = await hybrid_queue.get_task_result(calc_task_id)
        logger.info(f"Custom task status: {result.status.value if result else 'None'}")
        
    except Exception as e:
        logger.error(f"Error in custom task example: {e}")
    
    finally:
        await hybrid_queue.close()


async def example_monitoring():
    """Example of monitoring queue health and performance."""
    logger.info("\n=== Monitoring Example ===")
    
    try:
        await hybrid_queue.initialize()
        
        # Add some tasks to monitor
        logger.info("Adding tasks for monitoring...")
        
        task_ids = []
        for i in range(3):
            task_id = await hybrid_queue.enqueue_task(
                "analyze_file",
                args=[f"monitor_file_{i}", f"/path/to/file_{i}.py", "quick"],
                priority=QueuePriority.MEDIUM
            )
            task_ids.append(task_id)
        
        # Get detailed metrics
        logger.info("Getting detailed metrics...")
        metrics = await hybrid_queue.get_metrics()
        
        logger.info("Queue Health Status:")
        logger.info(f"  Overall Status: {metrics['status']}")
        logger.info(f"  Redis Tasks Enqueued: {metrics['redis_tasks_enqueued']}")
        logger.info(f"  RabbitMQ Tasks Processed: {metrics['rabbitmq_tasks_processed']}")
        logger.info(f"  Forwarding Rate: {metrics['forwarding_rate']:.2%}")
        logger.info(f"  Failed Forwards: {metrics['failed_forwards']}")
        
        logger.info("Queue Depths:")
        logger.info(f"  Redis Queue: {metrics['redis_queue_depth']}")
        logger.info(f"  RabbitMQ Queue: {metrics['rabbitmq_queue_depth']}")
        
        if metrics['last_health_check']:
            logger.info(f"  Last Health Check: {metrics['last_health_check']}")
        
        # Monitor individual task status
        logger.info("Individual Task Status:")
        for i, task_id in enumerate(task_ids):
            result = await hybrid_queue.get_task_result(task_id)
            status = result.status.value if result else "unknown"
            logger.info(f"  Task {i+1}: {status}")
        
    except Exception as e:
        logger.error(f"Error in monitoring example: {e}")
    
    finally:
        await hybrid_queue.close()


async def main():
    """Main example function."""
    logger.info("🚀 Hybrid Queue System Examples")
    logger.info("=" * 50)
    
    # Run all examples
    await example_basic_usage()
    await example_batch_processing()
    await example_custom_task()
    await example_monitoring()
    
    logger.info("\n✅ All examples completed!")
    logger.info("\nTo see the hybrid queue in action:")
    logger.info("1. Start the forwarder: python -m app.core.hybrid_forwarder")
    logger.info("2. Start the worker: python -m app.core.hybrid_worker")
    logger.info("3. Or start both: python start_hybrid_queue.py --mode both")


if __name__ == "__main__":
    asyncio.run(main())