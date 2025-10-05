"""
Simple test script for File Storage Service functionality.

This script tests basic file storage operations without requiring
a full test environment setup.
"""

import os
import tempfile
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

# Mock environment variables for testing
test_env = {
    'DO_SPACES_KEY': 'test_key',
    'DO_SPACES_SECRET': 'test_secret',
    'DO_SPACES_BUCKET': 'test_bucket',
    'DO_SPACES_REGION': 'nyc3',
    'DO_SPACES_ENDPOINT': 'https://nyc3.digitaloceanspaces.com',
    'MAX_FILE_SIZE_MB': '50',
    'FILE_UPLOAD_PATH': 'uploads/',
    'SIGNED_URL_EXPIRATION_HOURS': '24',
    'ALLOWED_FILE_EXTENSIONS': 'py,js,txt,pdf,jpg,png'
}


def test_service_initialization():
    """Test FileStorageService initialization"""
    print("Testing FileStorageService initialization...")
    
    with patch.dict(os.environ, test_env):
        try:
            from app.services.file_storage_service import FileStorageService
            service = FileStorageService()
            
            print("✅ Service initialized successfully")
            print(f"   Bucket: {service.bucket_name}")
            print(f"   Region: {service.region}")
            print(f"   Max file size: {service.max_file_size / (1024*1024):.0f}MB")
            print(f"   Allowed extensions: {len(service.allowed_extensions)} types")
            
            return True
        except Exception as e:
            print(f"❌ Service initialization failed: {e}")
            return False


def test_filename_sanitization():
    """Test filename sanitization"""
    print("\nTesting filename sanitization...")
    
    with patch.dict(os.environ, test_env):
        try:
            from app.services.file_storage_service import FileStorageService
            service = FileStorageService()
            
            test_cases = [
                ("normal_file.py", "normal_file.py"),
                ("file with spaces.txt", "file_with_spaces.txt"),
                ("../../../etc/passwd", ".._.._.._.._etc_passwd"),
                ("file/with\\slashes.js", "file_with_slashes.js"),
                ("", None)  # Should generate a random name
            ]
            
            for input_name, expected_pattern in test_cases:
                result = service._sanitize_filename(input_name)
                if expected_pattern is None:
                    # Check that a random name was generated
                    assert result.startswith("file_") and result.endswith(".bin")
                    print(f"   ✅ Empty filename -> {result}")
                else:
                    assert result == expected_pattern
                    print(f"   ✅ '{input_name}' -> '{result}'")
            
            return True
        except Exception as e:
            print(f"❌ Filename sanitization test failed: {e}")
            return False


def test_file_key_generation():
    """Test file key generation"""
    print("\nTesting file key generation...")
    
    with patch.dict(os.environ, test_env):
        try:
            from app.services.file_storage_service import FileStorageService
            service = FileStorageService()
            
            user_id = 123
            filename = "test_file.py"
            
            key1 = service._generate_file_key(user_id, filename)
            key2 = service._generate_file_key(user_id, filename)
            
            # Keys should be different (due to UUID)
            assert key1 != key2
            
            # Keys should follow expected pattern
            assert key1.startswith(f"{service.upload_path}{user_id}/")
            assert "_test_file.py" in key1
            
            print(f"   ✅ Generated key: {key1}")
            print(f"   ✅ Keys are unique: {key1 != key2}")
            
            return True
        except Exception as e:
            print(f"❌ File key generation test failed: {e}")
            return False


def test_file_hash_calculation():
    """Test file hash calculation"""
    print("\nTesting file hash calculation...")
    
    with patch.dict(os.environ, test_env):
        try:
            from app.services.file_storage_service import FileStorageService
            service = FileStorageService()
            
            test_content = b"Hello, World!"
            hash1 = service._calculate_file_hash(test_content)
            hash2 = service._calculate_file_hash(test_content)
            
            # Same content should produce same hash
            assert hash1 == hash2
            
            # Different content should produce different hash
            different_content = b"Hello, Universe!"
            hash3 = service._calculate_file_hash(different_content)
            assert hash1 != hash3
            
            # Hash should be SHA-256 (64 hex characters)
            assert len(hash1) == 64
            assert all(c in '0123456789abcdef' for c in hash1)
            
            print(f"   ✅ Hash for 'Hello, World!': {hash1}")
            print(f"   ✅ Consistent hashing: {hash1 == hash2}")
            print(f"   ✅ Different content produces different hash")
            
            return True
        except Exception as e:
            print(f"❌ File hash calculation test failed: {e}")
            return False


def test_file_validation():
    """Test file validation"""
    print("\nTesting file validation...")
    
    with patch.dict(os.environ, test_env):
        try:
            from app.services.file_storage_service import FileStorageService
            service = FileStorageService()
            
            # Test valid file
            valid_file = Mock()
            valid_file.filename = "test.py"
            valid_file.size = 1024  # 1KB
            
            try:
                service._validate_file(valid_file)
                print("   ✅ Valid file passed validation")
            except Exception as e:
                print(f"   ❌ Valid file failed validation: {e}")
                return False
            
            # Test file too large
            large_file = Mock()
            large_file.filename = "large.py"
            large_file.size = service.max_file_size + 1
            
            try:
                service._validate_file(large_file)
                print("   ❌ Large file should have failed validation")
                return False
            except Exception:
                print("   ✅ Large file correctly rejected")
            
            # Test invalid extension
            invalid_file = Mock()
            invalid_file.filename = "test.exe"
            invalid_file.size = 1024
            
            try:
                service._validate_file(invalid_file)
                print("   ❌ Invalid extension should have failed validation")
                return False
            except Exception:
                print("   ✅ Invalid extension correctly rejected")
            
            return True
        except Exception as e:
            print(f"❌ File validation test failed: {e}")
            return False


async def test_mock_upload_workflow():
    """Test the complete upload workflow with mocked S3"""
    print("\nTesting mock upload workflow...")
    
    with patch.dict(os.environ, test_env):
        try:
            # Mock the S3 client
            with patch('app.services.file_storage_service.boto3.client') as mock_boto3:
                mock_client = Mock()
                mock_boto3.return_value = mock_client
                mock_client.put_object.return_value = {}
                
                from app.services.file_storage_service import FileStorageService
                service = FileStorageService()
                
                # Create mock file
                mock_file = Mock()
                mock_file.filename = "test.py"
                mock_file.content_type = "text/x-python"
                async def mock_read():
                    return b"print('Hello, World!')"
                mock_file.read = mock_read
                
                # Create mock user and database session
                mock_user = Mock()
                mock_user.id = 123
                
                mock_db = Mock()
                mock_db.add = Mock()
                mock_db.commit = Mock()
                mock_db.refresh = Mock()
                
                # Mock the StoredFile model
                with patch('app.services.file_storage_service.StoredFile') as mock_stored_file:
                    mock_instance = Mock()
                    mock_instance.file_id = "test-file-id"
                    mock_instance.filename = "test.py"
                    mock_instance.file_size = 21
                    mock_instance.content_type = "text/x-python"
                    mock_instance.file_hash = "test-hash"
                    mock_instance.uploaded_at = datetime.utcnow()
                    
                    mock_stored_file.return_value = mock_instance
                    
                    # Test upload
                    result = await service.upload_file(mock_file, mock_user, mock_db)
                    
                    print(f"   ✅ Upload successful")
                    print(f"   ✅ File ID: {result.file_id}")
                    print(f"   ✅ Filename: {result.filename}")
                    print(f"   ✅ File size: {result.file_size} bytes")
                    print(f"   ✅ S3 put_object called: {mock_client.put_object.called}")
                    print(f"   ✅ Database add called: {mock_db.add.called}")
                    
                    return True
                    
        except Exception as e:
            print(f"❌ Mock upload workflow test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def run_all_tests():
    """Run all tests"""
    print("🧪 Running File Storage Service Tests")
    print("=" * 50)
    
    tests = [
        test_service_initialization,
        test_filename_sanitization,
        test_file_key_generation,
        test_file_hash_calculation,
        test_file_validation,
    ]
    
    async_tests = [
        test_mock_upload_workflow,
    ]
    
    passed = 0
    total = len(tests) + len(async_tests)
    
    # Run synchronous tests
    for test in tests:
        if test():
            passed += 1
    
    # Run asynchronous tests
    for test in async_tests:
        try:
            if asyncio.run(test()):
                passed += 1
        except Exception as e:
            print(f"❌ Async test failed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)