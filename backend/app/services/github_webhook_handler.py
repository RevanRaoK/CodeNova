"""
GitHub Webhook Handler Service

This service handles GitHub webhook events with signature verification, event routing,
and background job queuing for automated code analysis.

Requirements covered: 3.3, 3.4, 3.6
"""

import asyncio
import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.exceptions import GitHubIntegrationError
from app.models.github_integration import GitHubRepository, PRAnalysis, AnalysisStatus
from app.services.background_job_service import BackgroundJobService, JobPriority, background_job
from app.services.github_service import GitHubService

logger = logging.getLogger(__name__)


class GitHubWebhookHandler:
    """
    Service for handling GitHub webhook events with signature verification and background processing.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.webhook_secret = settings.GITHUB_WEBHOOK_SECRET
        self.background_job_service = BackgroundJobService()
        self.github_service = GitHubService(db_session)

    async def process_webhook(self, headers: Dict[str, str], payload: bytes) -> Dict[str, Any]:
        """
        Process GitHub webhook with signature verification and event routing.
        
        Args:
            headers: HTTP headers from webhook request
            payload: Raw webhook payload bytes
            
        Returns:
            Processing result with event details and queued jobs
            
        Requirements: 3.3, 3.4, 3.6
        """
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(headers, payload):
                raise GitHubIntegrationError("Invalid webhook signature")

            # Parse payload
            try:
                event_data = json.loads(payload.decode('utf-8'))
            except json.JSONDecodeError as e:
                raise GitHubIntegrationError(f"Invalid JSON payload: {e}")

            # Get event type and generate event ID
            event_type = headers.get('x-github-event', '').lower()
            event_id = self._generate_event_id(event_type, event_data)
            
            logger.info(f"Processing GitHub webhook event: {event_type} (ID: {event_id})")

            # Route event to appropriate handler
            result = await self._route_webhook_event(event_type, event_data, event_id)
            
            return {
                "event_id": event_id,
                "event_type": event_type,
                "message": result.get("message", "Event processed successfully"),
                "queue_analysis": result.get("queue_analysis", False),
                "event_data": event_data if result.get("queue_analysis") else None,
                "queued_jobs": result.get("queued_jobs", [])
            }

        except GitHubIntegrationError:
            raise
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise GitHubIntegrationError(f"Failed to process webhook: {e}")

    async def queue_pr_analysis(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Queue background analysis job for pull request events.
        
        Args:
            event_data: GitHub webhook event data
            
        Returns:
            Job queuing result
            
        Requirements: 3.4, 3.6
        """
        try:
            pr_data = event_data.get('pull_request', {})
            repo_data = event_data.get('repository', {})
            action = event_data.get('action', '')
            
            # Find repository integration
            repo_url = repo_data.get('html_url', '')
            repository = await self._get_repository_by_url(repo_url)
            
            if not repository:
                logger.warning(f"No repository integration found for {repo_url}")
                return {"status": "skipped", "reason": "Repository not integrated"}
            
            # Check if analysis should be triggered
            if not self._should_trigger_analysis(action, repository):
                return {"status": "skipped", "reason": f"Action '{action}' does not trigger analysis"}
            
            # Create or update PR analysis record
            pr_analysis = await self._create_or_update_pr_analysis(
                repository.id,
                pr_data,
                action == 'synchronize'  # Force reanalysis on sync
            )
            
            # Queue background analysis job
            job_id = await self.background_job_service.enqueue_job(
                job_name="analyze_github_pr",
                args=[repository.id, pr_data.get('number')],
                kwargs={
                    "pr_analysis_id": pr_analysis.id,
                    "force_reanalysis": action == 'synchronize',
                    "webhook_event_data": {
                        "action": action,
                        "pr_url": pr_data.get('html_url'),
                        "head_sha": pr_data.get('head', {}).get('sha'),
                        "base_sha": pr_data.get('base', {}).get('sha')
                    }
                },
                priority=JobPriority.HIGH,
                user_id=str(repository.user_id),
                metadata={
                    "repository_id": repository.id,
                    "pr_number": pr_data.get('number'),
                    "event_type": "pull_request",
                    "action": action
                }
            )
            
            logger.info(f"Queued PR analysis job {job_id} for PR #{pr_data.get('number')} in {repository.repo_name}")
            
            return {
                "status": "queued",
                "job_id": job_id,
                "pr_analysis_id": pr_analysis.id,
                "repository_id": repository.id,
                "pr_number": pr_data.get('number')
            }
            
        except Exception as e:
            logger.error(f"Failed to queue PR analysis: {e}")
            raise GitHubIntegrationError(f"Failed to queue analysis job: {e}")

    def _verify_webhook_signature(self, headers: Dict[str, str], payload: bytes) -> bool:
        """
        Verify GitHub webhook signature using HMAC-SHA256.
        
        Args:
            headers: HTTP headers containing signature
            payload: Raw webhook payload
            
        Returns:
            True if signature is valid, False otherwise
            
        Requirements: 3.3
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured - skipping signature verification")
            return True  # Allow in development, but log warning
        
        # Get signature from headers (try different header names)
        signature = (
            headers.get('x-hub-signature-256') or 
            headers.get('X-Hub-Signature-256') or
            headers.get('x-hub-signature') or
            headers.get('X-Hub-Signature')
        )
        
        if not signature:
            logger.error("No signature found in webhook headers")
            return False
        
        # Calculate expected signature
        if signature.startswith('sha256='):
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            expected_signature = f"sha256={expected_signature}"
        elif signature.startswith('sha1='):
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha1
            ).hexdigest()
            expected_signature = f"sha1={expected_signature}"
        else:
            logger.error(f"Unsupported signature format: {signature[:10]}...")
            return False
        
        # Compare signatures using constant-time comparison
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if not is_valid:
            logger.error("Webhook signature verification failed")
        
        return is_valid

    async def _route_webhook_event(self, event_type: str, event_data: Dict[str, Any], event_id: str) -> Dict[str, Any]:
        """
        Route webhook event to appropriate handler based on event type.
        
        Args:
            event_type: GitHub event type (e.g., 'pull_request', 'push')
            event_data: Parsed webhook payload
            event_id: Generated event ID
            
        Returns:
            Event processing result
            
        Requirements: 3.4
        """
        if event_type == "pull_request":
            return await self._handle_pull_request_event(event_data, event_id)
        elif event_type == "push":
            return await self._handle_push_event(event_data, event_id)
        elif event_type == "ping":
            return await self._handle_ping_event(event_data, event_id)
        elif event_type == "installation":
            return await self._handle_installation_event(event_data, event_id)
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            return {
                "message": f"Event type '{event_type}' not handled",
                "queue_analysis": False
            }

    async def _handle_pull_request_event(self, event_data: Dict[str, Any], event_id: str) -> Dict[str, Any]:
        """
        Handle pull request webhook events.
        
        Args:
            event_data: Pull request event data
            event_id: Event ID
            
        Returns:
            Processing result
            
        Requirements: 3.4, 3.6
        """
        action = event_data.get('action', '')
        pr_data = event_data.get('pull_request', {})
        repo_data = event_data.get('repository', {})
        
        logger.info(f"Processing PR event: action={action}, PR#{pr_data.get('number')} in {repo_data.get('full_name')}")
        
        # Actions that trigger analysis
        analysis_actions = ['opened', 'synchronize', 'reopened']
        
        if action in analysis_actions:
            return {
                "message": f"PR {action} event processed - analysis queued",
                "queue_analysis": True,
                "queued_jobs": []  # Will be populated after job is queued
            }
        elif action == 'closed':
            # Handle PR closure - could clean up analysis data if needed
            return {
                "message": f"PR closed event processed",
                "queue_analysis": False
            }
        else:
            return {
                "message": f"PR action '{action}' processed - no analysis needed",
                "queue_analysis": False
            }

    async def _handle_push_event(self, event_data: Dict[str, Any], event_id: str) -> Dict[str, Any]:
        """
        Handle push webhook events.
        
        Args:
            event_data: Push event data
            event_id: Event ID
            
        Returns:
            Processing result
        """
        ref = event_data.get('ref', '')
        commits = event_data.get('commits', [])
        repo_data = event_data.get('repository', {})
        
        logger.info(f"Processing push event: {len(commits)} commits to {ref} in {repo_data.get('full_name')}")
        
        # For now, just log push events - could implement branch analysis later
        return {
            "message": f"Push event processed - {len(commits)} commits to {ref}",
            "queue_analysis": False
        }

    async def _handle_ping_event(self, event_data: Dict[str, Any], event_id: str) -> Dict[str, Any]:
        """
        Handle ping webhook events (webhook test).
        
        Args:
            event_data: Ping event data
            event_id: Event ID
            
        Returns:
            Processing result
        """
        hook_id = event_data.get('hook_id')
        repo_data = event_data.get('repository', {})
        
        logger.info(f"Webhook ping received for hook {hook_id} in {repo_data.get('full_name')}")
        
        return {
            "message": "Webhook ping received and processed successfully",
            "queue_analysis": False
        }

    async def _handle_installation_event(self, event_data: Dict[str, Any], event_id: str) -> Dict[str, Any]:
        """
        Handle GitHub App installation events.
        
        Args:
            event_data: Installation event data
            event_id: Event ID
            
        Returns:
            Processing result
        """
        action = event_data.get('action', '')
        installation = event_data.get('installation', {})
        
        logger.info(f"GitHub App installation event: {action} for installation {installation.get('id')}")
        
        return {
            "message": f"Installation {action} event processed",
            "queue_analysis": False
        }

    def _generate_event_id(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """
        Generate unique event ID for tracking.
        
        Args:
            event_type: GitHub event type
            event_data: Event payload data
            
        Returns:
            Unique event ID
        """
        # Use GitHub's delivery ID if available, otherwise generate UUID
        delivery_id = event_data.get('delivery_id') or str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        return f"{event_type}_{timestamp}_{delivery_id[:8]}"

    def _should_trigger_analysis(self, action: str, repository: GitHubRepository) -> bool:
        """
        Determine if webhook action should trigger code analysis.
        
        Args:
            action: GitHub webhook action
            repository: Repository integration record
            
        Returns:
            True if analysis should be triggered
        """
        # Check if repository has analysis enabled
        if not repository.repository_settings.get('auto_analysis', True):
            return False
        
        # Check if repository is active
        if not repository.is_active:
            return False
        
        # Actions that trigger analysis
        analysis_actions = ['opened', 'synchronize', 'reopened']
        return action in analysis_actions

    async def _get_repository_by_url(self, repo_url: str) -> Optional[GitHubRepository]:
        """
        Get repository integration by URL.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Repository integration record or None
        """
        try:
            query = select(GitHubRepository).where(
                GitHubRepository.repo_url == repo_url,
                GitHubRepository.is_active == True
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get repository by URL {repo_url}: {e}")
            return None

    async def _create_or_update_pr_analysis(
        self, 
        repository_id: str, 
        pr_data: Dict[str, Any], 
        force_reanalysis: bool = False
    ) -> PRAnalysis:
        """
        Create or update PR analysis record.
        
        Args:
            repository_id: Repository ID
            pr_data: Pull request data from webhook
            force_reanalysis: Whether to force reanalysis
            
        Returns:
            PR analysis record
        """
        pr_number = pr_data.get('number')
        
        # Check for existing analysis
        query = select(PRAnalysis).where(
            PRAnalysis.repository_id == repository_id,
            PRAnalysis.pr_number == pr_number
        )
        result = await self.db.execute(query)
        existing_analysis = result.scalar_one_or_none()
        
        if existing_analysis and not force_reanalysis:
            # Update existing record with latest PR data
            existing_analysis.pr_title = pr_data.get('title')
            existing_analysis.head_sha = pr_data.get('head', {}).get('sha')
            existing_analysis.head_branch = pr_data.get('head', {}).get('ref')
            existing_analysis.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(existing_analysis)
            return existing_analysis
        
        # Create new analysis record
        pr_analysis = PRAnalysis(
            repository_id=repository_id,
            pr_number=pr_number,
            pr_title=pr_data.get('title'),
            pr_author=pr_data.get('user', {}).get('login'),
            head_sha=pr_data.get('head', {}).get('sha'),
            base_sha=pr_data.get('base', {}).get('sha'),
            head_branch=pr_data.get('head', {}).get('ref'),
            base_branch=pr_data.get('base', {}).get('ref'),
            status=AnalysisStatus.PENDING
        )
        
        self.db.add(pr_analysis)
        await self.db.commit()
        await self.db.refresh(pr_analysis)
        
        return pr_analysis

# Background job handler for GitHub PR analysis
@background_job("analyze_github_pr")
async def analyze_github_pr_job(job_id: str, repository_id: str, pr_number: int):
    """
    Background job handler for GitHub pull request analysis.
    
    Args:
        job_id: Background job ID
        repository_id: GitHub repository integration ID
        pr_number: Pull request number
        
    Requirements: 3.4, 3.6
    """
    from app.core.database import AsyncSessionLocal
    from app.services.background_job_service import background_job_service
    
    logger.info(f"Starting GitHub PR analysis job {job_id} for PR #{pr_number} in repository {repository_id}")
    
    async with AsyncSessionLocal() as db:
        try:
            # Update job progress
            await background_job_service.update_job_progress(
                job_id, 
                current_step=1, 
                total_steps=5, 
                message="Initializing PR analysis"
            )
            
            # Initialize GitHub service
            github_service = GitHubService(db)
            
            # Update progress
            await background_job_service.update_job_progress(
                job_id, 
                current_step=2, 
                total_steps=5, 
                message="Analyzing pull request"
            )
            
            # Perform the actual PR analysis
            analysis_result = await github_service.analyze_pull_request(
                repository_id=repository_id,
                pr_number=pr_number,
                force_reanalysis=True  # Always reanalyze for webhook events
            )
            
            # Update progress
            await background_job_service.update_job_progress(
                job_id, 
                current_step=4, 
                total_steps=5, 
                message="Analysis completed, processing results"
            )
            
            # Complete the job with results
            await background_job_service.complete_job(
                job_id, 
                result={
                    "analysis_id": analysis_result.id,
                    "repository_id": repository_id,
                    "pr_number": pr_number,
                    "issues_found": analysis_result.issues_found,
                    "errors_count": analysis_result.errors_count,
                    "warnings_count": analysis_result.warnings_count,
                    "status": analysis_result.status.value,
                    "completed_at": analysis_result.completed_at.isoformat() if analysis_result.completed_at else None
                }
            )
            
            logger.info(f"GitHub PR analysis job {job_id} completed successfully with {analysis_result.issues_found} issues found")
            
        except Exception as e:
            logger.error(f"GitHub PR analysis job {job_id} failed: {e}")
            await background_job_service.fail_job(job_id, str(e))
            raise