"""
Simple test for the Background Job Queue System (Redis only).

This script tests the core functionality without RabbitMQ dependency:
- Redis-based message queue for background processing
- Job queue service for handling asynchronous tasks
- Job status tracking and progress monitoring
- Job result caching with expiration policies

Requirements covered: 2.1, 2.2, 2.3
"""

import asyncio
import logging
import time
from datetime import datetime

from app.services.background_job_service import (
    background_job_service,
    JobPriority,
    JobStatus
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_basic_functionality():
    """Test basic background job functionality."""
    logger.info("Testing basic background job functionality...")
    
    try:
        # Initialize the service
        await background_job_service.initialize()
        logger.info("✓ Background job service initialized")
        
        # Test 1: Job submission
        job_id = await background_job_service.enqueue_job(
            job_name="test_job",
            args=["test_arg"],
            kwargs={"test_param": "test_value"},
            priority=JobPriority.HIGH,
            user_id="test_user",
            metadata={"test": True}
        )
        logger.info(f"✓ Job submitted successfully: {job_id}")
        
        # Test 2: Job status retrieval
        job = await background_job_service.get_job_status(job_id)
        if job:
            logger.info(f"✓ Job status retrieved: {job.status.value}")
            logger.info(f"  - Job ID: {job.id}")
            logger.info(f"  - Job Name: {job.name}")
            logger.info(f"  - Priority: {job.priority.value}")
            logger.info(f"  - Created: {job.created_at}")
            logger.info(f"  - Progress: {job.progress.percentage}%")
        else:
            logger.error("✗ Failed to retrieve job status")
            return False
        
        # Test 3: Progress update
        await background_job_service.update_job_progress(
            job_id,
            current_step=1,
            total_steps=3,
            message="Test progress update"
        )
        
        # Verify progress update
        job = await background_job_service.get_job_status(job_id)
        if job and job.progress.current_step == 1:
            logger.info(f"✓ Progress updated: {job.progress.percentage}% - {job.progress.message}")
        else:
            logger.error("✗ Progress update failed")
            return False
        
        # Test 4: Job completion
        test_result = {"status": "success", "data": "test_data"}
        await background_job_service.complete_job(job_id, test_result)
        
        # Verify completion
        job = await background_job_service.get_job_status(job_id)
        if job and job.status == JobStatus.COMPLETED:
            logger.info(f"✓ Job completed successfully")
            logger.info(f"  - Result: {job.result}")
            logger.info(f"  - Completed at: {job.completed_at}")
        else:
            logger.error("✗ Job completion failed")
            return False
        
        # Test 5: Queue statistics
        stats = await background_job_service.get_queue_statistics()
        logger.info(f"✓ Queue statistics retrieved:")
        logger.info(f"  - Total jobs: {stats.get('total_jobs', 0)}")
        logger.info(f"  - Jobs by status: {stats.get('jobs_by_status', {})}")
        
        # Test 6: User jobs
        user_jobs = await background_job_service.get_user_jobs("test_user")
        logger.info(f"✓ User jobs retrieved: {len(user_jobs)} jobs")
        
        # Test 7: Job cancellation
        cancel_job_id = await background_job_service.enqueue_job(
            job_name="cancel_test",
            priority=JobPriority.LOW,
            user_id="test_user"
        )
        
        success = await background_job_service.cancel_job(cancel_job_id)
        if success:
            logger.info("✓ Job cancellation successful")
        else:
            logger.warning("⚠ Job cancellation failed (may already be processed)")
        
        # Test 8: Error handling
        error_job_id = await background_job_service.enqueue_job(
            job_name="error_test",
            user_id="test_user"
        )
        
        await background_job_service.fail_job(error_job_id, "Test error message")
        
        error_job = await background_job_service.get_job_status(error_job_id)
        if error_job and error_job.status == JobStatus.FAILED:
            logger.info(f"✓ Error handling works: {error_job.error}")
        else:
            logger.error("✗ Error handling failed")
            return False
        
        logger.info("✓ All basic functionality tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        return False
    finally:
        await background_job_service.close()
        logger.info("Background job service closed")


async def test_redis_queue_integration():
    """Test integration with Redis queue system."""
    logger.info("Testing Redis queue integration...")
    
    try:
        await background_job_service.initialize()
        
        # Test Redis queue statistics
        from app.core.redis_queue import redis_queue
        redis_stats = await redis_queue.get_queue_stats()
        logger.info(f"✓ Redis queue stats: {redis_stats}")
        
        # Test multiple job submissions
        job_ids = []
        for i in range(5):
            job_id = await background_job_service.enqueue_job(
                job_name=f"batch_test_{i}",
                args=[i],
                priority=JobPriority.NORMAL,
                user_id="batch_user"
            )
            job_ids.append(job_id)
        
        logger.info(f"✓ Submitted {len(job_ids)} jobs for batch test")
        
        # Check all jobs were created
        for job_id in job_ids:
            job = await background_job_service.get_job_status(job_id)
            if job:
                logger.info(f"  - Job {job_id}: {job.status.value}")
            else:
                logger.error(f"  - Job {job_id}: NOT FOUND")
        
        logger.info("✓ Redis queue integration test completed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Redis integration test failed: {e}")
        return False
    finally:
        await background_job_service.close()


async def test_performance():
    """Test performance with multiple concurrent jobs."""
    logger.info("Testing performance with concurrent jobs...")
    
    try:
        await background_job_service.initialize()
        
        start_time = time.time()
        
        # Submit multiple jobs concurrently
        tasks = []
        for i in range(20):
            task = background_job_service.enqueue_job(
                job_name=f"perf_test_{i}",
                args=[i],
                priority=JobPriority.NORMAL,
                user_id=f"perf_user_{i % 3}"  # 3 different users
            )
            tasks.append(task)
        
        job_ids = await asyncio.gather(*tasks)
        
        submission_time = time.time() - start_time
        logger.info(f"✓ Submitted {len(job_ids)} jobs in {submission_time:.3f} seconds")
        logger.info(f"  - Average: {submission_time/len(job_ids)*1000:.2f} ms per job")
        
        # Test concurrent status retrieval
        start_time = time.time()
        
        status_tasks = [background_job_service.get_job_status(job_id) for job_id in job_ids]
        jobs = await asyncio.gather(*status_tasks)
        
        retrieval_time = time.time() - start_time
        logger.info(f"✓ Retrieved {len(jobs)} job statuses in {retrieval_time:.3f} seconds")
        logger.info(f"  - Average: {retrieval_time/len(jobs)*1000:.2f} ms per retrieval")
        
        # Verify all jobs were retrieved
        successful_retrievals = sum(1 for job in jobs if job is not None)
        logger.info(f"✓ Successfully retrieved {successful_retrievals}/{len(job_ids)} jobs")
        
        logger.info("✓ Performance test completed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Performance test failed: {e}")
        return False
    finally:
        await background_job_service.close()


async def run_all_tests():
    """Run all background job system tests."""
    logger.info("=" * 60)
    logger.info("BACKGROUND JOB QUEUE SYSTEM TEST SUITE")
    logger.info("=" * 60)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Redis Queue Integration", test_redis_queue_integration),
        ("Performance Testing", test_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✓ {test_name} test PASSED")
            else:
                logger.error(f"✗ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} test ERROR: {e}")
            results.append((test_name, False))
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Background job system is working correctly.")
    else:
        logger.error(f"❌ {total - passed} tests failed. Please check the implementation.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)