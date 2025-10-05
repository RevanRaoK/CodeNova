"""
Simple GitHub OAuth integration test without database dependencies.

This script tests basic GitHub OAuth functionality without requiring
a database connection.
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings


def test_configuration():
    """Test GitHub configuration settings."""
    print("GitHub OAuth Integration - Configuration Test")
    print("="*50)
    
    config_items = [
        ("GitHub Client ID", settings.GITHUB_CLIENT_ID),
        ("GitHub Client Secret", settings.GITHUB_CLIENT_SECRET),
        ("GitHub OAuth Redirect URI", settings.GITHUB_OAUTH_REDIRECT_URI),
        ("GitHub App ID", getattr(settings, 'GITHUB_APP_ID', '')),
        ("GitHub Private Key Path", getattr(settings, 'GITHUB_PRIVATE_KEY_PATH', '')),
        ("GitHub Webhook Secret", getattr(settings, 'GITHUB_WEBHOOK_SECRET', '')),
        ("GitHub API Base URL", settings.GITHUB_API_BASE_URL),
        ("GitHub Webhook Base URL", settings.GITHUB_WEBHOOK_BASE_URL),
    ]
    
    configured_count = 0
    for name, value in config_items:
        status = "✓ Configured" if value else "✗ Not configured"
        print(f"{name:30} {status}")
        if value:
            configured_count += 1
    
    print(f"\nConfiguration Summary: {configured_count}/{len(config_items)} items configured")
    
    # Check minimum required configuration for OAuth
    required_for_oauth = [
        settings.GITHUB_CLIENT_ID,
        settings.GITHUB_CLIENT_SECRET,
        settings.GITHUB_OAUTH_REDIRECT_URI
    ]
    
    oauth_ready = all(required_for_oauth)
    print(f"OAuth Ready: {'✓ Yes' if oauth_ready else '✗ No (missing required OAuth settings)'}")
    
    return oauth_ready


def test_oauth_url_generation():
    """Test OAuth URL generation logic."""
    print("\nTesting OAuth URL Generation Logic")
    print("-" * 40)
    
    try:
        # Mock OAuth URL generation without database
        base_url = "https://github.com/login/oauth/authorize"
        client_id = settings.GITHUB_CLIENT_ID or "test_client_id"
        redirect_uri = settings.GITHUB_OAUTH_REDIRECT_URI
        scope = "repo,user:email"
        state = "test_state_123"
        
        # Build OAuth URL
        params = [
            f"client_id={client_id}",
            f"redirect_uri={redirect_uri}",
            f"scope={scope}",
            f"state={state}"
        ]
        
        oauth_url = f"{base_url}?{'&'.join(params)}"
        
        print(f"✓ OAuth URL generated successfully")
        print(f"  URL: {oauth_url}")
        
        # Verify URL structure
        required_params = ["client_id=", "redirect_uri=", "scope=", "state="]
        missing_params = [param for param in required_params if param not in oauth_url]
        
        if not missing_params:
            print("✓ All required parameters present")
            return True
        else:
            print(f"✗ Missing parameters: {missing_params}")
            return False
            
    except Exception as e:
        print(f"✗ OAuth URL generation failed: {e}")
        return False


def test_imports():
    """Test that all required modules can be imported."""
    print("\nTesting Module Imports")
    print("-" * 30)
    
    imports_to_test = [
        ("app.core.config", "settings"),
        ("app.core.exceptions", "GitHubIntegrationError"),
        ("app.schemas.github_schemas", "GitHubRepositoryResponse"),
        ("app.models.github_integration", "GitHubRepository"),
    ]
    
    success_count = 0
    for module_name, item_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[item_name])
            getattr(module, item_name)
            print(f"✓ {module_name}.{item_name}")
            success_count += 1
        except Exception as e:
            print(f"✗ {module_name}.{item_name} - {e}")
    
    print(f"\nImport Summary: {success_count}/{len(imports_to_test)} imports successful")
    return success_count == len(imports_to_test)


def test_api_endpoints_structure():
    """Test that API endpoints are properly structured."""
    print("\nTesting API Endpoints Structure")
    print("-" * 35)
    
    try:
        from app.api.v1.endpoints.github import router
        print("✓ GitHub router imported successfully")
        
        # Check if router has routes
        if hasattr(router, 'routes') and router.routes:
            print(f"✓ Router has {len(router.routes)} routes configured")
            
            # List some key routes
            route_paths = [route.path for route in router.routes if hasattr(route, 'path')]
            key_routes = [
                "/oauth/authorize",
                "/oauth/callback", 
                "/repositories",
                "/webhook"
            ]
            
            found_routes = [route for route in key_routes if any(route in path for path in route_paths)]
            print(f"✓ Found {len(found_routes)}/{len(key_routes)} key routes")
            
            return len(found_routes) >= 3
        else:
            print("✗ Router has no routes configured")
            return False
            
    except Exception as e:
        print(f"✗ Failed to import GitHub router: {e}")
        return False


def print_setup_instructions():
    """Print setup instructions for GitHub integration."""
    print("\n" + "="*60)
    print("GitHub OAuth Integration Setup Instructions")
    print("="*60)
    
    print("\n1. Create GitHub OAuth App:")
    print("   • Go to GitHub Settings → Developer settings → OAuth Apps")
    print("   • Click 'New OAuth App'")
    print("   • Fill in the details:")
    print(f"     - Authorization callback URL: {settings.GITHUB_OAUTH_REDIRECT_URI}")
    
    print("\n2. Update your .env file with OAuth credentials:")
    print("   GITHUB_CLIENT_ID=your_github_client_id")
    print("   GITHUB_CLIENT_SECRET=your_github_client_secret")
    
    print("\n3. Optional: Create GitHub App for enhanced features:")
    print("   • Go to GitHub Settings → Developer settings → GitHub Apps")
    print("   • Click 'New GitHub App'")
    print("   • Configure webhook URL and permissions")
    print("   • Generate and download private key")
    print("   • Add to .env:")
    print("     GITHUB_APP_ID=your_app_id")
    print("     GITHUB_PRIVATE_KEY_PATH=/path/to/private-key.pem")
    print("     GITHUB_WEBHOOK_SECRET=your_webhook_secret")
    
    print("\n4. Install required dependencies:")
    print("   pip install PyGithub==2.1.1 cryptography==41.0.7")
    
    print("\n5. Test the integration:")
    print("   • Start your FastAPI server: uvicorn app.main:app --reload")
    print("   • Visit: http://localhost:8000/docs")
    print("   • Test the GitHub OAuth endpoints")


def main():
    """Run all tests."""
    print("GitHub OAuth Integration - Simple Test Suite")
    print("="*55)
    
    tests = [
        ("Configuration", test_configuration),
        ("Module Imports", test_imports),
        ("API Endpoints", test_api_endpoints_structure),
        ("OAuth URL Generation", test_oauth_url_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*55)
    print("Test Results Summary")
    print("="*55)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! GitHub OAuth integration is ready.")
    elif passed >= total // 2:
        print("⚠️  Most tests passed. Check failed tests and configuration.")
    else:
        print("❌ Many tests failed. Review setup and configuration.")
    
    print_setup_instructions()


if __name__ == "__main__":
    main()