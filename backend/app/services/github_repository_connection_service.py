"""
GitHub Repository Connection Service

This service handles GitHub repository connections, webhook setup, and integration management.
It provides methods for connecting repositories, managing webhooks, and triggering code analysis
for pull requests.

Requirements covered: 3.3, 3.5
"""

import asyncio
import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse

import httpx
from github import Github, GithubException
from github.Repository import Repository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import GitHubIntegrationError
from app.models.github_integration import GitHubRepository, PRAnalysis, AnalysisStatus
from app.models.github_oauth import GitHubOAuthIntegration
from app.models.users import User
from app.services.github_oauth_service import GitHubOAuthService
from app.services.background_job_service import BackgroundJobService
from app.services.github_api_client import GitHubAPIClient, create_github_api_client

logger = logging.getLogger(__name__)


class GitHubRepositoryConnectionService:
    """
    Service for managing GitHub repository connections and webhook setup.
    
    This service handles:
    - Repository connection and webhook setup
    - Repository integration management
    - Code analysis trigger for pull requests
    - Webhook configuration and validation
    
    Requirements covered: 3.3, 3.5
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.oauth_service = GitHubOAuthService()
        self.background_job_service = BackgroundJobService()
        
        # GitHub configuration
        self.webhook_secret = settings.GITHUB_WEBHOOK_SECRET
        self.webhook_base_url = settings.GITHUB_WEBHOOK_BASE_URL
        
        # Default webhook events to subscribe to
        self.default_webhook_events = [
            "pull_request",
            "push",
            "issues",
            "issue_comment",
            "pull_request_review",
            "pull_request_review_comment"
        ]
        
        # Default repository settings
        self.default_repo_settings = {
            "auto_analysis": True,
            "create_issues": True,
            "comment_on_prs": True,
            "analysis_on_push": False,
            "min_severity_for_issues": "error",
            "max_issues_per_pr": 10,
            "enable_inline_comments": True,
            "analysis_timeout_minutes": 30
        }
    
    async def connect_repository(
        self,
        user_id: int,
        repo_url: str,
        webhook_events: Optional[List[str]] = None,
        repository_settings: Optional[Dict[str, Any]] = None
    ) -> GitHubRepository:
        """
        Connect a GitHub repository for integration and set up webhook.
        
        Args:
            user_id: User ID connecting the repository
            repo_url: GitHub repository URL
            webhook_events: List of webhook events to subscribe to
            repository_settings: Custom repository settings
            
        Returns:
            GitHubRepository: Created repository integration
            
        Raises:
            GitHubIntegrationError: If connection fails
        """
        try:
            # Get user's GitHub OAuth integration
            oauth_integration = await self.oauth_service.get_user_integration(self.db, user_id)
            if not oauth_integration:
                raise GitHubIntegrationError(
                    "GitHub OAuth integration not found. Please authenticate with GitHub first."
                )
            
            # Validate and parse repository URL
            repo_name = self._extract_repo_name(repo_url)
            if not repo_name:
                raise GitHubIntegrationError("Invalid GitHub repository URL format")
            
            # Check if repository is already connected
            existing_repo = await self._get_repository_by_url(repo_url, user_id)
            if existing_repo:
                if existing_repo.is_active:
                    logger.info(f"Repository {repo_name} already connected for user {user_id}")
                    return existing_repo
                else:
                    # Reactivate existing repository
                    return await self._reactivate_repository(existing_repo, oauth_integration)
            
            # Initialize enhanced GitHub API client with rate limiting
            api_client = create_github_api_client(oauth_integration.access_token)
            
            try:
                # Verify repository access and get repository info
                repo_info = await self._verify_repository_access(api_client, repo_name)
            
                # Set up webhook only if we have sufficient permissions
                webhook_info = None
                if repo_info.get("can_setup_webhook", False):
                    try:
                        webhook_info = await self._setup_repository_webhook(
                            api_client,
                            repo_name,
                            webhook_events or self.default_webhook_events
                        )
                        logger.info(f"Webhook successfully set up for {repo_name}")
                    except Exception as webhook_error:
                        logger.warning(f"Failed to set up webhook for {repo_name}: {webhook_error}")
                        # Continue without webhook - we can still connect read-only
                else:
                    logger.info(f"Skipping webhook setup for {repo_name} - insufficient permissions (read-only access)")
                
                # Merge custom settings with defaults
                final_settings = {**self.default_repo_settings}
                if repository_settings:
                    final_settings.update(repository_settings)
                
                # Create repository integration record
                github_repo = GitHubRepository(
                    user_id=user_id,
                    repo_url=repo_url,
                    repo_name=repo_name,
                    webhook_id=webhook_info["webhook_id"] if webhook_info else None,
                    webhook_secret=self.webhook_secret if webhook_info else None,
                    access_token=oauth_integration.access_token,  # Store encrypted in production
                    default_branch=repo_info["default_branch"],
                    repository_settings=final_settings,
                    permissions=repo_info["permissions"],
                    is_active=True
                )
                
                self.db.add(github_repo)
                await self.db.commit()
                await self.db.refresh(github_repo)
                
                logger.info(f"Successfully connected repository {repo_name} for user {user_id}")
                
                # Queue initial repository scan if enabled
                if final_settings.get("auto_analysis", True):
                    await self._queue_initial_repository_scan(github_repo)
                
                return github_repo
                
            finally:
                await api_client.close()
            
        except GithubException as e:
            logger.error(f"GitHub API error connecting repository: {e}")
            if e.status == 404:
                raise GitHubIntegrationError("Repository not found or access denied")
            elif e.status == 403:
                raise GitHubIntegrationError("Insufficient permissions to access repository")
            else:
                raise GitHubIntegrationError(f"GitHub API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting repository: {e}")
            raise GitHubIntegrationError(f"Failed to connect repository: {e}")
    
    async def disconnect_repository(
        self,
        user_id: int,
        repository_id: str,
        remove_webhook: bool = True
    ) -> bool:
        """
        Disconnect a GitHub repository integration.
        
        Args:
            user_id: User ID
            repository_id: Repository integration ID
            remove_webhook: Whether to remove the webhook from GitHub
            
        Returns:
            bool: True if successfully disconnected
            
        Raises:
            GitHubIntegrationError: If disconnection fails
        """
        try:
            # Get repository integration
            repo_integration = await self._get_repository_by_id(repository_id, user_id)
            if not repo_integration:
                raise GitHubIntegrationError("Repository integration not found")
            
            # Remove webhook from GitHub if requested
            if remove_webhook and repo_integration.webhook_id:
                try:
                    await self._remove_repository_webhook(
                        repo_integration.access_token,
                        repo_integration.repo_name,
                        repo_integration.webhook_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to remove webhook from GitHub: {e}")
            
            # Mark repository as inactive
            repo_integration.is_active = False
            repo_integration.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Successfully disconnected repository {repo_integration.repo_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect repository: {e}")
            raise GitHubIntegrationError(f"Failed to disconnect repository: {e}")
    
    async def update_repository_settings(
        self,
        user_id: int,
        repository_id: str,
        settings: Dict[str, Any]
    ) -> GitHubRepository:
        """
        Update repository integration settings.
        
        Args:
            user_id: User ID
            repository_id: Repository integration ID
            settings: New settings to apply
            
        Returns:
            GitHubRepository: Updated repository integration
            
        Raises:
            GitHubIntegrationError: If update fails
        """
        try:
            # Get repository integration
            repo_integration = await self._get_repository_by_id(repository_id, user_id)
            if not repo_integration:
                raise GitHubIntegrationError("Repository integration not found")
            
            # Validate settings
            validated_settings = self._validate_repository_settings(settings)
            
            # Update settings
            current_settings = repo_integration.repository_settings or {}
            current_settings.update(validated_settings)
            repo_integration.repository_settings = current_settings
            repo_integration.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(repo_integration)
            
            logger.info(f"Updated settings for repository {repo_integration.repo_name}")
            return repo_integration
            
        except Exception as e:
            logger.error(f"Failed to update repository settings: {e}")
            raise GitHubIntegrationError(f"Failed to update repository settings: {e}")
    
    async def trigger_pull_request_analysis(
        self,
        repository_id: str,
        pr_number: int,
        force_reanalysis: bool = False,
        user_id: Optional[int] = None
    ) -> str:
        """
        Trigger code analysis for a pull request.
        
        Args:
            repository_id: Repository integration ID
            pr_number: Pull request number
            force_reanalysis: Whether to force reanalysis if already exists
            user_id: Optional user ID for permission checking
            
        Returns:
            str: Background job ID for the analysis
            
        Raises:
            GitHubIntegrationError: If analysis trigger fails
        """
        try:
            # Get repository integration
            repo_integration = await self._get_repository_by_id(repository_id, user_id)
            if not repo_integration:
                raise GitHubIntegrationError("Repository integration not found")
            
            # Check if analysis already exists and is recent
            if not force_reanalysis:
                existing_analysis = await self._get_pr_analysis(repository_id, pr_number)
                if existing_analysis and existing_analysis.status == AnalysisStatus.COMPLETED:
                    # Check if analysis is recent (within last hour)
                    if (datetime.utcnow() - existing_analysis.completed_at).total_seconds() < 3600:
                        logger.info(f"Recent analysis exists for PR {pr_number}, skipping")
                        return existing_analysis.id
            
            # Get PR information from GitHub
            pr_info = await self._get_pull_request_info(
                repo_integration.access_token,
                repo_integration.repo_name,
                pr_number
            )
            
            # Create or update PR analysis record
            pr_analysis = await self._create_or_update_pr_analysis(
                repository_id, pr_number, pr_info, force_reanalysis
            )
            
            # Queue background analysis job
            job_data = {
                "repository_id": repository_id,
                "pr_analysis_id": pr_analysis.id,
                "pr_number": pr_number,
                "repo_name": repo_integration.repo_name,
                "access_token": repo_integration.access_token,
                "settings": repo_integration.repository_settings
            }
            
            job_id = await self.background_job_service.enqueue_job(
                job_type="github_pr_analysis",
                job_data=job_data,
                priority="normal",
                timeout_minutes=repo_integration.repository_settings.get("analysis_timeout_minutes", 30)
            )
            
            # Update PR analysis with job ID
            pr_analysis.analysis_results = {"job_id": job_id}
            await self.db.commit()
            
            logger.info(f"Queued PR analysis job {job_id} for PR {pr_number}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to trigger PR analysis: {e}")
            raise GitHubIntegrationError(f"Failed to trigger PR analysis: {e}")
    
    async def get_repository_webhooks_status(
        self,
        user_id: int,
        repository_id: str
    ) -> Dict[str, Any]:
        """
        Get webhook status and configuration for a repository.
        
        Args:
            user_id: User ID
            repository_id: Repository integration ID
            
        Returns:
            Dict containing webhook status and configuration
            
        Raises:
            GitHubIntegrationError: If status check fails
        """
        try:
            # Get repository integration
            repo_integration = await self._get_repository_by_id(repository_id, user_id)
            if not repo_integration:
                raise GitHubIntegrationError("Repository integration not found")
            
            # Check webhook status on GitHub
            webhook_status = await self._check_webhook_status(
                repo_integration.access_token,
                repo_integration.repo_name,
                repo_integration.webhook_id
            )
            
            return {
                "repository_id": repository_id,
                "repo_name": repo_integration.repo_name,
                "webhook_id": repo_integration.webhook_id,
                "webhook_active": webhook_status["active"],
                "webhook_events": webhook_status["events"],
                "webhook_url": webhook_status["url"],
                "last_delivery": webhook_status.get("last_delivery"),
                "delivery_count": webhook_status.get("delivery_count", 0),
                "recent_deliveries": webhook_status.get("recent_deliveries", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get webhook status: {e}")
            raise GitHubIntegrationError(f"Failed to get webhook status: {e}")
    
    async def list_user_repositories(
        self,
        user_id: int,
        include_inactive: bool = False,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        List GitHub repositories connected by a user.
        
        Args:
            user_id: User ID
            include_inactive: Whether to include inactive repositories
            page: Page number for pagination
            per_page: Items per page
            
        Returns:
            Dict containing repositories and pagination info
        """
        try:
            offset = (page - 1) * per_page
            
            # Build query
            query = select(GitHubRepository).where(GitHubRepository.user_id == user_id)
            
            if not include_inactive:
                query = query.where(GitHubRepository.is_active == True)
            
            query = query.order_by(GitHubRepository.created_at.desc()).offset(offset).limit(per_page)
            
            # Execute query
            result = await self.db.execute(query)
            repositories = result.scalars().all()
            
            # Get total count
            count_query = select(GitHubRepository).where(GitHubRepository.user_id == user_id)
            if not include_inactive:
                count_query = count_query.where(GitHubRepository.is_active == True)
            
            from sqlalchemy import func
            count_result = await self.db.execute(select(func.count()).select_from(count_query.subquery()))
            total = count_result.scalar()
            
            return {
                "repositories": [self._format_repository_response(repo) for repo in repositories],
                "total": total,
                "page": page,
                "per_page": per_page,
                "has_next": (page * per_page) < total,
                "has_prev": page > 1
            }
            
        except Exception as e:
            logger.error(f"Failed to list user repositories: {e}")
            raise GitHubIntegrationError(f"Failed to list repositories: {e}")
    
    # Private helper methods
    
    def _extract_repo_name(self, repo_url: str) -> Optional[str]:
        """Extract owner/repo from GitHub URL."""
        try:
            parsed = urlparse(repo_url)
            if parsed.hostname not in ['github.com', 'www.github.com']:
                return None
            
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                owner, repo = path_parts[0], path_parts[1]
                # Remove .git suffix if present
                if repo.endswith('.git'):
                    repo = repo[:-4]
                return f"{owner}/{repo}"
            return None
        except Exception:
            return None
    
    async def _verify_repository_access(
        self,
        api_client: GitHubAPIClient,
        repo_name: str
    ) -> Dict[str, Any]:
        """Verify access to repository and get basic info."""
        def get_repo_info():
            github_client = api_client.get_github_client()
            repo = github_client.get_repo(repo_name)
            
            # Get repository permissions
            permissions = {
                "admin": repo.permissions.admin,
                "push": repo.permissions.push,
                "pull": repo.permissions.pull
            }
            
            # Note: We'll allow read-only access, but webhook setup will be skipped
            # if not repo.permissions.admin and not repo.permissions.push:
            #     raise GitHubIntegrationError(
            #         "Insufficient permissions. Admin or push access required for webhook setup."
            #     )
            
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "default_branch": repo.default_branch,
                "private": repo.private,
                "permissions": permissions,
                "description": repo.description,
                "language": repo.language,
                "size": repo.size,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "can_setup_webhook": repo.permissions.admin or repo.permissions.push
            }
        
        return await api_client.execute_with_retry(
            get_repo_info,
            f"verify_repository_access_{repo_name}"
        )
    
    async def _setup_repository_webhook(
        self,
        api_client: GitHubAPIClient,
        repo_name: str,
        webhook_events: List[str]
    ) -> Dict[str, Any]:
        """Set up webhook for repository."""
        def setup_webhook():
            github_client = api_client.get_github_client()
            repo = github_client.get_repo(repo_name)
            
            # Check for existing webhooks with our URL
            existing_webhooks = repo.get_hooks()
            webhook_url = f"{self.webhook_base_url}/api/v1/github/webhook"
            
            for hook in existing_webhooks:
                if hook.config.get("url") == webhook_url:
                    logger.info(f"Webhook already exists for {repo_name}, updating configuration")
                    # Update existing webhook
                    hook.edit(
                        config={
                            "url": webhook_url,
                            "content_type": "json",
                            "secret": self.webhook_secret,
                            "insecure_ssl": "0"
                        },
                        events=webhook_events,
                        active=True
                    )
                    return {
                        "webhook_id": str(hook.id),
                        "webhook_url": webhook_url,
                        "events": webhook_events,
                        "active": True
                    }
            
            # Create new webhook
            webhook_config = {
                "url": webhook_url,
                "content_type": "json",
                "secret": self.webhook_secret,
                "insecure_ssl": "0"
            }
            
            webhook = repo.create_hook(
                name="web",
                config=webhook_config,
                events=webhook_events,
                active=True
            )
            
            logger.info(f"Created webhook {webhook.id} for repository {repo_name}")
            
            return {
                "webhook_id": str(webhook.id),
                "webhook_url": webhook_url,
                "events": webhook_events,
                "active": True
            }
        
        return await api_client.execute_with_retry(
            setup_webhook,
            f"setup_webhook_{repo_name}"
        )
    
    async def _remove_repository_webhook(
        self,
        access_token: str,
        repo_name: str,
        webhook_id: str
    ) -> bool:
        """Remove webhook from repository."""
        api_client = create_github_api_client(access_token)
        
        try:
            def remove_webhook():
                github_client = api_client.get_github_client()
                repo = github_client.get_repo(repo_name)
                
                webhook = repo.get_hook(int(webhook_id))
                webhook.delete()
                
                logger.info(f"Removed webhook {webhook_id} from repository {repo_name}")
                return True
            
            return await api_client.execute_with_retry(
                remove_webhook,
                f"remove_webhook_{repo_name}_{webhook_id}"
            )
            
        except GitHubIntegrationError as e:
            if "not_found" in str(e).lower():
                logger.warning(f"Webhook {webhook_id} not found in repository {repo_name}")
                return True  # Consider it successful if webhook doesn't exist
            else:
                logger.error(f"Failed to remove webhook: {e}")
                raise
        finally:
            await api_client.close()
    
    async def _check_webhook_status(
        self,
        access_token: str,
        repo_name: str,
        webhook_id: str
    ) -> Dict[str, Any]:
        """Check webhook status on GitHub."""
        api_client = create_github_api_client(access_token)
        
        try:
            def check_webhook():
                github_client = api_client.get_github_client()
                repo = github_client.get_repo(repo_name)
                
                webhook = repo.get_hook(int(webhook_id))
                
                # Get recent deliveries
                deliveries = []
                try:
                    for delivery in webhook.get_deliveries()[:5]:  # Get last 5 deliveries
                        deliveries.append({
                            "id": delivery.id,
                            "delivered_at": delivery.delivered_at.isoformat() if delivery.delivered_at else None,
                            "status_code": delivery.status_code,
                            "event": delivery.event,
                            "action": delivery.action
                        })
                except Exception as e:
                    logger.warning(f"Failed to get webhook deliveries: {e}")
                
                return {
                    "active": webhook.active,
                    "events": webhook.events,
                    "url": webhook.config.get("url"),
                    "last_delivery": deliveries[0]["delivered_at"] if deliveries else None,
                    "delivery_count": len(deliveries),
                    "recent_deliveries": deliveries
                }
            
            return await api_client.execute_with_retry(
                check_webhook,
                f"check_webhook_status_{repo_name}_{webhook_id}"
            )
            
        except GitHubIntegrationError as e:
            if "not_found" in str(e).lower():
                return {
                    "active": False,
                    "events": [],
                    "url": None,
                    "error": "Webhook not found"
                }
            else:
                raise
        finally:
            await api_client.close()
    
    async def _get_repository_by_url(
        self,
        repo_url: str,
        user_id: Optional[int] = None
    ) -> Optional[GitHubRepository]:
        """Get repository integration by URL."""
        query = select(GitHubRepository).where(GitHubRepository.repo_url == repo_url)
        if user_id:
            query = query.where(GitHubRepository.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_repository_by_id(
        self,
        repository_id: str,
        user_id: Optional[int] = None
    ) -> Optional[GitHubRepository]:
        """Get repository integration by ID."""
        query = select(GitHubRepository).where(GitHubRepository.id == repository_id)
        if user_id:
            query = query.where(GitHubRepository.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_pr_analysis(
        self,
        repository_id: str,
        pr_number: int
    ) -> Optional[PRAnalysis]:
        """Get existing PR analysis."""
        result = await self.db.execute(
            select(PRAnalysis).where(
                PRAnalysis.repository_id == repository_id,
                PRAnalysis.pr_number == pr_number
            ).order_by(PRAnalysis.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def _get_pull_request_info(
        self,
        access_token: str,
        repo_name: str,
        pr_number: int
    ) -> Dict[str, Any]:
        """Get pull request information from GitHub."""
        api_client = create_github_api_client(access_token)
        
        try:
            def get_pr_info():
                github_client = api_client.get_github_client()
                repo = github_client.get_repo(repo_name)
                pr = repo.get_pull(pr_number)
                
                return {
                    "title": pr.title,
                    "author": pr.user.login,
                    "head_sha": pr.head.sha,
                    "base_sha": pr.base.sha,
                    "head_branch": pr.head.ref,
                    "base_branch": pr.base.ref,
                    "state": pr.state,
                    "created_at": pr.created_at.isoformat() if pr.created_at else None,
                    "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                    "html_url": pr.html_url
                }
            
            return await api_client.execute_with_retry(
                get_pr_info,
                f"get_pull_request_info_{repo_name}_{pr_number}"
            )
            
        finally:
            await api_client.close()
    
    async def _create_or_update_pr_analysis(
        self,
        repository_id: str,
        pr_number: int,
        pr_info: Dict[str, Any],
        force_reanalysis: bool = False
    ) -> PRAnalysis:
        """Create or update PR analysis record."""
        existing_analysis = await self._get_pr_analysis(repository_id, pr_number)
        
        if existing_analysis and not force_reanalysis:
            # Update existing analysis
            existing_analysis.pr_title = pr_info["title"]
            existing_analysis.pr_author = pr_info["author"]
            existing_analysis.head_sha = pr_info["head_sha"]
            existing_analysis.base_sha = pr_info["base_sha"]
            existing_analysis.head_branch = pr_info["head_branch"]
            existing_analysis.base_branch = pr_info["base_branch"]
            existing_analysis.status = AnalysisStatus.PENDING
            existing_analysis.updated_at = datetime.utcnow()
            
            pr_analysis = existing_analysis
        else:
            # Create new analysis
            pr_analysis = PRAnalysis(
                repository_id=repository_id,
                pr_number=pr_number,
                pr_title=pr_info["title"],
                pr_author=pr_info["author"],
                head_sha=pr_info["head_sha"],
                base_sha=pr_info["base_sha"],
                head_branch=pr_info["head_branch"],
                base_branch=pr_info["base_branch"],
                status=AnalysisStatus.PENDING
            )
            self.db.add(pr_analysis)
        
        await self.db.commit()
        await self.db.refresh(pr_analysis)
        
        return pr_analysis
    
    async def _reactivate_repository(
        self,
        repo_integration: GitHubRepository,
        oauth_integration: GitHubOAuthIntegration
    ) -> GitHubRepository:
        """Reactivate an inactive repository integration."""
        try:
            # Update access token in case it changed
            repo_integration.access_token = oauth_integration.access_token
            repo_integration.is_active = True
            repo_integration.updated_at = datetime.utcnow()
            
            # Verify webhook still exists and is active
            try:
                webhook_status = await self._check_webhook_status(
                    oauth_integration.access_token,
                    repo_integration.repo_name,
                    repo_integration.webhook_id
                )
                
                if not webhook_status.get("active"):
                    # Recreate webhook if inactive
                    api_client = create_github_api_client(oauth_integration.access_token)
                    try:
                        webhook_info = await self._setup_repository_webhook(
                            api_client,
                            repo_integration.repo_name,
                            self.default_webhook_events
                        )
                        repo_integration.webhook_id = webhook_info["webhook_id"]
                    finally:
                        await api_client.close()
                    
            except Exception as e:
                logger.warning(f"Failed to verify webhook during reactivation: {e}")
            
            await self.db.commit()
            await self.db.refresh(repo_integration)
            
            logger.info(f"Reactivated repository {repo_integration.repo_name}")
            return repo_integration
            
        except Exception as e:
            logger.error(f"Failed to reactivate repository: {e}")
            raise GitHubIntegrationError(f"Failed to reactivate repository: {e}")
    
    async def _queue_initial_repository_scan(self, repo_integration: GitHubRepository) -> None:
        """Queue initial repository scan for recent PRs."""
        try:
            job_data = {
                "repository_id": repo_integration.id,
                "repo_name": repo_integration.repo_name,
                "access_token": repo_integration.access_token,
                "scan_type": "initial",
                "max_prs": 5  # Scan last 5 PRs
            }
            
            await self.background_job_service.enqueue_job(
                job_type="github_repository_scan",
                job_data=job_data,
                priority="low",
                timeout_minutes=60
            )
            
            logger.info(f"Queued initial scan for repository {repo_integration.repo_name}")
            
        except Exception as e:
            # Don't fail repository connection if background job fails
            logger.warning(f"Failed to queue initial repository scan: {e}")
            # Continue without the initial scan
    
    def _validate_repository_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize repository settings."""
        validated = {}
        
        # Boolean settings
        bool_settings = [
            "auto_analysis", "create_issues", "comment_on_prs", 
            "analysis_on_push", "enable_inline_comments"
        ]
        for key in bool_settings:
            if key in settings:
                validated[key] = bool(settings[key])
        
        # String settings with validation
        if "min_severity_for_issues" in settings:
            severity = settings["min_severity_for_issues"]
            if severity in ["info", "warning", "error", "critical"]:
                validated["min_severity_for_issues"] = severity
        
        # Integer settings with bounds
        if "max_issues_per_pr" in settings:
            max_issues = int(settings["max_issues_per_pr"])
            validated["max_issues_per_pr"] = max(1, min(max_issues, 50))
        
        if "analysis_timeout_minutes" in settings:
            timeout = int(settings["analysis_timeout_minutes"])
            validated["analysis_timeout_minutes"] = max(5, min(timeout, 120))
        
        return validated
    
    def _format_repository_response(self, repo: GitHubRepository) -> Dict[str, Any]:
        """Format repository for API response."""
        return {
            "id": str(repo.id),  # Ensure string
            "repo_url": repo.repo_url,
            "repo_name": repo.repo_name,
            "default_branch": repo.default_branch or "main",  # Default if None
            "webhook_id": repo.webhook_id,
            "webhook_status": "active" if repo.is_active else "inactive",
            "repository_settings": repo.repository_settings or {},  # Default to empty dict
            "permissions": repo.permissions or {"admin": False, "push": False, "pull": True},  # Default permissions
            "created_at": repo.created_at,  # Keep as datetime for Pydantic
            "updated_at": repo.updated_at   # Keep as datetime for Pydantic
        }
