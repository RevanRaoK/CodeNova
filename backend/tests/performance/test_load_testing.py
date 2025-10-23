"""
Load Testing for CodeNova Platform

Tests system performance under load:
- Concurrent file uploads
- Analysis queue processing
- WebSocket connections
- Database query performance
"""

import pytest
import asyncio
import time
import concurrent.futures
from threading import Thread
from unittest.mock import Mock, patch

from app.main import app
from fastapi.testclient import TestClient


@pytest.mark.performance
@pytest.mark.slow
class TestConcurrentFileUploads:
    """Test system performance with concurrent file uploads."""
    
    def test_concurrent_single_file_uploads(self, authenticated_client, performance_timer):
        """Test uploading multiple files concurrently."""
        num_concurrent = 10
        
        def upload_file(file_num):
            """Upload a single file."""
            files = {
                "files": (f"test{file_num}.py", b"print('test')", "text/x-python")
            }
            response = authenticated_client.post(
                "/api/v1/files/upload-batch",
                files=files
            )
            return response.status_code == 200
        
        performance_timer.start()
        
        # Use thread pool for concurrent uploads
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(upload_file, i) for i in range(num_concurrent)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        performance_timer.stop()
        
        # All uploads should succeed
        assert all(results), "Some uploads failed"
        
        # Should complete within reasonable time (2 seconds per upload on average)
        performance_timer.assert_duration_under(num_concurrent * 2)
        
        print(f"\nConcurrent uploads: {num_concurrent} files in {performance_timer.duration():.2f}s")
    
    def test_large_batch_upload(self, authenticated_client, performance_timer):
        """Test uploading a large batch of files."""
        num_files = 20
        
        files = [
            ("files", (f"file{i}.py", b"def test(): pass", "text/x-python"))
            for i in range(num_files)
        ]
        
        performance_timer.start()
        response = authenticated_client.post(
            "/api/v1/files/upload-batch",
            files=files
        )
        performance_timer.stop()
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == num_files
        
        # Should accept batch quickly (< 5 seconds)
        performance_timer.assert_duration_under(5)
        
        print(f"\nBatch upload: {num_files} files accepted in {performance_timer.duration():.2f}s")
    
    def test_upload_throughput(self, authenticated_client):
        """Test upload throughput over time."""
        num_uploads = 50
        start_time = time.time()
        successful_uploads = 0
        
        for i in range(num_uploads):
            files = {
                "files": (f"test{i}.py", b"print('test')", "text/x-python")
            }
            response = authenticated_client.post(
                "/api/v1/files/upload-batch",
                files=files
            )
            if response.status_code == 200:
                successful_uploads += 1
        
        duration = time.time() - start_time
        throughput = successful_uploads / duration
        
        print(f"\nUpload throughput: {throughput:.2f} uploads/second")
        print(f"Total: {successful_uploads}/{num_uploads} successful in {duration:.2f}s")
        
        # Should maintain reasonable throughput
        assert throughput > 1.0, "Upload throughput too low"


@pytest.mark.performance
@pytest.mark.slow
class TestAnalysisQueuePerformance:
    """Test analysis queue processing performance."""
    
    def test_queue_processing_rate(self, authenticated_client, db_session):
        """Test how quickly the queue processes analyses."""
        num_analyses = 20
        batch_ids = []
        
        # Submit multiple analyses
        start_time = time.time()
        for i in range(num_analyses):
            files = {
                "files": (f"test{i}.py", b"def test(): pass", "text/x-python")
            }
            response = authenticated_client.post(
                "/api/v1/files/upload-batch",
                files=files
            )
            if response.status_code == 200:
                batch_ids.append(response.json()["batch_id"])
        
        submission_time = time.time() - start_time
        
        # Wait for all to complete
        max_wait = 120  # 2 minutes
        completed = 0
        check_start = time.time()
        
        while time.time() - check_start < max_wait:
            completed = 0
            for batch_id in batch_ids:
                response = authenticated_client.get(
                    f"/api/v1/files/batch/{batch_id}/status"
                )
                if response.status_code == 200:
                    status = response.json()
                    if status["status"] == "completed":
                        completed += 1
            
            if completed == len(batch_ids):
                break
            
            time.sleep(2)
        
        processing_time = time.time() - check_start
        
        print(f"\nQueue performance:")
        print(f"  Submission: {num_analyses} analyses in {submission_time:.2f}s")
        print(f"  Processing: {completed}/{num_analyses} completed in {processing_time:.2f}s")
        print(f"  Rate: {completed/processing_time:.2f} analyses/second")
        
        # Should complete most analyses
        assert completed >= num_analyses * 0.8, "Too many analyses failed to complete"
    
    def test_queue_under_load(self, authenticated_client):
        """Test queue behavior under heavy load."""
        num_concurrent = 30
        
        def submit_analysis(file_num):
            files = {
                "files": (f"load{file_num}.py", b"print('load test')", "text/x-python")
            }
            response = authenticated_client.post(
                "/api/v1/files/upload-batch",
                files=files
            )
            return response.status_code, response.json() if response.status_code == 200 else None
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_analysis, i) for i in range(num_concurrent)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        submission_time = time.time() - start_time
        
        successful = sum(1 for status, _ in results if status == 200)
        
        print(f"\nLoad test: {successful}/{num_concurrent} submitted in {submission_time:.2f}s")
        
        # Should handle most requests successfully
        assert successful >= num_concurrent * 0.9, "Too many requests failed under load"


@pytest.mark.performance
class TestDatabaseQueryPerformance:
    """Test database query performance."""
    
    def test_analysis_history_query_performance(self, authenticated_client, db_session, mock_user):
        """Test performance of analysis history queries."""
        from app.models.analysis import DirectAnalysis
        
        # Create many analysis records
        num_records = 100
        analyses = [
            DirectAnalysis(
                user_id=mock_user.id,
                filename=f"test{i}.py",
                code_content="test",
                status="completed"
            )
            for i in range(num_records)
        ]
        db_session.add_all(analyses)
        db_session.commit()
        
        # Test query performance
        start_time = time.time()
        response = authenticated_client.get(
            "/api/v1/analysis/direct/history?page=1&page_size=50"
        )
        query_time = time.time() - start_time
        
        assert response.status_code == 200
        
        print(f"\nHistory query: {num_records} records in {query_time:.3f}s")
        
        # Should be fast (< 1 second)
        assert query_time < 1.0, "History query too slow"
    
    def test_analytics_aggregation_performance(self, admin_client, db_session):
        """Test performance of analytics aggregation queries."""
        from app.models.analysis import DirectAnalysis
        from app.models.users import User
        
        # Create test data
        users = [
            User(
                email=f"user{i}@example.com",
                first_name=f"User{i}",
                last_name="Test",
                hashed_password="hashed"
            )
            for i in range(10)
        ]
        db_session.add_all(users)
        db_session.commit()
        
        # Create analyses for each user
        for user in users:
            analyses = [
                DirectAnalysis(
                    user_id=user.id,
                    filename=f"file{j}.py",
                    code_content="test",
                    status="completed"
                )
                for j in range(10)
            ]
            db_session.add_all(analyses)
        db_session.commit()
        
        # Test platform stats query
        start_time = time.time()
        response = admin_client.get("/api/v1/admin/analytics/platform")
        query_time = time.time() - start_time
        
        assert response.status_code == 200
        
        print(f"\nPlatform stats aggregation: {query_time:.3f}s")
        
        # Should be reasonably fast (< 2 seconds)
        assert query_time < 2.0, "Analytics aggregation too slow"
    
    def test_search_query_performance(self, admin_client, db_session):
        """Test performance of search queries."""
        from app.models.users import User
        
        # Create many users
        users = [
            User(
                email=f"testuser{i}@example.com",
                first_name=f"Test{i}",
                last_name="User",
                hashed_password="hashed"
            )
            for i in range(200)
        ]
        db_session.add_all(users)
        db_session.commit()
        
        # Test search performance
        start_time = time.time()
        response = admin_client.get("/api/v1/admin/users?search=testuser50")
        query_time = time.time() - start_time
        
        assert response.status_code == 200
        
        print(f"\nUser search: 200 records searched in {query_time:.3f}s")
        
        # Should be fast (< 0.5 seconds)
        assert query_time < 0.5, "Search query too slow"


@pytest.mark.performance
class TestAPIResponseTimes:
    """Test API endpoint response times."""
    
    def test_endpoint_response_times(self, authenticated_client, performance_timer):
        """Test response times for various endpoints."""
        endpoints = [
            ("GET", "/api/v1/analysis/direct/history"),
            ("GET", "/api/v1/analytics/dashboard"),
            ("GET", "/api/v1/analytics/issue-trends?timeframe=7d"),
            ("GET", "/api/v1/analytics/criticality-distribution?timeframe=7d"),
        ]
        
        results = {}
        
        for method, endpoint in endpoints:
            performance_timer.start()
            
            if method == "GET":
                response = authenticated_client.get(endpoint)
            
            performance_timer.stop()
            
            results[endpoint] = {
                "status": response.status_code,
                "time": performance_timer.duration()
            }
        
        print("\nAPI Response Times:")
        for endpoint, result in results.items():
            print(f"  {endpoint}: {result['time']:.3f}s (status: {result['status']})")
        
        # All endpoints should respond quickly
        for endpoint, result in results.items():
            assert result["time"] < 2.0, f"{endpoint} too slow"
    
    def test_concurrent_api_requests(self, authenticated_client):
        """Test API performance under concurrent requests."""
        num_concurrent = 20
        endpoint = "/api/v1/analytics/dashboard"
        
        def make_request():
            start = time.time()
            response = authenticated_client.get(endpoint)
            duration = time.time() - start
            return response.status_code, duration
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(num_concurrent)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        successful = sum(1 for status, _ in results if status == 200)
        avg_response_time = sum(duration for _, duration in results) / len(results)
        
        print(f"\nConcurrent API requests:")
        print(f"  Total: {successful}/{num_concurrent} successful")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Avg response time: {avg_response_time:.3f}s")
        
        # Should handle concurrent requests well
        assert successful >= num_concurrent * 0.95, "Too many failed requests"
        assert avg_response_time < 3.0, "Average response time too high"


@pytest.mark.performance
class TestMemoryAndResourceUsage:
    """Test memory and resource usage."""
    
    def test_large_file_handling(self, authenticated_client):
        """Test handling of large files."""
        # Create a large file (but within limits)
        large_content = b"# " + b"x" * (4 * 1024 * 1024)  # 4MB
        
        files = {
            "files": ("large.py", large_content, "text/x-python")
        }
        
        start_time = time.time()
        response = authenticated_client.post(
            "/api/v1/files/upload-batch",
            files=files
        )
        upload_time = time.time() - start_time
        
        print(f"\nLarge file upload: 4MB in {upload_time:.2f}s")
        
        # Should handle large files
        assert response.status_code in [200, 400, 413]
        
        if response.status_code == 200:
            # Should upload within reasonable time
            assert upload_time < 10.0, "Large file upload too slow"
    
    def test_pagination_efficiency(self, authenticated_client, db_session, mock_user):
        """Test pagination efficiency with large datasets."""
        from app.models.analysis import DirectAnalysis
        
        # Create many records
        num_records = 500
        analyses = [
            DirectAnalysis(
                user_id=mock_user.id,
                filename=f"test{i}.py",
                code_content="test",
                status="completed"
            )
            for i in range(num_records)
        ]
        db_session.add_all(analyses)
        db_session.commit()
        
        # Test different page sizes
        page_sizes = [10, 50, 100]
        
        for page_size in page_sizes:
            start_time = time.time()
            response = authenticated_client.get(
                f"/api/v1/analysis/direct/history?page=1&page_size={page_size}"
            )
            query_time = time.time() - start_time
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["analyses"]) <= page_size
            
            print(f"Pagination (page_size={page_size}): {query_time:.3f}s")
            
            # Should be efficient regardless of page size
            assert query_time < 1.0, f"Pagination with page_size={page_size} too slow"
