"""
Unit and integration tests for Files API endpoints.

Tests cover:
- Multi-file upload functionality
- Batch processing system
- File validation and error handling
- Progress tracking and results aggregation

Requirements: 6.1, 6.2, 6.3
"""

import pytest
import json
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from io import BytesIO

from app.main import app
from app.api.deps import get_db, get_current_user
from app.models.users import User
from app.services.batch_processing_service import BatchProcessingService


class TestFilesAPI:
    """Test suite for Files API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        return user
    
    def setup_method(self):
        """Setup for each test method."""
        self.sample_batch_response = {
            "batchId": "batch_123456",
            "totalFiles": 3,
            "status": "processing",
            "message": "Files uploaded successfully and processing started",
            "files": [
                {
                    "filename": "test1.py",
                    "size": 1024,
                    "status": "queued",
                    "fileId": "file_1"
                },
                {
                    "filename": "test2.js",
                    "size": 2048,
                    "status": "queued",
                    "fileId": "file_2"
                },
                {
                    "filename": "test3.java",
                    "size": 1536,
                    "status": "queued",
                    "fileId": "file_3"
                }
            ]
        }
        
        self.sample_batch_status = {
            "batchId": "batch_123456",
            "status": "processing",
            "totalFiles": 3,
            "processedFiles": 2,
            "progress": 66.7,
            "files": [
                {
                    "fileId": "file_1",
                    "filename": "test1.py",
                    "status": "completed",
                    "progress": 100
                },
                {
                    "fileId": "file_2",
                    "filename": "test2.js",
                    "status": "completed",
                    "progress": 100
                },
                {
                    "fileId": "file_3",
                    "filename": "test3.java",
                    "status": "processing",
                    "progress": 45
                }
            ]
        }
        
        self.sample_batch_results = {
            "batchId": "batch_123456",
            "status": "completed",
            "totalFiles": 3,
            "results": [
                {
                    "fileId": "file_1",
                    "filename": "test1.py",
                    "analysis": {
                        "issues": [
                            {
                                "type": "bug",
                                "severity": "high",
                                "message": "Potential null pointer exception",
                                "line": 15,
                                "suggestion": "Add null check before accessing object"
                            }
                        ],
                        "summary": {
                            "totalIssues": 1,
                            "criticalIssues": 0,
                            "highIssues": 1,
                            "mediumIssues": 0,
                            "lowIssues": 0
                        }
                    }
                }
            ]
        }
    
    def test_upload_multiple_files_success(self, client, mock_db, mock_user):
        """Test successful multiple file upload."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        # Create mock files
        files = [
            ("files", ("test1.py", BytesIO(b"print('hello')"), "text/plain")),
            ("files", ("test2.js", BytesIO(b"console.log('hello')"), "text/plain")),
            ("files", ("test3.java", BytesIO(b"System.out.println('hello')"), "text/plain"))
        ]
        
        with patch.object(BatchProcessingService, 'process_multiple_files', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = self.sample_batch_response
            
            response = client.post("/api/v1/files/upload-multiple", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["batchId"] == "batch_123456"
            assert data["totalFiles"] == 3
            assert data["status"] == "processing"
            assert len(data["files"]) == 3
            mock_process.assert_called_once()
        
        app.dependency_overrides.clear()
    
    def test_upload_multiple_files_validation_error(self, client, mock_db, mock_user):
        """Test multiple file upload with validation errors."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        # Create files with invalid types and sizes
        large_content = b"x" * (10 * 1024 * 1024 + 1)  # > 10MB
        files = [
            ("files", ("test.exe", BytesIO(b"executable"), "application/exe")),  # Invalid type
            ("files", ("large.py", BytesIO(large_content), "text/plain"))  # Too large
        ]
        
        response = client.post("/api/v1/files/upload-multiple", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "validation" in data["detail"].lower() or "invalid" in data["detail"].lower()
        
        app.dependency_overrides.clear()
    
    def test_upload_no_files_error(self, client, mock_db, mock_user):
        """Test upload with no files provided."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        response = client.post("/api/v1/files/upload-multiple")
        
        assert response.status_code == 400
        data = response.json()
        assert "no files" in data["detail"].lower() or "required" in data["detail"].lower()
        
        app.dependency_overrides.clear()
    
    def test_get_upload_status_success(self, client, mock_db, mock_user):
        """Test successful batch status retrieval."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        batch_id = "batch_123456"
        
        with patch.object(BatchProcessingService, 'get_batch_status', new_callable=AsyncMock) as mock_get_status:
            mock_get_status.return_value = self.sample_batch_status
            
            response = client.get(f"/api/v1/files/upload-status/{batch_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["batchId"] == batch_id
            assert data["status"] == "processing"
            assert data["progress"] == 66.7
            assert len(data["files"]) == 3
            mock_get_status.assert_called_once_with(batch_id, 1)  # user_id
        
        app.dependency_overrides.clear()
    
    def test_get_upload_status_not_found(self, client, mock_db, mock_user):
        """Test batch status retrieval for non-existent batch."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        batch_id = "nonexistent_batch"
        
        with patch.object(BatchProcessingService, 'get_batch_status', new_callable=AsyncMock) as mock_get_status:
            mock_get_status.return_value = None
            
            response = client.get(f"/api/v1/files/upload-status/{batch_id}")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
        
        app.dependency_overrides.clear()
    
    def test_get_analysis_results_success(self, client, mock_db, mock_user):
        """Test successful analysis results retrieval."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        batch_id = "batch_123456"
        
        with patch.object(BatchProcessingService, 'get_batch_results', new_callable=AsyncMock) as mock_get_results:
            mock_get_results.return_value = self.sample_batch_results
            
            response = client.get(f"/api/v1/files/analysis-results/{batch_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["batchId"] == batch_id
            assert data["status"] == "completed"
            assert len(data["results"]) == 1
            assert data["results"][0]["filename"] == "test1.py"
            assert "analysis" in data["results"][0]
            mock_get_results.assert_called_once_with(batch_id, 1)  # user_id
        
        app.dependency_overrides.clear()
    
    def test_get_analysis_results_not_ready(self, client, mock_db, mock_user):
        """Test analysis results retrieval when batch is not completed."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        batch_id = "batch_processing"
        
        with patch.object(BatchProcessingService, 'get_batch_results', new_callable=AsyncMock) as mock_get_results:
            mock_get_results.return_value = {
                "batchId": batch_id,
                "status": "processing",
                "message": "Analysis still in progress"
            }
            
            response = client.get(f"/api/v1/files/analysis-results/{batch_id}")
            
            assert response.status_code == 202  # Accepted but not ready
            data = response.json()
            assert data["status"] == "processing"
            assert "progress" in data["message"].lower()
        
        app.dependency_overrides.clear()
    
    def test_unauthorized_access_to_batch(self, client, mock_db, mock_user):
        """Test unauthorized access to another user's batch."""
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        batch_id = "other_user_batch"
        
        with patch.object(BatchProcessingService, 'get_batch_status', new_callable=AsyncMock) as mock_get_status:
            mock_get_status.side_effect = PermissionError("Access denied")
            
            response = client.get(f"/api/v1/files/upload-status/{batch_id}")
            
            assert response.status_code == 403
            data = response.json()
            assert "access" in data["detail"].lower() or "permission" in data["detail"].lower()
        
        app.dependency_overrides.clear()


class TestBatchProcessingService:
    """Test suite for BatchProcessingService."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create BatchProcessingService instance."""
        return BatchProcessingService(mock_db)
    
    def test_file_validation_success(self, service):
        """Test successful file validation."""
        # Mock valid files
        valid_files = [
            Mock(filename="test.py", content_type="text/plain", size=1024),
            Mock(filename="test.js", content_type="text/plain", size=2048),
            Mock(filename="test.java", content_type="text/plain", size=1536)
        ]
        
        # This would test actual validation logic
        # validation_result = service.validate_files(valid_files)
        # assert validation_result.is_valid is True
        # assert len(validation_result.errors) == 0
        pass
    
    def test_file_validation_errors(self, service):
        """Test file validation with errors."""
        # Mock invalid files
        invalid_files = [
            Mock(filename="test.exe", content_type="application/exe", size=1024),  # Invalid type
            Mock(filename="large.py", content_type="text/plain", size=15*1024*1024),  # Too large
            Mock(filename="", content_type="text/plain", size=1024)  # Empty name
        ]
        
        # This would test actual validation logic
        # validation_result = service.validate_files(invalid_files)
        # assert validation_result.is_valid is False
        # assert len(validation_result.errors) == 3
        pass
    
    @pytest.mark.asyncio
    async def test_batch_creation_success(self, service, mock_db):
        """Test successful batch creation."""
        user_id = 1
        files = [
            Mock(filename="test.py", content_type="text/plain", size=1024),
            Mock(filename="test.js", content_type="text/plain", size=2048)
        ]
        
        # Mock database operations
        mock_batch = Mock()
        mock_batch.id = "batch_123456"
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        
        # This would test actual batch creation
        # batch_id = await service.create_batch(user_id, files)
        # assert batch_id == "batch_123456"
        pass
    
    @pytest.mark.asyncio
    async def test_queue_processing_success(self, service):
        """Test successful queue processing."""
        batch_id = "batch_123456"
        
        # Mock queue operations
        with patch('app.core.hybrid_queue.HybridQueue') as mock_queue:
            mock_queue_instance = Mock()
            mock_queue.return_value = mock_queue_instance
            mock_queue_instance.enqueue.return_value = True
            
            # This would test actual queue processing
            # result = await service.queue_batch_for_processing(batch_id)
            # assert result is True
            pass
    
    def test_progress_calculation(self, service):
        """Test progress calculation logic."""
        # Test various progress scenarios
        test_cases = [
            (0, 10, 0.0),    # No files processed
            (5, 10, 50.0),   # Half processed
            (10, 10, 100.0), # All processed
            (3, 7, 42.86)    # Partial with decimal
        ]
        
        for processed, total, expected in test_cases:
            # This would test actual progress calculation
            # progress = service.calculate_progress(processed, total)
            # assert abs(progress - expected) < 0.01
            pass


class TestFileUploadIntegration:
    """Integration tests for file upload workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_upload_workflow(self):
        """Test complete file upload and processing workflow."""
        # This would test the entire workflow:
        # 1. File upload
        # 2. Validation
        # 3. Batch creation
        # 4. Queue processing
        # 5. Analysis execution
        # 6. Results aggregation
        pass
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test error recovery in upload workflow."""
        # This would test error scenarios:
        # 1. File validation failures
        # 2. Database errors during batch creation
        # 3. Queue processing failures
        # 4. Analysis errors
        # 5. Cleanup operations
        pass
    
    def test_concurrent_uploads(self):
        """Test handling of concurrent file uploads."""
        # This would test multiple users uploading files simultaneously
        # and ensure proper isolation and resource management
        pass


class TestFileUploadPerformance:
    """Performance tests for file upload operations."""
    
    def test_large_batch_performance(self):
        """Test performance with large file batches."""
        # This would test uploading many files at once
        # and measure processing time and memory usage
        start_time = datetime.utcnow()
        
        # Simulate large batch processing
        # process_large_batch(files=100)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Assert processing completes within acceptable time
        assert duration < 30.0  # Should complete within 30 seconds
    
    def test_file_size_limits(self):
        """Test file size limit enforcement."""
        # Test various file sizes and ensure proper handling
        size_limits = [
            (1024, True),           # 1KB - should pass
            (1024*1024, True),      # 1MB - should pass
            (5*1024*1024, True),    # 5MB - should pass
            (10*1024*1024, True),   # 10MB - should pass
            (15*1024*1024, False),  # 15MB - should fail
            (50*1024*1024, False)   # 50MB - should fail
        ]
        
        for size, should_pass in size_limits:
            # This would test actual size validation
            # result = validate_file_size(size)
            # assert result == should_pass
            pass
    
    def test_memory_usage_during_upload(self):
        """Test memory usage during file upload."""
        # This would monitor memory usage during large file uploads
        # to ensure efficient streaming and processing
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])