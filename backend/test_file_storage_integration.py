"""
Integration tests for File Storage Service and API endpoints.

This module tests the complete file storage workflow including:
- File upload, download, delete, and list operations
- Digital Ocean Spaces integration (mocked)
- Database operations and metadata management
- API endpoint functionality with authentication
- Error handling and edge cases

Requirements covered: 4.1, 4.2, 4.3, 4.4, 4.5
"""

import pytest
import asyncio
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from io import BytesIO

from app.main import app
from app.core.database import get_db, Base
from app.models.users import User
from app.models.file_storage import StoredFile
from app.services.file_storage_service import FileStorageService, FileStorageError
from app.core.security import create_access_token


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_file_storage.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def setup_database():
    """Set up test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Clean up test database file
    if os.path.exists("./test_file_storage.db"):
        os.remove("./test_file_storage.db")


@pytest.fixture
def db_session():
    """Create a database session for testing"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for API requests"""
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_s3_client():
    """Mock S3 client for Digital Ocean Spaces"""
    with patch('app.services.file_storage_service.boto3.client') as mock_boto3:
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        
        # Mock successful operations
        mock_client.put_object.return_value = {}
        mock_client.get_object.return_value = {
            'Body': Mock(read=lambda: b'test file content')
        }
        mock_client.delete_object.return_value = {}
        mock_client.generate_presigned_url.return_value = "https://signed-url.example.com"
        
        yield mock_client


class TestFileStorageService:
    """Test the FileStorageService class"""
    
    def test_service_initialization(self):
        """Test service initialization with environment variables"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com'
        }):
            service = FileStorageService()
            assert service.spaces_key == 'test_key'
            assert service.spaces_secret == 'test_secret'
            assert service.bucket_name == 'test_bucket'
            assert service.endpoint_url == 'https://test.digitaloceanspaces.com'
    
    def test_service_initialization_missing_config(self):
        """Test service initialization with missing configuration"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(FileStorageError) as exc_info:
                FileStorageService()
            assert exc_info.value.error_code == "CONFIG_ERROR"
    
    def test_generate_file_key(self):
        """Test file key generation"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com'
        }):
            service = FileStorageService()
            file_key = service._generate_file_key(123, "test_file.py")
            
            assert file_key.startswith("uploads/123/")
            assert file_key.endswith("_test_file.py")
            assert len(file_key.split('/')) >= 4  # uploads/user_id/date/uuid_filename
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com'
        }):
            service = FileStorageService()
            
            # Test normal filename
            assert service._sanitize_filename("test_file.py") == "test_file.py"
            
            # Test filename with special characters
            assert service._sanitize_filename("test/file\\name.py") == "test_file_name.py"
            
            # Test empty filename
            sanitized = service._sanitize_filename("")
            assert sanitized.startswith("file_") and sanitized.endswith(".bin")
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self, setup_database, db_session, test_user, mock_s3_client):
        """Test successful file upload"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com'
        }):
            service = FileStorageService()
            
            # Create mock upload file
            mock_file = Mock()
            mock_file.filename = "test.py"
            mock_file.content_type = "text/x-python"
            mock_file.read = asyncio.coroutine(lambda: b"print('hello world')")
            
            result = await service.upload_file(mock_file, test_user, db_session)
            
            assert result.filename == "test.py"
            assert result.file_size == len(b"print('hello world')")
            assert result.content_type == "text/x-python"
            assert result.file_hash is not None
            
            # Verify database record was created
            stored_file = db_session.query(StoredFile).filter_by(file_id=result.file_id).first()
            assert stored_file is not None
            assert stored_file.user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, setup_database, db_session, test_user, mock_s3_client):
        """Test file upload with file too large"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com',
            'MAX_FILE_SIZE_MB': '1'  # 1MB limit
        }):
            service = FileStorageService()
            
            # Create mock file that's too large
            large_content = b"x" * (2 * 1024 * 1024)  # 2MB
            mock_file = Mock()
            mock_file.filename = "large.txt"
            mock_file.content_type = "text/plain"
            mock_file.read = asyncio.coroutine(lambda: large_content)
            
            with pytest.raises(FileStorageError) as exc_info:
                await service.upload_file(mock_file, test_user, db_session)
            
            assert exc_info.value.error_code == "FILE_TOO_LARGE"
    
    @pytest.mark.asyncio
    async def test_download_file_success(self, setup_database, db_session, test_user, mock_s3_client):
        """Test successful file download"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com'
        }):
            service = FileStorageService()
            
            # First upload a file
            mock_file = Mock()
            mock_file.filename = "test.py"
            mock_file.content_type = "text/x-python"
            test_content = b"print('hello world')"
            mock_file.read = asyncio.coroutine(lambda: test_content)
            
            upload_result = await service.upload_file(mock_file, test_user, db_session)
            
            # Now download it
            download_result = await service.download_file(upload_result.file_id, test_user, db_session)
            
            assert download_result.filename == "test.py"
            assert download_result.content == test_content
            assert download_result.content_type == "text/x-python"
    
    @pytest.mark.asyncio
    async def test_download_file_not_found(self, setup_database, db_session, test_user, mock_s3_client):
        """Test download of non-existent file"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com'
        }):
            service = FileStorageService()
            
            with pytest.raises(FileStorageError) as exc_info:
                await service.download_file("nonexistent-file-id", test_user, db_session)
            
            assert exc_info.value.error_code == "FILE_NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_delete_file_success(self, setup_database, db_session, test_user, mock_s3_client):
        """Test successful file deletion"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com'
        }):
            service = FileStorageService()
            
            # First upload a file
            mock_file = Mock()
            mock_file.filename = "test.py"
            mock_file.content_type = "text/x-python"
            mock_file.read = asyncio.coroutine(lambda: b"print('hello world')")
            
            upload_result = await service.upload_file(mock_file, test_user, db_session)
            
            # Now delete it
            success = await service.delete_file(upload_result.file_id, test_user, db_session)
            
            assert success is True
            
            # Verify file is deleted from database
            stored_file = db_session.query(StoredFile).filter_by(file_id=upload_result.file_id).first()
            assert stored_file is None
    
    @pytest.mark.asyncio
    async def test_list_user_files(self, setup_database, db_session, test_user, mock_s3_client):
        """Test listing user files"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com'
        }):
            service = FileStorageService()
            
            # Upload multiple files
            for i in range(3):
                mock_file = Mock()
                mock_file.filename = f"test_{i}.py"
                mock_file.content_type = "text/x-python"
                mock_file.read = asyncio.coroutine(lambda: f"print('file {i}')".encode())
                
                await service.upload_file(mock_file, test_user, db_session)
            
            # List files
            result = await service.list_user_files(test_user, db_session, limit=10, offset=0)
            
            assert result.total_count == 3
            assert len(result.files) == 3
            assert result.total_size > 0
    
    @pytest.mark.asyncio
    async def test_generate_signed_url(self, setup_database, db_session, test_user, mock_s3_client):
        """Test signed URL generation"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com'
        }):
            service = FileStorageService()
            
            # First upload a file
            mock_file = Mock()
            mock_file.filename = "test.py"
            mock_file.content_type = "text/x-python"
            mock_file.read = asyncio.coroutine(lambda: b"print('hello world')")
            
            upload_result = await service.upload_file(mock_file, test_user, db_session)
            
            # Generate signed URL
            signed_url = await service.generate_signed_url(upload_result.file_id, test_user, db_session)
            
            assert signed_url == "https://signed-url.example.com"


class TestFileStorageAPI:
    """Test the File Storage API endpoints"""
    
    @pytest.mark.asyncio
    async def test_upload_endpoint_success(self, setup_database, client, auth_headers, mock_s3_client):
        """Test successful file upload via API"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com'
        }):
            # Create test file
            test_content = b"print('hello world')"
            
            response = client.post(
                "/api/v1/storage/upload",
                headers=auth_headers,
                files={"file": ("test.py", BytesIO(test_content), "text/x-python")},
                data={"metadata": '{"description": "test file"}'}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["filename"] == "test.py"
            assert data["file_size"] == len(test_content)
            assert data["content_type"] == "text/x-python"
            assert "file_id" in data
            assert "file_hash" in data
    
    def test_upload_endpoint_unauthorized(self, setup_database, client, mock_s3_client):
        """Test file upload without authentication"""
        test_content = b"print('hello world')"
        
        response = client.post(
            "/api/v1/storage/upload",
            files={"file": ("test.py", BytesIO(test_content), "text/x-python")}
        )
        
        assert response.status_code == 401
    
    def test_upload_endpoint_invalid_file_type(self, setup_database, client, auth_headers, mock_s3_client):
        """Test file upload with invalid file type"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com',
            'ALLOWED_FILE_EXTENSIONS': 'py,js,txt'
        }):
            test_content = b"binary content"
            
            response = client.post(
                "/api/v1/storage/upload",
                headers=auth_headers,
                files={"file": ("test.exe", BytesIO(test_content), "application/octet-stream")}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["detail"]["error"] == "INVALID_FILE_TYPE"
    
    def test_list_files_endpoint(self, setup_database, client, auth_headers, mock_s3_client):
        """Test file listing endpoint"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com'
        }):
            response = client.get(
                "/api/v1/storage/list?limit=10&offset=0",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "files" in data
            assert "total_count" in data
            assert "total_size" in data
            assert isinstance(data["files"], list)
    
    def test_storage_info_endpoint(self, setup_database, client, auth_headers, mock_s3_client):
        """Test storage info endpoint"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com'
        }):
            response = client.get(
                "/api/v1/storage/storage-info",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "max_file_size_mb" in data
            assert "allowed_extensions" in data
            assert "user_stats" in data
            assert isinstance(data["allowed_extensions"], list)


class TestFileStorageErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_s3_connection_error(self, setup_database, db_session, test_user):
        """Test handling of S3 connection errors"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com'
        }):
            with patch('app.services.file_storage_service.boto3.client') as mock_boto3:
                mock_client = Mock()
                mock_boto3.return_value = mock_client
                
                # Mock S3 error
                from botocore.exceptions import ClientError
                mock_client.put_object.side_effect = ClientError(
                    {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
                    'PutObject'
                )
                
                service = FileStorageService()
                
                mock_file = Mock()
                mock_file.filename = "test.py"
                mock_file.content_type = "text/x-python"
                mock_file.read = asyncio.coroutine(lambda: b"print('hello world')")
                
                with pytest.raises(FileStorageError) as exc_info:
                    await service.upload_file(mock_file, test_user, db_session)
                
                assert exc_info.value.error_code == "UPLOAD_FAILED"
    
    def test_invalid_metadata_format(self, setup_database, client, auth_headers, mock_s3_client):
        """Test handling of invalid metadata format"""
        with patch.dict(os.environ, {
            'DO_SPACES_KEY': 'test_key',
            'DO_SPACES_SECRET': 'test_secret',
            'DO_SPACES_BUCKET': 'test_bucket',
            'DO_SPACES_ENDPOINT': 'https://test.digitaloceanspaces.com'
        }):
            test_content = b"print('hello world')"
            
            response = client.post(
                "/api/v1/storage/upload",
                headers=auth_headers,
                files={"file": ("test.py", BytesIO(test_content), "text/x-python")},
                data={"metadata": "invalid json"}
            )
            
            assert response.status_code == 400
            assert "Invalid metadata format" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])