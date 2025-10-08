"""
Test script for Digital Ocean Spaces configuration and connectivity.

This script tests the Digital Ocean Spaces integration to ensure
files can be uploaded and retrieved properly.
"""

import asyncio
import os
import tempfile
from datetime import datetime
from fastapi import UploadFile
from io import BytesIO

from app.services.file_storage_service import file_storage_service, FileStorageError
from app.core.database import SessionLocal
from app.models.users import User


async def test_do_spaces_config():
    """Test Digital Ocean Spaces configuration."""
    print("=" * 60)
    print("DIGITAL OCEAN SPACES CONFIGURATION TEST")
    print("=" * 60)
    
    try:
        # Test configuration validation
        print("1. Testing configuration validation...")
        file_storage_service._validate_configuration()
        print("✓ Configuration validation passed")
        
        # Test client initialization
        print("\n2. Testing client initialization...")
        client = file_storage_service.client
        print("✓ S3 client initialized successfully")
        
        # Test bucket access
        print("\n3. Testing bucket access...")
        try:
            # Try to list objects in the bucket (this will test credentials and bucket access)
            response = client.list_objects_v2(
                Bucket=file_storage_service.bucket_name,
                MaxKeys=1
            )
            print(f"✓ Successfully accessed bucket: {file_storage_service.bucket_name}")
            print(f"  - Bucket exists and is accessible")
            print(f"  - Current object count: {response.get('KeyCount', 0)}")
            
        except Exception as e:
            print(f"✗ Bucket access failed: {e}")
            return False
        
        return True
        
    except FileStorageError as e:
        print(f"✗ Configuration error: {e.message}")
        print(f"  Error code: {e.error_code}")
        if e.details:
            print(f"  Details: {e.details}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


async def test_file_upload():
    """Test file upload functionality."""
    print("\n" + "=" * 60)
    print("FILE UPLOAD TEST")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Create a test user (or get existing one)
        test_user = db.query(User).first()
        if not test_user:
            print("✗ No test user found in database")
            print("  Please create a user account first")
            return False
        
        print(f"Using test user: {test_user.email} (ID: {test_user.id})")
        
        # Create a test file
        test_content = f"""
# Test File for Digital Ocean Spaces Upload
# Generated at: {datetime.now().isoformat()}

def hello_world():
    print("Hello from Digital Ocean Spaces!")
    return "Upload test successful"

if __name__ == "__main__":
    hello_world()
"""
        
        # Create a mock UploadFile
        test_filename = f"test_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        file_bytes = test_content.encode('utf-8')
        
        # Create a proper UploadFile mock
        class MockUploadFile:
            def __init__(self, filename, content_bytes, content_type="text/plain"):
                self.filename = filename
                self.content_type = content_type
                self._content = content_bytes
                self.size = len(content_bytes)
                print(f"DEBUG: MockUploadFile created with content type: {type(content_bytes)}")
            
            async def read(self):
                print(f"DEBUG: MockUploadFile.read() returning type: {type(self._content)}")
                return self._content
        
        mock_file = MockUploadFile(test_filename, file_bytes, "text/x-python")
        
        print(f"\n1. Uploading test file: {test_filename}")
        print(f"   File size: {len(file_bytes)} bytes")
        print(f"   Content type: {mock_file.content_type}")
        
        # Upload the file
        result = await file_storage_service.upload_file(
            file=mock_file,
            user=test_user,
            db=db,
            metadata={"test": True, "purpose": "configuration_test"}
        )
        
        print("✓ File uploaded successfully!")
        print(f"  - File ID: {result.file_id}")
        print(f"  - Spaces URL: {result.spaces_url}")
        print(f"  - File hash: {result.file_hash}")
        print(f"  - Upload time: {result.uploaded_at}")
        
        # Test file download
        print(f"\n2. Testing file download...")
        download_result = await file_storage_service.download_file(
            file_id=result.file_id,
            user=test_user,
            db=db
        )
        
        print("✓ File downloaded successfully!")
        print(f"  - Downloaded size: {download_result.file_size} bytes")
        print(f"  - Content matches: {download_result.content == file_bytes}")
        
        # Test signed URL generation
        print(f"\n3. Testing signed URL generation...")
        signed_url = await file_storage_service.generate_signed_url(
            file_id=result.file_id,
            user=test_user,
            db=db,
            expiration_hours=1
        )
        
        print("✓ Signed URL generated successfully!")
        print(f"  - URL length: {len(signed_url)} characters")
        print(f"  - URL starts with: {signed_url[:50]}...")
        
        # Test file info retrieval
        print(f"\n4. Testing file info retrieval...")
        file_info = await file_storage_service.get_file_info(
            file_id=result.file_id,
            user=test_user,
            db=db
        )
        
        print("✓ File info retrieved successfully!")
        print(f"  - Filename: {file_info['filename']}")
        print(f"  - Size: {file_info['file_size']} bytes")
        print(f"  - Content type: {file_info['content_type']}")
        
        # Clean up - delete the test file
        print(f"\n5. Cleaning up test file...")
        delete_success = await file_storage_service.delete_file(
            file_id=result.file_id,
            user=test_user,
            db=db
        )
        
        if delete_success:
            print("✓ Test file deleted successfully!")
        else:
            print("✗ Failed to delete test file")
        
        return True
        
    except FileStorageError as e:
        print(f"✗ File storage error: {e.message}")
        print(f"  Error code: {e.error_code}")
        if e.details:
            print(f"  Details: {e.details}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_file_list():
    """Test file listing functionality."""
    print("\n" + "=" * 60)
    print("FILE LISTING TEST")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Get test user
        test_user = db.query(User).first()
        if not test_user:
            print("✗ No test user found in database")
            return False
        
        print(f"Testing file listing for user: {test_user.email}")
        
        # List user files
        file_list = await file_storage_service.list_user_files(
            user=test_user,
            db=db,
            limit=10,
            offset=0
        )
        
        print("✓ File listing successful!")
        print(f"  - Total files: {file_list.total_count}")
        print(f"  - Total size: {file_list.total_size} bytes")
        print(f"  - Files in this page: {len(file_list.files)}")
        
        if file_list.files:
            print("\n  Recent files:")
            for i, file_info in enumerate(file_list.files[:3], 1):
                print(f"    {i}. {file_info['filename']} ({file_info['file_size']} bytes)")
        
        return True
        
    except Exception as e:
        print(f"✗ File listing error: {e}")
        return False
    finally:
        db.close()


async def main():
    """Run all tests."""
    print("Starting Digital Ocean Spaces integration tests...\n")
    
    # Test 1: Configuration
    config_ok = await test_do_spaces_config()
    
    if not config_ok:
        print("\n❌ Configuration test failed. Please check your .env file.")
        print("\nRequired environment variables:")
        print("- DO_SPACES_KEY")
        print("- DO_SPACES_SECRET") 
        print("- DO_SPACES_BUCKET")
        print("- DO_SPACES_ENDPOINT")
        return
    
    # Test 2: File operations
    upload_ok = await test_file_upload()
    
    # Test 3: File listing
    list_ok = await test_file_list()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Configuration Test: {'✓ PASS' if config_ok else '✗ FAIL'}")
    print(f"File Upload Test:   {'✓ PASS' if upload_ok else '✗ FAIL'}")
    print(f"File Listing Test:  {'✓ PASS' if list_ok else '✗ FAIL'}")
    
    if all([config_ok, upload_ok, list_ok]):
        print("\n🎉 All tests passed! Digital Ocean Spaces integration is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the configuration and try again.")


if __name__ == "__main__":
    asyncio.run(main())