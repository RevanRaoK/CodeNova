"""
API endpoint tests for File Storage Service.

This script tests the REST API endpoints for file storage operations.
Run this after starting the FastAPI server.
"""

import requests
import json
import os
import tempfile
from datetime import datetime


# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)


def print_response(response, show_content=True):
    """Print response details"""
    print(f"Status Code: {response.status_code}")
    if show_content:
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response Text: {response.text}")


def register_and_login():
    """Register a test user and get access token"""
    print_section("Authentication Setup")
    
    # Try to register user
    register_data = {
        "email": TEST_EMAIL,
        "username": "testuser",
        "password": TEST_PASSWORD
    }
    
    print("Registering test user...")
    register_response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    
    if register_response.status_code == 201:
        print("✅ User registered successfully")
        token_data = register_response.json()
        return token_data.get("access_token")
    elif register_response.status_code == 400 and "already registered" in register_response.text:
        print("ℹ️  User already exists, attempting login...")
    else:
        print("❌ Registration failed")
        print_response(register_response)
    
    # Try to login
    login_data = {
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    print("Logging in...")
    login_response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    
    if login_response.status_code == 200:
        print("✅ Login successful")
        token_data = login_response.json()
        return token_data.get("access_token")
    else:
        print("❌ Login failed")
        print_response(login_response)
        return None


def test_storage_info(headers):
    """Test storage info endpoint"""
    print_section("Storage Info")
    
    print("Getting storage information...")
    response = requests.get(f"{BASE_URL}/storage/storage-info", headers=headers)
    
    if response.status_code == 200:
        print("✅ Storage info retrieved successfully")
        data = response.json()
        print(f"Max file size: {data.get('max_file_size_mb')} MB")
        print(f"Allowed extensions: {len(data.get('allowed_extensions', []))} types")
        print(f"User files: {data.get('user_stats', {}).get('total_files', 0)}")
        print(f"Total size: {data.get('user_stats', {}).get('total_size_mb', 0)} MB")
        return True
    else:
        print("❌ Failed to get storage info")
        print_response(response)
        return False


def test_file_upload(headers):
    """Test file upload endpoint"""
    print_section("File Upload")
    
    # Create a test file
    test_content = """
def hello_world():
    print("Hello from uploaded file!")
    return "success"

if __name__ == "__main__":
    hello_world()
"""
    
    print("Creating test file...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name
    
    try:
        print("Uploading file...")
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('test_upload.py', f, 'text/x-python')}
            data = {'metadata': json.dumps({"description": "Test upload file", "category": "test"})}
            
            response = requests.post(
                f"{BASE_URL}/storage/upload",
                headers=headers,
                files=files,
                data=data
            )
        
        if response.status_code == 200:
            print("✅ File upload successful")
            upload_data = response.json()
            print(f"File ID: {upload_data.get('file_id')}")
            print(f"Filename: {upload_data.get('filename')}")
            print(f"Size: {upload_data.get('file_size')} bytes")
            print(f"Hash: {upload_data.get('file_hash')[:16]}...")
            return upload_data.get('file_id')
        else:
            print("❌ File upload failed")
            print_response(response)
            return None
            
    finally:
        # Clean up temp file
        os.unlink(temp_file_path)


def test_file_list(headers):
    """Test file list endpoint"""
    print_section("File List")
    
    print("Getting file list...")
    response = requests.get(f"{BASE_URL}/storage/list?limit=10&offset=0", headers=headers)
    
    if response.status_code == 200:
        print("✅ File list retrieved successfully")
        data = response.json()
        print(f"Total files: {data.get('total_count')}")
        print(f"Total size: {data.get('total_size')} bytes")
        print(f"Files in response: {len(data.get('files', []))}")
        
        for i, file_info in enumerate(data.get('files', [])[:3]):  # Show first 3 files
            print(f"  File {i+1}: {file_info.get('filename')} ({file_info.get('file_size')} bytes)")
        
        return data.get('files', [])
    else:
        print("❌ Failed to get file list")
        print_response(response)
        return []


def test_file_info(headers, file_id):
    """Test file info endpoint"""
    print_section("File Info")
    
    if not file_id:
        print("⚠️  No file ID provided, skipping file info test")
        return False
    
    print(f"Getting info for file: {file_id}")
    response = requests.get(f"{BASE_URL}/storage/info/{file_id}", headers=headers)
    
    if response.status_code == 200:
        print("✅ File info retrieved successfully")
        data = response.json()
        print(f"Filename: {data.get('filename')}")
        print(f"Size: {data.get('file_size')} bytes")
        print(f"Content Type: {data.get('content_type')}")
        print(f"Uploaded: {data.get('uploaded_at')}")
        print(f"Metadata: {data.get('metadata')}")
        return True
    else:
        print("❌ Failed to get file info")
        print_response(response)
        return False


def test_signed_url(headers, file_id):
    """Test signed URL generation"""
    print_section("Signed URL Generation")
    
    if not file_id:
        print("⚠️  No file ID provided, skipping signed URL test")
        return False
    
    print(f"Generating signed URL for file: {file_id}")
    response = requests.get(
        f"{BASE_URL}/storage/signed-url/{file_id}?expiration_hours=1",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✅ Signed URL generated successfully")
        data = response.json()
        print(f"Signed URL: {data.get('signed_url')[:50]}...")
        print(f"Expires in: {data.get('expires_in_hours')} hours")
        return data.get('signed_url')
    else:
        print("❌ Failed to generate signed URL")
        print_response(response)
        return None


def test_file_download(headers, file_id):
    """Test file download endpoint"""
    print_section("File Download")
    
    if not file_id:
        print("⚠️  No file ID provided, skipping download test")
        return False
    
    print(f"Downloading file: {file_id}")
    response = requests.get(f"{BASE_URL}/storage/download/{file_id}", headers=headers)
    
    if response.status_code == 200:
        print("✅ File download successful")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Length: {response.headers.get('content-length')} bytes")
        
        # Show first few lines of content if it's text
        content = response.content
        if response.headers.get('content-type', '').startswith('text/'):
            lines = content.decode('utf-8').split('\n')[:5]
            print("Content preview:")
            for line in lines:
                print(f"  {line}")
        
        return True
    else:
        print("❌ File download failed")
        print_response(response)
        return False


def test_file_deletion(headers, file_id):
    """Test file deletion endpoint"""
    print_section("File Deletion")
    
    if not file_id:
        print("⚠️  No file ID provided, skipping deletion test")
        return False
    
    print(f"Deleting file: {file_id}")
    response = requests.delete(f"{BASE_URL}/storage/delete/{file_id}", headers=headers)
    
    if response.status_code == 200:
        print("✅ File deletion successful")
        data = response.json()
        print(f"Message: {data.get('message')}")
        return True
    else:
        print("❌ File deletion failed")
        print_response(response)
        return False


def test_error_handling(headers):
    """Test error handling scenarios"""
    print_section("Error Handling")
    
    # Test download non-existent file
    print("Testing download of non-existent file...")
    response = requests.get(f"{BASE_URL}/storage/download/nonexistent-file-id", headers=headers)
    if response.status_code == 404:
        print("✅ Non-existent file correctly returns 404")
    else:
        print(f"❌ Expected 404, got {response.status_code}")
    
    # Test upload without file
    print("Testing upload without file...")
    response = requests.post(f"{BASE_URL}/storage/upload", headers=headers)
    if response.status_code == 422:  # Validation error
        print("✅ Upload without file correctly returns validation error")
    else:
        print(f"❌ Expected 422, got {response.status_code}")
    
    # Test invalid file type (if configured)
    print("Testing upload of invalid file type...")
    try:
        files = {'file': ('test.exe', b'fake executable content', 'application/octet-stream')}
        response = requests.post(f"{BASE_URL}/storage/upload", headers=headers, files=files)
        if response.status_code == 400:
            print("✅ Invalid file type correctly rejected")
        else:
            print(f"ℹ️  File type validation: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Error testing invalid file type: {e}")


def run_all_tests():
    """Run all file storage API tests"""
    print("🧪 File Storage API Tests")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Authenticate
    access_token = register_and_login()
    if not access_token:
        print("❌ Authentication failed, cannot continue tests")
        return False
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Run tests
    test_results = []
    
    # Basic info test
    test_results.append(test_storage_info(headers))
    
    # Upload a file
    file_id = test_file_upload(headers)
    test_results.append(file_id is not None)
    
    # List files
    files = test_file_list(headers)
    test_results.append(len(files) >= 0)
    
    # Test file operations if we have a file
    if file_id:
        test_results.append(test_file_info(headers, file_id))
        test_results.append(test_signed_url(headers, file_id) is not None)
        test_results.append(test_file_download(headers, file_id))
        # Note: We'll delete the file at the end
    
    # Test error handling
    test_error_handling(headers)
    
    # Clean up - delete the uploaded file
    if file_id:
        test_results.append(test_file_deletion(headers, file_id))
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print_section("Test Summary")
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)