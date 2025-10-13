"""
Test GitHub Repository Connection Service

This test file validates the GitHub Repository Connection Service functionality
including repository connection, webhook setup, and integration management.

Requirements covered: 3.3, 3.5
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from github import Github, GithubException

from app.services.github_repository_connection_service import GitHubRepositoryConnectionService
from app.models.github_integration import GitHubRepository, PRAnalysis, AnalysisStatus
from app.models.github_oauth import GitHubOAuthIntegration
from app.models.users import User
from app.core.exceptions import GitHubIntegrationError


class TestGitHubRepositoryConnectionService:
    """Test cases for GitHub Repository Connection Service."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock(spec=AsyncSession)
    
    @pytest.fixture
    def mock_oauth_service(self):
        """Mock OAuth service."""
        return Mock()
    
    @pytest.fixture
    def mock_background_job_service(self):
        """Mock background job service."""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_db_session):
        """Create service instance with mocked dependencies."""
        with patch('app.services.github_repository_connection_service.GitHubOAuthService'), \
             patch('app.services.github_repository_connection_service.BackgroundJobService'):
            return GitHubRepositoryConnectionService(mock_db_session)
    
    @pytest.fixture
    def mock_oauth_integration(self):
        """Mock OAuth integration."""
        return GitHubOAuthIntegration(
            id="oauth-123",
            user_id=1,
            github_user_id=12345,
            github_username="testuser",
            access_token="github_token_123",
            is_active=True
        )
    
    @pytest.fixture
    def mock_repo_info(self):
        """Mock repository information."""
        return {
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "default_branch": "main",
            "private": False,
            "permissions": {
                "admin": True,
                "push": True,
                "pull": True
            },
            "description": "Test repository",
            "language": "Python",
            "size": 1024,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-12-01T00:00:00Z"
        }
    
    @pytest.mark.asyncio
    async def test_connect_repository_success(
        self, 
        service, 
        mock_db_session, 
        mock_oauth_integration,
        mock_repo_info
    ):
        """Test successful repository connection."""
        # Setup mocks
        service.oauth_service.get_user_integration = AsyncMock(return_value=mock_oauth_integration)
        service._verify_repository_access = AsyncMock(return_value=mock_repo_info)
        service._setup_repository_webhook = AsyncMock(return_value={
            "webhook_id": "webhook-123",
            "webhook_url": "https://api.example.com/webhook",
            "events": ["pull_request", "push"],
            "active": True
        })
        service._get_repository_by_url = AsyncMock(return_value=None)
        service._queue_initial_repository_scan = AsyncMock()
        
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        # Test repository connection
        result = await service.connect_repository(
            user_id=1,
            repo_url="https://github.com/testuser/test-repo"
        )
        
        # Verify results
        assert result is not None
        assert result.user_id == 1
        assert result.repo_name == "testuser/test-repo"
        assert result.webhook_id == "webhook-123"
        assert result.is_active is True
        
        # Verify service calls
        service.oauth_service.get_user_integration.assert_called_once_with(mock_db_session, 1)
        service._verify_repository_access.assert_called_once()
        service._setup_repository_webhook.assert_called_once()
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_repository_no_oauth(self, service, mock_db_session):
        """Test repository connection without OAuth integration."""
        # Setup mocks
        service.oauth_service.get_user_integration = AsyncMock(return_value=None)
        
        # Test repository connection
        with pytest.raises(GitHubIntegrationError) as exc_info:
            await service.connect_repository(
                user_id=1,
                repo_url="https://github.com/testuser/test-repo"
            )
        
        assert "GitHub OAuth integration not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_connect_repository_invalid_url(self, service, mock_db_session, mock_oauth_integration):
        """Test repository connection with invalid URL."""
        # Setup mocks
        service.oauth_service.get_user_integration = AsyncMock(return_value=mock_oauth_integration)
        
        # Test repository connection with invalid URL
        with pytest.raises(GitHubIntegrationError) as exc_info:
            await service.connect_repository(
                user_id=1,
                repo_url="https://invalid-url.com/repo"
            )
        
        assert "Invalid GitHub repository URL format" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_connect_repository_already_exists(
        self, 
        service, 
        mock_db_session, 
        mock_oauth_integration
    ):
        """Test repository connection when repository already exists."""
        # Create existing repository
        existing_repo = GitHubRepository(
            id="repo-123",
            user_id=1,
            repo_url="https://github.com/testuser/test-repo",
            repo_name="testuser/test-repo",
            is_active=True
        )
        
        # Setup mocks
        service.oauth_service.get_user_integration = AsyncMock(return_value=mock_oauth_integration)
        service._get_repository_by_url = AsyncMock(return_value=existing_repo)
        
        # Test repository connection
        result = await service.connect_repository(
            user_id=1,
            repo_url="https://github.com/testuser/test-repo"
        )
        
        # Verify existing repository is returned
        assert result == existing_repo
        assert result.is_active is True
    
    @pytest.mark.asyncio
    async def test_disconnect_repository_success(self, service, mock_db_session):
        """Test successful repository disconnection."""
        # Create repository to disconnect
        repo_integration = GitHubRepository(
            id="repo-123",
            user_id=1,
            repo_url="https://github.com/testuser/test-repo",
            repo_name="testuser/test-repo",
            webhook_id="webhook-123",
            access_token="token-123",
            is_active=True
        )
        
        # Setup mocks
        service._get_repository_by_id = AsyncMock(return_value=repo_integration)
        service._remove_repository_webhook = AsyncMock(return_value=True)
        mock_db_session.commit = AsyncMock()
        
        # Test repository disconnection
        result = await service.disconnect_repository(
            user_id=1,
            repository_id="repo-123",
            remove_webhook=True
        )
        
        # Verify results
        assert result is True
        assert repo_integration.is_active is False
        
        # Verify service calls
        service._get_repository_by_id.assert_called_once_with("repo-123", 1)
        service._remove_repository_webhook.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_repository_not_found(self, service, mock_db_session):
        """Test repository disconnection when repository not found."""
        # Setup mocks
        service._get_repository_by_id = AsyncMock(return_value=None)
        
        # Test repository disconnection
        with pytest.raises(GitHubIntegrationError) as exc_info:
            await service.disconnect_repository(
                user_id=1,
                repository_id="repo-123"
            )
        
        assert "Repository integration not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_update_repository_settings_success(self, service, mock_db_session):
        """Test successful repository settings update."""
        # Create repository
        repo_integration = GitHubRepository(
            id="repo-123",
            user_id=1,
            repository_settings={"auto_analysis": True}
        )
        
        # Setup mocks
        service._get_repository_by_id = AsyncMock(return_value=repo_integration)
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        # Test settings update
        new_settings = {
            "auto_analysis": False,
            "create_issues": True,
            "max_issues_per_pr": 5
        }
        
        result = await service.update_repository_settings(
            user_id=1,
            repository_id="repo-123",
            settings=new_settings
        )
        
        # Verify results
        assert result == repo_integration
        assert repo_integration.repository_settings["auto_analysis"] is False
        assert repo_integration.repository_settings["create_issues"] is True
        assert repo_integration.repository_settings["max_issues_per_pr"] == 5
        
        # Verify service calls
        service._get_repository_by_id.assert_called_once_with("repo-123", 1)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trigger_pull_request_analysis_success(self, service, mock_db_session):
        """Test successful PR analysis trigger."""
        # Create repository
        repo_integration = GitHubRepository(
            id="repo-123",
            user_id=1,
            repo_name="testuser/test-repo",
            access_token="token-123",
            repository_settings={"analysis_timeout_minutes": 30}
        )
        
        # Mock PR info
        pr_info = {
            "title": "Test PR",
            "author": "testuser",
            "head_sha": "abc123",
            "base_sha": "def456",
            "head_branch": "feature",
            "base_branch": "main",
            "state": "open",
            "html_url": "https://github.com/testuser/test-repo/pull/1"
        }
        
        # Setup mocks
        service._get_repository_by_id = AsyncMock(return_value=repo_integration)
        service._get_pr_analysis = AsyncMock(return_value=None)
        service._get_pull_request_info = AsyncMock(return_value=pr_info)
        service._create_or_update_pr_analysis = AsyncMock(return_value=Mock(id="analysis-123"))
        service.background_job_service.queue_job = AsyncMock(return_value="job-123")
        mock_db_session.commit = AsyncMock()
        
        # Test PR analysis trigger
        result = await service.trigger_pull_request_analysis(
            repository_id="repo-123",
            pr_number=1,
            force_reanalysis=False,
            user_id=1
        )
        
        # Verify results
        assert result == "job-123"
        
        # Verify service calls
        service._get_repository_by_id.assert_called_once_with("repo-123", 1)
        service._get_pull_request_info.assert_called_once()
        service._create_or_update_pr_analysis.assert_called_once()
        service.background_job_service.queue_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_repository_webhooks_status_success(self, service, mock_db_session):
        """Test successful webhook status retrieval."""
        # Create repository
        repo_integration = GitHubRepository(
            id="repo-123",
            user_id=1,
            repo_name="testuser/test-repo",
            webhook_id="webhook-123",
            access_token="token-123"
        )
        
        # Mock webhook status
        webhook_status = {
            "active": True,
            "events": ["pull_request", "push"],
            "url": "https://api.example.com/webhook",
            "last_delivery": "2023-12-01T12:00:00Z",
            "delivery_count": 5,
            "recent_deliveries": []
        }
        
        # Setup mocks
        service._get_repository_by_id = AsyncMock(return_value=repo_integration)
        service._check_webhook_status = AsyncMock(return_value=webhook_status)
        
        # Test webhook status retrieval
        result = await service.get_repository_webhooks_status(
            user_id=1,
            repository_id="repo-123"
        )
        
        # Verify results
        assert result["repository_id"] == "repo-123"
        assert result["repo_name"] == "testuser/test-repo"
        assert result["webhook_id"] == "webhook-123"
        assert result["webhook_active"] is True
        assert result["webhook_events"] == ["pull_request", "push"]
        
        # Verify service calls
        service._get_repository_by_id.assert_called_once_with("repo-123", 1)
        service._check_webhook_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_user_repositories_success(self, service, mock_db_session):
        """Test successful user repositories listing."""
        # Create mock repositories
        repo1 = GitHubRepository(
            id="repo-1",
            user_id=1,
            repo_name="testuser/repo1",
            is_active=True
        )
        repo2 = GitHubRepository(
            id="repo-2",
            user_id=1,
            repo_name="testuser/repo2",
            is_active=True
        )
        
        # Mock database results
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [repo1, repo2]
        
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 2
        
        mock_db_session.execute = AsyncMock(side_effect=[mock_result, mock_count_result])
        
        # Test repository listing
        result = await service.list_user_repositories(
            user_id=1,
            include_inactive=False,
            page=1,
            per_page=20
        )
        
        # Verify results
        assert result["total"] == 2
        assert result["page"] == 1
        assert result["per_page"] == 20
        assert len(result["repositories"]) == 2
        assert result["repositories"][0]["id"] == "repo-1"
        assert result["repositories"][1]["id"] == "repo-2"
    
    def test_extract_repo_name_valid_urls(self, service):
        """Test repository name extraction from valid URLs."""
        test_cases = [
            ("https://github.com/owner/repo", "owner/repo"),
            ("https://github.com/owner/repo.git", "owner/repo"),
            ("https://www.github.com/owner/repo", "owner/repo"),
            ("https://github.com/owner/repo/", "owner/repo"),
        ]
        
        for url, expected in test_cases:
            result = service._extract_repo_name(url)
            assert result == expected, f"Failed for URL: {url}"
    
    def test_extract_repo_name_invalid_urls(self, service):
        """Test repository name extraction from invalid URLs."""
        invalid_urls = [
            "https://gitlab.com/owner/repo",
            "https://github.com/owner",
            "https://github.com/",
            "invalid-url",
            "",
        ]
        
        for url in invalid_urls:
            result = service._extract_repo_name(url)
            assert result is None, f"Should return None for URL: {url}"
    
    def test_validate_repository_settings(self, service):
        """Test repository settings validation."""
        # Test valid settings
        settings = {
            "auto_analysis": True,
            "create_issues": False,
            "min_severity_for_issues": "error",
            "max_issues_per_pr": 10,
            "analysis_timeout_minutes": 30
        }
        
        result = service._validate_repository_settings(settings)
        
        assert result["auto_analysis"] is True
        assert result["create_issues"] is False
        assert result["min_severity_for_issues"] == "error"
        assert result["max_issues_per_pr"] == 10
        assert result["analysis_timeout_minutes"] == 30
    
    def test_validate_repository_settings_bounds(self, service):
        """Test repository settings validation with bounds checking."""
        # Test settings with out-of-bounds values
        settings = {
            "max_issues_per_pr": 100,  # Should be capped at 50
            "analysis_timeout_minutes": 200,  # Should be capped at 120
            "min_severity_for_issues": "invalid"  # Should be ignored
        }
        
        result = service._validate_repository_settings(settings)
        
        assert result["max_issues_per_pr"] == 50
        assert result["analysis_timeout_minutes"] == 120
        assert "min_severity_for_issues" not in result
    
    def test_format_repository_response(self, service):
        """Test repository response formatting."""
        repo = GitHubRepository(
            id="repo-123",
            repo_url="https://github.com/testuser/test-repo",
            repo_name="testuser/test-repo",
            default_branch="main",
            webhook_id="webhook-123",
            repository_settings={"auto_analysis": True},
            permissions={"admin": True},
            is_active=True,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 12, 1)
        )
        
        result = service._format_repository_response(repo)
        
        assert result["id"] == "repo-123"
        assert result["repo_name"] == "testuser/test-repo"
        assert result["webhook_status"] == "active"
        assert result["is_active"] is True
        assert "created_at" in result
        assert "updated_at" in result


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])