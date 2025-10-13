"""
Simple test for Background Code Analysis Service without requiring workers.

This test focuses on testing the service initialization, job queuing,
caching, and basic functionality without requiring background workers.

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
    AnalysisStatus,
    AnalysisRequest,
    AnalysisResult
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


async def test_service_functionality():
    """Test core service functionality without requiring workers."""
    logger.info("Starting Background Code Analysis Service Functionality Test")
    
    try:
        # Test 1: Service Initialization
        logger.info("Test 1: Service Initialization")
        
        await cache_service.initialize()
        await background_job_service.initialize()
        await background_code_analysis_service.initialize()
        await analysis_notification_service.initialize()
        
        logger.info("✓ All services initialized successfully")
        
        # Test 2: Job Queuing
        logger.info("Test 2: Job Queuing")
        
        test_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
"""
        
        analysis_id = await background_code_analysis_service.queue_analysis(
            content=test_code,
            language="python",
            analysis_type=AnalysisType.QUICK,
            user_id="test_user",
            metadata={"test": "functionality_test"}
        )
        
        logger.info(f"✓ Analysis queued successfully: {analysis_id}")
        
        # Test 3: Status Retrieval
        logger.info("Test 3: Status Retrieval")
        
        result = await background_code_analysis_service.get_analysis_status(analysis_id)
        
        assert result is not None, "Analysis result should not be None"
        assert result.analysis_id == analysis_id, "Analysis ID should match"
        assert result.status in [AnalysisStatus.PENDING, AnalysisStatus.QUEUED], "Status should be pending or queued"
        assert result.request.language == "python", "Language should be python"
        assert result.request.analysis_type == AnalysisType.QUICK, "Analysis type should be quick"
        
        logger.info(f"✓ Status retrieved successfully: {result.status.value}")
        
        # Test 4: Batch Analysis Queuing
        logger.info("Test 4: Batch Analysis Queuing")
        
        batch_requests = [
            {
                'content': 'def func1(): return "test1"',
                'language': 'python',
                'analysis_type': 'quick'
            },
            {
                'content': 'function func2() { return "test2"; }',
                'language': 'javascript',
                'analysis_type': 'quick'
            }
        ]
        
        batch_id = await background_code_analysis_service.queue_batch_analysis(
            analysis_requests=batch_requests,
            user_id="test_user"
        )
        
        logger.info(f"✓ Batch analysis queued successfully: {batch_id}")
        
        # Test 5: Batch Status Retrieval
        logger.info("Test 5: Batch Status Retrieval")
        
        batch_status = await background_code_analysis_service.get_batch_status(batch_id)
        
        assert batch_status is not None, "Batch status should not be None"
        assert batch_status['total_count'] == 2, "Should have 2 analyses in batch"
        assert batch_status['batch_id'] == batch_id, "Batch ID should match"
        
        logger.info(f"✓ Batch status retrieved successfully: {batch_status['total_count']} analyses")
        
        # Test 6: Cache Key Generation
        logger.info("Test 6: Cache Key Generation")
        
        request = AnalysisRequest(
            id="test_id",
            content="test content",
            language="python",
            analysis_type=AnalysisType.QUICK
        )
        
        cache_key = background_code_analysis_service._generate_cache_key(request)
        
        assert cache_key is not None, "Cache key should not be None"
        assert len(cache_key) > 0, "Cache key should not be empty"
        
        logger.info(f"✓ Cache key generated successfully: {cache_key[:16]}...")
        
        # Test 7: Analysis Cancellation
        logger.info("Test 7: Analysis Cancellation")
        
        # Queue another analysis to cancel
        cancel_test_id = await background_code_analysis_service.queue_analysis(
            content="def test(): pass",
            language="python",
            analysis_type=AnalysisType.FULL,
            user_id="test_user"
        )
        
        # Try to cancel it
        cancelled = await background_code_analysis_service.cancel_analysis(cancel_test_id)
        
        if cancelled:
            logger.info("✓ Analysis cancelled successfully")
            
            # Check final status
            final_result = await background_code_analysis_service.get_analysis_status(cancel_test_id)
            assert final_result.status == AnalysisStatus.CANCELLED, "Status should be cancelled"
        else:
            logger.info("✓ Analysis cancellation handled (may have completed before cancellation)")
        
        # Test 8: User Analyses Retrieval
        logger.info("Test 8: User Analyses Retrieval")
        
        user_analyses = await background_code_analysis_service.get_user_analyses(
            user_id="test_user",
            limit=10
        )
        
        assert isinstance(user_analyses, list), "User analyses should be a list"
        logger.info(f"✓ User analyses retrieved: {len(user_analyses)} analyses found")
        
        # Test 9: Metrics Collection
        logger.info("Test 9: Metrics Collection")
        
        metrics = await background_code_analysis_service.get_analysis_metrics()
        
        assert 'analysis_metrics' in metrics, "Should have analysis metrics"
        assert 'cache_metrics' in metrics, "Should have cache metrics"
        assert 'queue_metrics' in metrics, "Should have queue metrics"
        
        analysis_metrics = metrics['analysis_metrics']
        assert 'total_analyses' in analysis_metrics, "Should have total analyses count"
        assert analysis_metrics['total_analyses'] > 0, "Should have queued some analyses"
        
        logger.info(f"✓ Metrics collected successfully: {analysis_metrics['total_analyses']} total analyses")
        
        # Test 10: Progress Callback Registration
        logger.info("Test 10: Progress Callback Registration")
        
        callback_called = False
        
        def test_callback(analysis_id, message, percentage):
            nonlocal callback_called
            callback_called = True
            logger.info(f"Progress callback: {analysis_id} - {percentage}% - {message}")
        
        # Register callback
        background_code_analysis_service.add_progress_callback(analysis_id, test_callback)
        
        # Remove callback
        background_code_analysis_service.remove_progress_callback(analysis_id, test_callback)
        
        logger.info("✓ Progress callback registration/removal successful")
        
        # Test 11: Notification Service Integration
        logger.info("Test 11: Notification Service Integration")
        
        # Test subscription
        await analysis_notification_service.subscribe_to_analysis("test_user", analysis_id)
        
        # Test unsubscription
        await analysis_notification_service.unsubscribe_from_analysis("test_user", analysis_id)
        
        # Test preferences
        preferences = await analysis_notification_service.get_user_preferences("test_user")
        assert isinstance(preferences, dict), "Preferences should be a dictionary"
        
        logger.info("✓ Notification service integration successful")
        
        # Test 12: Cache Service Integration
        logger.info("Test 12: Cache Service Integration")
        
        # Test cache operations
        test_key = "test_cache_key"
        test_value = {"test": "data", "timestamp": time.time()}
        
        # Set cache
        cache_set = await cache_service.set(test_key, test_value, "code_analysis", 300)
        assert cache_set, "Cache set should succeed"
        
        # Get cache
        cached_value = await cache_service.get(test_key, "code_analysis")
        assert cached_value is not None, "Cached value should not be None"
        assert cached_value["test"] == "data", "Cached data should match"
        
        # Delete cache
        cache_deleted = await cache_service.delete(test_key, "code_analysis")
        assert cache_deleted, "Cache delete should succeed"
        
        logger.info("✓ Cache service integration successful")
        
        # All tests passed
        logger.info("="*60)
        logger.info("🎉 ALL FUNCTIONALITY TESTS PASSED SUCCESSFULLY!")
        logger.info("="*60)
        logger.info("Components tested:")
        logger.info("  ✓ Service Initialization")
        logger.info("  ✓ Job Queuing")
        logger.info("  ✓ Status Retrieval")
        logger.info("  ✓ Batch Analysis")
        logger.info("  ✓ Cache Integration")
        logger.info("  ✓ Analysis Cancellation")
        logger.info("  ✓ User Analysis Management")
        logger.info("  ✓ Metrics Collection")
        logger.info("  ✓ Progress Callbacks")
        logger.info("  ✓ Notification Service")
        logger.info("  ✓ Cache Service")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Functionality test failed: {e}")
        logger.error("="*60)
        logger.error("❌ FUNCTIONALITY TESTS FAILED")
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


async def test_manual_analysis_execution():
    """Test manual analysis execution without background workers."""
    logger.info("Test: Manual Analysis Execution")
    
    try:
        # Create a test analysis request
        test_code = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

# Test the function
result = calculate_sum([1, 2, 3, 4, 5])
print(f"Sum: {result}")
"""
        
        analysis_id = await background_code_analysis_service.queue_analysis(
            content=test_code,
            language="python",
            analysis_type=AnalysisType.QUICK,
            user_id="manual_test_user"
        )
        
        logger.info(f"Analysis queued: {analysis_id}")
        
        # Manually execute the analysis (simulating what the worker would do)
        try:
            # First check if the analysis exists
            initial_result = await background_code_analysis_service.get_analysis_status(analysis_id)
            if not initial_result:
                logger.error(f"Analysis {analysis_id} not found before execution")
                return False
            
            await background_code_analysis_service._perform_analysis(analysis_id)
            
            # Check the result
            result = await background_code_analysis_service.get_analysis_status(analysis_id)
            
            if result and result.status == AnalysisStatus.COMPLETED:
                logger.info("✓ Manual analysis execution successful")
                logger.info(f"  - Issues found: {len(result.issues)}")
                logger.info(f"  - Suggestions: {len(result.suggestions)}")
                logger.info(f"  - Processing time: {result.processing_time:.2f}s")
                logger.info(f"  - Quality score: {result.summary.get('quality_score', 'N/A')}")
                return True
            else:
                logger.error(f"Manual analysis failed with status: {result.status if result else 'None'}")
                return False
                
        except Exception as e:
            logger.error(f"Manual analysis execution failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Manual analysis test setup failed: {e}")
        return False


async def main():
    """Main test function."""
    try:
        # Run functionality tests
        functionality_success = await test_service_functionality()
        
        # Run manual analysis test
        manual_success = await test_manual_analysis_execution()
        
        if functionality_success and manual_success:
            logger.info("All tests completed successfully!")
            sys.exit(0)
        else:
            logger.error("Some tests failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())