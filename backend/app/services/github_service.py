"""
GitHub Integration Service

This service handles GitHub API interactions, webhook processing, and automated code analysis
for pull requests. It provides methods for repository management, PR analysis, and issue creation.

Requirements covered: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse

import httpx
from github import Github, GithubException
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.Issue import Issue
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.github_integration import GitHubRepository, PRAnalysis, AnalysisStatus
from app.services.github_api_client import GitHubAPIClient, create_github_api_client
from app.models.users import User
from app.services.analysis_service import AnalysisService
from app.services.cache_service import CacheService
from app.services.github_api_client import GitHubAPIClient, create_github_api_client
from app.core.exceptions import GitHubIntegrationError

logger = logging.getLogger(__name__)


class GitHubService:
    """
    Service for GitHub integration including OAuth, webhooks, and automated analysis.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.analysis_service = AnalysisService(db_session)
        self.cache_service = CacheService()
        
        # GitHub API configuration
        self.github_app_id = settings.GITHUB_APP_ID
        self.github_private_key = self._load_private_key()
        self.webhook_secret = settings.GITHUB_WEBHOOK_SECRET
        self.client_id = settings.GITHUB_CLIENT_ID
        self.client_secret = settings.GITHUB_CLIENT_SECRET
        
        # Initialize GitHub client
        self.github_client = None
        if self.github_private_key:
            self.github_client = Github(auth=self._get_github_auth())

    def _load_private_key(self) -> Optional[str]:
        """Load GitHub App private key from file or environment variable."""
        try:
            if hasattr(settings, 'GITHUB_PRIVATE_KEY') and settings.GITHUB_PRIVATE_KEY:
                return settings.GITHUB_PRIVATE_KEY
            
            if hasattr(settings, 'GITHUB_PRIVATE_KEY_PATH') and settings.GITHUB_PRIVATE_KEY_PATH:
                with open(settings.GITHUB_PRIVATE_KEY_PATH, 'r') as key_file:
                    return key_file.read()
            
            logger.warning("GitHub private key not found in environment or file")
            return None
        except Exception as e:
            logger.error(f"Failed to load GitHub private key: {e}")
            return None

    def _get_github_auth(self):
        """Get GitHub authentication object."""
        from github import Auth
        return Auth.AppAuth(self.github_app_id, self.github_private_key)

    async def setup_repository_webhook(
        self, 
        user_id: int, 
        repo_url: str, 
        access_token: str
    ) -> GitHubRepository:
        """
        Set up webhook for a GitHub repository.
        
        Requirements: 8.1, 8.2
        """
        try:
            # Parse repository URL
            repo_name = self._extract_repo_name(repo_url)
            if not repo_name:
                raise GitHubIntegrationError("Invalid repository URL format")

            # Initialize enhanced GitHub API client with rate limiting
            api_client = create_github_api_client(access_token)
            
            def get_repo():
                user_github = api_client.get_github_client()
                return user_github.get_repo(repo_name)
            
            repo = await api_client.execute_with_retry(get_repo, f"get_repo_{repo_name}")

            # Check if repository integration already exists
            existing_repo = await self._get_repository_by_url(repo_url, user_id)
            if existing_repo:
                logger.info(f"Repository {repo_name} already integrated for user {user_id}")
                return existing_repo

            # Create webhook with retry logic
            def create_webhook():
                webhook_config = {
                    "url": f"{settings.GITHUB_WEBHOOK_BASE_URL}/webhook",
                    "content_type": "json",
                    "secret": self.webhook_secret,
                    "insecure_ssl": "0"
                }
                
                webhook_events = ["pull_request", "push"]
                return repo.create_hook("web", webhook_config, webhook_events, active=True)
            
            webhook = await api_client.execute_with_retry(create_webhook, f"create_webhook_{repo_name}")

            # Store repository integration
            github_repo = GitHubRepository(
                user_id=user_id,
                repo_url=repo_url,
                repo_name=repo_name,
                webhook_id=str(webhook.id),
                webhook_secret=self.webhook_secret,
                access_token=access_token,  # Store encrypted in production
                default_branch=repo.default_branch,
                repository_settings={
                    "auto_analysis": True,
                    "create_issues": True,
                    "comment_on_prs": True
                },
                permissions={
                    "contents": "read",
                    "issues": "write",
                    "pull_requests": "write"
                }
            )

            self.db.add(github_repo)
            await self.db.commit()
            await self.db.refresh(github_repo)

            logger.info(f"Successfully set up webhook for repository {repo_name}")
            return github_repo

        except GitHubIntegrationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error setting up webhook: {e}")
            raise GitHubIntegrationError(f"Failed to set up repository integration: {e}")
        finally:
            if 'api_client' in locals():
                await api_client.close()

    async def handle_webhook_event(self, headers: Dict[str, str], payload: bytes) -> Dict[str, Any]:
        """
        Handle incoming GitHub webhook events.
        
        Requirements: 8.3, 8.4
        """
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(headers, payload):
                raise GitHubIntegrationError("Invalid webhook signature")

            # Parse payload
            event_data = json.loads(payload.decode('utf-8'))
            event_type = headers.get('X-GitHub-Event', '')

            logger.info(f"Received GitHub webhook event: {event_type}")

            # Handle different event types
            if event_type == "pull_request":
                return await self._handle_pull_request_event(event_data)
            elif event_type == "push":
                return await self._handle_push_event(event_data)
            elif event_type == "ping":
                return {"status": "success", "message": "Webhook ping received"}
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {"status": "ignored", "message": f"Event type {event_type} not handled"}

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse webhook payload: {e}")
            raise GitHubIntegrationError("Invalid JSON payload")
        except Exception as e:
            logger.error(f"Error handling webhook event: {e}")
            raise GitHubIntegrationError(f"Failed to process webhook: {e}")

    async def analyze_pull_request(
        self, 
        repository_id: str, 
        pr_number: int, 
        force_reanalysis: bool = False
    ) -> PRAnalysis:
        """
        Analyze a pull request and create issues if needed.
        
        Requirements: 8.4, 8.5
        """
        try:
            # Get repository integration
            repo_integration = await self._get_repository_by_id(repository_id)
            if not repo_integration:
                raise GitHubIntegrationError("Repository integration not found")

            # Check for existing analysis
            existing_analysis = await self._get_pr_analysis(repository_id, pr_number)
            if existing_analysis and not force_reanalysis:
                logger.info(f"PR analysis already exists for {pr_number}")
                return existing_analysis

            # Initialize enhanced GitHub API client
            api_client = create_github_api_client(repo_integration.access_token)
            
            def get_repo_and_pr():
                github = api_client.get_github_client()
                repo = github.get_repo(repo_integration.repo_name)
                pr = repo.get_pull(pr_number)
                return repo, pr
            
            repo, pr = await api_client.execute_with_retry(
                get_repo_and_pr, 
                f"get_repo_pr_{repo_integration.repo_name}_{pr_number}"
            )

            # Create or update PR analysis record
            pr_analysis = existing_analysis or PRAnalysis(
                repository_id=repository_id,
                pr_number=pr_number,
                pr_title=pr.title,
                pr_author=pr.user.login,
                head_sha=pr.head.sha,
                base_sha=pr.base.sha,
                head_branch=pr.head.ref,
                base_branch=pr.base.ref,
                status=AnalysisStatus.PENDING
            )

            if not existing_analysis:
                self.db.add(pr_analysis)
            
            pr_analysis.status = AnalysisStatus.IN_PROGRESS
            pr_analysis.started_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(pr_analysis)

            # Get changed files in the PR with retry logic
            changed_files = await self._get_pr_changed_files(api_client, repo, pr)
            
            # Analyze each changed file
            analysis_results = []
            total_issues = 0
            total_errors = 0
            total_warnings = 0

            for file_data in changed_files:
                try:
                    file_analysis = await self.analysis_service.analyze_code_content(
                        content=file_data['content'],
                        filename=file_data['filename'],
                        language=file_data.get('language', 'unknown')
                    )
                    
                    analysis_results.append({
                        'filename': file_data['filename'],
                        'analysis': file_analysis,
                        'changes': file_data.get('changes', [])
                    })
                    
                    # Count issues
                    if file_analysis.get('issues'):
                        for issue in file_analysis['issues']:
                            total_issues += 1
                            if issue.get('severity') == 'error':
                                total_errors += 1
                            elif issue.get('severity') == 'warning':
                                total_warnings += 1

                except Exception as e:
                    logger.error(f"Failed to analyze file {file_data['filename']}: {e}")
                    analysis_results.append({
                        'filename': file_data['filename'],
                        'error': str(e)
                    })

            # Update analysis record with results
            pr_analysis.analysis_results = {
                'files': analysis_results,
                'summary': {
                    'total_files': len(changed_files),
                    'total_issues': total_issues,
                    'total_errors': total_errors,
                    'total_warnings': total_warnings
                },
                'metadata': {
                    'analyzed_at': datetime.utcnow().isoformat(),
                    'pr_url': pr.html_url,
                    'commit_sha': pr.head.sha
                }
            }
            
            pr_analysis.issues_found = total_issues
            pr_analysis.errors_count = total_errors
            pr_analysis.warnings_count = total_warnings
            pr_analysis.status = AnalysisStatus.COMPLETED
            pr_analysis.completed_at = datetime.utcnow()

            # Create GitHub issues and comments if configured
            if repo_integration.repository_settings.get('create_issues', True) and total_issues > 0:
                created_issues = await self._create_github_issues(api_client, repo, pr_analysis)
                pr_analysis.issues_created = created_issues

            if repo_integration.repository_settings.get('comment_on_prs', True):
                comment_ids = await self._post_pr_comments(api_client, repo, pr, pr_analysis)
                pr_analysis.comments_posted = comment_ids

            await self.db.commit()
            await self.db.refresh(pr_analysis)

            logger.info(f"Successfully analyzed PR {pr_number} with {total_issues} issues found")
            return pr_analysis

        except GitHubIntegrationError:
            # Update analysis record with error
            if 'pr_analysis' in locals():
                pr_analysis.status = AnalysisStatus.FAILED
                pr_analysis.error_message = str(e)
                pr_analysis.completed_at = datetime.utcnow()
                await self.db.commit()
            raise
        except Exception as e:
            # Update analysis record with error
            if 'pr_analysis' in locals():
                pr_analysis.status = AnalysisStatus.FAILED
                pr_analysis.error_message = str(e)
                pr_analysis.completed_at = datetime.utcnow()
                await self.db.commit()
            
            logger.error(f"Failed to analyze PR {pr_number}: {e}")
            raise GitHubIntegrationError(f"PR analysis failed: {e}")
        finally:
            if 'api_client' in locals():
                await api_client.close()

    async def create_repository_issue(
        self, 
        repository_id: str, 
        title: str, 
        body: str, 
        labels: List[str] = None
    ) -> str:
        """
        Create an issue in the GitHub repository.
        
        Requirements: 8.5
        """
        try:
            # Get repository integration
            repo_integration = await self._get_repository_by_id(repository_id)
            if not repo_integration:
                raise GitHubIntegrationError("Repository integration not found")

            # Initialize enhanced GitHub API client
            api_client = create_github_api_client(repo_integration.access_token)
            
            try:
                def create_issue():
                    github = api_client.get_github_client()
                    repo = github.get_repo(repo_integration.repo_name)
                    return repo.create_issue(
                        title=title,
                        body=body,
                        labels=labels or []
                    )
                
                issue = await api_client.execute_with_retry(
                    create_issue,
                    f"create_issue_{repo_integration.repo_name}"
                )

                logger.info(f"Created GitHub issue #{issue.number} in {repo_integration.repo_name}")
                return issue.html_url
            
            finally:
                await api_client.close()

        except GitHubIntegrationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating issue: {e}")
            raise GitHubIntegrationError(f"Failed to create repository issue: {e}")

    async def get_oauth_authorization_url(self, state: str = None) -> str:
        """
        Generate GitHub OAuth authorization URL.
        
        Requirements: 8.1
        """
        base_url = "https://github.com/login/oauth/authorize"
        params = {
            "client_id": self.client_id,
            "redirect_uri": settings.GITHUB_OAUTH_REDIRECT_URI,
            "scope": "repo,user:email",
            "state": state or ""
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"

    async def exchange_oauth_code(self, code: str, state: str = None) -> Dict[str, Any]:
        """
        Exchange OAuth code for access token.
        
        Requirements: 8.1
        """
        print(f"DEBUG: Starting OAuth exchange for code: {code[:10]}..., state: {state}")
        logger.error(f"DEBUG: Starting OAuth exchange for code: {code[:10]}..., state: {state}")
        try:
            # Use enhanced API client for OAuth exchange
            logger.error("DEBUG: Creating GitHub API client for OAuth exchange")
            api_client = GitHubAPIClient(enable_rate_limit_handling=True)
            user_data = None  # Initialize user_data
            
            try:
                logger.error("DEBUG: Making OAuth token exchange request")
                response = await api_client.http_request_with_retry(
                    "POST",
                    "https://github.com/login/oauth/access_token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "redirect_uri": settings.GITHUB_OAUTH_REDIRECT_URI
                    },
                    headers={"Accept": "application/json"}
                )
                
                logger.error(f"DEBUG: OAuth exchange response status: {response.status_code}")
                logger.error(f"DEBUG: OAuth exchange response headers: {dict(response.headers)}")
                logger.error(f"DEBUG: OAuth exchange response content: '{response.text}'")
                
                if response.status_code != 200:
                    raise GitHubIntegrationError("Failed to exchange OAuth code")
                
                # Handle both JSON and plain text responses from GitHub
                try:
                    token_data = response.json()
                    logger.error(f"DEBUG: OAuth response parsed as JSON: {token_data}")
                except ValueError as json_error:
                    # GitHub sometimes returns the token as plain text
                    response_text = response.text.strip()
                    logger.error(f"DEBUG: OAuth response parsed as plain text: '{response_text}' (JSON error: {json_error})")
                    if response_text.startswith('gho_') or response_text.startswith('"gho_'):
                        # It's a GitHub access token (might be quoted)
                        clean_token = response_text.strip('"')
                        token_data = {
                            'access_token': clean_token,
                            'token_type': 'bearer',
                            'scope': ''
                        }
                        logger.error(f"DEBUG: Parsed GitHub token: {clean_token[:10]}...")
                    else:
                        logger.error(f"DEBUG: Invalid OAuth response format: {response_text[:100]}")
                        raise GitHubIntegrationError(f"Invalid OAuth response format: {response_text[:100]}")
                
                if "error" in token_data:
                    raise GitHubIntegrationError(f"OAuth error: {token_data['error_description']}")
                
                if "access_token" not in token_data:
                    raise GitHubIntegrationError("Invalid OAuth response: missing access_token")
                
                logger.error(f"DEBUG: About to create API client with token: {token_data['access_token'][:10]}...")
                try:
                    user_api_client = create_github_api_client(token_data['access_token'])
                    logger.error("DEBUG: API client created successfully")
                except Exception as client_error:
                    logger.error(f"DEBUG: Exception during API client creation: {client_error}")
                    raise
                try:
                    logger.error("DEBUG: About to fetch user data...")
                    user_response = await user_api_client.http_request_with_retry(
                        "GET",
                        "https://api.github.com/user"
                    )
                    
                    logger.error(f"DEBUG: User API response status: {user_response.status_code}")
                    logger.error(f"DEBUG: User API response headers: {dict(user_response.headers)}")
                    
                    if user_response.status_code != 200:
                        logger.error(f"GitHub user API returned status {user_response.status_code}: {user_response.text}")
                        raise GitHubIntegrationError(f"Failed to fetch user data: HTTP {user_response.status_code}")
                    
                    try:
                        user_data = user_response.json()
                        logger.error(f"DEBUG: User data fetched successfully: {user_data.get('login', 'unknown')}")
                    except ValueError as json_error:
                        logger.error(f"Failed to parse user data as JSON: {user_response.text} (error: {json_error})")
                        raise GitHubIntegrationError(f"Invalid JSON response from GitHub user API: {user_response.text[:100]}")
                        
                except Exception as user_fetch_error:
                    logger.error(f"Error during user data fetch: {user_fetch_error}")
                    raise
                finally:
                    await user_api_client.close()
            
            finally:
                await api_client.close()
                
            # Check if user_data was successfully retrieved
            if user_data is None:
                raise GitHubIntegrationError("Failed to retrieve user information from GitHub")
                
            return {
                "access_token": token_data["access_token"],
                "token_type": token_data.get("token_type", "bearer"),
                "scope": token_data.get("scope", ""),
                "user": {
                    "id": user_data["id"],
                    "login": user_data["login"],
                    "email": user_data.get("email"),
                    "name": user_data.get("name")
                }
            }

        except GitHubIntegrationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during OAuth exchange: {e}")
            raise GitHubIntegrationError(f"OAuth exchange failed: {e}")

    # Private helper methods

    def _extract_repo_name(self, repo_url: str) -> Optional[str]:
        """Extract owner/repo from GitHub URL."""
        try:
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                return f"{path_parts[0]}/{path_parts[1]}"
            return None
        except Exception:
            return None

    def _verify_webhook_signature(self, headers: Dict[str, str], payload: bytes) -> bool:
        """Verify GitHub webhook signature."""
        signature = headers.get('X-Hub-Signature-256', '')
        if not signature:
            return False
        
        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)

    async def _handle_pull_request_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pull request webhook events."""
        action = event_data.get('action')
        pr_data = event_data.get('pull_request', {})
        repo_data = event_data.get('repository', {})
        
        if action in ['opened', 'synchronize', 'reopened']:
            # Find repository integration
            repo_url = repo_data.get('html_url', '')
            repo_integration = await self._get_repository_by_url(repo_url)
            
            if repo_integration:
                # Trigger PR analysis asynchronously
                asyncio.create_task(
                    self.analyze_pull_request(
                        repository_id=repo_integration.id,
                        pr_number=pr_data.get('number'),
                        force_reanalysis=(action == 'synchronize')
                    )
                )
                
                return {
                    "status": "success",
                    "message": f"PR analysis triggered for #{pr_data.get('number')}"
                }
        
        return {"status": "ignored", "message": f"PR action '{action}' not handled"}

    async def _handle_push_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle push webhook events."""
        # For future implementation - could trigger branch analysis
        return {"status": "ignored", "message": "Push events not yet implemented"}

    async def _get_repository_by_url(self, repo_url: str, user_id: int = None) -> Optional[GitHubRepository]:
        """Get repository integration by URL."""
        query = select(GitHubRepository).where(GitHubRepository.repo_url == repo_url)
        if user_id:
            query = query.where(GitHubRepository.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_repository_by_id(self, repository_id: str) -> Optional[GitHubRepository]:
        """Get repository integration by ID."""
        result = await self.db.execute(
            select(GitHubRepository).where(GitHubRepository.id == repository_id)
        )
        return result.scalar_one_or_none()

    async def _get_pr_analysis(self, repository_id: str, pr_number: int) -> Optional[PRAnalysis]:
        """Get existing PR analysis."""
        result = await self.db.execute(
            select(PRAnalysis).where(
                PRAnalysis.repository_id == repository_id,
                PRAnalysis.pr_number == pr_number
            )
        )
        return result.scalar_one_or_none()

    async def _get_pr_changed_files(self, api_client: GitHubAPIClient, repo: Repository, pr: PullRequest) -> List[Dict[str, Any]]:
        """Get changed files in a pull request with their content."""
        changed_files = []
        
        def get_files():
            return pr.get_files()
        
        try:
            files = await api_client.execute_with_retry(get_files, "get_pr_files")
            
            for file in files:
                if file.status in ['added', 'modified']:
                    try:
                        # Get file content with retry logic
                        def get_file_content():
                            file_content = repo.get_contents(file.filename, ref=pr.head.sha)
                            return file_content.decoded_content.decode('utf-8')
                        
                        content = await api_client.execute_with_retry(
                            get_file_content, 
                            f"get_file_content_{file.filename}"
                        )
                        
                        changed_files.append({
                            'filename': file.filename,
                            'content': content,
                            'status': file.status,
                            'additions': file.additions,
                            'deletions': file.deletions,
                            'changes': file.changes,
                            'language': self._detect_language(file.filename)
                        })
                    except Exception as e:
                        logger.warning(f"Failed to get content for file {file.filename}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to get PR changed files: {e}")
            
        return changed_files

    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala'
        }
        
        for ext, lang in extension_map.items():
            if filename.lower().endswith(ext):
                return lang
        
        return 'unknown'

    async def _create_github_issues(self, api_client: GitHubAPIClient, repo: Repository, pr_analysis: PRAnalysis) -> List[str]:
        """Create GitHub issues for analysis results."""
        created_issues = []
        
        try:
            analysis_results = pr_analysis.analysis_results
            if not analysis_results or not analysis_results.get('files'):
                return created_issues
            
            # Group issues by severity
            high_priority_issues = []
            medium_priority_issues = []
            
            for file_result in analysis_results['files']:
                if 'analysis' in file_result and 'issues' in file_result['analysis']:
                    for issue in file_result['analysis']['issues']:
                        issue_data = {
                            'file': file_result['filename'],
                            'line': issue.get('line', 'unknown'),
                            'message': issue.get('message', ''),
                            'severity': issue.get('severity', 'info'),
                            'rule': issue.get('rule', 'unknown')
                        }
                        
                        if issue.get('severity') == 'error':
                            high_priority_issues.append(issue_data)
                        else:
                            medium_priority_issues.append(issue_data)
            
            # Create issues for high priority problems
            if high_priority_issues:
                def create_high_priority_issue():
                    issue_body = self._format_issue_body(high_priority_issues, pr_analysis)
                    return repo.create_issue(
                        title=f"Code Analysis: Critical Issues in PR #{pr_analysis.pr_number}",
                        body=issue_body,
                        labels=['bug', 'code-analysis', 'high-priority']
                    )
                
                issue = await api_client.execute_with_retry(
                    create_high_priority_issue,
                    f"create_high_priority_issue_pr_{pr_analysis.pr_number}"
                )
                created_issues.append(issue.html_url)
            
            # Create issues for medium priority problems if there are many
            if len(medium_priority_issues) > 5:
                def create_medium_priority_issue():
                    issue_body = self._format_issue_body(medium_priority_issues, pr_analysis)
                    return repo.create_issue(
                        title=f"Code Analysis: Quality Issues in PR #{pr_analysis.pr_number}",
                        body=issue_body,
                        labels=['enhancement', 'code-analysis', 'medium-priority']
                    )
                
                issue = await api_client.execute_with_retry(
                    create_medium_priority_issue,
                    f"create_medium_priority_issue_pr_{pr_analysis.pr_number}"
                )
                created_issues.append(issue.html_url)
                
        except Exception as e:
            logger.error(f"Failed to create GitHub issues: {e}")
            
        return created_issues

    async def _post_pr_comments(self, api_client: GitHubAPIClient, repo: Repository, pr: PullRequest, pr_analysis: PRAnalysis) -> List[str]:
        """Post analysis results as PR comments."""
        comment_ids = []
        
        try:
            # Create summary comment with retry logic
            def create_summary_comment():
                summary = self._format_pr_comment_summary(pr_analysis)
                return pr.create_issue_comment(summary)
            
            comment = await api_client.execute_with_retry(
                create_summary_comment,
                f"create_summary_comment_pr_{pr_analysis.pr_number}"
            )
            comment_ids.append(str(comment.id))
            
            # Create inline comments for specific issues (limit to avoid spam)
            inline_comments_posted = 0
            max_inline_comments = 10
            
            analysis_results = pr_analysis.analysis_results
            if analysis_results and analysis_results.get('files'):
                for file_result in analysis_results['files']:
                    if inline_comments_posted >= max_inline_comments:
                        break
                        
                    if 'analysis' in file_result and 'issues' in file_result['analysis']:
                        for issue in file_result['analysis']['issues']:
                            if inline_comments_posted >= max_inline_comments:
                                break
                                
                            if issue.get('severity') == 'error':
                                try:
                                    # Create review comment on specific line with retry logic
                                    def create_review_comment():
                                        return pr.create_review_comment(
                                            body=f"**{issue.get('rule', 'Code Analysis')}**: {issue.get('message', '')}",
                                            commit=repo.get_commit(pr_analysis.head_sha),
                                            path=file_result['filename'],
                                            line=issue.get('line', 1)
                                        )
                                    
                                    await api_client.execute_with_retry(
                                        create_review_comment,
                                        f"create_review_comment_{file_result['filename']}_{issue.get('line', 1)}"
                                    )
                                    inline_comments_posted += 1
                                except Exception as e:
                                    logger.warning(f"Failed to create inline comment: {e}")
                                    
        except Exception as e:
            logger.error(f"Failed to post PR comments: {e}")
            
        return comment_ids

    def _format_issue_body(self, issues: List[Dict[str, Any]], pr_analysis: PRAnalysis) -> str:
        """Format GitHub issue body with analysis results."""
        body = f"""# Code Analysis Results

**Pull Request**: #{pr_analysis.pr_number} - {pr_analysis.pr_title}
**Author**: {pr_analysis.pr_author}
**Analyzed**: {pr_analysis.completed_at.strftime('%Y-%m-%d %H:%M:%S')} UTC

## Issues Found ({len(issues)})

"""
        
        for i, issue in enumerate(issues[:20], 1):  # Limit to first 20 issues
            body += f"""### {i}. {issue['file']} (Line {issue['line']})

**Severity**: {issue['severity'].upper()}
**Rule**: {issue['rule']}
**Message**: {issue['message']}

---

"""
        
        if len(issues) > 20:
            body += f"\n*... and {len(issues) - 20} more issues. Check the full analysis results in the platform dashboard.*\n"
        
        body += f"""
## Summary

- **Total Issues**: {len(issues)}
- **Files Analyzed**: {len(set(issue['file'] for issue in issues))}

*This issue was automatically created by the code analysis system.*
"""
        
        return body

    def _format_pr_comment_summary(self, pr_analysis: PRAnalysis) -> str:
        """Format PR comment with analysis summary."""
        analysis_results = pr_analysis.analysis_results
        summary = analysis_results.get('summary', {})
        
        comment = f"""## 🔍 Code Analysis Results

**Analysis completed** for PR #{pr_analysis.pr_number}

### Summary
- **Files analyzed**: {summary.get('total_files', 0)}
- **Issues found**: {summary.get('total_issues', 0)}
- **Errors**: {summary.get('total_errors', 0)} 🔴
- **Warnings**: {summary.get('total_warnings', 0)} 🟡

"""
        
        if summary.get('total_errors', 0) > 0:
            comment += "⚠️ **Critical issues found** - Please review the errors before merging.\n\n"
        elif summary.get('total_warnings', 0) > 0:
            comment += "ℹ️ **Some warnings found** - Consider addressing them to improve code quality.\n\n"
        else:
            comment += "✅ **No critical issues found** - Code looks good!\n\n"
        
        comment += "*View detailed results in the [platform dashboard](https://yourdomain.com/dashboard)*"
        
        return comment