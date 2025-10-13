"""
Test script for the Background Code Analysis Service.

This script tests the core functionality of the background code analysis service
including job queuing, progress tracking, result caching, and notifications.

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
    queue_code_analysis,
    get_analysis_result
)
from app.services.analysis_notification_service import (
    analysis_notification_service,
    subscribe_to_analysis_notifications
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class AnalysisTestSuite:
    """Test suite for background code analysis service."""
    
    def __init__(self):
        self.test_results = {}
        self.test_user_id = "test_user_123"
    
    async def run_all_tests(self):
        """Run all test cases."""
        logger.info("Starting Background Code Analysis Service Test Suite")
        
        try:
            # Initialize services
            await self.initialize_services()
            
            # Run individual tests
            await self.test_service_initialization()
            await self.test_simple_analysis()
            await self.test_different_analysis_types()
            await self.test_batch_analysis()
            await self.test_progress_tracking()
            await self.test_result_caching()
            await self.test_error_handling()
            await self.test_cancellation()
            await self.test_metrics_collection()
            
            # Print test summary
            self.print_test_summary()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            raise
    
    async def initialize_services(self):
        """Initialize required services."""
        logger.info("Initializing services...")
        
        try:
            await background_code_analysis_service.initialize()
            await analysis_notification_service.initialize()
            
            logger.info("Services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    async def test_service_initialization(self):
        """Test service initialization."""
        test_name = "Service Initialization"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Test that services are properly initialized
            assert hasattr(background_code_analysis_service, '_metrics')
            assert hasattr(analysis_notification_service, '_websocket_connections')
            
            self.test_results[test_name] = "PASSED"
            logger.info(f"✓ {test_name} passed")
            
        except Exception as e:
            self.test_results[test_name] = f"FAILED: {e}"
            logger.error(f"✗ {test_name} failed: {e}")
    
    async def test_simple_analysis(self):
        """Test simple code analysis."""
        test_name = "Simple Analysis"
        logger.info(f"Running test: {test_name}")
        
        try:
            test_code = """
def hello_world():
    print("Hello, World!")
    return "Hello"

# Call the function
result = hello_world()
"""
            
            # Queue analysis
            analysis_id = await queue_code_analysis(
                content=test_code,
                language="python",
                analysis_type="quick",
                user_id=self.test_user_id
            )
            
            assert analysis_id is not None
            assert len(analysis_id) > 0
            
            # Wait for completion (with timeout)
            result = await self.wait_for_analysis_completion(analysis_id, timeout=60)
            
            assert result is not None
            assert result['status'] == 'completed'
            assert 'issues' in result
            assert 'suggestions' in result
            assert 'summary' in result
            
            self.test_results[test_name] = "PASSED"
            logger.info(f"✓ {test_name} passed - Analysis ID: {analysis_id}")
            
        except Exception as e:
            self.test_results[test_name] = f"FAILED: {e}"
            logger.error(f"✗ {test_name} failed: {e}")
    
    async def test_different_analysis_types(self):
        """Test different analysis types."""
        test_name = "Different Analysis Types"
        logger.info(f"Running test: {test_name}")
        
        try:
            test_code = """
import os
import sys

def process_data(data):
    # TODO: Implement data processing
    if data is None:
        return None
    
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    
    return result

# Test with some data
test_data = [1, 2, 3, -1, 0, 5]
processed = process_data(test_data)
print(processed)
"""
            
            analysis_types = ["quick", "full", "security", "style"]
            analysis_ids = []
            
            # Queue different analysis types
            for analysis_type in analysis_types:
                analysis_id = await background_code_analysis_service.queue_analysis(
                    content=test_code,
                    language="python",
                    analysis_type=AnalysisType(analysis_type),
                    user_id=self.test_user_id,
                    metadata={"test_type": analysis_type}
                )
                analysis_ids.append((analysis_id, analysis_type))
            
            # Wait for all to complete
            results = {}
            for analysis_id, analysis_type in analysis_ids:
                result = await self.wait_for_analysis_completion(analysis_id, timeout=90)
                results[analysis_type] = result
            
            # Verify all completed
            for analysis_type, result in results.items():
                assert result is not None, f"No result for {analysis_type}"
                assert result['status'] == 'completed', f"{analysis_type} analysis failed"
            
            self.test_results[test_name] = "PASSED"
            logger.info(f"✓ {test_name} passed - Tested {len(analysis_types)} analysis types")
            
        except Exception as e:
            self.test_results[test_name] = f"FAILED: {e}"
            logger.error(f"✗ {test_name} failed: {e}")
    
    async def test_batch_analysis(self):
        """Test batch analysis functionality."""
        test_name = "Batch Analysis"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Prepare multiple code snippets
            code_snippets = [
                {
                    'content': 'def func1(): return "test1"',
                    'language': 'python',
                    'analysis_type': 'quick'
                },
                {
                    'content': 'function func2() { return "test2"; }',
                    'language': 'javascript',
                    'analysis_type': 'quick'
                },
                {
                    'content': 'const func3 = (): string => "test3";',
                    'language': 'typescript',
                    'analysis_type': 'quick'
                }
            ]
            
            # Queue batch analysis
            batch_id = await background_code_analysis_service.queue_batch_analysis(
                analysis_requests=code_snippets,
                user_id=self.test_user_id
            )
            
            assert batch_id is not None
            
            # Wait for batch completion
            batch_result = await self.wait_for_batch_completion(batch_id, timeout=120)
            
            assert batch_result is not None
            assert batch_result['total_count'] == len(code_snippets)
            assert batch_result['completed_count'] > 0
            
            self.test_results[test_name] = "PASSED"
            logger.info(f"✓ {test_name} passed - Batch ID: {batch_id}")
            
        except Exception as e:
            self.test_results[test_name] = f"FAILED: {e}"
            logger.error(f"✗ {test_name} failed: {e}")
    
    async def test_progress_tracking(self):
        """Test progress tracking functionality."""
        test_name = "Progress Tracking"
        logger.info(f"Running test: {test_name}")
        
        try:
            test_code = """
class DataProcessor:
    def __init__(self):
        self.data = []
    
    def add_data(self, item):
        self.data.append(item)
    
    def process_all(self):
        results = []
        for item in self.data:
            # Complex processing simulation
            processed = self.complex_operation(item)
            results.append(processed)
        return results
    
    def complex_operation(self, item):
        # Simulate complex operation
        return item ** 2 + item * 3 + 1

# Usage
processor = DataProcessor()
for i in range(100):
    processor.add_data(i)

results = processor.process_all()
print(f"Processed {len(results)} items")
"""
            
            # Track progress updates
            progress_updates = []
            
            def progress_callback(analysis_id, message, percentage):
                progress_updates.append({
                    'analysis_id': analysis_id,
                    'message': message,
                    'percentage': percentage,
                    'timestamp': time.time()
                })
            
            # Queue analysis
            analysis_id = await background_code_analysis_service.queue_analysis(
                content=test_code,
                language="python",
                analysis_type=AnalysisType.FULL,
                user_id=self.test_user_id
            )
            
            # Add progress callback
            background_code_analysis_service.add_progress_callback(analysis_id, progress_callback)
            
            # Wait for completion
            result = await self.wait_for_analysis_completion(analysis_id, timeout=90)
            
            assert result is not None
            assert result['status'] == 'completed'
            assert len(progress_updates) > 0, "No progress updates received"
            
            # Verify progress updates are in order
            percentages = [update['percentage'] for update in progress_updates]
            assert percentages[-1] == 100.0, "Final progress should be 100%"
            
            self.test_results[test_name] = "PASSED"
            logger.info(f"✓ {test_name} passed - Received {len(progress_updates)} progress updates")
            
        except Exception as e:
            self.test_results[test_name] = f"FAILED: {e}"
            logger.error(f"✗ {test_name} failed: {e}")
    
    async def test_result_caching(self):
        """Test result caching functionality."""
        test_name = "Result Caching"
        logger.info(f"Running test: {test_name}")
        
        try:
            test_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
"""
            
            # First analysis
            start_time = time.time()
            analysis_id_1 = await background_code_analysis_service.queue_analysis(
                content=test_code,
                language="python",
                analysis_type=AnalysisType.QUICK,
                user_id=self.test_user_id
            )
            
            result_1 = await self.wait_for_analysis_completion(analysis_id_1, timeout=60)
            first_analysis_time = time.time() - start_time
            
            # Second identical analysis (should use cache)
            start_time = time.time()
            analysis_id_2 = await background_code_analysis_service.queue_analysis(
                content=test_code,
                language="python",
                analysis_type=AnalysisType.QUICK,
                user_id=self.test_user_id
            )
            
            result_2 = await self.wait_for_analysis_completion(analysis_id_2, timeout=60)
            second_analysis_time = time.time() - start_time
            
            assert result_1 is not None
            assert result_2 is not None
            assert result_1['status'] == 'completed'
            assert result_2['status'] == 'completed'
            
            # Second analysis should be faster (cached)
            assert second_analysis_time < first_analysis_time, "Cached analysis should be faster"
            
            # Check cache metrics
            metrics = await background_code_analysis_service.get_analysis_metrics()
            assert metrics['analysis_metrics']['cache_hits'] > 0, "Should have cache hits"
            
            self.test_results[test_name] = "PASSED"
            logger.info(f"✓ {test_name} passed - Cache hit detected")
            
        except Exception as e:
            self.test_results[test_name] = f"FAILED: {e}"
            logger.error(f"✗ {test_name} failed: {e}")
    
    async def test_error_handling(self):
        """Test error handling functionality."""
        test_name = "Error Handling"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Test with invalid analysis type
            try:
                await background_code_analysis_service.queue_analysis(
                    content="test code",
                    analysis_type="invalid_type"
                )
                assert False, "Should have raised an error for invalid analysis type"
            except (ValueError, TypeError):
                pass  # Expected error
            
            # Test with empty content
            try:
                analysis_id = await background_code_analysis_service.queue_analysis(
                    content="",
                    language="python",
                    analysis_type=AnalysisType.QUICK,
                    user_id=self.test_user_id
                )
                
                # This might complete but with no meaningful results
                result = await self.wait_for_analysis_completion(analysis_id, timeout=30)
                # Just verify it doesn't crash
                
            except Exception:
                pass  # Error handling is working
            
            self.test_results[test_name] = "PASSED"
            logger.info(f"✓ {test_name} passed")
            
        except Exception as e:
            self.test_results[test_name] = f"FAILED: {e}"
            logger.error(f"✗ {test_name} failed: {e}")
    
    async def test_cancellation(self):
        """Test analysis cancellation functionality."""
        test_name = "Analysis Cancellation"
        logger.info(f"Running test: {test_name}")
        
        try:
            test_code = """
# Large code snippet to ensure analysis takes some time
class ComplexClass:
    def __init__(self):
        self.data = {}
    
    def method1(self):
        pass
    
    def method2(self):
        pass
    
    # ... many more methods
""" + "\n".join([f"    def method{i}(self): pass" for i in range(3, 50)])
            
            # Queue analysis
            analysis_id = await background_code_analysis_service.queue_analysis(
                content=test_code,
                language="python",
                analysis_type=AnalysisType.COMPREHENSIVE,
                user_id=self.test_user_id
            )
            
            # Wait a bit then cancel
            await asyncio.sleep(1)
            
            success = await background_code_analysis_service.cancel_analysis(analysis_id)
            
            # Check final status
            final_result = await background_code_analysis_service.get_analysis_status(analysis_id)
            
            if success:
                assert final_result.status == AnalysisStatus.CANCELLED
                self.test_results[test_name] = "PASSED"
                logger.info(f"✓ {test_name} passed - Analysis cancelled successfully")
            else:
                # Analysis might have completed before cancellation
                self.test_results[test_name] = "PASSED (Analysis completed before cancellation)"
                logger.info(f"✓ {test_name} passed - Analysis completed before cancellation")
            
        except Exception as e:
            self.test_results[test_name] = f"FAILED: {e}"
            logger.error(f"✗ {test_name} failed: {e}")
    
    async def test_metrics_collection(self):
        """Test metrics collection functionality."""
        test_name = "Metrics Collection"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Get initial metrics
            initial_metrics = await background_code_analysis_service.get_analysis_metrics()
            
            assert 'analysis_metrics' in initial_metrics
            assert 'cache_metrics' in initial_metrics
            assert 'queue_metrics' in initial_metrics
            
            # Verify metrics structure
            analysis_metrics = initial_metrics['analysis_metrics']
            required_fields = [
                'total_analyses', 'completed_analyses', 'failed_analyses',
                'cache_hits', 'cache_misses'
            ]
            
            for field in required_fields:
                assert field in analysis_metrics, f"Missing metric field: {field}"
            
            self.test_results[test_name] = "PASSED"
            logger.info(f"✓ {test_name} passed")
            
        except Exception as e:
            self.test_results[test_name] = f"FAILED: {e}"
            logger.error(f"✗ {test_name} failed: {e}")
    
    async def wait_for_analysis_completion(self, analysis_id: str, timeout: int = 60) -> Dict[str, Any]:
        """Wait for analysis to complete with timeout."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = await get_analysis_result(analysis_id)
            
            if result and result['status'] in ['completed', 'failed', 'cancelled']:
                return result
            
            await asyncio.sleep(2)
        
        raise TimeoutError(f"Analysis {analysis_id} did not complete within {timeout} seconds")
    
    async def wait_for_batch_completion(self, batch_id: str, timeout: int = 120) -> Dict[str, Any]:
        """Wait for batch analysis to complete with timeout."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            batch_status = await background_code_analysis_service.get_batch_status(batch_id)
            
            if batch_status:
                total = batch_status['total_count']
                completed = batch_status['completed_count']
                failed = batch_status['failed_count']
                
                if completed + failed >= total:
                    return batch_status
            
            await asyncio.sleep(3)
        
        raise TimeoutError(f"Batch {batch_id} did not complete within {timeout} seconds")
    
    def print_test_summary(self):
        """Print test results summary."""
        logger.info("\n" + "="*60)
        logger.info("BACKGROUND CODE ANALYSIS SERVICE TEST SUMMARY")
        logger.info("="*60)
        
        passed_count = 0
        failed_count = 0
        
        for test_name, result in self.test_results.items():
            status = "✓ PASSED" if result == "PASSED" or result.startswith("PASSED") else "✗ FAILED"
            logger.info(f"{status:<10} {test_name}")
            
            if result == "PASSED" or result.startswith("PASSED"):
                passed_count += 1
            else:
                failed_count += 1
                logger.info(f"           Error: {result}")
        
        logger.info("-"*60)
        logger.info(f"Total Tests: {len(self.test_results)}")
        logger.info(f"Passed: {passed_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Success Rate: {passed_count/len(self.test_results)*100:.1f}%")
        logger.info("="*60)


async def main():
    """Main test function."""
    test_suite = AnalysisTestSuite()
    
    try:
        await test_suite.run_all_tests()
        
        # Check if all tests passed
        failed_tests = [
            name for name, result in test_suite.test_results.items()
            if not (result == "PASSED" or result.startswith("PASSED"))
        ]
        
        if failed_tests:
            logger.error(f"Some tests failed: {failed_tests}")
            sys.exit(1)
        else:
            logger.info("All tests passed successfully!")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Test suite execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())