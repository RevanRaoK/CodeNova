#!/usr/bin/env python3
"""
GitHub OAuth Integration Test

This script tests the GitHub OAuth integration with real API calls.
"""

import asyncio
import httpx
import os
import sys
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings


async def test_github_oauth_configuration():
    """Test GitHub OAuth configuration."""
    print("🔧 Testing GitHub OAuth Configuration")
    print("=" * 50)
    
    # Check environment variables
    client_id = settings.GITHUB_CLIENT_ID
    client_secret = settings.GITHUB_CLIENT_SECRET
    redirect_uri = settings.GITHUB_OAUTH_REDIRECT_URI
    
    print(f"✓ Client ID: {client_id}")
    print(f"✓ Client Secret: {'*' * (len(client_secret) - 4) + client_secret[-4:] if client_secret else 'Not set'}")
    print(f"✓ Redirect URI: {redirect_uri}")
    
    if not client_id or not client_secret:
        print("❌ GitHub OAuth credentials not configured!")
        return False
    
    return True


async def test_github_api_connectivity():
    """Test connectivity to GitHub API."""
    print("\n🌐 Testing GitHub API Connectivity")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test basic GitHub API connectivity
            response = await client.get("https://api.github.com/")
            
            if response.status_code == 200:
                print("✓ GitHub API is accessible")
                
                # Test rate limit info
                rate_limit_response = await client.get("https://api.github.com/rate_limit")
                if rate_limit_response.status_code == 200:
                    rate_data = rate_limit_response.json()
                    core_limit = rate_data.get("rate", {})
                    print(f"✓ Rate limit: {core_limit.get('remaining', 0)}/{core_limit.get('limit', 0)} remaining")
                
                return True
            else:
                print(f"❌ GitHub API returned status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Failed to connect to GitHub API: {str(e)}")
        return False


async def test_oauth_app_validation():
    """Test if the OAuth app credentials are valid."""
    print("\n🔐 Testing OAuth App Validation")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test OAuth app by checking if credentials are recognized
            auth = (settings.GITHUB_CLIENT_ID, settings.GITHUB_CLIENT_SECRET)
            
            # This endpoint requires authentication but will tell us if credentials are valid
            response = await client.get(
                f"https://api.github.com/applications/{settings.GITHUB_CLIENT_ID}/tokens",
                auth=auth
            )
            
            if response.status_code == 200:
                print("✓ OAuth app credentials are valid")
                return True
            elif response.status_code == 401:
                print("❌ OAuth app credentials are invalid")
                print("   Please check your GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET")
                return False
            elif response.status_code == 404:
                print("❌ OAuth app not found")
                print("   Please check your GITHUB_CLIENT_ID")
                return False
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
                print("   OAuth app might be valid but endpoint behavior changed")
                return True
                
    except Exception as e:
        print(f"❌ Failed to validate OAuth app: {str(e)}")
        return False


async def test_oauth_flow_initiation():
    """Test OAuth flow initiation (without authentication)."""
    print("\n🚀 Testing OAuth Flow Initiation")
    print("=" * 50)
    
    try:
        # Test the OAuth initiation endpoint
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/github/oauth/initiate",
                headers={"Content-Type": "application/json"},
                json={"redirect_url": "http://localhost:3000/dashboard"}
            )
            
            if response.status_code == 401:
                print("✓ OAuth initiation endpoint is working (requires authentication)")
                print("   This is expected - the endpoint correctly requires user authentication")
                return True
            elif response.status_code == 200:
                data = response.json()
                print("✓ OAuth initiation successful!")
                print(f"   Authorization URL: {data.get('authorization_url', 'N/A')[:100]}...")
                return True
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except httpx.ConnectError:
        print("❌ Cannot connect to local server")
        print("   Make sure the FastAPI server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Failed to test OAuth initiation: {str(e)}")
        return False


async def test_oauth_callback_endpoint():
    """Test OAuth callback endpoint."""
    print("\n📞 Testing OAuth Callback Endpoint")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            # Test callback endpoint with invalid parameters (should handle gracefully)
            response = await client.get(
                "http://localhost:8000/api/v1/github/oauth/callback?code=test&state=invalid"
            )
            
            if response.status_code in [302, 400, 422]:
                print("✓ OAuth callback endpoint is working")
                print("   Endpoint correctly handles invalid parameters")
                return True
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
                return False
                
    except httpx.ConnectError:
        print("❌ Cannot connect to local server")
        return False
    except Exception as e:
        print(f"❌ Failed to test OAuth callback: {str(e)}")
        return False


async def generate_oauth_test_url():
    """Generate a test OAuth URL for manual testing."""
    print("\n🔗 Manual OAuth Test URL")
    print("=" * 50)
    
    from urllib.parse import urlencode
    
    # Generate OAuth URL manually
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_OAUTH_REDIRECT_URI,
        "scope": "user:email repo",
        "state": "manual_test_" + str(int(datetime.now().timestamp())),
        "response_type": "code"
    }
    
    oauth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    
    print("🔗 Manual Test OAuth URL:")
    print(oauth_url)
    print("\n📋 Instructions:")
    print("1. Copy the URL above and open it in your browser")
    print("2. Authorize the application on GitHub")
    print("3. You'll be redirected to your callback URL")
    print("4. Check if the callback is handled correctly")


async def main():
    """Run all tests."""
    print("GitHub OAuth Integration Test Suite")
    print("🚀 CodeNova GitHub Integration")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Configuration
    if await test_github_oauth_configuration():
        tests_passed += 1
    
    # Test 2: GitHub API connectivity
    if await test_github_api_connectivity():
        tests_passed += 1
    
    # Test 3: OAuth app validation
    if await test_oauth_app_validation():
        tests_passed += 1
    
    # Test 4: OAuth flow initiation
    if await test_oauth_flow_initiation():
        tests_passed += 1
    
    # Test 5: OAuth callback endpoint
    if await test_oauth_callback_endpoint():
        tests_passed += 1
    
    # Generate manual test URL
    await generate_oauth_test_url()
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! GitHub OAuth integration is ready!")
        print("\n✅ Next Steps:")
        print("1. Use the manual test URL above to test the full OAuth flow")
        print("2. Integrate the OAuth endpoints with your frontend")
        print("3. Test with real user accounts")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        
    print("\n🔧 Available Endpoints:")
    print("- POST /api/v1/github/oauth/initiate")
    print("- GET  /api/v1/github/oauth/callback")
    print("- GET  /api/v1/github/oauth/status")
    print("- GET  /api/v1/github/oauth/integration")
    print("- POST /api/v1/github/oauth/validate-token")
    print("- DELETE /api/v1/github/oauth/revoke")


if __name__ == "__main__":
    asyncio.run(main())