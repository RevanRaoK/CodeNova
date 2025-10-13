"""
Tests for GitHub API Rate Limiting and Error Handling

This test suite verifies the implementation of exponential backoff, retry logic,
and comprehensive error handling for GitHub API interactions.

Requirements covered: 3.7, 5.3, 5.5
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import httpx
from github import GithubException

from app.services.github_api_client import (
    GitHubAPIClient, 
    GitHubErrorType, 
    RateLimitInfo, 
    RetryConfig,
    create_github_api_client
)
from app.core.exceptions import GitHubIntegrationError


class TestGitHubAPIClient:
    """Test GitHub API client rate limiting and error handling."""
    
    @pytest.fixture
    def retry_config(self):
        """Create test retry configuration."""
        return RetryConfig(
            max_retries=2,
            base_delay=0.1,  # Fast for testing
            max_delay=1.0,
            exponential_base=2.0,
            jitter=False  # Disable jitter for predictable tests
        )
    
    @pytest.fixture
    def api_client(self, retry_config):
        """Create test API client."""
        return GitHubAPIClient(
            access_token="test_token",
            retry_config=retry_config,
            enable_rate_limit_handling=True
        )
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_calculation(self, api_client):
        """Test exponential backoff delay calculation."""
        # Test delay calculation for different attempts
        delay_0 = api_client._calculate_retry_delay(0)
        delay_1 = api_client._calculate_retry_delay(1)
        delay_2 = api_client._calculate_retry_delay(2)
        
        assert delay_0 == 0.1  # base_delay * (2^0) = 0.1
        assert delay_1 == 0.2  # base_delay * (2^1) = 0.2
        assert delay_2 == 0.4  # base_delay * (2^2) = 0.4
        
        # Test max delay cap
        delay_large = api_client._calculate_retry_delay(10)
        assert delay_large == 1.0  # Should be capped at max_delay
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, api_client):
        """Test rate limit detection and waiting."""
        # Mock rate limit info
        rate_limit = RateLimitInfo(
            limit=5000,
            remaining=0,  # No requests remaining
            reset_time=datetime.utcnow() + timedelta(seconds=0.2),
            used=5000,
            resource="core"
        )
        
        api_client._rate_limits["core"] = rate_limit
        
        # Mock operation that should wait for rate limit reset
        operation_called = False
        def test_operation():
            nonlocal operation_called
            operation_called = True
            return "success"
        
        start_time = datetime.utcnow()
        result = await api_client.execute_with_retry(
            test_operation,
            "test_operation",
            "core"
        )
        end_time = datetime.utcnow()
        
        # Should have waited for rate limit reset
        assert (end_time - start_time).total_seconds() >= 0.2
        assert result == "success"
        assert operation_called
    
    @pytest.mark.asyncio
    async def test_github_exception_categorization(self, api_client):
        """Test GitHub exception categorization."""
        # Test different error types
        auth_error = GithubException(401, {"message": "Bad credentials"}, {})
        assert api_client._categorize_github_error(auth_error) == GitHubErrorType.AUTHENTICATION
        
        rate_limit_error = GithubException(403, {"message": "API rate limit exceeded"}, {})
        assert api_client._categorize_github_error(rate_limit_error) == GitHubErrorType.RATE_LIMIT
        
        not_found_error = GithubException(404, {"message": "Not Found"}, {})
        assert api_client._categorize_github_error(not_found_error) == GitHubErrorType.NOT_FOUND
        
        server_error = GithubException(500, {"message": "Internal Server Error"}, {})
        assert api_client._categorize_github_error(server_error) == GitHubErrorType.SERVER_ERROR
    
    @pytest.mark.asyncio
    async def test_retry_logic_for_transient_failures(self, api_client):
        """Test retry logic for transient server errors."""
        call_count = 0
        
        def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise GithubException(500, {"message": "Server Error"}, {})
            return "success"
        
        result = await api_client.execute_with_retry(
            failing_operation,
            "failing_operation"
        )
        
        assert result == "success"
        assert call_count == 3  # Should retry twice before succeeding
    
    @pytest.mark.asyncio
    async def test_no_retry_for_auth_errors(self, api_client):
        """Test that authentication errors are not retried."""
        call_count = 0
        
        def auth_failing_operation():
            nonlocal call_count
            call_count += 1
            raise GithubException(401, {"message": "Bad credentials"}, {})
        
        with pytest.raises(GitHubIntegrationError) as exc_info:
            await api_client.execute_with_retry(
                auth_failing_operation,
                "auth_failing_operation"
            )
        
        assert "authentication failed" in str(exc_info.value).lower()
        assert call_count == 1  # Should not retry auth errors
    
    @pytest.mark.asyncio
    async def test_http_request_with_retry(self, api_client):
        """Test HTTP request retry logic."""
        with patch.object(api_client, '_http_client') as mock_client:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {
                'X-RateLimit-Limit': '5000',
                'X-RateLimit-Remaining': '4999',
                'X-RateLimit-Reset': str(int((datetime.utcnow() + timedelta(hours=1)).timestamp()))
            }
            mock_response.json.return_value = {"test": "data"}
            
            mock_client.request = AsyncMock(return_value=mock_response)
            
            response = await api_client.http_request_with_retry(
                "GET",
                "https://api.github.com/user"
            )
            
            assert response.status_code == 200
            mock_client.request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_http_request_rate_limit_handling(self, api_client):
        """Test HTTP request rate limit response handling."""
        with patch.object(api_client, '_http_client') as mock_client:
            # Mock rate limit response followed by success
            rate_limit_response = Mock()
            rate_limit_response.status_code = 429
            rate_limit_response.headers = {
                'X-RateLimit-Reset': str(int((datetime.utcnow() + timedelta(seconds=0.1)).timestamp())),
                'Retry-After': '1'
            }
            
            success_response = Mock()
            success_response.status_code = 200
            success_response.headers = {}
            success_response.json.return_value = {"test": "data"}
            
            mock_client.request = AsyncMock(side_effect=[rate_limit_response, success_response])
            
            start_time = datetime.utcnow()
            response = await api_client.http_request_with_retry(
                "GET",
                "https://api.github.com/user"
            )
            end_time = datetime.utcnow()
            
            assert response.status_code == 200
            assert mock_client.request.call_count == 2
            # Should have waited for rate limit
            assert (end_time - start_time).total_seconds() >= 0.1
    
    @pytest.mark.asyncio
    async def test_rate_limit_info_update(self, api_client):
        """Test rate limit information update from headers."""
        headers = {
            'X-RateLimit-Limit': '5000',
            'X-RateLimit-Remaining': '4999',
            'X-RateLimit-Reset': str(int((datetime.utcnow() + timedelta(hours=1)).timestamp())),
            'X-RateLimit-Used': '1'
        }
        
        api_client._update_rate_limit_from_headers(headers, "core")
        
        rate_limit = api_client._rate_limits.get("core")
        assert rate_limit is not None
        assert rate_limit.limit == 5000
        assert rate_limit.remaining == 4999
        assert rate_limit.used == 1
        assert rate_limit.resource == "core"
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_status(self, api_client):
        """Test getting rate limit status from GitHub API."""
        with patch.object(api_client, 'http_request_with_retry') as mock_request:
            mock_response = Mock()
            mock_response.json.return_value = {
                "resources": {
                    "core": {
                        "limit": 5000,
                        "remaining": 4999,
                        "reset": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
                        "used": 1
                    },
                    "search": {
                        "limit": 30,
                        "remaining": 29,
                        "reset": int((datetime.utcnow() + timedelta(minutes=1)).timestamp()),
                        "used": 1
                    }
                }
            }
            mock_request.return_value = mock_response
            
            rate_limits = await api_client.get_rate_limit_status()
            
            assert "core" in rate_limits
            assert "search" in rate_limits
            assert rate_limits["core"].limit == 5000
            assert rate_limits["search"].limit == 30
    
    @pytest.mark.asyncio
    async def test_client_cleanup(self, api_client):
        """Test proper cleanup of HTTP client."""
        with patch.object(api_client._http_client, 'aclose') as mock_close:
            await api_client.close()
            mock_close.assert_called_once()


class TestGitHubAPIIntegration:
    """Integration tests for GitHub API client with actual services."""
    
    @pytest.mark.asyncio
    async def test_create_github_api_client_factory(self):
        """Test GitHub API client factory function."""
        client = create_github_api_client(
            access_token="test_token",
            max_retries=5,
            enable_rate_limiting=True
        )
        
        assert client.access_token == "test_token"
        assert client.retry_config.max_retries == 5
        assert client.enable_rate_limit_handling is True
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_github_client_integration(self):
        """Test integration with PyGithub client."""
        client = GitHubAPIClient(access_token="test_token")
        
        # Should be able to get GitHub client
        github_client = client.get_github_client()
        assert github_client is not None
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_error_conversion(self):
        """Test error conversion from GitHub exceptions to application errors."""
        client = GitHubAPIClient(access_token="test_token")
        
        # Test authentication error conversion
        github_error = GithubException(401, {"message": "Bad credentials"}, {})
        app_error = client._convert_github_error(github_error, GitHubErrorType.AUTHENTICATION)
        
        assert isinstance(app_error, GitHubIntegrationError)
        assert "authentication failed" in str(app_error).lower()
        assert app_error.status_code == 401
        
        await client.close()


class TestRetryConfiguration:
    """Test retry configuration and behavior."""
    
    def test_retry_config_defaults(self):
        """Test default retry configuration values."""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
    
    def test_retry_config_custom_values(self):
        """Test custom retry configuration values."""
        config = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=1.5,
            jitter=False
        )
        
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 1.5
        assert config.jitter is False


if __name__ == "__main__":
    pytest.main([__file__])