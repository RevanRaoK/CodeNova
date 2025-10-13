"""
GitHub API Client with Rate Limiting and Error Handling

This service provides a centralized GitHub API client with comprehensive rate limiting,
exponential backoff, retry logic, and error handling for all GitHub API interactions.

Requirements covered: 3.7, 5.3, 5.5
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, TypeVar, Union
from dataclasses import dataclass
from enum import Enum

import httpx
from github import Github, GithubException
from github.GithubRetry import GithubRetry
from github.Requester import Requester

from app.core.config import settings
from app.core.exceptions import GitHubIntegrationError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class GitHubErrorType(Enum):
    """GitHub API error types for categorized handling."""
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    VALIDATION = "validation"
    NETWORK = "network"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"


@dataclass
class RateLimitInfo:
    """Rate limit information from GitHub API."""
    limit: int
    remaining: int
    reset_time: datetime
    used: int
    resource: str = "core"


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


class GitHubAPIClient:
    """
    Enhanced GitHub API client with rate limiting, error handling, and retry logic.
    
    This client wraps both PyGithub and direct HTTP calls to provide:
    - Automatic rate limit handling with exponential backoff
    - Comprehensive error handling and categorization
    - Retry logic for transient failures
    - Request/response logging and monitoring
    
    Requirements covered: 3.7, 5.3, 5.5
    """
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None,
        enable_rate_limit_handling: bool = True
    ):
        print(f"DEBUG: GitHubAPIClient.__init__ called with token: {access_token[:10] if access_token else None}...")
        self.access_token = access_token
        self.retry_config = retry_config or RetryConfig()
        self.enable_rate_limit_handling = enable_rate_limit_handling
        
        # Rate limit tracking
        self._rate_limits: Dict[str, RateLimitInfo] = {}
        self._last_rate_limit_check = datetime.utcnow()
        
        print("DEBUG: About to create GitHub client...")
        # Initialize GitHub client with custom retry configuration
        self._github_client = self._create_github_client()
        print("DEBUG: GitHub client created")
        
        print("DEBUG: About to get default headers...")
        # HTTP client for direct API calls
        headers = self._get_default_headers()
        print(f"DEBUG: Headers: {headers}")
        
        print("DEBUG: About to create httpx client...")
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers=headers
        )
        print("DEBUG: httpx client created")
    
    def _create_github_client(self) -> Optional[Github]:
        """Create PyGithub client with custom retry configuration."""
        if not self.access_token:
            return None
        
        print(f"DEBUG: Creating GithubRetry with max_retries={self.retry_config.max_retries}")
        # Configure retry behavior for PyGithub
        retry = GithubRetry(
            total=self.retry_config.max_retries,
            backoff_factor=self.retry_config.base_delay,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"]
        )
        print(f"DEBUG: GithubRetry created: {retry}")
        
        print(f"DEBUG: Creating Github client with login_or_token={self.access_token[:10]}...")
        try:
            # PyGithub 2.x uses 'login_or_token' instead of 'auth'
            github_client = Github(
                login_or_token=self.access_token,
                retry=retry,
                per_page=100  # Optimize pagination
            )
            print(f"DEBUG: Github client created successfully: {github_client}")
            return github_client
        except Exception as e:
            print(f"DEBUG: Exception in Github constructor: {e}")
            raise
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for HTTP requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": f"CodeNova-GitHub-Integration/{settings.APP_VERSION or '1.0.0'}"
        }
        
        if self.access_token:
            headers["Authorization"] = f"token {self.access_token}"
        
        return headers
    
    async def execute_with_retry(
        self,
        operation: Callable[[], T],
        operation_name: str,
        resource_type: str = "core"
    ) -> T:
        """
        Execute GitHub API operation with retry logic and rate limit handling.
        
        Args:
            operation: Function to execute (GitHub API call)
            operation_name: Name of the operation for logging
            resource_type: GitHub API resource type (core, search, etc.)
            
        Returns:
            Result of the operation
            
        Raises:
            GitHubIntegrationError: If operation fails after all retries
        """
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # Check rate limits before making request
                if self.enable_rate_limit_handling:
                    await self._check_and_wait_for_rate_limit(resource_type)
                
                # Execute the operation
                start_time = time.time()
                result = operation()
                execution_time = time.time() - start_time
                
                logger.debug(f"GitHub API operation '{operation_name}' completed in {execution_time:.2f}s")
                
                # Update rate limit info if available
                await self._update_rate_limit_info(resource_type)
                
                return result
                
            except GithubException as e:
                last_exception = e
                error_type = self._categorize_github_error(e)
                
                logger.warning(
                    f"GitHub API operation '{operation_name}' failed (attempt {attempt + 1}): "
                    f"{error_type.value} - {e}"
                )
                
                # Handle specific error types
                if error_type == GitHubErrorType.RATE_LIMIT:
                    await self._handle_rate_limit_error(e, resource_type)
                    continue  # Retry after rate limit handling
                
                elif error_type in [GitHubErrorType.AUTHENTICATION, GitHubErrorType.AUTHORIZATION]:
                    # Don't retry auth errors
                    raise self._convert_github_error(e, error_type)
                
                elif error_type == GitHubErrorType.NOT_FOUND:
                    # Don't retry 404 errors
                    raise self._convert_github_error(e, error_type)
                
                elif error_type in [GitHubErrorType.SERVER_ERROR, GitHubErrorType.NETWORK]:
                    # Retry server errors and network issues
                    if attempt < self.retry_config.max_retries:
                        delay = self._calculate_retry_delay(attempt)
                        logger.info(f"Retrying '{operation_name}' in {delay:.2f}s...")
                        await asyncio.sleep(delay)
                        continue
                
                # For other errors, convert and raise
                raise self._convert_github_error(e, error_type)
                
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error in GitHub API operation '{operation_name}': {e}")
                
                # Retry unexpected errors
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"Retrying '{operation_name}' in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    continue
                
                raise GitHubIntegrationError(f"GitHub API operation failed: {e}")
        
        # If we get here, all retries failed
        if last_exception:
            if isinstance(last_exception, GithubException):
                error_type = self._categorize_github_error(last_exception)
                raise self._convert_github_error(last_exception, error_type)
            else:
                raise GitHubIntegrationError(f"GitHub API operation failed after {self.retry_config.max_retries} retries: {last_exception}")
        
        raise GitHubIntegrationError(f"GitHub API operation '{operation_name}' failed after all retries")
    
    async def http_request_with_retry(
        self,
        method: str,
        url: str,
        resource_type: str = "core",
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request to GitHub API with retry logic and rate limit handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            resource_type: GitHub API resource type
            **kwargs: Additional arguments for httpx request
            
        Returns:
            HTTP response
            
        Raises:
            GitHubIntegrationError: If request fails after all retries
        """
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # Check rate limits before making request
                if self.enable_rate_limit_handling:
                    await self._check_and_wait_for_rate_limit(resource_type)
                
                # Make the request
                start_time = time.time()
                response = await self._http_client.request(method, url, **kwargs)
                execution_time = time.time() - start_time
                
                logger.debug(f"GitHub HTTP {method} {url} completed in {execution_time:.2f}s (status: {response.status_code})")
                
                # Update rate limit info from response headers
                self._update_rate_limit_from_headers(response.headers, resource_type)
                
                # Handle rate limit responses
                if response.status_code == 429:
                    await self._handle_rate_limit_response(response, resource_type)
                    continue  # Retry after rate limit handling
                
                # Handle other error status codes
                if response.status_code >= 400:
                    error_type = self._categorize_http_error(response.status_code)
                    
                    if error_type in [GitHubErrorType.AUTHENTICATION, GitHubErrorType.AUTHORIZATION, GitHubErrorType.NOT_FOUND]:
                        # Don't retry these errors
                        raise self._convert_http_error(response, error_type)
                    
                    elif error_type == GitHubErrorType.SERVER_ERROR and attempt < self.retry_config.max_retries:
                        # Retry server errors
                        delay = self._calculate_retry_delay(attempt)
                        logger.info(f"Retrying {method} {url} in {delay:.2f}s...")
                        await asyncio.sleep(delay)
                        continue
                    
                    # Convert and raise error
                    raise self._convert_http_error(response, error_type)
                
                return response
                
            except httpx.RequestError as e:
                last_exception = e
                logger.warning(f"Network error for {method} {url} (attempt {attempt + 1}): {e}")
                
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"Retrying {method} {url} in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    continue
                
                raise GitHubIntegrationError(f"Network error: {e}")
            
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error for {method} {url}: {e}")
                
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"Retrying {method} {url} in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    continue
                
                raise GitHubIntegrationError(f"Unexpected error: {e}")
        
        # If we get here, all retries failed
        if last_exception:
            raise GitHubIntegrationError(f"HTTP request failed after {self.retry_config.max_retries} retries: {last_exception}")
        
        raise GitHubIntegrationError(f"HTTP request {method} {url} failed after all retries")
    
    async def get_rate_limit_status(self) -> Dict[str, RateLimitInfo]:
        """
        Get current rate limit status for all resources.

        Returns:
            Dictionary of rate limit information by resource type
        """
        try:
            # Make direct request without rate limit checking to avoid recursion
            response = await self._http_client.get("https://api.github.com/rate_limit")
            data = response.json()

            rate_limits = {}
            for resource, info in data.get("resources", {}).items():
                rate_limits[resource] = RateLimitInfo(
                    limit=info["limit"],
                    remaining=info["remaining"],
                    reset_time=datetime.fromtimestamp(info["reset"]),
                    used=info["used"],
                    resource=resource
                )

            self._rate_limits.update(rate_limits)
            return rate_limits

        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return self._rate_limits
    
    def get_github_client(self) -> Github:
        """
        Get PyGithub client instance.
        
        Returns:
            Configured PyGithub client
            
        Raises:
            GitHubIntegrationError: If no access token is configured
        """
        if not self._github_client:
            raise GitHubIntegrationError("GitHub client not initialized - access token required")
        
        return self._github_client
    
    async def close(self):
        """Close HTTP client connections."""
        await self._http_client.aclose()
    
    # Private helper methods
    
    def _categorize_github_error(self, error: GithubException) -> GitHubErrorType:
        """Categorize GitHub API error for appropriate handling."""
        if error.status == 401:
            return GitHubErrorType.AUTHENTICATION
        elif error.status == 403:
            if "rate limit" in str(error).lower():
                return GitHubErrorType.RATE_LIMIT
            return GitHubErrorType.AUTHORIZATION
        elif error.status == 404:
            return GitHubErrorType.NOT_FOUND
        elif error.status == 422:
            return GitHubErrorType.VALIDATION
        elif error.status >= 500:
            return GitHubErrorType.SERVER_ERROR
        else:
            return GitHubErrorType.UNKNOWN
    
    def _categorize_http_error(self, status_code: int) -> GitHubErrorType:
        """Categorize HTTP error status code."""
        if status_code == 401:
            return GitHubErrorType.AUTHENTICATION
        elif status_code == 403:
            return GitHubErrorType.AUTHORIZATION
        elif status_code == 404:
            return GitHubErrorType.NOT_FOUND
        elif status_code == 422:
            return GitHubErrorType.VALIDATION
        elif status_code == 429:
            return GitHubErrorType.RATE_LIMIT
        elif status_code >= 500:
            return GitHubErrorType.SERVER_ERROR
        else:
            return GitHubErrorType.UNKNOWN
    
    def _convert_github_error(self, error: GithubException, error_type: GitHubErrorType) -> GitHubIntegrationError:
        """Convert GitHub API error to application error."""
        error_messages = {
            GitHubErrorType.AUTHENTICATION: "GitHub authentication failed - invalid or expired token",
            GitHubErrorType.AUTHORIZATION: "GitHub authorization failed - insufficient permissions",
            GitHubErrorType.NOT_FOUND: "GitHub resource not found or access denied",
            GitHubErrorType.VALIDATION: f"GitHub API validation error: {error}",
            GitHubErrorType.RATE_LIMIT: "GitHub API rate limit exceeded",
            GitHubErrorType.SERVER_ERROR: f"GitHub API server error: {error}",
            GitHubErrorType.NETWORK: f"GitHub API network error: {error}",
            GitHubErrorType.UNKNOWN: f"GitHub API error: {error}"
        }
        
        message = error_messages.get(error_type, f"GitHub API error: {error}")
        return GitHubIntegrationError(message, error_type=error_type.value, status_code=error.status)
    
    def _convert_http_error(self, response: httpx.Response, error_type: GitHubErrorType) -> GitHubIntegrationError:
        """Convert HTTP error response to application error."""
        try:
            error_data = response.json()
            error_message = error_data.get("message", f"HTTP {response.status_code}")
        except:
            error_message = f"HTTP {response.status_code}"
        
        error_messages = {
            GitHubErrorType.AUTHENTICATION: "GitHub authentication failed - invalid or expired token",
            GitHubErrorType.AUTHORIZATION: "GitHub authorization failed - insufficient permissions",
            GitHubErrorType.NOT_FOUND: "GitHub resource not found or access denied",
            GitHubErrorType.VALIDATION: f"GitHub API validation error: {error_message}",
            GitHubErrorType.RATE_LIMIT: "GitHub API rate limit exceeded",
            GitHubErrorType.SERVER_ERROR: f"GitHub API server error: {error_message}",
            GitHubErrorType.UNKNOWN: f"GitHub API error: {error_message}"
        }
        
        message = error_messages.get(error_type, f"GitHub API error: {error_message}")
        return GitHubIntegrationError(message, error_type=error_type.value, status_code=response.status_code)
    
    async def _check_and_wait_for_rate_limit(self, resource_type: str):
        """Check rate limits and wait if necessary."""
        rate_limit = self._rate_limits.get(resource_type)

        if not rate_limit:
            # Get fresh rate limit info if we don't have it
            await self.get_rate_limit_status()
            rate_limit = self._rate_limits.get(resource_type)

        if rate_limit and rate_limit.remaining <= 1:
            # Calculate wait time until reset
            now = datetime.utcnow()
            if rate_limit.reset_time > now:
                wait_time = (rate_limit.reset_time - now).total_seconds() + 1
                logger.warning(f"Rate limit exceeded for {resource_type}. Waiting {wait_time:.1f}s until reset...")
                await asyncio.sleep(wait_time)

                # Refresh rate limit info after waiting
                await self.get_rate_limit_status()

    async def _handle_rate_limit_error(self, error: GithubException, resource_type: str):
        """Handle rate limit error with appropriate waiting."""
        # Try to extract reset time from error
        reset_time = None
        if hasattr(error, 'headers') and error.headers:
            reset_timestamp = error.headers.get('X-RateLimit-Reset')
            if reset_timestamp:
                try:
                    reset_time = datetime.fromtimestamp(int(reset_timestamp))
                except (ValueError, TypeError):
                    pass
        
        if reset_time:
            wait_time = max(0, (reset_time - datetime.utcnow()).total_seconds() + 1)
        else:
            # Fallback to exponential backoff
            wait_time = min(60, self.retry_config.base_delay * (2 ** 3))  # Max 60 seconds
        
        logger.warning(f"Rate limit hit for {resource_type}. Waiting {wait_time:.1f}s...")
        await asyncio.sleep(wait_time)
        
        # Refresh rate limit info
        await self.get_rate_limit_status()
    
    async def _handle_rate_limit_response(self, response: httpx.Response, resource_type: str):
        """Handle 429 rate limit response."""
        # Extract reset time from headers
        reset_timestamp = response.headers.get('X-RateLimit-Reset')
        retry_after = response.headers.get('Retry-After')
        
        if reset_timestamp:
            try:
                reset_time = datetime.fromtimestamp(int(reset_timestamp))
                wait_time = max(0, (reset_time - datetime.utcnow()).total_seconds() + 1)
            except (ValueError, TypeError):
                wait_time = 60  # Fallback
        elif retry_after:
            try:
                wait_time = int(retry_after)
            except (ValueError, TypeError):
                wait_time = 60  # Fallback
        else:
            wait_time = 60  # Default fallback
        
        logger.warning(f"Rate limit response (429) for {resource_type}. Waiting {wait_time:.1f}s...")
        await asyncio.sleep(wait_time)
        
        # Refresh rate limit info
        await self.get_rate_limit_status()
    
    def _update_rate_limit_from_headers(self, headers: Dict[str, str], resource_type: str):
        """Update rate limit info from response headers."""
        try:
            limit = headers.get('X-RateLimit-Limit')
            remaining = headers.get('X-RateLimit-Remaining')
            reset = headers.get('X-RateLimit-Reset')
            used = headers.get('X-RateLimit-Used')
            
            if all([limit, remaining, reset]):
                self._rate_limits[resource_type] = RateLimitInfo(
                    limit=int(limit),
                    remaining=int(remaining),
                    reset_time=datetime.fromtimestamp(int(reset)),
                    used=int(used) if used else 0,
                    resource=resource_type
                )
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse rate limit headers: {e}")
    
    async def _update_rate_limit_info(self, resource_type: str):
        """Update rate limit info periodically."""
        now = datetime.utcnow()
        
        # Only update if it's been more than 30 seconds since last check
        if (now - self._last_rate_limit_check).total_seconds() > 30:
            try:
                await self.get_rate_limit_status()
                self._last_rate_limit_check = now
            except Exception as e:
                logger.debug(f"Failed to update rate limit info: {e}")
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter."""
        delay = self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt)
        delay = min(delay, self.retry_config.max_delay)
        
        if self.retry_config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay


# Convenience functions for creating configured clients

def create_github_api_client(
    access_token: str,
    max_retries: int = 3,
    enable_rate_limiting: bool = True
) -> GitHubAPIClient:
    """
    Create a configured GitHub API client.
    
    Args:
        access_token: GitHub access token
        max_retries: Maximum number of retries for failed requests
        enable_rate_limiting: Whether to enable automatic rate limit handling
        
    Returns:
        Configured GitHubAPIClient instance
    """
    retry_config = RetryConfig(max_retries=max_retries)
    return GitHubAPIClient(
        access_token=access_token,
        retry_config=retry_config,
        enable_rate_limit_handling=enable_rate_limiting
    )


def create_app_github_client() -> GitHubAPIClient:
    """
    Create GitHub API client for GitHub App authentication.
    
    Returns:
        GitHubAPIClient configured for GitHub App
    """
    # This would use GitHub App authentication if configured
    return GitHubAPIClient(
        access_token=None,  # Would use App authentication
        enable_rate_limit_handling=True
    )