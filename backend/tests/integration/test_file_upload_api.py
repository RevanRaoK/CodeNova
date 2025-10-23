"""
Integration tests for file upload API endpoints.

Tests cover:
- Batch file upload
- File validation
- Batch status retrieval
- Error handling

Requirements: 15.3, 15.4
"""

import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.main import app
from app.api.deps import get_current_user
from app.models.users import User, UserRole


class TestFileUploadAPI:
    """Integration tests for file upload endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Create mock authenticated user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.role = UserRole.USER
        user.is_active = True
        return user
    
    @pytest.fixture
    def authenticated_client(self, client, mock_user):
        """Create authenticated test client."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        yield client
        app.dependency_overrides.clear()
    
    def create_test_file(self, filename: str, content: str):
        """Helper to create test file."""
        return (filename, io.BytesIO(content.encode()), "text/plain")
    
    # Upload Batch Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_upload_batch_single_file(self, authenticated_client):
        """Test uploading a single file."""
        with patch('app.services.file_upload_service.FileUploadService.upload_files_batch') as mock_upload:
            # Mock the batch response
            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.total_files = 1
            mock_batch.completed_files = 0
            mock_batch.failed_files = 0
            mock_batch.status = "processing"
            mock_batch.created_at = "2025-01-01T00:00:00"
            
            mock_file = Mock()
            mock_file.id = "file-123"
            mock_file.original_filename = "test.py"
            mock_file.status = "queued"
            mock_file.file_size = 100
            mock_file.language = "python"
            
            mock_batch.files = [mock_file]
            mock_upload.return_value = mock_batch
            
            files = [self.create_test_file("test.py", "print('hello')")]
            
            response = authenticated_client.post(
                "/api/v1/files/upload-batch",
                files={"files": files}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["batch_id"] == "batch-123"
            assert data["total_files"] == 1
            assert len(data["files"]) == 1
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_upload_batch_multiple_files(self, authenticated_client):
        """Test uploading multiple files."""
        with patch('app.services.file_upload_service.FileUploadService.upload_files_batch') as mock_upload:
            mock_batch = Mock()
            mock_batch.id = "batch-456"
            mock_batch.total_files = 3
            mock_batch.completed_files = 0
            mock_batch.failed_files = 0
            mock_batch.status = "processing"
            mock_batch.created_at = "2025-01-01T00:00:00"
            mock_batch.files = []
            
            for i in range(3):
                mock_file = Mock()
                mock_file.id = f"file-{i}"
                mock_file.original_filename = f"test{i}.py"
                mock_file.status = "queued"
                mock_file.file_size = 100
                mock_file.language = "python"
                mock_batch.files.append(mock_file)
            
            mock_upload.return_value = mock_batch
            
            files = [
                self.create_test_file("test1.py", "print('1')"),
                self.create_test_file("test2.py", "print('2')"),
                self.create_test_file("test3.py", "print('3')")
            ]
            
            response = authenticated_client.post(
                "/api/v1/files/upload-batch",
                files={"files": files}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_files"] == 3
            assert len(data["files"]) == 3
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_upload_batch_no_files(self, authenticated_client):
        """Test upload with no files returns error."""
        response = authenticated_client.post(
            "/api/v1/files/upload-batch",
            files={}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_upload_batch_too_many_files(self, authenticated_client):
        """Test upload with too many files returns error."""
        # Create 51 files (exceeds limit of 50)
        files = [
            self.create_test_file(f"test{i}.py", f"print('{i}')")
            for i in range(51)
        ]
        
        response = authenticated_client.post(
            "/api/v1/files/upload-batch",
            files={"files": files}
        )
        
        assert response.status_code == 400
        assert "Too many files" in response.json()["detail"]
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_upload_batch_unauthenticated(self, client):
        """Test upload without authentication returns error."""
        files = [self.create_test_file("test.py", "print('hello')")]
        
        response = client.post(
            "/api/v1/files/upload-batch",
            files={"files": files}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_upload_batch_validation_error(self, authenticated_client):
        """Test upload with invalid file returns error."""
        with patch('app.services.file_upload_service.FileUploadService.upload_files_batch') as mock_upload:
            mock_upload.side_effect = ValueError("Invalid file type")
            
            files = [self.create_test_file("test.exe", "binary content")]
            
            response = authenticated_client.post(
                "/api/v1/files/upload-batch",
                files={"files": files}
            )
            
            assert response.status_code == 400
            assert "Invalid file type" in response.json()["detail"]
    
    # Batch Status Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_batch_status_success(self, authenticated_client):
        """Test retrieving batch status."""
        with patch('app.services.file_upload_service.FileUploadService.get_batch_status') as mock_status:
            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "completed"
            mock_batch.total_files = 3
            mock_batch.completed_files = 3
            mock_batch.failed_files = 0
            mock_batch.created_at = "2025-01-01T00:00:00"
            mock_batch.completed_at = "2025-01-01T00:05:00"
            mock_batch.files = []
            
            mock_status.return_value = mock_batch
            
            response = authenticated_client.get("/api/v1/files/batch/batch-123/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["batch_id"] == "batch-123"
            assert data["status"] == "completed"
            assert data["progress_percentage"] == 100.0
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_batch_status_not_found(self, authenticated_client):
        """Test retrieving non-existent batch returns error."""
        with patch('app.services.file_upload_service.FileUploadService.get_batch_status') as mock_status:
            mock_status.return_value = None
            
            response = authenticated_client.get("/api/v1/files/batch/invalid-batch/status")
            
            assert response.status_code == 404
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_batch_status_partial_completion(self, authenticated_client):
        """Test batch status with partial completion."""
        with patch('app.services.file_upload_service.FileUploadService.get_batch_status') as mock_status:
            mock_batch = Mock()
            mock_batch.id = "batch-123"
            mock_batch.status = "processing"
            mock_batch.total_files = 10
            mock_batch.completed_files = 6
            mock_batch.failed_files = 1
            mock_batch.created_at = "2025-01-01T00:00:00"
            mock_batch.completed_at = None
            mock_batch.files = []
            
            mock_status.return_value = mock_batch
            
            response = authenticated_client.get("/api/v1/files/batch/batch-123/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "processing"
            assert data["completed_files"] == 6
            assert data["failed_files"] == 1
            # Progress = (6 + 1) / 10 * 100 = 70%
            assert data["progress_percentage"] == 70.0
    
    # File List Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_user_files(self, authenticated_client):
        """Test retrieving user's uploaded files."""
        with patch('app.services.file_upload_service.FileUploadService.get_user_files') as mock_files:
            mock_files.return_value = (
                [
                    {
                        "id": "file-1",
                        "filename": "test1.py",
                        "status": "completed",
                        "created_at": "2025-01-01T00:00:00"
                    },
                    {
                        "id": "file-2",
                        "filename": "test2.py",
                        "status": "completed",
                        "created_at": "2025-01-01T00:01:00"
                    }
                ],
                2  # total count
            )
            
            response = authenticated_client.get("/api/v1/files/list")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert len(data["files"]) == 2
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_user_files_with_pagination(self, authenticated_client):
        """Test file list with pagination."""
        with patch('app.services.file_upload_service.FileUploadService.get_user_files') as mock_files:
            mock_files.return_value = ([], 0)
            
            response = authenticated_client.get("/api/v1/files/list?page=2&page_size=10")
            
            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 2
            assert data["page_size"] == 10
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_user_files_with_status_filter(self, authenticated_client):
        """Test file list with status filter."""
        with patch('app.services.file_upload_service.FileUploadService.get_user_files') as mock_files:
            mock_files.return_value = ([], 0)
            
            response = authenticated_client.get("/api/v1/files/list?status=completed")
            
            assert response.status_code == 200
            mock_files.assert_called_once()
            # Verify status filter was passed
            call_kwargs = mock_files.call_args[1]
            assert call_kwargs.get("status") == "completed"
