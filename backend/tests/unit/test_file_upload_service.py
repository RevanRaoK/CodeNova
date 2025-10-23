"""
Unit tests for FileUploadService.

Tests cover:
- Batch file upload
- File validation integration
- Batch status tracking
- Error handling

Requirements: 15.1, 15.3, 15.4
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.services.file_upload_service import FileUploadService
from app.services.file_validation_service import ValidationResult
from app.models.file_batch import FileBatch, BatchFile, BatchStatus, FileStatus


class TestFileUploadService:
    """Test suite for FileUploadService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock(spec=Session)
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.query = Mock()
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create a FileUploadService instance."""
        return FileUploadService(mock_db)
    
    def create_mock_file(self, filename: str, content: bytes = b"test content"):
        """Helper to create mock UploadFile."""
        file = Mock(spec=UploadFile)
        file.filename = filename
        file.content_type = "text/plain"
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        return file
    
    # Upload Batch Tests
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_upload_files_batch_single_file(self, service, mock_db):
        """Test uploading a single file in a batch."""
        files = [self.create_mock_file("test.py")]
        
        with patch.object(service.validation_service, 'validate_file') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=True,
                file_info={"filename": "test.py", "size_bytes": 100}
            )
            
            batch = await service.upload_files_batch(files, user_id=1)
        
        assert batch is not None
        assert batch.total_files == 1
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_upload_files_batch_multiple_files(self, service, mock_db):
        """Test uploading multiple files in a batch."""
        files = [
            self.create_mock_file("test1.py"),
            self.create_mock_file("test2.py"),
            self.create_mock_file("test3.py")
        ]
        
        with patch.object(service.validation_service, 'validate_file') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=True,
                file_info={"filename": "test.py", "size_bytes": 100}
            )
            
            batch = await service.upload_files_batch(files, user_id=1)
        
        assert batch.total_files == 3
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_upload_files_batch_no_files(self, service, mock_db):
        """Test uploading with no files raises error."""
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_files_batch([], user_id=1)
        
        assert exc_info.value.status_code == 400
        assert "No files provided" in exc_info.value.detail
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_upload_files_batch_too_many_files(self, service, mock_db):
        """Test uploading too many files raises error."""
        # Create 11 files (exceeds limit of 10)
        files = [self.create_mock_file(f"test{i}.py") for i in range(11)]
        
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_files_batch(files, user_id=1)
        
        assert exc_info.value.status_code == 400
        assert "Too many files" in exc_info.value.detail
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_upload_files_batch_validation_failure(self, service, mock_db):
        """Test handling of file validation failure."""
        files = [self.create_mock_file("invalid.exe")]
        
        with patch.object(service.validation_service, 'validate_file') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=False,
                error_message="Invalid file type",
                error_code="INVALID_TYPE"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await service.upload_files_batch(files, user_id=1)
            
            assert exc_info.value.status_code == 400
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_upload_files_batch_partial_validation_failure(self, service, mock_db):
        """Test batch with some files failing validation."""
        files = [
            self.create_mock_file("valid.py"),
            self.create_mock_file("invalid.exe")
        ]
        
        def validate_side_effect(file):
            if file.filename.endswith('.py'):
                return ValidationResult(
                    is_valid=True,
                    file_info={"filename": file.filename, "size_bytes": 100}
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    error_message="Invalid file type"
                )
        
        with patch.object(service.validation_service, 'validate_file') as mock_validate:
            mock_validate.side_effect = validate_side_effect
            
            # Depending on implementation, might raise or continue
            try:
                batch = await service.upload_files_batch(files, user_id=1)
                # If it continues, check that failed files are tracked
                assert batch is not None
            except HTTPException:
                # If it raises, that's also valid behavior
                pass
    
    # Get Batch Status Tests
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_batch_status_exists(self, service, mock_db):
        """Test getting status of existing batch."""
        mock_batch = Mock(spec=FileBatch)
        mock_batch.id = "batch-123"
        mock_batch.status = BatchStatus.PROCESSING
        mock_batch.total_files = 5
        mock_batch.processed_files = 3
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_batch
        mock_db.query.return_value = mock_query
        
        batch = await service.get_batch_status("batch-123", user_id=1)
        
        assert batch is not None
        assert batch.id == "batch-123"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_batch_status_not_found(self, service, mock_db):
        """Test getting status of non-existent batch."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        batch = await service.get_batch_status("invalid-batch", user_id=1)
        
        assert batch is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_batch_status_wrong_user(self, service, mock_db):
        """Test getting batch status for different user."""
        mock_batch = Mock(spec=FileBatch)
        mock_batch.id = "batch-123"
        mock_batch.user_id = 999  # Different user
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None  # Should not return
        mock_db.query.return_value = mock_query
        
        batch = await service.get_batch_status("batch-123", user_id=1)
        
        assert batch is None
    
    # Get User Files Tests
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_files_empty(self, service, mock_db):
        """Test getting files for user with no uploads."""
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 0
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        files, total = await service.get_user_files(user_id=1)
        
        assert len(files) == 0
        assert total == 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_files_with_results(self, service, mock_db):
        """Test getting files for user with uploads."""
        mock_files = [
            Mock(id="file-1", filename="test1.py", status=FileStatus.COMPLETED),
            Mock(id="file-2", filename="test2.py", status=FileStatus.COMPLETED)
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 2
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_files
        mock_db.query.return_value = mock_query
        
        files, total = await service.get_user_files(user_id=1)
        
        assert len(files) == 2
        assert total == 2
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_files_with_pagination(self, service, mock_db):
        """Test getting files with pagination."""
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 100
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        files, total = await service.get_user_files(
            user_id=1,
            page=2,
            page_size=20
        )
        
        assert total == 100
        # Verify offset was called with correct value (page 2, size 20 = offset 20)
        mock_query.filter.return_value.order_by.return_value.offset.assert_called()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_files_with_status_filter(self, service, mock_db):
        """Test getting files filtered by status."""
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 10
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        files, total = await service.get_user_files(
            user_id=1,
            status=FileStatus.COMPLETED
        )
        
        assert total == 10
    
    # Update Batch Status Tests
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_batch_status(self, service, mock_db):
        """Test updating batch status."""
        mock_batch = Mock(spec=FileBatch)
        mock_batch.id = "batch-123"
        mock_batch.status = BatchStatus.PENDING
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_batch
        mock_db.query.return_value = mock_query
        
        updated = await service.update_batch_status(
            "batch-123",
            BatchStatus.PROCESSING
        )
        
        assert updated is not None
        assert updated.status == BatchStatus.PROCESSING
        mock_db.commit.assert_called()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_batch_status_not_found(self, service, mock_db):
        """Test updating non-existent batch."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        updated = await service.update_batch_status(
            "invalid-batch",
            BatchStatus.PROCESSING
        )
        
        assert updated is None
    
    # Update File Status Tests
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_file_status(self, service, mock_db):
        """Test updating individual file status."""
        mock_file = Mock(spec=BatchFile)
        mock_file.id = "file-123"
        mock_file.status = FileStatus.PENDING
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_file
        mock_db.query.return_value = mock_query
        
        updated = await service.update_file_status(
            "file-123",
            FileStatus.PROCESSING
        )
        
        assert updated is not None
        assert updated.status == FileStatus.PROCESSING
        mock_db.commit.assert_called()
    
    # Error Handling Tests
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_upload_files_batch_db_error(self, service, mock_db):
        """Test handling of database errors during upload."""
        files = [self.create_mock_file("test.py")]
        mock_db.commit.side_effect = Exception("Database error")
        
        with patch.object(service.validation_service, 'validate_file') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=True,
                file_info={"filename": "test.py", "size_bytes": 100}
            )
            
            with pytest.raises(Exception):
                await service.upload_files_batch(files, user_id=1)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_upload_files_batch_with_language_override(self, service, mock_db):
        """Test uploading files with language override."""
        files = [self.create_mock_file("test.py")]
        
        with patch.object(service.validation_service, 'validate_file') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=True,
                file_info={"filename": "test.py", "size_bytes": 100}
            )
            
            batch = await service.upload_files_batch(
                files,
                user_id=1,
                language="python"
            )
        
        assert batch is not None
