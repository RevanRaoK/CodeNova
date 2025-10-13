#!/usr/bin/env python3
"""
Test script for the enhanced logging system.

This script demonstrates and tests various features of the enhanced logging system
including structured logging, error tracking, performance monitoring, and alerting.
"""

import asyncio
import time
import random
from datetime import datetime
from typing import Dict, Any

# Import the enhanced logging system
from app.core.enhanced_logging import (
    ErrorSeverity,
    IntegrationComponent,
    ErrorContext,
    log_integration_operation,
    log_integration_context,
    create_error_context,
    error_handler,
    performance_monitor,
    health_check_logger,
    log_analyzer,
    setup_enhanced_logging,
    cleanup_old_logs
)


class TestIntegrationOperations:
    """Test class to demonstrate integration logging."""
    
    @log_integration_operation(IntegrationComponent.FILE_STORAGE, "upload_file")
    async def test_file_upload(self, filename: str, size_mb: float):
        """Simulate file upload operation."""
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.1, 2.0))
        
        # Simulate occasional failures
        if random.random() < 0.1:  # 10% failure rate
            raise Exception(f"Failed to upload {filename}: Storage quota exceeded")
        
        return {"filename": filename, "size_mb": size_mb, "upload_id": f"upload_{random.randint(1000, 9999)}"}
    
    @log_integration_operation(IntegrationComponent.GITHUB_API, "fetch_repositories")
    async def test_github_fetch(self, user_id: int):
        """Simulate GitHub API operation."""
        await asyncio.sleep(random.uniform(0.2, 1.5))
        
        # Simulate rate limiting errors
        if random.random() < 0.05:  # 5% rate limit
            raise Exception("GitHub API rate limit exceeded")
        
        # Simulate authentication errors
        if random.random() < 0.03:  # 3% auth errors
            raise Exception("GitHub authentication failed")
        
        return {"repositories": random.randint(1, 50), "user_id": user_id}
    
    @log_integration_operation(IntegrationComponent.JOB_QUEUE, "process_background_job")
    def test_job_processing(self, job_id: str, job_type: str):
        """Simulate background job processing."""
        time.sleep(random.uniform(0.1, 3.0))
        
        # Simulate job failures
        if random.random() < 0.08:  # 8% failure rate
            raise Exception(f"Job {job_id} failed: Invalid job configuration")
        
        return {"job_id": job_id, "job_type": job_type, "status": "completed"}


async def test_basic_logging():
    """Test basic logging functionality."""
    print("Testing basic logging functionality...")
    
    # Get loggers for different components
    file_logger = error_handler.get_logger(IntegrationComponent.FILE_STORAGE)
    github_logger = error_handler.get_logger(IntegrationComponent.GITHUB_API)
    
    # Test basic operation logging
    file_logger.log_operation("test_operation", level="info", test_param="test_value")
    github_logger.log_operation("api_call", level="debug", endpoint="/user/repos")
    
    # Test error logging
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        error_context = create_error_context(
            IntegrationComponent.FILE_STORAGE,
            "test_error_logging",
            e,
            ErrorSeverity.MEDIUM,
            user_id=123,
            test_metadata="error_test"
        )
        file_logger.log_error(error_context)
    
    print("✓ Basic logging tests completed")


async def test_integration_decorators():
    """Test integration operation decorators."""
    print("Testing integration decorators...")
    
    test_ops = TestIntegrationOperations()
    
    # Test multiple operations to generate logs and metrics
    tasks = []
    
    # File upload operations
    for i in range(10):
        tasks.append(test_ops.test_file_upload(f"file_{i}.txt", random.uniform(1.0, 100.0)))
    
    # GitHub operations
    for i in range(8):
        tasks.append(test_ops.test_github_fetch(random.randint(1, 1000)))
    
    # Job processing operations (sync)
    for i in range(5):
        try:
            test_ops.test_job_processing(f"job_{i}", "analysis")
        except Exception:
            pass  # Expected failures for testing
    
    # Execute async operations
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful_ops = sum(1 for r in results if not isinstance(r, Exception))
    failed_ops = len(results) - successful_ops
    
    print(f"✓ Integration decorator tests completed: {successful_ops} successful, {failed_ops} failed")


def test_context_manager():
    """Test logging context manager."""
    print("Testing logging context manager...")
    
    # Test successful context
    with log_integration_context(
        IntegrationComponent.USER_PROFILE,
        "update_profile",
        user_id=456,
        profile_fields=["name", "email"]
    ) as logger:
        time.sleep(0.1)  # Simulate work
        logger.log_operation("profile_validation", level="info", validation_result="passed")
    
    # Test context with exception
    try:
        with log_integration_context(
            IntegrationComponent.CONFIGURATION,
            "load_config",
            config_file="app.yaml"
        ) as logger:
            logger.log_operation("config_parsing", level="info", status="started")
            raise Exception("Configuration file not found")
    except Exception:
        pass  # Expected for testing
    
    print("✓ Context manager tests completed")


def test_performance_monitoring():
    """Test performance monitoring functionality."""
    print("Testing performance monitoring...")
    
    # Record some performance metrics
    for i in range(20):
        component = random.choice(list(IntegrationComponent))
        operation = f"test_operation_{random.randint(1, 5)}"
        duration = random.uniform(0.1, 5.0)
        success = random.random() > 0.1  # 90% success rate
        
        performance_monitor.record_operation(
            component,
            operation,
            duration,
            success,
            test_run=True,
            iteration=i
        )
    
    # Generate performance report
    report = performance_monitor.get_performance_report()
    
    print(f"✓ Performance monitoring tests completed")
    print(f"  - Monitored operations: {len(report.get('operations', {}))}")
    
    # Print sample metrics
    for component, operations in list(report.get('operations', {}).items())[:2]:
        for operation, metrics in list(operations.items())[:1]:
            print(f"  - {component}.{operation}: {metrics['total_calls']} calls, "
                  f"{metrics['success_rate_percent']:.1f}% success rate, "
                  f"{metrics['avg_duration']:.3f}s avg duration")


def test_health_check_logging():
    """Test health check logging."""
    print("Testing health check logging...")
    
    # Test various health check scenarios
    services = ["database", "redis", "github_api", "file_storage"]
    
    for service in services:
        # Simulate health checks with varying results
        status = "healthy" if random.random() > 0.2 else "unhealthy"
        response_time = random.uniform(0.01, 0.5)
        
        details = {
            "endpoint": f"http://{service}.internal:8080/health",
            "status_code": 200 if status == "healthy" else 503
        }
        
        health_check_logger.log_health_check(service, status, response_time, details)
    
    # Test dependency checks
    dependencies = ["postgresql", "redis", "github.com"]
    
    for dependency in dependencies:
        available = random.random() > 0.1  # 90% availability
        error_message = None if available else f"Connection timeout to {dependency}"
        
        health_check_logger.log_dependency_check(dependency, available, error_message)
    
    print("✓ Health check logging tests completed")


def test_log_analysis():
    """Test log analysis functionality."""
    print("Testing log analysis...")
    
    # Analyze error patterns (this will work with actual log files if they exist)
    try:
        error_patterns = log_analyzer.analyze_error_patterns(hours=1)
        print(f"✓ Error pattern analysis completed for {len(error_patterns)} components")
        
        # Show sample error patterns
        for component, patterns in list(error_patterns.items())[:2]:
            if patterns["total_errors"] > 0:
                print(f"  - {component}: {patterns['total_errors']} errors, "
                      f"{len(patterns['error_types'])} error types")
    
    except Exception as e:
        print(f"  - Error pattern analysis skipped: {e}")
    
    # Get performance insights
    try:
        insights = log_analyzer.get_performance_insights(hours=1)
        print(f"✓ Performance insights generated")
        print(f"  - Slow operations: {len(insights['slow_operations'])}")
        print(f"  - High error rate operations: {len(insights['high_error_rate_operations'])}")
    
    except Exception as e:
        print(f"  - Performance insights skipped: {e}")


async def run_comprehensive_test():
    """Run comprehensive test of the enhanced logging system."""
    print("=" * 60)
    print("Enhanced Logging System - Comprehensive Test")
    print("=" * 60)
    
    # Setup logging system
    setup_enhanced_logging()
    print("✓ Enhanced logging system initialized")
    
    # Run all tests
    await test_basic_logging()
    await test_integration_decorators()
    test_context_manager()
    test_performance_monitoring()
    test_health_check_logging()
    test_log_analysis()
    
    # Test log cleanup (won't delete anything in test)
    cleanup_old_logs()
    print("✓ Log cleanup test completed")
    
    print("\n" + "=" * 60)
    print("All enhanced logging tests completed successfully!")
    print("=" * 60)
    
    # Show final performance report
    print("\nFinal Performance Report:")
    report = performance_monitor.get_performance_report()
    
    total_operations = 0
    total_calls = 0
    
    for component, operations in report.get('operations', {}).items():
        for operation, metrics in operations.items():
            total_operations += 1
            total_calls += metrics['total_calls']
    
    print(f"Total monitored operations: {total_operations}")
    print(f"Total operation calls: {total_calls}")


if __name__ == "__main__":
    # Run the comprehensive test
    asyncio.run(run_comprehensive_test())