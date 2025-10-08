"""
Test script for the Background Job Queue System.

This script tests the implementation of task 3:
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
    JobStatus,
    background_job
)
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@background_job("test_simple_job")
async def test_simple_job(job_id: str, message: str = "Hello World"):
    """Simple test job for basic functionality."""
    logger.info(f"Starting simple job {job_id} with message: {message}")
    
    # Update progress
    await background_job_service.update_job_progress(
        job_id, 
        current_step=1, 
        total_steps=3, 
        message="Processing step 1"
    )
    
    await asyncio.sleep(1)
    
    await background_job_service.update_job_progress(
        job_id, 
        current_step=2, 
        total_steps=3, 
        message="Processing step 2"
    )
    
    await asyncio.sleep(1)
    
    await background_job_service.update_job_progress(
        job_id, 
        current_step=3, 
        total_steps=3, 
        message="Finalizing"
    )
    
    result = {
        "message": message,
        "processed_at": datetime.utcnow().isoformat(),
        "job_id": job_id
    }
    
    await background_job_service.complete_job(job_id, result)
    logger.info(f"Completed simple job {job_id}")


@background_job("test_error_job")
async def test_error_job(job_id: str, should_fail: bool = True):
    """Test job that demonstrates error handling."""
    logger.info(f"Starting error job {job_id}")
    
    await background_job_service.update_job_progress(
        job_id, 
        current_step=1, 
        total_steps=2, 
        message="Starting error test"
    )
    
    await asyncio.sleep(0.5)
    
    if should_fail:
        raise Exception("Intentional test error")
    
    await background_job_service.complete_job(job_id, {"status": "success"})


@background_job("test_long_job")
async def test_long_job(job_id: str, duration: int = 10):
    """Test job with longer duration for progress tracking."""
    logger.info(f"Starting long job {job_id} with duration {duration}s")
    
    steps = duration
    for i in range(steps):
        await background_job_service.update_job_progress(
            job_id,
            current_step=i + 1,
            total_steps=steps,
            message=f"Processing step {i + 1} of {steps}",
            details={"current_time": datetime.utcnow().isoformat()}
        )
        
        await asyncio.sleep(1)
    
    result = {
        "duration": duration,
        "steps_completed": steps,
        "completed_at": datetime.utcnow().isoformat()
    }
    
    await background_job_service.complete_job(job_id, result)
    logger.info(f"Completed long job {job_id}")


async def test_job_submission():
    """Test job submission functionality."""
    logger.info("Testing job submission...")
    
    # Test simple job
    job_id1 = await background_job_service.enqueue_job(
        job_name="test_simple_job",
        args=["Test message from submission test"],
        priority=JobPriority.HIGH,
        user_id="test_user_1",
        metadata={"test_type": "submission"}
    )
    
    logger.info(f"Submitted simple job: {job_id1}")
    
    # Test error job
    job_id2 = await background_job_service.enqueue_job(
        job_name="test_error_job",
        kwargs={"should_fail": True},
        priority=JobPriority.NORMAL,
        user_id="test_user_1",
        metadata={"test_type": "error_handling"}
    )
    
    logger.info(f"Submitted error job: {job_id2}")
    
    # Test long job
    job_id3 = await background_job_service.enqueue_job(
        job_name="test_long_job",
        kwargs={"duration": 5},
        priority=JobPriority.LOW,
        user_id="test_user_2",
        metadata={"test_type": "progress_tracking"}
    )
    
    logger.info(f"Submitted long job: {job_id3}")
    
    return [job_id1, job_id2, job_id3]


async def test_job_status_tracking(job_ids):
    """Test job status tracking functionality."""
    logger.info("Testing job status tracking...")
    
    for job_id in job_ids:
        job = await background_job_service.get_job_status(job_id)
        if job:
            logger.info(f"Job {job_id}: Status={job.status.value}, Progress={job.progress.percentage:.1f}%")
        else:
            logger.warning(f"Job {job_id} not found")


async def test_queue_statistics():
    """Test queue statistics functionality."""
    logger.info("Testing queue statistics...")
    
    stats = await background_job_service.get_queue_statistics()
    logger.info(f"Queue statistics: {stats}")


async def test_user_jobs():
    """Test user job retrieval functionality."""
    logger.info("Testing user job retrieval...")
    
    # Get jobs for test users
    user1_jobs = await background_job_service.get_user_jobs("test_user_1")
    user2_jobs = await background_job_service.get_user_jobs("test_user_2")
    
    logger.info(f"User 1 has {len(user1_jobs)} jobs")
    logger.info(f"User 2 has {len(user2_jobs)} jobs")
    
    for job in user1_jobs:
        logger.info(f"  Job {job.id}: {job.name} - {job.status.value}")


async def monitor_job_progress(job_id: str, timeout: int = 30):
    """Monitor a job's progress until completion."""
    logger.info(f"Monitoring job {job_id} progress...")
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        job = await background_job_service.get_job_status(job_id)
        
        if not job:
            logger.error(f"Job {job_id} not found")
            break
        
        logger.info(f"Job {job_id}: {job.status.value} - {job.progress.percentage:.1f}% - {job.progress.message}")
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            if job.status == JobStatus.COMPLETED:
                logger.info(f"Job {job_id} completed successfully. Result: {job.result}")
            elif job.status == JobStatus.FAILED:
                logger.error(f"Job {job_id} failed: {job.error}")
            break
        
        await asyncio.sleep(2)
    else:
        logger.warning(f"Job {job_id} monitoring timed out")


async def test_job_cancellation():
    """Test job cancellation functionality."""
    logger.info("Testing job cancellation...")
    
    # Submit a long job
    job_id = await background_job_service.enqueue_job(
        job_name="test_long_job",
        kwargs={"duration": 20},
        priority=JobPriority.NORMAL,
        user_id="test_user_cancel",
        metadata={"test_type": "cancellation"}
    )
    
    logger.info(f"Submitted job for cancellation test: {job_id}")
    
    # Wait a bit then cancel
    await asyncio.sleep(2)
    
    success = await background_job_service.cancel_job(job_id)
    logger.info(f"Job cancellation {'successful' if success else 'failed'}")
    
    # Check final status
    job = await background_job_service.get_job_status(job_id)
    if job:
        logger.info(f"Final job status: {job.status.value}")


async def run_comprehensive_test():
    """Run comprehensive test of the background job system."""
    logger.info("Starting comprehensive background job system test...")
    
    try:
        # Initialize the service
        await background_job_service.initialize()
        logger.info("Background job service initialized")
        
        # Test 1: Job submission
        job_ids = await test_job_submission()
        
        # Test 2: Initial status check
        await asyncio.sleep(1)
        await test_job_status_tracking(job_ids)
        
        # Test 3: Queue statistics
        await test_queue_statistics()
        
        # Test 4: Monitor one job's progress
        if job_ids:
            await monitor_job_progress(job_ids[0], timeout=15)
        
        # Test 5: User jobs
        await test_user_jobs()
        
        # Test 6: Job cancellation
        await test_job_cancellation()
        
        # Test 7: Final statistics
        await asyncio.sleep(2)
        await test_queue_statistics()
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        # Cleanup
        await background_job_service.close()
        logger.info("Background job service closed")


if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())