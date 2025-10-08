#!/usr/bin/env python3
"""
Test script to verify Digital Ocean Spaces configuration and connectivity.

Run this script to test your Digital Ocean Spaces setup before using the file storage service.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_spaces_configuration():
    """Test Digital Ocean Spaces configuration and connectivity"""
    print("🔍 Testing Digital Ocean Spaces Configuration...")
    print("=" * 50)
    
    # Check required environment variables
    required_vars = {
        'DO_SPACES_KEY': os.getenv('DO_SPACES_KEY'),
        'DO_SPACES_SECRET': os.getenv('DO_SPACES_SECRET'),
        'DO_SPACES_BUCKET': os.getenv('DO_SPACES_BUCKET'),
        'DO_SPACES_REGION': os.getenv('DO_SPACES_REGION'),
        'DO_SPACES_ENDPOINT': os.getenv('DO_SPACES_ENDPOINT')
    }
    
    print("1. Environment Variables Check:")
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if var_value:
            # Mask sensitive values
            if 'SECRET' in var_name or 'KEY' in var_name:
                display_value = f"{var_value[:8]}..." if len(var_value) > 8 else "***"
            else:
                display_value = var_value
            print(f"   ✅ {var_name}: {display_value}")
        else:
            print(f"   ❌ {var_name}: Not set")
            missing_vars.append(var_name)
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set these variables in your .env file:")
        for var in missing_vars:
            print(f"   {var}=your_value_here")
        return False
    
    print("\n2. Client Initialization:")
    try:
        client = boto3.client(
            's3',
            region_name=required_vars['DO_SPACES_REGION'],
            endpoint_url=required_vars['DO_SPACES_ENDPOINT'],
            aws_access_key_id=required_vars['DO_SPACES_KEY'],
            aws_secret_access_key=required_vars['DO_SPACES_SECRET']
        )
        print("   ✅ S3 client initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize S3 client: {e}")
        return False
    
    print("\n3. Bucket Access Test:")
    try:
        # Test bucket access by listing objects (limit to 1)
        response = client.list_objects_v2(
            Bucket=required_vars['DO_SPACES_BUCKET'],
            MaxKeys=1
        )
        print(f"   ✅ Successfully accessed bucket: {required_vars['DO_SPACES_BUCKET']}")
        
        # Show bucket info
        object_count = response.get('KeyCount', 0)
        print(f"   📊 Bucket contains {object_count} objects (showing max 1)")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"   ❌ Bucket does not exist: {required_vars['DO_SPACES_BUCKET']}")
        elif error_code == 'AccessDenied':
            print(f"   ❌ Access denied to bucket: {required_vars['DO_SPACES_BUCKET']}")
        else:
            print(f"   ❌ Error accessing bucket: {error_code} - {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False
    
    print("\n4. Upload Test:")
    test_key = "test-connection/test-file.txt"
    test_content = "This is a test file to verify Digital Ocean Spaces connectivity."
    
    try:
        # Upload test file
        client.put_object(
            Bucket=required_vars['DO_SPACES_BUCKET'],
            Key=test_key,
            Body=test_content.encode('utf-8'),
            ContentType='text/plain'
        )
        print(f"   ✅ Successfully uploaded test file: {test_key}")
        
        # Download test file
        response = client.get_object(
            Bucket=required_vars['DO_SPACES_BUCKET'],
            Key=test_key
        )
        downloaded_content = response['Body'].read().decode('utf-8')
        
        if downloaded_content == test_content:
            print("   ✅ Successfully downloaded and verified test file")
        else:
            print("   ❌ Downloaded content doesn't match uploaded content")
            return False
        
        # Clean up test file
        client.delete_object(
            Bucket=required_vars['DO_SPACES_BUCKET'],
            Key=test_key
        )
        print("   ✅ Successfully cleaned up test file")
        
    except ClientError as e:
        print(f"   ❌ Upload test failed: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"   ❌ Upload test failed with unexpected error: {e}")
        return False
    
    print("\n5. URL Generation Test:")
    try:
        # Test signed URL generation
        signed_url = client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': required_vars['DO_SPACES_BUCKET'],
                'Key': 'test-url-generation'
            },
            ExpiresIn=3600
        )
        print("   ✅ Successfully generated signed URL")
        print(f"   🔗 URL format: {signed_url[:50]}...")
        
    except Exception as e:
        print(f"   ❌ Failed to generate signed URL: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Digital Ocean Spaces is properly configured.")
    print("\nYour file storage service should work correctly.")
    return True

def show_configuration_help():
    """Show help for configuring Digital Ocean Spaces"""
    print("\n📋 Digital Ocean Spaces Configuration Help:")
    print("=" * 50)
    print("1. Create a Space in Digital Ocean Console:")
    print("   - Go to https://cloud.digitalocean.com/spaces")
    print("   - Click 'Create a Space'")
    print("   - Choose a region and unique name")
    print("   - Set File Listing to 'Restricted'")
    
    print("\n2. Generate API Keys:")
    print("   - Go to API section in Digital Ocean Console")
    print("   - Click 'Spaces Keys' tab")
    print("   - Generate new key pair")
    
    print("\n3. Set Environment Variables in .env file:")
    print("   DO_SPACES_KEY=your_access_key_id")
    print("   DO_SPACES_SECRET=your_secret_access_key")
    print("   DO_SPACES_BUCKET=your-space-name")
    print("   DO_SPACES_REGION=your-region  # e.g., nyc3, sfo3, ams3")
    print("   DO_SPACES_ENDPOINT=https://your-region.digitaloceanspaces.com")
    
    print("\n4. Optional Settings:")
    print("   MAX_FILE_SIZE_MB=50")
    print("   SIGNED_URL_EXPIRATION_HOURS=24")
    print("   FILE_UPLOAD_PATH=uploads/")

if __name__ == "__main__":
    print("Digital Ocean Spaces Connection Test")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found in current directory")
        print("Please create a .env file with your Digital Ocean Spaces configuration.")
        show_configuration_help()
        sys.exit(1)
    
    # Run the test
    success = test_spaces_configuration()
    
    if not success:
        print("\n❌ Configuration test failed!")
        show_configuration_help()
        sys.exit(1)
    else:
        print("\n✅ Configuration test successful!")
        sys.exit(0)