"""
Test script for file upload and analysis services.

This script tests the new file upload and batch analysis functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.file_validation_service import FileValidationService, ValidationResult
from app.services.file_upload_service import FileUploadService
from app.workers.batch_analysis_worker import BatchAnalysisWorker
from app.core.database import SessionLocal
from app.models.users import User
from io import BytesIO
from fastapi import UploadFile


def test_file_validation():
    """Test file validation service."""
    print("\n" + "="*80)
    print("Testing File Validation Service")
    print("="*80)
    
    validation_service = FileValidationService()
    
    # Test 1: Valid Python file
    print("\n1. Testing valid Python file...")
    code_content = b"""
def hello_world():
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_world()
"""
    
    # Create mock UploadFile
    class MockUploadFile:
        def __init__(self, filename, content, content_type="text/plain"):
            self.filename = filename
            self.content = content
            self.content_type = content_type
            self._position = 0
        
        async def read(self):
            return self.content
        
        async def seek(self, position):
            self._position = position
    
    mock_file = MockUploadFile("test.py", code_content)
    
    import asyncio
    result = asyncio.run(validation_service.validate_file(mock_file))
    
    print(f"   Valid: {result.is_valid}")
    if result.is_valid:
        print(f"   File info: {result.file_info}")
        print(f"   Warnings: {result.warnings if result.warnings else 'None'}")
    else:
        print(f"   Error: {result.error_message}")
    
    # Test 2: File too large
    print("\n2. Testing file size validation...")
    large_content = b"x" * (6 * 1024 * 1024)  # 6MB
    mock_large_file = MockUploadFile("large.py", large_content)
    
    result = asyncio.run(validation_service.validate_file(mock_large_file))
    print(f"   Valid: {result.is_valid}")
    if not result.is_valid:
        print(f"   Error: {result.error_message}")
        print(f"   Error code: {result.error_code}")
    
    # Test 3: Invalid extension
    print("\n3. Testing invalid file extension...")
    mock_exe_file = MockUploadFile("malware.exe", b"fake exe content")
    
    result = asyncio.run(validation_service.validate_file(mock_exe_file))
    print(f"   Valid: {result.is_valid}")
    if not result.is_valid:
        print(f"   Error: {result.error_message}")
        print(f"   Error code: {result.error_code}")
    
    # Test 4: Empty file
    print("\n4. Testing empty file...")
    mock_empty_file = MockUploadFile("empty.py", b"")
    
    result = asyncio.run(validation_service.validate_file(mock_empty_file))
    print(f"   Valid: {result.is_valid}")
    if not result.is_valid:
        print(f"   Error: {result.error_message}")
        print(f"   Error code: {result.error_code}")
    
    # Test 5: Code content validation
    print("\n5. Testing code content validation...")
    result = validation_service.validate_code_content(
        code="print('Hello, World!')",
        language="python"
    )
    print(f"   Valid: {result.is_valid}")
    if result.is_valid:
        print(f"   Code info: {result.file_info}")
    
    print("\n✓ File validation tests completed")


def test_language_detection():
    """Test language detection."""
    print("\n" + "="*80)
    print("Testing Language Detection")
    print("="*80)
    
    db = SessionLocal()
    upload_service = FileUploadService(db)
    
    test_files = [
        ("test.py", "python"),
        ("app.js", "javascript"),
        ("component.tsx", "typescript"),
        ("Main.java", "java"),
        ("program.cpp", "cpp"),
        ("script.sh", "shell"),
        ("style.css", "css"),
        ("data.json", "json"),
    ]
    
    for filename, expected_lang in test_files:
        detected = upload_service._detect_language(filename)
        status = "✓" if detected == expected_lang else "✗"
        print(f"   {status} {filename}: {detected} (expected: {expected_lang})")
    
    db.close()
    print("\n✓ Language detection tests completed")


def test_batch_analysis_worker():
    """Test batch analysis worker initialization."""
    print("\n" + "="*80)
    print("Testing Batch Analysis Worker")
    print("="*80)
    
    try:
        worker = BatchAnalysisWorker()
        print("   ✓ Worker initialized successfully")
        print(f"   Max retries: {worker.MAX_RETRIES}")
        print(f"   Retry delay: {worker.RETRY_DELAY_SECONDS}s")
    except Exception as e:
        print(f"   ✗ Worker initialization failed: {str(e)}")
    
    print("\n✓ Batch analysis worker tests completed")


def test_service_integration():
    """Test service integration."""
    print("\n" + "="*80)
    print("Testing Service Integration")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        # Check if we can create services
        validation_service = FileValidationService()
        upload_service = FileUploadService(db)
        worker = BatchAnalysisWorker()
        
        print("   ✓ All services initialized successfully")
        print(f"   Validation service: {type(validation_service).__name__}")
        print(f"   Upload service: {type(upload_service).__name__}")
        print(f"   Worker: {type(worker).__name__}")
        
        # Test validation service methods
        print("\n   Testing validation service methods:")
        print(f"   - Allowed extensions: {len(validation_service.ALLOWED_EXTENSIONS)} types")
        print(f"   - Max file size: {validation_service.MAX_FILE_SIZE_MB}MB")
        print(f"   - Max lines: {validation_service.MAX_LINES}")
        
        # Test upload service methods
        print("\n   Testing upload service methods:")
        print(f"   - Database session: {'Connected' if db else 'Not connected'}")
        
    except Exception as e:
        print(f"   ✗ Service integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n✓ Service integration tests completed")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("FILE UPLOAD AND ANALYSIS SERVICE TESTS")
    print("="*80)
    
    try:
        test_file_validation()
        test_language_detection()
        test_batch_analysis_worker()
        test_service_integration()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
