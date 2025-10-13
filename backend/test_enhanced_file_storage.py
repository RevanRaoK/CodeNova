#!/usr/bin/env python3
"""
Test script for Enhanced File Storage Service (Task 5).

This script tests the implementation of:
- Concurrent processing of multiple files
- Error isolation for batch operations
- Batch tracking and metadata management
- Background job queuing for code analysis

Requirements covered: 2.1, 2.2, 2.3, 2.6
"""

import asyncio
import logging
import sys
import os
import tempfile
from datetime import datetime
from typing import List

# Add the backend directory to Python path
sys.path.append('.')

from app.services.file_storage_service import file_storage_service, FileStorageError
from app.services.background_job_service import background_job_service
from app.core.database import get_db
from app.models.users import User
from app.models.file_storage import StoredFile
from fastapi import UploadFile
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockUploadFile:
    """Mock UploadFile for testing purposes."""
    
    def __init__(self, filename: str, content: bytes, content_type: str = "text/plain"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self.size = len(content)
        self._file = io.BytesIO(content)
    
    async def read(self) -> bytes:
        """Read file content."""
        return self.content
    
    async def seek(self, position: int):
        """Seek to position in file."""
        self._file.seek(position)


async def create_test_files() -> List[MockUploadFile]:
    """Create test files for upload testing."""
    test_files = [
        MockUploadFile(
            "test_python.py",
            b"""def hello_world():
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    hello_world()
""",
            "text/x-python"
        ),
        MockUploadFile(
            "test_javascript.js",
            b"""function greetUser(name) {
    console.log(`Hello, ${name}!`);
    return true;
}

greetUser("World");
""",
            "application/javascript"
        ),
        MockUploadFile(
            "config.json",
            b"""{
    "app_name": "test_app",
    "version": "1.0.0",
    "debug": true,
    "database": {
        "host": "localhost",
        "port": 5432
    }
}""",
            "application/json"
        ),
        MockUploadFile(
            "readme.md",
            b"""# Test Project

This is a test project for file upload functionality.

## Features

- Multiple file upload
- Background processing
- Error handling
""",
            "text/markdown"
        )
    ]
    
    return test_files


async def create_test_user(db) -> User:
    """Create a test user for file operations."""
    # Check if test user already exists
    existing_user = db.query(User).filter(User.email == "test_enhanced_storage@example.com").first()
    if existing_user:
        return existing_user
    
    # Create new test user
    test_user = User(
        email="test_enhanced_storage@example.com",
        username="test_enhanced_storage",
        hashed_password="test_password_hash",
        is_active=True,
        is_verified=True
    )
    
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    return test_user


async def test_concurrent_upload():
    """Test concurrent file upload with batch processing."""
    logger.info("Testing concurrent file upload with batch processing...")
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Create test user
        test_user = await create_test_user(db)
        logger.info(f"Created test user: {test_user.email}")
        
        # Create test files
        test_files = await create_test_files()
        logger.info(f"Created {len(test_files)} test files")
        
        # Test batch metadata
        batch_metadata = {
            "test_run": True,
            "test_timestamp": datetime.utcnow().isoformat(),
            "test_description": "Enhanced file storage test"
        }
        
        # Perform batch upload
        logger.info("Starting batch upload...")
        start_time = datetime.utcnow()
        
        batch_result = await file_storage_service.upload_multiple_files(
            files=test_files,
            user=test_user,
            db=db,
            metadata=batch_metadata
        )
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Verify results
        logger.info(f"Batch upload completed in {processing_time:.2f} seconds")
        logger.info(f"Batch ID: {batch_result.batch_id}")
        logger.info(f"Total files: {batch_result.total_files}")
        logger.info(f"Successful uploads: {batch_result.successful_uploads}")
        logger.info(f"Failed uploads: {batch_result.failed_uploads}")
        logger.info(f"Analysis jobs queued: {len(batch_result.analysis_job_ids)}")
        
        # Verify all files were uploaded successfully
        assert batch_result.total_files == len(test_files), f"Expected {len(test_files)} files, got {batch_result.total_files}"
        assert batch_result.successful_uploads == len(test_files), f"Expected all files to succeed, got {batch_result.successful_uploads}"
        assert batch_result.failed_uploads == 0, f"Expected no failures, got {batch_result.failed_uploads}"
        assert len(batch_result.analysis_job_ids) > 0, "Expected analysis jobs to be queued"
        
        # Verify batch tracking in database
        uploaded_files = db.query(StoredFile).filter(StoredFile.batch_id == batch_result.batch_id).all()
        assert len(uploaded_files) == len(test_files), f"Expected {len(test_files)} files in database, got {len(uploaded_files)}"
        
        # Verify metadata storage
        for stored_file in uploaded_files:
            assert stored_file.batch_id == batch_result.batch_id, "Batch ID should be stored"
            assert stored_file.upload_metadata is not None, "Upload metadata should be stored"
            assert stored_file.processing_status == "completed", "Processing status should be completed"
        
        logger.info("✓ Concurrent upload test passed")
        return batch_result
        
    finally:
        db.close()


async def test_error_isolation():
    """Test error isolation in batch operations."""
    logger.info("Testing error isolation in batch operations...")
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Create test user
        test_user = await create_test_user(db)
        
        # Create mixed test files (some valid, some invalid)
        test_files = [
            MockUploadFile("valid1.py", b"print('Hello')", "text/x-python"),
            MockUploadFile("", b"invalid filename", "text/plain"),  # Invalid: empty filename
            MockUploadFile("valid2.js", b"console.log('Hello');", "application/javascript"),
            MockUploadFile("toolarge.txt", b"x" * (50 * 1024 * 1024), "text/plain"),  # Invalid: too large
            MockUploadFile("valid3.json", b'{"test": true}', "application/json")
        ]
        
        # Perform batch upload with expected failures
        logger.info("Starting batch upload with expected failures...")
        
        batch_result = await file_storage_service.upload_multiple_files(
            files=test_files,
            user=test_user,
            db=db,
            metadata={"test_error_isolation": True}
        )
        
        # Verify error isolation worked
        logger.info(f"Batch completed with {batch_result.successful_uploads} successes and {batch_result.failed_uploads} failures")
        
        # Should have some successes and some failures
        assert batch_result.successful_uploads > 0, "Should have some successful uploads"
        assert batch_result.failed_uploads > 0, "Should have some failed uploads"
        assert batch_result.successful_uploads + batch_result.failed_uploads == batch_result.total_files
        
        # Verify failed files have error information
        for failed_file in batch_result.failed_files:
            assert "filename" in failed_file, "Failed file should have filename"
            assert "error_code" in failed_file, "Failed file should have error code"
            assert "error_message" in failed_file, "Failed file should have error message"
        
        logger.info("✓ Error isolation test passed")
        return batch_result
        
    finally:
        db.close()


async def test_background_job_integration():
    """Test background job queuing for analysis."""
    logger.info("Testing background job integration...")
    
    try:
        # Initialize background job service
        await background_job_service.initialize()
        logger.info("Background job service initialized")
        
        # Get some job statistics before
        initial_stats = await background_job_service.get_queue_statistics()
        logger.info(f"Initial queue stats: {initial_stats}")
        
        # Perform a small batch upload to generate analysis jobs
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            test_user = await create_test_user(db)
            
            # Create a single test file for analysis
            test_files = [
                MockUploadFile(
                    "analysis_test.py",
                    b"""def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# This could be optimized with memoization
result = calculate_fibonacci(10)
print(f"Fibonacci(10) = {result}")
""",
                    "text/x-python"
                )
            ]
            
            batch_result = await file_storage_service.upload_multiple_files(
                files=test_files,
                user=test_user,
                db=db,
                metadata={"analysis_test": True}
            )
            
            # Verify analysis jobs were queued
            assert len(batch_result.analysis_job_ids) > 0, "Analysis jobs should be queued"
            
            # Check job status
            for job_id in batch_result.analysis_job_ids:
                job_status = await background_job_service.get_job_status(job_id)
                if job_status:
                    logger.info(f"Analysis job {job_id}: {job_status.status.value}")
                    assert job_status.name == "file_code_analysis", "Job should be file code analysis"
                else:
                    logger.warning(f"Could not retrieve status for job {job_id}")
            
            logger.info("✓ Background job integration test passed")
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Background job integration test failed: {e}")
        raise
    finally:
        try:
            await background_job_service.close()
        except Exception as e:
            logger.debug(f"Error closing background job service: {e}")


async def test_batch_size_limits():
    """Test batch size validation."""
    logger.info("Testing batch size limits...")
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        test_user = await create_test_user(db)
        
        # Create too many files (more than limit of 10)
        too_many_files = [
            MockUploadFile(f"file_{i}.txt", f"Content {i}".encode(), "text/plain")
            for i in range(15)  # 15 files, limit is 10
        ]
        
        # Should raise an error
        try:
            await file_storage_service.upload_multiple_files(
                files=too_many_files,
                user=test_user,
                db=db
            )
            assert False, "Should have raised an error for too many files"
        except FileStorageError as e:
            assert e.error_code == "BATCH_SIZE_EXCEEDED", f"Expected BATCH_SIZE_EXCEEDED, got {e.error_code}"
            logger.info(f"✓ Correctly rejected batch with {len(too_many_files)} files")
        
        # Test empty file list
        try:
            await file_storage_service.upload_multiple_files(
                files=[],
                user=test_user,
                db=db
            )
            assert False, "Should have raised an error for empty file list"
        except FileStorageError as e:
            assert e.error_code == "NO_FILES_PROVIDED", f"Expected NO_FILES_PROVIDED, got {e.error_code}"
            logger.info("✓ Correctly rejected empty file list")
        
        logger.info("✓ Batch size limits test passed")
        
    finally:
        db.close()


async def run_comprehensive_test():
    """Run comprehensive test of enhanced file storage functionality."""
    logger.info("Starting comprehensive enhanced file storage test...")
    
    try:
        # Test 1: Concurrent upload with batch processing
        logger.info("\n" + "="*50)
        logger.info("TEST 1: Concurrent Upload with Batch Processing")
        logger.info("="*50)
        batch_result = await test_concurrent_upload()
        
        # Test 2: Error isolation
        logger.info("\n" + "="*50)
        logger.info("TEST 2: Error Isolation in Batch Operations")
        logger.info("="*50)
        await test_error_isolation()
        
        # Test 3: Background job integration
        logger.info("\n" + "="*50)
        logger.info("TEST 3: Background Job Integration")
        logger.info("="*50)
        await test_background_job_integration()
        
        # Test 4: Batch size limits
        logger.info("\n" + "="*50)
        logger.info("TEST 4: Batch Size Validation")
        logger.info("="*50)
        await test_batch_size_limits()
        
        logger.info("\n" + "="*50)
        logger.info("ALL TESTS PASSED!")
        logger.info("="*50)
        logger.info("Enhanced file storage service is working correctly:")
        logger.info("  ✓ Concurrent processing of multiple files")
        logger.info("  ✓ Error isolation for batch operations")
        logger.info("  ✓ Batch tracking and metadata management")
        logger.info("  ✓ Background job queuing for code analysis")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    # Run the comprehensive test
    success = asyncio.run(run_comprehensive_test())
    
    if success:
        logger.info("Enhanced file storage test completed successfully!")
        sys.exit(0)
    else:
        logger.error("Enhanced file storage test failed!")
        sys.exit(1)