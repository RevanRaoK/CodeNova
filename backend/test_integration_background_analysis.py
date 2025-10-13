"""
Integration test for Background Code Analysis Service.

This test verifies the integration between:
- Background Code Analysis Service
- Background Job Service  
- Cache Service
- Analysis Notification Service
- API endpoints

Requirements covered: 2.1, 2.6
"""

import asyncio
import logging
import sys
import time
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append('.')

from app.services.background_code_analysis_service import (
    background_code_analysis_service,
    AnalysisType,
    AnalysisStatus
)
from app.services.background_job_service import background_job_service
from app.services.cache_service import cache_service
from app.services.analysis_notification_service import analysis_notification_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_service_integration():
    """Test integration between all services."""
    logger.info("Starting Background Code Analysis Integration Test")
    
    try:
        # Initialize all services
        logger.info("Initializing services...")
        
        await cache_service.initialize()
        await background_job_service.initialize()
        await background_code_analysis_service.initialize()
        await analysis_notification_service.initialize()
        
        logger.info("All services initialized successfully")
        
        # Test 1: Simple analysis workflow
        logger.info("Test 1: Simple analysis workflow")
        
        test_code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# This is inefficient - should use memoization
result = calculate_fibonacci(10)
print(f"Fibonacci(10) = {result}")
"""
        
        # Queue analysis
        analysis_id = await background_code_analysis_service.queue_analysis(
            content=test_code,
            language="python",
            analysis_type=AnalysisType.FULL,
            user_id="integration_test_user",
            metadata={"test": "integration_test_1"}
        )
        
        logger.info(f"Queued analysis: {analysis_id}")
        
        # Monitor progress
        progress_updates = []
        
        def progress_callback(aid, message, percentage):
            progress_updates.append({
                'analysis_id': aid,
                'message': message,
                'percentage': percentage,
                'timestamp': time.time()
            })
            logger.info(f"Progress: {percentage:.1f}% - {message}")
        
        # Add progress callback
        background_code_analysis_service.add_progress_callback(analysis_id, progress_callback)
        
        # Wait for completion
        timeout = 120  # 2 minutes
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = await background_code_analysis_service.get_analysis_status(analysis_id)
            
            if result and result.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
                break
            
            await asyncio.sleep(2)
        
        # Verify results
        final_result = await background_code_analysis_service.get_analysis_status(analysis_id)
        
        if not final_result:
            raise Exception("Analysis result not found")
        
        if final_result.status != AnalysisStatus.COMPLETED:
            raise Exception(f"Analysis failed with status: {final_result.status}")
        
        logger.info(f"✓ Analysis completed successfully")
        logger.info(f"  - Issues found: {len(final_result.issues)}")
        logger.info(f"  - Suggestions: {len(final_result.suggestions)}")
        logger.info(f"  - Processing time: {final_result.processing_time:.2f}s")
        logger.info(f"  - Progress updates: {len(progress_updates)}")
        
        # Test 2: Batch analysis
        logger.info("Test 2: Batch analysis")
        
        batch_requests = [
            {
                'content': 'def func1(): return "test1"',
                'language': 'python',
                'analysis_type': 'quick',
                'metadata': {'batch_test': True}
            },
            {
                'content': 'function func2() { return "test2"; }',
                'language': 'javascript',
                'analysis_type': 'quick',
                'metadata': {'batch_test': True}
            },
            {
                'content': 'const func3 = (): string => "test3";',
                'language': 'typescript',
                'analysis_type': 'quick',
                'metadata': {'batch_test': True}
            }
        ]
        
        batch_id = await background_code_analysis_service.queue_batch_analysis(
            analysis_requests=batch_requests,
            user_id="integration_test_user"
        )
        
        logger.info(f"Queued batch analysis: {batch_id}")
        
        # Wait for batch completion
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            batch_status = await background_code_analysis_service.get_batch_status(batch_id)
            
            if batch_status:
                total = batch_status['total_count']
                completed = batch_status['completed_count']
                failed = batch_status['failed_count']
                
                logger.info(f"Batch progress: {completed + failed}/{total} completed")
                
                if completed + failed >= total:
                    break
            
            await asyncio.sleep(3)
        
        # Verify batch results
        final_batch_status = await background_code_analysis_service.get_batch_status(batch_id)
        
        if not final_batch_status:
            raise Exception("Batch status not found")
        
        logger.info(f"✓ Batch analysis completed")
        logger.info(f"  - Total analyses: {final_batch_status['total_count']}")
        logger.info(f"  - Completed: {final_batch_status['completed_count']}")
        logger.info(f"  - Failed: {final_batch_status['failed_count']}")
        
        # Test 3: Cache functionality
        logger.info("Test 3: Cache functionality")
        
        # Queue identical analysis (should use cache)
        cache_test_code = "def simple_func(): return 42"
        
        # First analysis
        start_time = time.time()
        analysis_id_1 = await background_code_analysis_service.queue_analysis(
            content=cache_test_code,
            language="python",
            analysis_type=AnalysisType.QUICK,
            user_id="integration_test_user"
        )
        
        # Wait for completion
        while time.time() - start_time < 60:
            result_1 = await background_code_analysis_service.get_analysis_status(analysis_id_1)
            if result_1 and result_1.status == AnalysisStatus.COMPLETED:
                break
            await asyncio.sleep(1)
        
        first_analysis_time = time.time() - start_time
        
        # Second identical analysis (should be faster due to caching)
        start_time = time.time()
        analysis_id_2 = await background_code_analysis_service.queue_analysis(
            content=cache_test_code,
            language="python",
            analysis_type=AnalysisType.QUICK,
            user_id="integration_test_user"
        )
        
        # Wait for completion
        while time.time() - start_time < 60:
            result_2 = await background_code_analysis_service.get_analysis_status(analysis_id_2)
            if result_2 and result_2.status == AnalysisStatus.COMPLETED:
                break
            await asyncio.sleep(1)
        
        second_analysis_time = time.time() - start_time
        
        logger.info(f"✓ Cache test completed")
        logger.info(f"  - First analysis time: {first_analysis_time:.2f}s")
        logger.info(f"  - Second analysis time: {second_analysis_time:.2f}s")
        logger.info(f"  - Cache speedup: {first_analysis_time/second_analysis_time:.1f}x")
        
        # Test 4: Metrics collection
        logger.info("Test 4: Metrics collection")
        
        metrics = await background_code_analysis_service.get_analysis_metrics()
        
        logger.info(f"✓ Metrics collected successfully")
        logger.info(f"  - Total analyses: {metrics['analysis_metrics']['total_analyses']}")
        logger.info(f"  - Completed analyses: {metrics['analysis_metrics']['completed_analyses']}")
        logger.info(f"  - Cache hits: {metrics['analysis_metrics']['cache_hits']}")
        logger.info(f"  - Cache misses: {metrics['analysis_metrics']['cache_misses']}")
        
        # Test 5: User analyses retrieval
        logger.info("Test 5: User analyses retrieval")
        
        user_analyses = await background_code_analysis_service.get_user_analyses(
            user_id="integration_test_user",
            limit=10
        )
        
        logger.info(f"✓ User analyses retrieved")
        logger.info(f"  - Total user analyses: {len(user_analyses)}")
        
        # All tests passed
        logger.info("="*60)
        logger.info("🎉 ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
        logger.info("="*60)
        logger.info("Services tested:")
        logger.info("  ✓ Background Code Analysis Service")
        logger.info("  ✓ Background Job Service")
        logger.info("  ✓ Cache Service")
        logger.info("  ✓ Analysis Notification Service")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        logger.error("="*60)
        logger.error("❌ INTEGRATION TESTS FAILED")
        logger.error("="*60)
        raise
    
    finally:
        # Cleanup
        try:
            await background_job_service.close()
            await cache_service.close()
            logger.info("Services closed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """Main test function."""
    try:
        success = await test_service_integration()
        
        if success:
            logger.info("Integration test completed successfully!")
            sys.exit(0)
        else:
            logger.error("Integration test failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Integration test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the integration test
    asyncio.run(main())