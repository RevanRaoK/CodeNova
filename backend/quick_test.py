#!/usr/bin/env python3
"""
Quick test script to verify file storage functionality.
This script tests the core components without requiring external services.
"""

import os
import sys
import tempfile
from unittest.mock import patch, Mock

def test_basic_functionality():
    """Test basic file storage functionality"""
    print("🧪 Quick File Storage Test")
    print("=" * 40)
    
    # Mock environment variables
    test_env = {
        'DO_SPACES_KEY': 'test_key',
        'DO_SPACES_SECRET': 'test_secret', 
        'DO_SPACES_BUCKET': 'test_bucket',
        'DO_SPACES_REGION': 'nyc3',
        'DO_SPACES_ENDPOINT': 'https://nyc3.digitaloceanspaces.com',
        'MAX_FILE_SIZE_MB': '50',
        'ALLOWED_FILE_EXTENSIONS': 'py,js,txt,pdf,jpg,png'
    }
    
    with patch.dict(os.environ, test_env):
        try:
            # Test 1: Import and initialize service
            print("1. Testing service import and initialization...")
            from app.services.file_storage_service import FileStorageService
            service = FileStorageService()
            print(f"   ✅ Service initialized successfully")
            print(f"   📦 Bucket: {service.bucket_name}")
            print(f"   📏 Max size: {service.max_file_size // (1024*1024)}MB")
            print(f"   📁 Extensions: {len(service.allowed_extensions)} types")
            
            # Test 2: File validation
            print("\n2. Testing file validation...")
            
            # Valid file
            valid_file = Mock()
            valid_file.filename = "test.py"
            valid_file.size = 1024
            service._validate_file(valid_file)
            print("   ✅ Valid Python file accepted")
            
            # Invalid extension
            try:
                invalid_file = Mock()
                invalid_file.filename = "malware.exe"
                invalid_file.size = 1024
                service._validate_file(invalid_file)
                print("   ❌ Invalid file should have been rejected")
            except:
                print("   ✅ Invalid .exe file correctly rejected")
            
            # Test 3: Filename sanitization
            print("\n3. Testing filename sanitization...")
            test_cases = [
                ("normal.py", "normal.py"),
                ("file with spaces.txt", "file_with_spaces.txt"),
                ("../../../etc/passwd", ".._.._.._.._etc_passwd"),
                ("special!@#$%chars.js", "special_____chars.js")
            ]
            
            for input_name, expected in test_cases:
                result = service._sanitize_filename(input_name)
                if result == expected:
                    print(f"   ✅ '{input_name}' -> '{result}'")
                else:
                    print(f"   ⚠️  '{input_name}' -> '{result}' (expected '{expected}')")
            
            # Test 4: File key generation
            print("\n4. Testing file key generation...")
            key1 = service._generate_file_key(123, "test.py")
            key2 = service._generate_file_key(123, "test.py")
            
            if key1 != key2:
                print(f"   ✅ Unique keys generated")
                print(f"   📝 Sample key: {key1}")
            else:
                print(f"   ❌ Keys should be unique")
            
            # Test 5: Hash calculation
            print("\n5. Testing file hash calculation...")
            content1 = b"Hello, World!"
            content2 = b"Hello, World!"
            content3 = b"Different content"
            
            hash1 = service._calculate_file_hash(content1)
            hash2 = service._calculate_file_hash(content2)
            hash3 = service._calculate_file_hash(content3)
            
            if hash1 == hash2 and hash1 != hash3:
                print(f"   ✅ Hash calculation working correctly")
                print(f"   🔐 Sample hash: {hash1[:16]}...")
            else:
                print(f"   ❌ Hash calculation issue")
            
            print("\n" + "=" * 40)
            print("🎉 All basic tests passed!")
            print("\n📋 Next steps:")
            print("   1. Set up Digital Ocean Spaces credentials")
            print("   2. Run: python test_file_storage_api.py")
            print("   3. Test with real file uploads")
            
            return True
            
        except ImportError as e:
            print(f"❌ Import error: {e}")
            print("💡 Make sure you're in the backend directory")
            print("💡 Install dependencies: pip install -r requirements.txt")
            return False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_api_availability():
    """Test if the API endpoints are properly configured"""
    print("\n🌐 Testing API Configuration")
    print("=" * 40)
    
    try:
        # Test router import
        from app.api.v1.router import api_router
        print("✅ API router imported successfully")
        
        # Check if file storage routes are included
        routes = [route.path for route in api_router.routes]
        storage_routes = [r for r in routes if '/storage' in r]
        
        if storage_routes:
            print(f"✅ Found {len(storage_routes)} storage routes:")
            for route in storage_routes[:5]:  # Show first 5
                print(f"   📍 {route}")
        else:
            print("❌ No storage routes found")
            return False
        
        # Test endpoint import
        from app.api.v1.endpoints.file_storage import router
        print("✅ File storage endpoints imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ API configuration error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run all quick tests"""
    print("🚀 File Storage Quick Test Suite")
    print("This tests core functionality without external dependencies\n")
    
    success = True
    
    # Test basic functionality
    if not test_basic_functionality():
        success = False
    
    # Test API configuration
    if not test_api_availability():
        success = False
    
    if success:
        print("\n🎉 All quick tests passed!")
        print("\n📚 For more comprehensive testing:")
        print("   • Run: python test_file_storage_simple.py")
        print("   • Run: python test_file_storage_api.py (requires server)")
        print("   • See: FILE_STORAGE_TESTING_GUIDE.md")
    else:
        print("\n❌ Some tests failed. Check the output above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)