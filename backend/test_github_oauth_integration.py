"""
Test script for GitHub OAuth integration.

This script tests the GitHub OAuth flow and basic API functionality
to ensure the integration is working correctly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.github_service import GitHubService
from app.core.database import get_db_session


async def test_github_oauth_flow():
    """Test the GitHub OAuth authorization URL generation."""
    print("Testing GitHub OAuth integration...")
    
    # Test configuration
    print(f"GitHub Client ID configured: {'Yes' if settings.GITHUB_CLIENT_ID else 'No'}")
    print(f"GitHub Client Secret configured: {'Yes' if settings.GITHUB_CLIENT_SECRET else 'No'}")
    print(f"GitHub Redirect URI: {settings.GITHUB_OAUTH_REDIRECT_URI}")
    
    try:
        # Create a mock database session
        async with get_db_session() as db:
            github_service = GitHubService(db)
            
            # Test OAuth URL generation
            auth_url = await github_service.get_oauth_authorization_url("test_state")
            print(f"✓ OAuth authorization URL generated successfully")
            print(f"  URL: {auth_url}")
            
            # Verify URL contains required parameters
            assert "client_id=" in auth_url
            assert "redirect_uri=" in auth_url
            assert "scope=" in auth_url
            assert "state=test_state" in auth_url
            print("✓ OAuth URL contains all required parameters")
            
    except Exception as e:
        print(f"✗ OAuth URL generation failed: {e}")
        return False
    
    return True


async def test_github_service_initialization():
    """Test GitHub service initialization."""
    print("\nTesting GitHub service initialization...")
    
    try:
        async with get_db_session() as db:
            github_service = GitHubService(db)
            print("✓ GitHub service initialized successfully")
            
            # Check if GitHub client is available (requires private key)
            if github_service.github_client:
                print("✓ GitHub App client initialized")
            else:
                print("⚠ GitHub App client not initialized (private key not configured)")
            
            return True
            
    except Exception as e:
        print(f"✗ GitHub service initialization failed: {e}")
        return False


async def test_webhook_signature_verification():
    """Test webhook signature verification."""
    print("\nTesting webhook signature verification...")
    
    try:
        async with get_db_session() as db:
            github_service = GitHubService(db)
            
            # Test with mock data
            test_payload = b'{"test": "data"}'
            test_headers = {
                "X-Hub-Signature-256": "sha256=invalid_signature"
            }
            
            # This should return False for invalid signature
            is_valid = github_service._verify_webhook_signature(test_headers, test_payload)
            
            if not is_valid:
                print("✓ Webhook signature verification working (correctly rejected invalid signature)")
                return True
            else:
                print("✗ Webhook signature verification failed (accepted invalid signature)")
                return False
                
    except Exception as e:
        print(f"✗ Webhook signature verification test failed: {e}")
        return False


def print_configuration_guide():
    """Print configuration guide for GitHub integration."""
    print("\n" + "="*60)
    print("GitHub Integration Configuration Guide")
    print("="*60)
    
    print("\nTo complete the GitHub OAuth integration setup:")
    print("\n1. Create a GitHub OAuth App:")
    print("   - Go to GitHub Settings → Developer settings → OAuth Apps")
    print("   - Click 'New OAuth App'")
    print("   - Set Authorization callback URL to:")
    print(f"     {settings.GITHUB_OAUTH_REDIRECT_URI}")
    
    print("\n2. Add to your .env file:")
    print("   GITHUB_CLIENT_ID=your_oauth_client_id")
    print("   GITHUB_CLIENT_SECRET=your_oauth_client_secret")
    
    print("\n3. For GitHub App integration (optional):")
    print("   - Create a GitHub App in your GitHub settings")
    print("   - Generate and download a private key")
    print("   - Add to your .env file:")
    print("   GITHUB_APP_ID=your_app_id")
    print("   GITHUB_PRIVATE_KEY_PATH=/path/to/private-key.pem")
    print("   GITHUB_WEBHOOK_SECRET=your_webhook_secret")
    
    print("\n4. Test the integration:")
    print("   - Start your FastAPI server")
    print("   - Visit: http://localhost:8000/api/v1/github/oauth/authorize")
    print("   - Complete the OAuth flow")
    
    print("\nFor detailed setup instructions, see:")
    print("backend/GITHUB_INTEGRATION_SETUP.md")


async def main():
    """Run all GitHub integration tests."""
    print("GitHub OAuth Integration Test Suite")
    print("="*50)
    
    tests = [
        test_github_service_initialization,
        test_github_oauth_flow,
        test_webhook_signature_verification
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "="*50)
    print("Test Results Summary")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! GitHub OAuth integration is ready.")
    else:
        print("⚠ Some tests failed. Check configuration and dependencies.")
    
    print_configuration_guide()


if __name__ == "__main__":
    asyncio.run(main())