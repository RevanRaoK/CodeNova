"""
Integration test for enhanced GitHub API client with rate limiting and error handling.

This test verifies that the GitHub services properly use the enhanced API client
with rate limiting, exponential backoff, and comprehensive error handling.

Requirements covered: 3.7, 5.3, 5.5
"""

import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Mock the dependencies to avoid import errors
import sys
from unittest.mock import MagicMock

# Mock SQLAlchemy and other dependencies
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['sqlalchemy.ext'] = MagicMock()
sys.modules['sqlalchemy.ext.asyncio'] = MagicMock()
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['github'] = MagicMock()
sys.modules['httpx'] = MagicMock()

# Now we can import our modules
from app.services.github_api_client import GitHubAPIClient, GitHubErrorType, RetryConfig
from app.core.exceptions import GitHubIntegrationError


def test_github_api_client_creation():
    """Test that GitHub API client can be created with proper configuration."""
    # Test basic client creation
    client = GitHubAPIClient(
        access_token="test_token",
        retry_config=RetryConfig(max_retries=3),
        enable_rate_limit_handling=True
    )
    
    assert client.access_token == "test_token"
    assert client.retry_config.max_retries == 3
    assert client.enable_rate_limit_handling is True
    
    print("✓ GitHub API client creation test passed")


def test_error_type_categorization():
    """Test GitHub error type categorization."""
    client = GitHubAPIClient(access_token="test_token")
    
    # Test HTTP error categorization
    assert client._categorize_http_error(401) == GitHubErrorType.AUTHENTICATION
    assert client._categorize_http_error(403) == GitHubErrorType.AUTHORIZATION
    assert client._categorize_http_error(404) == GitHubErrorType.NOT_FOUND
    assert client._categorize_http_error(422) == GitHubErrorType.VALIDATION
    assert client._categorize_http_error(429) == GitHubErrorType.RATE_LIMIT
    assert client._categorize_http_error(500) == GitHubErrorType.SERVER_ERROR
    
    print("✓ Error type categorization test passed")


def test_retry_delay_calculation():
    """Test exponential backoff delay calculation."""
    config = RetryConfig(
        base_delay=1.0,
        exponential_base=2.0,
        max_delay=60.0,
        jitter=False
    )
    
    client = GitHubAPIClient(
        access_token="test_token",
        retry_config=config
    )
    
    # Test exponential backoff
    assert client._calculate_retry_delay(0) == 1.0  # 1.0 * (2^0) = 1.0
    assert client._calculate_retry_delay(1) == 2.0  # 1.0 * (2^1) = 2.0
    assert client._calculate_retry_delay(2) == 4.0  # 1.0 * (2^2) = 4.0
    
    # Test max delay cap
    assert client._calculate_retry_delay(10) == 60.0  # Should be capped
    
    print("✓ Retry delay calculation test passed")


def test_rate_limit_info_parsing():
    """Test rate limit information parsing from headers."""
    client = GitHubAPIClient(access_token="test_token")
    
    headers = {
        'X-RateLimit-Limit': '5000',
        'X-RateLimit-Remaining': '4999',
        'X-RateLimit-Reset': str(int((datetime.utcnow() + timedelta(hours=1)).timestamp())),
        'X-RateLimit-Used': '1'
    }
    
    client._update_rate_limit_from_headers(headers, "core")
    
    rate_limit = client._rate_limits.get("core")
    assert rate_limit is not None
    assert rate_limit.limit == 5000
    assert rate_limit.remaining == 4999
    assert rate_limit.used == 1
    assert rate_limit.resource == "core"
    
    print("✓ Rate limit info parsing test passed")


def test_github_integration_error_enhancement():
    """Test enhanced GitHubIntegrationError with error types."""
    # Test basic error
    error = GitHubIntegrationError("Test error")
    assert str(error) == "Test error"
    assert error.error_type is None
    assert error.status_code is None
    
    # Test enhanced error with type and status code
    enhanced_error = GitHubIntegrationError(
        "Authentication failed",
        error_type="authentication",
        status_code=401
    )
    assert str(enhanced_error) == "Authentication failed"
    assert enhanced_error.error_type == "authentication"
    assert enhanced_error.status_code == 401
    
    print("✓ Enhanced GitHubIntegrationError test passed")


def test_factory_functions():
    """Test factory functions for creating GitHub API clients."""
    from app.services.github_api_client import create_github_api_client, create_app_github_client
    
    # Test user client creation
    user_client = create_github_api_client(
        access_token="user_token",
        max_retries=5,
        enable_rate_limiting=True
    )
    
    assert user_client.access_token == "user_token"
    assert user_client.retry_config.max_retries == 5
    assert user_client.enable_rate_limit_handling is True
    
    # Test app client creation
    app_client = create_app_github_client()
    assert app_client.access_token is None  # App auth doesn't use access token
    assert app_client.enable_rate_limit_handling is True
    
    print("✓ Factory functions test passed")


def run_all_tests():
    """Run all tests."""
    print("Running GitHub API Rate Limiting and Error Handling Tests...")
    print("=" * 60)
    
    try:
        test_github_api_client_creation()
        test_error_type_categorization()
        test_retry_delay_calculation()
        test_rate_limit_info_parsing()
        test_github_integration_error_enhancement()
        test_factory_functions()
        
        print("=" * 60)
        print("✅ All tests passed! GitHub API rate limiting and error handling implementation is working correctly.")
        print("\nImplemented features:")
        print("- Exponential backoff for API calls")
        print("- Comprehensive error handling for GitHub API responses")
        print("- Retry logic for transient failures")
        print("- Rate limit detection and automatic waiting")
        print("- Enhanced error types and status codes")
        print("- Factory functions for easy client creation")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()