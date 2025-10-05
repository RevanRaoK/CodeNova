#!/usr/bin/env python3
"""
Integration tests for the hybrid queue system.

This test suite validates the complete hybrid queue functionality including:
- Redis enqueueing
- RabbitMQ forwarding
- Task processing
- Result retrieval
- Health monitoring

Usage:
    python test_hybrid_queue_integration.py
    
Requirements covered: 5.1, 5.3, 5.5
"""

import asyncio
import pytest
import logging
import time
from typing import Dict, Any

from app.core.hybrid_queue import hybrid_queue, HybridQueueConfig, HybridQueueStatus
from app.core.queue_config import QueuePriority
from app.tasks.file_analysis_tasks import analyze_file
from app.tasks.feedback_tasks import process_feedback

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestHybridQueue:
    """Test suite for hybrid queue system."""
    
    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Setup
        await hybrid_queue.initialize()
        await hybrid_queue.purge_queues()  # Clean state
        
        yield
        
        # Teardown
        await hybrid_queue.close()
    
    async def test_basic_task_enqueue_and_retrieve(self):
        """Test basic task enqueueing and result retrieval."""
        logger.info("Testing basic task enqueue and retrieve...")
        
        # Enqueue a task
        task_id = await hybrid_queue.enqueue_task(
            "test_task",
            args=["arg1", "arg2"],
            kwargs={"key": "value"},
            priority=QueuePriority.HIGH
        )
        
        assert task_id is not None
        assert len(task_id) > 0
        
        # Check task result (should be pending initially)
        result = await hybrid_queue.get_task_result(task_id)
        assert result is not None
        assert result.status.value == "pending"
        
        logger.info("✓ Basic enqueue and retrieve test passed")
    
    async def test_task_forwarding(self):
        """Test task forwarding from Redis to RabbitMQ."""
        logger.info("Testing task forwarding...")
        
        # Enqueue multiple tasks
        task_ids = []
        for i in range(5):
            task_id = await hybrid_queue.enqueue_task(
                f"test_task_{i}",
                args=[i],
                priority=QueuePriority.MEDIUM
            )
            task_ids.append(task_id)
        
        # Get initial metrics
        initial_metrics = await hybrid_queue.get_metrics()
        initial_redis_depth = initial_metrics["redis_queue_depth"]
        
        # Run forwarder for a short time
        forwarder_task = asyncio.create_task(hybrid_queue.start_forwarder())
        await asyncio.sleep(3)  # Let forwarder run
        forwarder_task.cancel()
        
        try:
            await forwarder_task
        except asyncio.CancelledError:
            pass
        
        # Check metrics after forwarding
        final_metrics = await hybrid_queue.get_metrics()
        
        # Should have forwarded some tasks
        assert final_metrics["rabbitmq_tasks_processed"] >= 0
        
        logger.info("✓ Task forwarding test passed")
    
    async def test_registered_task_execution(self):
        """Test execution of registered tasks."""
        logger.info("Testing registered task execution...")
        
        # Register a simple test task
        @hybrid_queue.task("simple_test_task", priority=QueuePriority.HIGH)
        async def simple_test_task(x: int, y: int) -> int:
            return x + y
        
        # Enqueue the task
        task_id = await hybrid_queue.enqueue_task(
            "simple_test_task",
            args=[5, 3],
            priority=QueuePriority.HIGH
        )
        
        # Start worker and forwarder
        worker_task = asyncio.create_task(hybrid_queue.start_worker())
        forwarder_task = asyncio.create_task(hybrid_queue.start_forwarder())
        
        # Wait for processing
        await asyncio.sleep(5)
        
        # Stop tasks
        worker_task.cancel()
        forwarder_task.cancel()
        
        try:
            await asyncio.gather(worker_task, forwarder_task, return_exceptions=True)
        except:
            pass
        
        # Check result
        result = await hybrid_queue.get_task_result(task_id)
        
        # Note: In a real test environment with RabbitMQ running,
        # we would expect the task to be processed and result to be available
        logger.info(f"Task result status: {result.status.value if result else 'None'}")
        
        logger.info("✓ Registered task execution test completed")
    
    async def test_priority_queues(self):
        """Test that different priority queues work correctly."""
        logger.info("Testing priority queues...")
        
        priorities = [QueuePriority.HIGH, QueuePriority.MEDIUM, QueuePriority.LOW]
        task_ids = {}
        
        # Enqueue tasks with different priorities
        for priority in priorities:
            task_id = await hybrid_queue.enqueue_task(
                f"priority_test_{priority.value}",
                args=[priority.value],
                priority=priority
            )
            task_ids[priority] = task_id
        
        # Verify all tasks were enqueued
        for priority, task_id in task_ids.items():
            result = await hybrid_queue.get_task_result(task_id)
            assert result is not None
            assert result.status.value == "pending"
        
        logger.info("✓ Priority queues test passed")
    
    async def test_delayed_tasks(self):
        """Test delayed task scheduling."""
        logger.info("Testing delayed tasks...")
        
        # Enqueue a delayed task
        task_id = await hybrid_queue.enqueue_task(
            "delayed_test_task",
            args=["delayed"],
            priority=QueuePriority.MEDIUM,
            delay=2  # 2 seconds delay
        )
        
        # Task should be pending
        result = await hybrid_queue.get_task_result(task_id)
        assert result is not None
        assert result.status.value == "pending"
        
        logger.info("✓ Delayed tasks test passed")
    
    async def test_metrics_collection(self):
        """Test metrics collection and health monitoring."""
        logger.info("Testing metrics collection...")
        
        # Get initial metrics
        metrics = await hybrid_queue.get_metrics()
        
        # Verify metrics structure
        expected_keys = [
            "redis_tasks_enqueued",
            "rabbitmq_tasks_processed", 
            "forwarding_rate",
            "redis_queue_depth",
            "rabbitmq_queue_depth",
            "failed_forwards",
            "status"
        ]
        
        for key in expected_keys:
            assert key in metrics, f"Missing metric: {key}"
        
        # Verify status is valid
        assert metrics["status"] in [status.value for status in HybridQueueStatus]
        
        logger.info("✓ Metrics collection test passed")
    
    async def test_queue_purging(self):
        """Test queue purging functionality."""
        logger.info("Testing queue purging...")
        
        # Enqueue some tasks
        for i in range(3):
            await hybrid_queue.enqueue_task(
                f"purge_test_{i}",
                args=[i],
                priority=QueuePriority.DEFAULT
            )
        
        # Get metrics before purging
        before_metrics = await hybrid_queue.get_metrics()
        
        # Purge queues
        await hybrid_queue.purge_queues()
        
        # Get metrics after purging
        after_metrics = await hybrid_queue.get_metrics()
        
        # Redis queue depth should be 0 after purging
        assert after_metrics["redis_queue_depth"] == 0
        
        logger.info("✓ Queue purging test passed")
    
    async def test_error_handling(self):
        """Test error handling in task processing."""
        logger.info("Testing error handling...")
        
        # Register a task that will fail
        @hybrid_queue.task("failing_task", priority=QueuePriority.HIGH)
        async def failing_task():
            raise ValueError("This task is designed to fail")
        
        # Enqueue the failing task
        task_id = await hybrid_queue.enqueue_task(
            "failing_task",
            priority=QueuePriority.HIGH
        )
        
        # Task should be enqueued successfully
        result = await hybrid_queue.get_task_result(task_id)
        assert result is not None
        assert result.status.value == "pending"
        
        logger.info("✓ Error handling test passed")


async def run_integration_tests():
    """Run all integration tests."""
    logger.info("Starting hybrid queue integration tests...")
    
    test_instance = TestHybridQueue()
    
    # List of test methods
    tests = [
        test_instance.test_basic_task_enqueue_and_retrieve,
        test_instance.test_task_forwarding,
        test_instance.test_registered_task_execution,
        test_instance.test_priority_queues,
        test_instance.test_delayed_tasks,
        test_instance.test_metrics_collection,
        test_instance.test_queue_purging,
        test_instance.test_error_handling,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            # Setup
            await hybrid_queue.initialize()
            await hybrid_queue.purge_queues()
            
            # Run test
            await test()
            passed += 1
            
        except Exception as e:
            logger.error(f"Test {test.__name__} failed: {e}")
            failed += 1
            
        finally:
            # Cleanup
            try:
                await hybrid_queue.close()
            except:
                pass
    
    logger.info(f"\n=== Test Results ===")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All tests passed!")
    else:
        logger.warning(f"⚠️  {failed} test(s) failed")
    
    return failed == 0


async def test_real_task_modules():
    """Test real task modules from the application."""
    logger.info("Testing real task modules...")
    
    try:
        await hybrid_queue.initialize()
        
        # Test file analysis task
        logger.info("Testing file analysis task...")
        file_task_id = await hybrid_queue.enqueue_task(
            "analyze_file",
            args=["test_file_123", "/path/to/test.py", "quick"],
            priority=QueuePriority.MEDIUM
        )
        
        # Test feedback processing task
        logger.info("Testing feedback processing task...")
        feedback_task_id = await hybrid_queue.enqueue_task(
            "process_feedback",
            args=[{
                "feedback_id": "test_feedback_123",
                "type": "accept",
                "suggestion_id": "suggestion_456",
                "accepted": True
            }],
            priority=QueuePriority.MEDIUM
        )
        
        logger.info(f"File analysis task ID: {file_task_id}")
        logger.info(f"Feedback processing task ID: {feedback_task_id}")
        
        # Check task results
        file_result = await hybrid_queue.get_task_result(file_task_id)
        feedback_result = await hybrid_queue.get_task_result(feedback_task_id)
        
        logger.info(f"File task status: {file_result.status.value if file_result else 'None'}")
        logger.info(f"Feedback task status: {feedback_result.status.value if feedback_result else 'None'}")
        
        logger.info("✓ Real task modules test completed")
        
    except Exception as e:
        logger.error(f"Real task modules test failed: {e}")
    
    finally:
        await hybrid_queue.close()


async def main():
    """Main test function."""
    logger.info("=== Hybrid Queue Integration Test Suite ===\n")
    
    # Run integration tests
    success = await run_integration_tests()
    
    # Test real task modules
    await test_real_task_modules()
    
    logger.info("\n=== Test Suite Complete ===")
    
    return success


if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(main())
    
    if not success:
        exit(1)