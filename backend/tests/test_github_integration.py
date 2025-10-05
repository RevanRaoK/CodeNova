"""
GitHub Integration Tests with Mocked API Responses

This module contains comprehensive tests for GitHub integration functionality
including OAuth, webhooks, repository management, and PR analysis.

Requirements covered: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
"""

import asyncio
import json
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

import httpx
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.main import app
from app.core.database import get_db_session
from app.models.github_integration import GitHubRepository, PRAnalysis, AnalysisStatus
from app.models.users import User
from app.services.github_service import GitHubService
from app.core.exceptions import GitHubIntegrationError
from app.schemas.github_schemas import (
    OAuthStateResponse,
    OAuthCallbackResponse,
    GitHubRepositoryResponse,
    PRAnalysisResponse,
    WebhookEventResponse
)

# T
est fixtures and mock data
@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = Mock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    return user


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def github_service(mock_db_session):
    """Create a GitHub service instance with mocked dependencies."""
    with patch('app.services.github_service.settings') as mock_settings:
        mock_settings.GITHUB_CLIENT_ID = "test_client_id"
        mock_settings.GITHUB_CLIENT_SECRET = "test_client_secret"
        mock_settings.GITHUB_OAUTH_REDIRECT_URI = "http://localhost:8000/api/v1/github/oauth/callback"
        mock_settings.GITHUB_WEBHOOK_SECRET = "test_webhook_secret"
        mock_settings.GITHUB_APP_ID = "12345"
        mock_settings.GITHUB_PRIVATE_KEY = None
        
        service = GitHubService(mock_db_session)
        return service


@pytest.fixture
def mock_github_oauth_response():
    """Mock GitHub OAuth token exchange response."""
    return {
        "access_token": "gho_test_token_123456789",
        "token_type": "bearer",
        "scope": "repo,user:email"
    }


@pytest.fixture
def mock_github_user_response():
    """Mock GitHub user API response."""
    return {
        "id": 12345,
        "login": "testuser",
        "email": "test@example.com",
        "name": "Test User"
    }


@pytest.fixture
def mock_repository_data():
    """Mock repository data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "user_id": 1,
        "repo_url": "https://github.com/testuser/testrepo",
        "repo_name": "testuser/testrepo",
        "webhook_id": "12345",
        "webhook_secret": "test_webhook_secret",
        "access_token": "gho_test_token",
        "default_branch": "main",
        "repository_settings": {
            "auto_analysis": True,
            "create_issues": True,
            "comment_on_prs": True
        },
        "permissions": {
            "contents": "read",
            "issues": "write",
            "pull_requests": "write"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_pr_data():
    """Mock pull request data for testing."""
    return {
        "number": 1,
        "title": "Test PR",
        "user": {"login": "testuser"},
        "head": {"sha": "abc123", "ref": "feature-branch"},
        "base": {"sha": "def456", "ref": "main"},
        "html_url": "https://github.com/testuser/testrepo/pull/1"
    }


@pytest.fixture
def mock_webhook_payload():
    """Mock GitHub webhook payload."""
    return {
        "action": "opened",
        "number": 1,
        "pull_request": {
            "number": 1,
            "title": "Test PR",
            "user": {"login": "testuser"},
            "head": {"sha": "abc123", "ref": "feature-branch"},
            "base": {"sha": "def456", "ref": "main"}
        },
        "repository": {
            "html_url": "https://github.com/testuser/testrepo",
            "name": "testrepo",
            "full_name": "testuser/testrepo"
        }
    }


class TestGitHubOAuth:
    """Test GitHub OAuth functionality."""

    @pytest.mark.asyncio
    async def test_get_oauth_authorization_url(self, github_service):
        """Test OAuth authorization URL generation."""
        state = "test_state_123"
        
        url = await github_service.get_oauth_authorization_url(state)
        
        assert "https://github.com/login/oauth/authorize" in url
        assert "client_id=test_client_id" in url
        assert f"state={state}" in url
        assert "scope=repo,user:email" in url
        assert "redirect_uri=" in url

    @pytest.mark.asyncio
    async def test_exchange_oauth_code_success(self, github_service, mock_github_oauth_response, mock_github_user_response):
        """Test successful OAuth code exchange."""
        code = "test_oauth_code"
        state = "test_state"
        
        # Mock the HTTP requests
        with patch('httpx.AsyncClient') as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            
            # Mock token exchange response
            token_response = Mock()
            token_response.status_code = 200
            token_response.json.return_value = mock_github_oauth_response
            
            # Mock user info response
            user_response = Mock()
            user_response.json.return_value = mock_github_user_response
            
            mock_context.post.return_value = token_response
            mock_context.get.return_value = user_response
            
            result = await github_service.exchange_oauth_code(code, state)
            
            assert result["access_token"] == "gho_test_token_123456789"
            assert result["user"]["login"] == "testuser"
            assert result["user"]["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_exchange_oauth_code_failure(self, github_service):
        """Test OAuth code exchange failure."""
        code = "invalid_code"
        state = "test_state"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            
            # Mock failed token exchange
            token_response = Mock()
            token_response.status_code = 400
            token_response.json.return_value = {
                "error": "bad_verification_code",
                "error_description": "The code passed is incorrect or expired."
            }
            
            mock_context.post.return_value = token_response
            
            with pytest.raises(GitHubIntegrationError):
                await github_service.exchange_oauth_code(code, state)


class TestRepositoryManagement:
    """Test repository management functionality."""

    @pytest.mark.asyncio
    async def test_setup_repository_webhook_success(self, github_service, mock_user, mock_db_session):
        """Test successful repository webhook setup."""
        repo_url = "https://github.com/testuser/testrepo"
        access_token = "gho_test_token"
        
        # Mock GitHub API responses
        with patch('github.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            mock_repo = Mock()
            mock_repo.default_branch = "main"
            mock_github.get_repo.return_value = mock_repo
            
            mock_webhook = Mock()
            mock_webhook.id = 12345
            mock_repo.create_hook.return_value = mock_webhook
            
            # Mock database operations
            mock_db_session.add = Mock()
            mock_db_session.commit = AsyncMock()
            mock_db_session.refresh = AsyncMock()
            
            # Mock existing repository check
            mock_db_session.execute = AsyncMock()
            mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
            
            result = await github_service.setup_repository_webhook(
                user_id=mock_user.id,
                repo_url=repo_url,
                access_token=access_token
            )
            
            assert isinstance(result, GitHubRepository)
            assert result.repo_url == repo_url
            assert result.user_id == mock_user.id
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_repository_webhook_already_exists(self, github_service, mock_user, mock_db_session, mock_repository_data):
        """Test repository webhook setup when repository already exists."""
        repo_url = "https://github.com/testuser/testrepo"
        access_token = "gho_test_token"
        
        # Mock existing repository
        existing_repo = GitHubRepository(**mock_repository_data)
        mock_db_session.execute = AsyncMock()
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_repo
        
        result = await github_service.setup_repository_webhook(
            user_id=mock_user.id,
            repo_url=repo_url,
            access_token=access_token
        )
        
        assert result == existing_repo

    @pytest.mark.asyncio
    async def test_setup_repository_webhook_github_error(self, github_service, mock_user, mock_db_session):
        """Test repository webhook setup with GitHub API error."""
        repo_url = "https://github.com/testuser/testrepo"
        access_token = "invalid_token"
        
        with patch('github.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            from github import GithubException
            mock_github.get_repo.side_effect = GithubException(401, "Bad credentials")
            
            # Mock no existing repository
            mock_db_session.execute = AsyncMock()
            mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
            
            with pytest.raises(GitHubIntegrationError):
                await github_service.setup_repository_webhook(
                    user_id=mock_user.id,
                    repo_url=repo_url,
                    access_token=access_token
                )


class TestWebhookHandling:
    """Test webhook event handling."""

    @pytest.mark.asyncio
    async def test_handle_webhook_event_pull_request(self, github_service, mock_webhook_payload):
        """Test handling pull request webhook events."""
        headers = {
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=test_signature"
        }
        payload = json.dumps(mock_webhook_payload).encode('utf-8')
        
        # Mock signature verification
        with patch.object(github_service, '_verify_webhook_signature', return_value=True):
            with patch.object(github_service, '_handle_pull_request_event', return_value={"status": "success"}) as mock_handler:
                result = await github_service.handle_webhook_event(headers, payload)
                
                assert result["status"] == "success"
                mock_handler.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    async def test_handle_webhook_event_invalid_signature(self, github_service, mock_webhook_payload):
        """Test webhook event handling with invalid signature."""
        headers = {
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=invalid_signature"
        }
        payload = json.dumps(mock_webhook_payload).encode('utf-8')
        
        # Mock signature verification failure
        with patch.object(github_service, '_verify_webhook_signature', return_value=False):
            with pytest.raises(GitHubIntegrationError, match="Invalid webhook signature"):
                await github_service.handle_webhook_event(headers, payload)

    @pytest.mark.asyncio
    async def test_handle_webhook_event_ping(self, github_service):
        """Test handling ping webhook events."""
        headers = {
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": "sha256=test_signature"
        }
        payload = json.dumps({"zen": "test"}).encode('utf-8')
        
        with patch.object(github_service, '_verify_webhook_signature', return_value=True):
            result = await github_service.handle_webhook_event(headers, payload)
            
            assert result["status"] == "success"
            assert "ping" in result["message"]

    def test_verify_webhook_signature_valid(self, github_service):
        """Test webhook signature verification with valid signature."""
        payload = b'{"test": "data"}'
        
        # Calculate expected signature
        import hmac
        import hashlib
        expected_signature = hmac.new(
            github_service.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "X-Hub-Signature-256": f"sha256={expected_signature}"
        }
        
        result = github_service._verify_webhook_signature(headers, payload)
        assert result is True

    def test_verify_webhook_signature_invalid(self, github_service):
        """Test webhook signature verification with invalid signature."""
        payload = b'{"test": "data"}'
        headers = {
            "X-Hub-Signature-256": "sha256=invalid_signature"
        }
        
        result = github_service._verify_webhook_signature(headers, payload)
        assert result is False


class TestPullRequestAnalysis:
    """Test pull request analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_pull_request_success(self, github_service, mock_db_session, mock_repository_data, mock_pr_data):
        """Test successful pull request analysis."""
        repository_id = mock_repository_data["id"]
        pr_number = 1
        
        # Mock repository lookup
        mock_repo = GitHubRepository(**mock_repository_data)
        mock_db_session.execute = AsyncMock()
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_repo
        
        # Mock GitHub API
        with patch('github.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            mock_repo_obj = Mock()
            mock_github.get_repo.return_value = mock_repo_obj
            
            mock_pr = Mock()
            mock_pr.title = mock_pr_data["title"]
            mock_pr.user.login = mock_pr_data["user"]["login"]
            mock_pr.head.sha = mock_pr_data["head"]["sha"]
            mock_pr.base.sha = mock_pr_data["base"]["sha"]
            mock_pr.head.ref = mock_pr_data["head"]["ref"]
            mock_pr.base.ref = mock_pr_data["base"]["ref"]
            mock_pr.html_url = mock_pr_data["html_url"]
            mock_repo_obj.get_pull.return_value = mock_pr
            
            # Mock file changes
            mock_file = Mock()
            mock_file.filename = "test.py"
            mock_file.status = "modified"
            mock_file.additions = 10
            mock_file.deletions = 5
            mock_file.changes = 15
            mock_pr.get_files.return_value = [mock_file]
            
            # Mock file content
            mock_content = Mock()
            mock_content.decoded_content = b"print('hello world')"
            mock_repo_obj.get_contents.return_value = mock_content
            
            # Mock analysis service
            with patch.object(github_service, 'analysis_service') as mock_analysis:
                mock_analysis.analyze_code_content = AsyncMock(return_value={
                    "issues": [
                        {
                            "line": 1,
                            "message": "Missing docstring",
                            "severity": "warning",
                            "rule": "missing-docstring"
                        }
                    ]
                })
                
                # Mock database operations
                mock_db_session.add = Mock()
                mock_db_session.commit = AsyncMock()
                mock_db_session.refresh = AsyncMock()
                
                result = await github_service.analyze_pull_request(
                    repository_id=repository_id,
                    pr_number=pr_number
                )
                
                assert isinstance(result, PRAnalysis)
                assert result.pr_number == pr_number
                assert result.status == AnalysisStatus.COMPLETED
                assert result.issues_found == 1

    @pytest.mark.asyncio
    async def test_analyze_pull_request_repository_not_found(self, github_service, mock_db_session):
        """Test pull request analysis with non-existent repository."""
        repository_id = "non-existent-id"
        pr_number = 1
        
        # Mock repository lookup returning None
        mock_db_session.execute = AsyncMock()
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(GitHubIntegrationError, match="Repository integration not found"):
            await github_service.analyze_pull_request(
                repository_id=repository_id,
                pr_number=pr_number
            )

    @pytest.mark.asyncio
    async def test_analyze_pull_request_existing_analysis(self, github_service, mock_db_session, mock_repository_data):
        """Test pull request analysis with existing analysis."""
        repository_id = mock_repository_data["id"]
        pr_number = 1
        
        # Mock repository lookup
        mock_repo = GitHubRepository(**mock_repository_data)
        
        # Mock existing analysis
        existing_analysis = PRAnalysis(
            id=str(uuid.uuid4()),
            repository_id=repository_id,
            pr_number=pr_number,
            pr_title="Test PR",
            pr_author="testuser",
            head_sha="abc123",
            base_sha="def456",
            head_branch="feature",
            base_branch="main",
            status=AnalysisStatus.COMPLETED,
            issues_found=0
        )
        
        # Mock database calls
        call_count = 0
        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            result = Mock()
            if call_count == 1:  # Repository lookup
                result.scalar_one_or_none.return_value = mock_repo
            else:  # Analysis lookup
                result.scalar_one_or_none.return_value = existing_analysis
            return result
        
        mock_db_session.execute = mock_execute
        
        result = await github_service.analyze_pull_request(
            repository_id=repository_id,
            pr_number=pr_number,
            force_reanalysis=False
        )
        
        assert result == existing_analysis


class TestIssueCreation:
    """Test GitHub issue creation functionality."""

    @pytest.mark.asyncio
    async def test_create_repository_issue_success(self, github_service, mock_db_session, mock_repository_data):
        """Test successful GitHub issue creation."""
        repository_id = mock_repository_data["id"]
        title = "Test Issue"
        body = "This is a test issue"
        labels = ["bug", "high-priority"]
        
        # Mock repository lookup
        mock_repo = GitHubRepository(**mock_repository_data)
        mock_db_session.execute = AsyncMock()
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_repo
        
        # Mock GitHub API
        with patch('github.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            mock_repo_obj = Mock()
            mock_github.get_repo.return_value = mock_repo_obj
            
            mock_issue = Mock()
            mock_issue.number = 123
            mock_issue.html_url = "https://github.com/testuser/testrepo/issues/123"
            mock_repo_obj.create_issue.return_value = mock_issue
            
            result = await github_service.create_repository_issue(
                repository_id=repository_id,
                title=title,
                body=body,
                labels=labels
            )
            
            assert result == mock_issue.html_url
            mock_repo_obj.create_issue.assert_called_once_with(
                title=title,
                body=body,
                labels=labels
            )

    @pytest.mark.asyncio
    async def test_create_repository_issue_repository_not_found(self, github_service, mock_db_session):
        """Test issue creation with non-existent repository."""
        repository_id = "non-existent-id"
        title = "Test Issue"
        body = "This is a test issue"
        
        # Mock repository lookup returning None
        mock_db_session.execute = AsyncMock()
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(GitHubIntegrationError, match="Repository integration not found"):
            await github_service.create_repository_issue(
                repository_id=repository_id,
                title=title,
                body=body
            )


class TestUtilityMethods:
    """Test utility methods."""

    def test_extract_repo_name_valid_url(self, github_service):
        """Test repository name extraction from valid GitHub URL."""
        test_cases = [
            ("https://github.com/owner/repo", "owner/repo"),
            ("https://github.com/owner/repo.git", "owner/repo.git"),
            ("https://github.com/owner/repo/", "owner/repo"),
            ("http://github.com/owner/repo", "owner/repo"),
        ]
        
        for url, expected in test_cases:
            result = github_service._extract_repo_name(url)
            assert result == expected

    def test_extract_repo_name_invalid_url(self, github_service):
        """Test repository name extraction from invalid URLs."""
        test_cases = [
            "https://github.com/owner",
            "https://example.com/owner/repo",
            "invalid-url",
            "",
        ]
        
        for url in test_cases:
            result = github_service._extract_repo_name(url)
            assert result is None

    def test_detect_language(self, github_service):
        """Test programming language detection from filename."""
        test_cases = [
            ("test.py", "python"),
            ("app.js", "javascript"),
            ("component.tsx", "typescript"),
            ("Main.java", "java"),
            ("program.cpp", "cpp"),
            ("script.sh", "unknown"),  # Not in the mapping
            ("README.md", "unknown"),
        ]
        
        for filename, expected in test_cases:
            result = github_service._detect_language(filename)
            assert result == expected


# Integration test fixtures for API endpoints
@pytest.fixture
def test_client():
    """Create a test client for API endpoint testing."""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock current user for API tests."""
    user = Mock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    return user


class TestGitHubAPIEndpoints:
    """Test GitHub API endpoints with mocked responses."""

    def test_get_oauth_authorization_url_endpoint(self, test_client):
        """Test OAuth authorization URL endpoint."""
        with patch('app.api.v1.endpoints.github.GitHubService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_oauth_authorization_url = AsyncMock(
                return_value="https://github.com/login/oauth/authorize?client_id=test&state=test"
            )
            
            response = test_client.get("/api/v1/github/oauth/authorize")
            
            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            assert "state" in data

    def test_oauth_callback_endpoint_success(self, test_client):
        """Test OAuth callback endpoint with successful response."""
        with patch('app.api.v1.endpoints.github.GitHubService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.exchange_oauth_code = AsyncMock(return_value={
                "access_token": "gho_test_token",
                "token_type": "bearer",
                "scope": "repo,user:email",
                "user": {
                    "id": 12345,
                    "login": "testuser",
                    "email": "test@example.com",
                    "name": "Test User"
                }
            })
            
            # Mock oauth_states
            with patch('app.api.v1.endpoints.github.oauth_states', {"test_state": {"redirect_url": None}}):
                response = test_client.get(
                    "/api/v1/github/oauth/callback",
                    params={"code": "test_code", "state": "test_state"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["user_info"]["login"] == "testuser"

    def test_oauth_callback_endpoint_invalid_state(self, test_client):
        """Test OAuth callback endpoint with invalid state."""
        with patch('app.api.v1.endpoints.github.oauth_states', {}):
            response = test_client.get(
                "/api/v1/github/oauth/callback",
                params={"code": "test_code", "state": "invalid_state"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid or expired OAuth state" in data["detail"]

    def test_webhook_endpoint(self, test_client):
        """Test webhook endpoint."""
        webhook_payload = {
            "action": "opened",
            "pull_request": {"number": 1, "title": "Test PR"},
            "repository": {"html_url": "https://github.com/owner/repo"}
        }
        
        headers = {
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=test_signature"
        }
        
        response = test_client.post(
            "/api/v1/github/webhook",
            json=webhook_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"

    def test_health_endpoint(self, test_client):
        """Test GitHub integration health endpoint."""
        response = test_client.get("/api/v1/github/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "github_api_accessible" in data
        assert "connected_repositories" in data

    def test_webhook_config_endpoint(self, test_client):
        """Test webhook configuration endpoint."""
        response = test_client.get("/api/v1/github/webhook/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "webhook_url" in data
        assert "supported_events" in data
        assert "signature_verification" in data


# Performance and load testing
class TestGitHubIntegrationPerformance:
    """Test performance aspects of GitHub integration."""

    @pytest.mark.asyncio
    async def test_concurrent_webhook_processing(self, github_service):
        """Test concurrent webhook event processing."""
        webhook_payloads = [
            {
                "action": "opened",
                "number": i,
                "pull_request": {"number": i, "title": f"Test PR {i}"},
                "repository": {"html_url": "https://github.com/owner/repo"}
            }
            for i in range(1, 6)
        ]
        
        headers = {
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=test_signature"
        }
        
        # Mock signature verification and event handling
        with patch.object(github_service, '_verify_webhook_signature', return_value=True):
            with patch.object(github_service, '_handle_pull_request_event', return_value={"status": "success"}):
                
                tasks = []
                for payload in webhook_payloads:
                    payload_bytes = json.dumps(payload).encode('utf-8')
                    task = github_service.handle_webhook_event(headers, payload_bytes)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                
                assert len(results) == 5
                for result in results:
                    assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_large_pr_analysis(self, github_service, mock_db_session, mock_repository_data):
        """Test analysis of PR with many files."""
        repository_id = mock_repository_data["id"]
        pr_number = 1
        
        # Mock repository lookup
        mock_repo = GitHubRepository(**mock_repository_data)
        mock_db_session.execute = AsyncMock()
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_repo
        
        # Mock GitHub API with many files
        with patch('github.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            mock_repo_obj = Mock()
            mock_github.get_repo.return_value = mock_repo_obj
            
            mock_pr = Mock()
            mock_pr.title = "Large PR"
            mock_pr.user.login = "testuser"
            mock_pr.head.sha = "abc123"
            mock_pr.base.sha = "def456"
            mock_pr.head.ref = "feature"
            mock_pr.base.ref = "main"
            mock_pr.html_url = "https://github.com/owner/repo/pull/1"
            mock_repo_obj.get_pull.return_value = mock_pr
            
            # Create many mock files
            mock_files = []
            for i in range(50):  # 50 files
                mock_file = Mock()
                mock_file.filename = f"file_{i}.py"
                mock_file.status = "modified"
                mock_file.additions = 10
                mock_file.deletions = 5
                mock_file.changes = 15
                mock_files.append(mock_file)
            
            mock_pr.get_files.return_value = mock_files
            
            # Mock file content
            mock_content = Mock()
            mock_content.decoded_content = b"print('hello world')"
            mock_repo_obj.get_contents.return_value = mock_content
            
            # Mock analysis service
            with patch.object(github_service, 'analysis_service') as mock_analysis:
                mock_analysis.analyze_code_content = AsyncMock(return_value={
                    "issues": []  # No issues for performance test
                })
                
                # Mock database operations
                mock_db_session.add = Mock()
                mock_db_session.commit = AsyncMock()
                mock_db_session.refresh = AsyncMock()
                
                start_time = datetime.utcnow()
                result = await github_service.analyze_pull_request(
                    repository_id=repository_id,
                    pr_number=pr_number
                )
                end_time = datetime.utcnow()
                
                # Verify the analysis completed
                assert isinstance(result, PRAnalysis)
                assert result.status == AnalysisStatus.COMPLETED
                
                # Check that it completed in reasonable time (should be fast with mocks)
                duration = (end_time - start_time).total_seconds()
                assert duration < 5.0  # Should complete within 5 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])