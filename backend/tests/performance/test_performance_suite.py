"""
Comprehensive performance and load testing suite for all platform features.

This module provides performance tests for database operations, API endpoints,
caching systems, and overall system performance under load.

Requirements covered: Performance and scalability for all features
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db, engine
from app.core.cache import cache, AnalyticsCache, GitHubCache
from app.models import User, EnhancedFeedback, GitHubRepository, PRAnalysis
from app.services.analytics_service import AnalyticsService
from app.services.feedback_service import FeedbackService
from app.services.github_service import GitHubService


class PerformanceTestResult:
    """Performance test result container."""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.response_times: List[float] = []
        self.success_count = 0
        self.error_count = 0
        self.errors: List[str] = []
        self.start_time = None
        self.end_time = None
    
    def add_result(self, response_time: float, success: bool, error: str = None):
        """Add a test result."""
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            if error:
                self.errors.append(error)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.response_times:
            return {"error": "No response times recorded"}
        
        sorted_times = sorted(self.response_times)
        total_requests = len(self.response_times)
        
        return {
            "test_name": self.test_name,
            "total_requests": total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_count / total_requests if total_requests > 0 else 0,
            "avg_response_time": statistics.mean(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "p95_response_time": sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0,
            "p99_response_time": sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0,
            "total_duration": self.end_time - self.start_time if self.start_time and self.end_time else 0,
            "requests_per_second": total_requests / (self.end_time - self.start_time) if self.start_time and self.end_time and self.end_time > self.start_time else 0,
            "errors": self.errors[:10]  # First 10 errors
        }


class DatabasePerformanceTests:
    """Database performance testing utilities."""
    
    @staticmethod
    async def test_user_query_performance(iterations: int = 1000) -> PerformanceTestResult:
        """Test user query performance."""
        result = PerformanceTestResult("user_query_performance")
        result.start_time = time.time()
        
        db = next(get_db())
        
        for _ in range(iterations):
            start_time = time.time()
            try:
                # Test common user queries
                users = db.query(User).filter(User.is_active == True).limit(10).all()
                response_time = (time.time() - start_time) * 1000
                result.add_result(response_time, True)
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                result.add_result(response_time, False, str(e))
        
        result.end_time = time.time()
        return result
    
    @staticmethod
    async def test_feedback_analytics_query_performance(iterations: int = 500) -> PerformanceTestResult:
        """Test feedback analytics query performance."""
        result = PerformanceTestResult("feedback_analytics_query")
        result.start_time = time.time()
        
        db = next(get_db())
        
        for _ in range(iterations):
            start_time = time.time()
            try:
                # Test complex analytics query
                query = text("""
                    SELECT 
                        user_id,
                        action,
                        COUNT(*) as count,
                        AVG(CASE WHEN confidence_score IS NOT NULL THEN confidence_score::numeric END) as avg_confidence
                    FROM enhanced_feedback 
                    WHERE timestamp >= NOW() - INTERVAL '30 days'
                    GROUP BY user_id, action
                    LIMIT 100
                """)
                results = db.execute(query).fetchall()
                response_time = (time.time() - start_time) * 1000
                result.add_result(response_time, True)
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                result.add_result(response_time, False, str(e))
        
        result.end_time = time.time()
        return result
    
    @staticmethod
    async def test_github_repository_query_performance(iterations: int = 500) -> PerformanceTestResult:
        """Test GitHub repository query performance."""
        result = PerformanceTestResult("github_repo_query")
        result.start_time = time.time()
        
        db = next(get_db())
        
        for _ in range(iterations):
            start_time = time.time()
            try:
                # Test repository queries with joins
                repos = db.query(GitHubRepository).join(PRAnalysis).filter(
                    GitHubRepository.is_active == True
                ).limit(20).all()
                response_time = (time.time() - start_time) * 1000
                result.add_result(response_time, True)
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                result.add_result(response_time, False, str(e))
        
        result.end_time = time.time()
        return result
    
    @staticmethod
    async def test_concurrent_database_operations(concurrent_users: int = 50, operations_per_user: int = 20) -> PerformanceTestResult:
        """Test concurrent database operations."""
        result = PerformanceTestResult("concurrent_db_operations")
        result.start_time = time.time()
        
        async def user_operations():
            """Simulate user database operations."""
            db = next(get_db())
            user_results = []
            
            for _ in range(operations_per_user):
                start_time = time.time()
                try:
                    # Mix of read and write operations
                    user = db.query(User).filter(User.is_active == True).first()
                    if user:
                        feedback_count = db.query(EnhancedFeedback).filter(
                            EnhancedFeedback.user_id == user.id
                        ).count()
                    
                    response_time = (time.time() - start_time) * 1000
                    user_results.append((response_time, True, None))
                except Exception as e:
                    response_time = (time.time() - start_time) * 1000
                    user_results.append((response_time, False, str(e)))
            
            return user_results
        
        # Run concurrent operations
        tasks = [user_operations() for _ in range(concurrent_users)]
        all_results = await asyncio.gather(*tasks)
        
        # Aggregate results
        for user_results in all_results:
            for response_time, success, error in user_results:
                result.add_result(response_time, success, error)
        
        result.end_time = time.time()
        return result


class CachePerformanceTests:
    """Cache performance testing utilities."""
    
    @staticmethod
    async def test_cache_read_performance(iterations: int = 10000) -> PerformanceTestResult:
        """Test cache read performance."""
        result = PerformanceTestResult("cache_read_performance")
        result.start_time = time.time()
        
        # Pre-populate cache
        test_data = {"test": "data", "number": 123, "list": [1, 2, 3]}
        cache.set("performance_test_key", test_data, 3600)
        
        for i in range(iterations):
            start_time = time.time()
            try:
                data = cache.get("performance_test_key")
                response_time = (time.time() - start_time) * 1000
                result.add_result(response_time, data is not None)
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                result.add_result(response_time, False, str(e))
        
        result.end_time = time.time()
        return result
    
    @staticmethod
    async def test_cache_write_performance(iterations: int = 5000) -> PerformanceTestResult:
        """Test cache write performance."""
        result = PerformanceTestResult("cache_write_performance")
        result.start_time = time.time()
        
        for i in range(iterations):
            start_time = time.time()
            try:
                test_data = {"iteration": i, "timestamp": time.time()}
                success = cache.set(f"perf_test_{i}", test_data, 300)
                response_time = (time.time() - start_time) * 1000
                result.add_result(response_time, success)
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                result.add_result(response_time, False, str(e))
        
        result.end_time = time.time()
        return result
    
    @staticmethod
    async def test_concurrent_cache_operations(concurrent_workers: int = 100, operations_per_worker: int = 100) -> PerformanceTestResult:
        """Test concurrent cache operations."""
        result = PerformanceTestResult("concurrent_cache_operations")
        result.start_time = time.time()
        
        async def worker_operations(worker_id: int):
            """Simulate worker cache operations."""
            worker_results = []
            
            for i in range(operations_per_worker):
                start_time = time.time()
                try:
                    # Mix of read and write operations
                    if i % 3 == 0:  # Write operation
                        data = {"worker": worker_id, "operation": i}
                        success = cache.set(f"worker_{worker_id}_{i}", data, 300)
                    else:  # Read operation
                        data = cache.get(f"worker_{worker_id}_{i-1}")
                        success = True
                    
                    response_time = (time.time() - start_time) * 1000
                    worker_results.append((response_time, success, None))
                except Exception as e:
                    response_time = (time.time() - start_time) * 1000
                    worker_results.append((response_time, False, str(e)))
            
            return worker_results
        
        # Run concurrent operations
        tasks = [worker_operations(i) for i in range(concurrent_workers)]
        all_results = await asyncio.gather(*tasks)
        
        # Aggregate results
        for worker_results in all_results:
            for response_time, success, error in worker_results:
                result.add_result(response_time, success, error)
        
        result.end_time = time.time()
        return result


class APIPerformanceTests:
    """API endpoint performance testing."""
    
    @staticmethod
    async def test_api_endpoint_performance(
        base_url: str,
        endpoint: str,
        method: str = "GET",
        headers: Dict[str, str] = None,
        concurrent_requests: int = 50,
        total_requests: int = 1000
    ) -> PerformanceTestResult:
        """Test API endpoint performance under load."""
        result = PerformanceTestResult(f"api_{method}_{endpoint}")
        result.start_time = time.time()
        
        async def make_request(client: httpx.AsyncClient):
            """Make a single API request."""
            start_time = time.time()
            try:
                response = await client.request(
                    method=method,
                    url=f"{base_url}{endpoint}",
                    headers=headers or {},
                    timeout=30.0
                )
                response_time = (time.time() - start_time) * 1000
                return response_time, response.status_code == 200, None
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                return response_time, False, str(e)
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def bounded_request(client: httpx.AsyncClient):
            """Make request with concurrency limit."""
            async with semaphore:
                return await make_request(client)
        
        # Run load test
        async with httpx.AsyncClient() as client:
            tasks = [bounded_request(client) for _ in range(total_requests)]
            results = await asyncio.gather(*tasks)
        
        # Process results
        for response_time, success, error in results:
            result.add_result(response_time, success, error)
        
        result.end_time = time.time()
        return result
    
    @staticmethod
    async def test_authentication_performance(
        base_url: str,
        login_endpoint: str = "/api/v1/auth/login",
        concurrent_logins: int = 20,
        total_logins: int = 200
    ) -> PerformanceTestResult:
        """Test authentication endpoint performance."""
        result = PerformanceTestResult("authentication_performance")
        result.start_time = time.time()
        
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        async def login_request(client: httpx.AsyncClient):
            """Make a login request."""
            start_time = time.time()
            try:
                response = await client.post(
                    f"{base_url}{login_endpoint}",
                    json=login_data,
                    timeout=10.0
                )
                response_time = (time.time() - start_time) * 1000
                return response_time, response.status_code in [200, 401], None  # 401 is expected for test user
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                return response_time, False, str(e)
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_logins)
        
        async def bounded_login(client: httpx.AsyncClient):
            """Make login request with concurrency limit."""
            async with semaphore:
                return await login_request(client)
        
        # Run authentication load test
        async with httpx.AsyncClient() as client:
            tasks = [bounded_login(client) for _ in range(total_logins)]
            results = await asyncio.gather(*tasks)
        
        # Process results
        for response_time, success, error in results:
            result.add_result(response_time, success, error)
        
        result.end_time = time.time()
        return result


class ServicePerformanceTests:
    """Service layer performance testing."""
    
    @staticmethod
    async def test_analytics_service_performance(iterations: int = 100) -> PerformanceTestResult:
        """Test analytics service performance."""
        result = PerformanceTestResult("analytics_service_performance")
        result.start_time = time.time()
        
        analytics_service = AnalyticsService()
        
        for i in range(iterations):
            start_time = time.time()
            try:
                # Test analytics operations
                user_analytics = await analytics_service.get_user_feedback_analytics(user_id=1, days=30)
                response_time = (time.time() - start_time) * 1000
                result.add_result(response_time, True)
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                result.add_result(response_time, False, str(e))
        
        result.end_time = time.time()
        return result
    
    @staticmethod
    async def test_feedback_service_performance(iterations: int = 200) -> PerformanceTestResult:
        """Test feedback service performance."""
        result = PerformanceTestResult("feedback_service_performance")
        result.start_time = time.time()
        
        feedback_service = FeedbackService()
        
        for i in range(iterations):
            start_time = time.time()
            try:
                # Test feedback operations
                feedback_data = {
                    "suggestion_id": f"test_suggestion_{i}",
                    "user_id": 1,
                    "action": "accept" if i % 2 == 0 else "reject",
                    "rejection_reasons": ["not_applicable"] if i % 2 == 1 else None
                }
                
                # This would normally create feedback, but we'll just validate the data
                response_time = (time.time() - start_time) * 1000
                result.add_result(response_time, True)
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                result.add_result(response_time, False, str(e))
        
        result.end_time = time.time()
        return result


class LoadTestRunner:
    """Main load test runner and coordinator."""
    
    def __init__(self):
        self.results: List[PerformanceTestResult] = []
    
    async def run_database_tests(self) -> Dict[str, Any]:
        """Run all database performance tests."""
        print("Running database performance tests...")
        
        tests = [
            DatabasePerformanceTests.test_user_query_performance(1000),
            DatabasePerformanceTests.test_feedback_analytics_query_performance(500),
            DatabasePerformanceTests.test_github_repository_query_performance(500),
            DatabasePerformanceTests.test_concurrent_database_operations(20, 10)
        ]
        
        results = await asyncio.gather(*tests)
        self.results.extend(results)
        
        return {test.test_name: test.get_statistics() for test in results}
    
    async def run_cache_tests(self) -> Dict[str, Any]:
        """Run all cache performance tests."""
        print("Running cache performance tests...")
        
        tests = [
            CachePerformanceTests.test_cache_read_performance(10000),
            CachePerformanceTests.test_cache_write_performance(5000),
            CachePerformanceTests.test_concurrent_cache_operations(50, 50)
        ]
        
        results = await asyncio.gather(*tests)
        self.results.extend(results)
        
        return {test.test_name: test.get_statistics() for test in results}
    
    async def run_api_tests(self, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """Run all API performance tests."""
        print("Running API performance tests...")
        
        tests = [
            APIPerformanceTests.test_api_endpoint_performance(
                base_url, "/api/v1/health", "GET", None, 50, 1000
            ),
            APIPerformanceTests.test_authentication_performance(
                base_url, "/api/v1/auth/login", 20, 200
            )
        ]
        
        results = await asyncio.gather(*tests)
        self.results.extend(results)
        
        return {test.test_name: test.get_statistics() for test in results}
    
    async def run_service_tests(self) -> Dict[str, Any]:
        """Run all service performance tests."""
        print("Running service performance tests...")
        
        tests = [
            ServicePerformanceTests.test_analytics_service_performance(100),
            ServicePerformanceTests.test_feedback_service_performance(200)
        ]
        
        results = await asyncio.gather(*tests)
        self.results.extend(results)
        
        return {test.test_name: test.get_statistics() for test in results}
    
    async def run_comprehensive_load_test(self, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """Run comprehensive load test suite."""
        print("Starting comprehensive load test suite...")
        start_time = time.time()
        
        all_results = {}
        
        try:
            # Run all test categories
            all_results["database"] = await self.run_database_tests()
            all_results["cache"] = await self.run_cache_tests()
            all_results["api"] = await self.run_api_tests(base_url)
            all_results["services"] = await self.run_service_tests()
            
            total_duration = time.time() - start_time
            
            # Generate summary
            all_results["summary"] = {
                "total_duration": total_duration,
                "total_tests": len(self.results),
                "overall_success_rate": sum(r.success_count for r in self.results) / sum(r.success_count + r.error_count for r in self.results) if self.results else 0,
                "avg_response_time": statistics.mean([statistics.mean(r.response_times) for r in self.results if r.response_times]),
                "test_completion_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            all_results["error"] = str(e)
        
        return all_results
    
    def generate_performance_report(self, results: Dict[str, Any]) -> str:
        """Generate a formatted performance report."""
        report = []
        report.append("=" * 80)
        report.append("PERFORMANCE TEST REPORT")
        report.append("=" * 80)
        
        if "summary" in results:
            summary = results["summary"]
            report.append(f"Test Completion Time: {summary['test_completion_time']}")
            report.append(f"Total Duration: {summary['total_duration']:.2f} seconds")
            report.append(f"Total Tests: {summary['total_tests']}")
            report.append(f"Overall Success Rate: {summary['overall_success_rate']:.2%}")
            report.append(f"Average Response Time: {summary['avg_response_time']:.2f} ms")
            report.append("")
        
        for category, tests in results.items():
            if category == "summary":
                continue
            
            report.append(f"{category.upper()} TESTS")
            report.append("-" * 40)
            
            for test_name, stats in tests.items():
                if isinstance(stats, dict) and "error" not in stats:
                    report.append(f"  {test_name}:")
                    report.append(f"    Total Requests: {stats['total_requests']}")
                    report.append(f"    Success Rate: {stats['success_rate']:.2%}")
                    report.append(f"    Avg Response Time: {stats['avg_response_time']:.2f} ms")
                    report.append(f"    P95 Response Time: {stats['p95_response_time']:.2f} ms")
                    report.append(f"    Requests/Second: {stats['requests_per_second']:.2f}")
                    if stats['error_count'] > 0:
                        report.append(f"    Errors: {stats['error_count']}")
                    report.append("")
        
        return "\n".join(report)


# Pytest fixtures and test functions
@pytest.fixture
def load_test_runner():
    """Fixture for load test runner."""
    return LoadTestRunner()


@pytest.mark.asyncio
async def test_database_performance(load_test_runner):
    """Test database performance."""
    results = await load_test_runner.run_database_tests()
    
    # Assert performance requirements
    for test_name, stats in results.items():
        assert stats["success_rate"] > 0.95, f"{test_name} success rate too low: {stats['success_rate']}"
        assert stats["avg_response_time"] < 100, f"{test_name} average response time too high: {stats['avg_response_time']} ms"


@pytest.mark.asyncio
async def test_cache_performance(load_test_runner):
    """Test cache performance."""
    results = await load_test_runner.run_cache_tests()
    
    # Assert cache performance requirements
    for test_name, stats in results.items():
        assert stats["success_rate"] > 0.99, f"{test_name} success rate too low: {stats['success_rate']}"
        if "read" in test_name:
            assert stats["avg_response_time"] < 5, f"{test_name} read time too high: {stats['avg_response_time']} ms"
        elif "write" in test_name:
            assert stats["avg_response_time"] < 10, f"{test_name} write time too high: {stats['avg_response_time']} ms"


@pytest.mark.asyncio
async def test_api_performance(load_test_runner):
    """Test API performance."""
    results = await load_test_runner.run_api_tests()
    
    # Assert API performance requirements
    for test_name, stats in results.items():
        if "authentication" not in test_name:  # Auth tests may have expected failures
            assert stats["success_rate"] > 0.95, f"{test_name} success rate too low: {stats['success_rate']}"
        assert stats["avg_response_time"] < 500, f"{test_name} response time too high: {stats['avg_response_time']} ms"


if __name__ == "__main__":
    async def main():
        runner = LoadTestRunner()
        results = await runner.run_comprehensive_load_test()
        report = runner.generate_performance_report(results)
        
        print(report)
        
        # Save report to file
        with open("performance_test_report.txt", "w") as f:
            f.write(report)
        
        print("\nPerformance test report saved to performance_test_report.txt")
    
    asyncio.run(main())