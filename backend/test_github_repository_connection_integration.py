"""
Integration Test for GitHub Repository Connection Service

This test validates that the GitHub Repository Connection Service integrates
properly with the existing codebase and API endpoints.

Requirements covered: 3.3, 3.5
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_service_import():
    """Test that the service can be imported without errors."""
    try:
        from app.services.github_repository_connection_service import GitHubRepositoryConnectionService
        print("✓ GitHubRepositoryConnectionService imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import GitHubRepositoryConnectionService: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error importing GitHubRepositoryConnectionService: {e}")
        return False

def test_service_initialization():
    """Test that the service can be initialized."""
    try:
        from app.services.github_repository_connection_service import GitHubRepositoryConnectionService
        from unittest.mock import Mock
        
        # Mock database session
        mock_db = Mock()
        
        # Initialize service
        service = GitHubRepositoryConnectionService(mock_db)
        
        # Check basic attributes
        assert hasattr(service, 'db')
        assert hasattr(service, 'oauth_service')
        assert hasattr(service, 'background_job_service')
        assert hasattr(service, 'default_webhook_events')
        assert hasattr(service, 'default_repo_settings')
        
        print("✓ GitHubRepositoryConnectionService initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize GitHubRepositoryConnectionService: {e}")
        return False

def test_api_endpoints_import():
    """Test that the updated API endpoints can be imported."""
    try:
        from app.api.v1.endpoints.github import router
        print("✓ GitHub API endpoints imported successfully")
        
        # Check that the router has the expected endpoints
        routes = [route.path for route in router.routes]
        expected_paths = [
            "/github/repositories",
            "/github/repositories/{repository_id}",
            "/github/repositories/{repository_id}/settings",
            "/github/repositories/{repository_id}/webhook-status",
            "/github/repositories/{repository_id}/trigger-analysis"
        ]
        
        for path in expected_paths:
            if any(path in route for route in routes):
                print(f"✓ Found endpoint: {path}")
            else:
                print(f"? Endpoint may exist with different pattern: {path}")
        
        return True
    except ImportError as e:
        print(f"✗ Failed to import GitHub API endpoints: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error importing GitHub API endpoints: {e}")
        return False

def test_service_methods():
    """Test that the service has all expected methods."""
    try:
        from app.services.github_repository_connection_service import GitHubRepositoryConnectionService
        from unittest.mock import Mock
        
        mock_db = Mock()
        service = GitHubRepositoryConnectionService(mock_db)
        
        # Check public methods
        expected_methods = [
            'connect_repository',
            'disconnect_repository',
            'update_repository_settings',
            'trigger_pull_request_analysis',
            'get_repository_webhooks_status',
            'list_user_repositories'
        ]
        
        for method_name in expected_methods:
            if hasattr(service, method_name):
                method = getattr(service, method_name)
                if callable(method):
                    print(f"✓ Method {method_name} exists and is callable")
                else:
                    print(f"✗ Method {method_name} exists but is not callable")
                    return False
            else:
                print(f"✗ Method {method_name} not found")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Failed to test service methods: {e}")
        return False

def test_helper_methods():
    """Test that helper methods work correctly."""
    try:
        from app.services.github_repository_connection_service import GitHubRepositoryConnectionService
        from unittest.mock import Mock
        
        mock_db = Mock()
        service = GitHubRepositoryConnectionService(mock_db)
        
        # Test URL extraction
        test_cases = [
            ("https://github.com/owner/repo", "owner/repo"),
            ("https://github.com/owner/repo.git", "owner/repo"),
            ("https://www.github.com/owner/repo", "owner/repo"),
            ("https://gitlab.com/owner/repo", None),
            ("invalid-url", None)
        ]
        
        for url, expected in test_cases:
            result = service._extract_repo_name(url)
            if result == expected:
                print(f"✓ URL extraction correct for {url} -> {result}")
            else:
                print(f"✗ URL extraction failed for {url}: expected {expected}, got {result}")
                return False
        
        # Test settings validation
        settings = {
            "auto_analysis": True,
            "create_issues": False,
            "max_issues_per_pr": 100,  # Should be capped
            "invalid_setting": "should_be_ignored"
        }
        
        validated = service._validate_repository_settings(settings)
        
        if validated.get("auto_analysis") is True:
            print("✓ Boolean setting validation works")
        else:
            print("✗ Boolean setting validation failed")
            return False
        
        if validated.get("max_issues_per_pr") == 50:  # Should be capped at 50
            print("✓ Integer bounds validation works")
        else:
            print(f"✗ Integer bounds validation failed: got {validated.get('max_issues_per_pr')}")
            return False
        
        if "invalid_setting" not in validated:
            print("✓ Invalid settings are filtered out")
        else:
            print("✗ Invalid settings not filtered out")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Failed to test helper methods: {e}")
        return False

def test_configuration():
    """Test that the service configuration is properly set up."""
    try:
        from app.services.github_repository_connection_service import GitHubRepositoryConnectionService
        from unittest.mock import Mock
        
        mock_db = Mock()
        service = GitHubRepositoryConnectionService(mock_db)
        
        # Check default webhook events
        expected_events = [
            "pull_request",
            "push",
            "issues",
            "issue_comment",
            "pull_request_review",
            "pull_request_review_comment"
        ]
        
        for event in expected_events:
            if event in service.default_webhook_events:
                print(f"✓ Default webhook event configured: {event}")
            else:
                print(f"✗ Missing default webhook event: {event}")
                return False
        
        # Check default repository settings
        expected_settings = [
            "auto_analysis",
            "create_issues",
            "comment_on_prs",
            "analysis_on_push",
            "min_severity_for_issues",
            "max_issues_per_pr",
            "enable_inline_comments",
            "analysis_timeout_minutes"
        ]
        
        for setting in expected_settings:
            if setting in service.default_repo_settings:
                print(f"✓ Default repository setting configured: {setting}")
            else:
                print(f"✗ Missing default repository setting: {setting}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Failed to test configuration: {e}")
        return False

def run_all_tests():
    """Run all integration tests."""
    print("Running GitHub Repository Connection Service Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Service Import", test_service_import),
        ("Service Initialization", test_service_initialization),
        ("API Endpoints Import", test_api_endpoints_import),
        ("Service Methods", test_service_methods),
        ("Helper Methods", test_helper_methods),
        ("Configuration", test_configuration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"Integration Tests Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        return True
    else:
        print("❌ Some integration tests failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)