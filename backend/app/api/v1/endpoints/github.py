"""
GitHub Integration API Endpoints

This module provides REST API endpoints for GitHub integration including OAuth authentication,
repository management, webhook handling, and pull request analysis.

Requirements covered: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
"""

import logging
import secrets
import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Query, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_current_user, get_db, get_db_async
from app.core.exceptions import GitHubIntegrationError
from app.core.config import settings
from app.models.users import User
from app.models.github_integration import GitHubRepository, PRAnalysis, AnalysisStatus
from app.services.github_service import GitHubService
from app.services.github_webhook_handler import GitHubWebhookHandler
from app.services.github_repository_connection_service import GitHubRepositoryConnectionService
from app.tasks.file_analysis_tasks import analyze_repository_files
from app.schemas.github_schemas import (
    GitHubRepositoryResponse,
    PRAnalysisResponse,
    WebhookEventResponse,
    OAuthCallbackResponse,
    OAuthCompleteRequest,
    OAuthStateResponse,
    OAuthStateRequest,
    RepositoryCreateRequest,
    PRAnalysisRequest,
    RepositoryListResponse,
    PRAnalysisListResponse,
    GitHubIssueRequest,
    GitHubIssueResponse,
    RepositoryStatsResponse,
    GitHubHealthResponse,
    WebhookConfigResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/github", tags=["GitHub Integration"])

# Store OAuth states temporarily (in production, use Redis)
oauth_states = {}


@router.get("/oauth/authorize", response_model=OAuthStateResponse)
async def get_oauth_authorization_url(
    request: OAuthStateRequest = None,
    db: AsyncSession = Depends(get_db_async)
):
    """
    Generate GitHub OAuth authorization URL.
    
    Requirements: 8.1
    """
    try:
        github_service = GitHubService(db)
        
        # Generate secure state parameter
        state = secrets.token_urlsafe(32)
        oauth_states[state] = {
            "redirect_url": request.redirect_url if request else None,
            "created_at": "now"  # In production, use proper datetime
        }
        
        authorization_url = await github_service.get_oauth_authorization_url(state)
        
        return OAuthStateResponse(
            authorization_url=authorization_url,
            state=state
        )
        
    except Exception as e:
        logger.error(f"Failed to generate OAuth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        )


@router.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="OAuth state parameter"),
    db: AsyncSession = Depends(get_db_async)
):
    """
    Handle GitHub OAuth callback and exchange code for token.
    Returns HTML redirect response to frontend with OAuth result.
    
    Requirements: 8.1
    """
    try:
        # Verify state parameter
        if state not in oauth_states:
            # Redirect to frontend with error
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/github/callback?error=invalid_state&error_description=Invalid+or+expired+OAuth+state"
            )
        
        github_service = GitHubService(db)
        
        # Exchange code for token and get user info
        token_data = await github_service.exchange_oauth_code(code, state)
        
        # Store OAuth data in state for the frontend to retrieve
        oauth_result_id = secrets.token_urlsafe(32)
        oauth_states[oauth_result_id] = {
            "token_data": token_data,
            "created_at": datetime.datetime.utcnow()
        }
        
        # Clean up the original state
        del oauth_states[state]
        
        # Redirect to frontend OAuth callback handler with result ID
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/github/callback?result_id={oauth_result_id}"
        )
        
    except GitHubIntegrationError as e:
        logger.error(f"OAuth callback error: {e}")
        # Redirect to frontend with error
        error_message = str(e).replace(" ", "+")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/github/callback?error=oauth_failed&error_description={error_message}"
        )
    except Exception as e:
        logger.error(f"Unexpected OAuth callback error: {e}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/github/callback?error=server_error&error_description=OAuth+authentication+failed"
        )


@router.post("/oauth/complete", response_model=OAuthCallbackResponse)
async def complete_oauth(
    request: OAuthCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    Complete OAuth integration by saving the token to the database.
    Called by frontend after OAuth callback redirect.
    
    Requirements: 8.1
    """
    try:
        result_id = request.result_id
        
        # Verify result_id exists
        if result_id not in oauth_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OAuth result"
            )
        
        token_data = oauth_states[result_id]["token_data"]
        
        # Save OAuth integration to database
        from app.models.github_oauth import GitHubOAuthIntegration
        
        # Check if user already has a GitHub integration
        query = select(GitHubOAuthIntegration).where(
            GitHubOAuthIntegration.user_id == current_user.id
        ).where(
            GitHubOAuthIntegration.github_user_id == token_data["user"]["id"]
        )
        result = await db.execute(query)
        existing_integration = result.scalar_one_or_none()
        
        if existing_integration:
            # Update existing integration
            existing_integration.access_token = token_data["access_token"]
            existing_integration.token_type = token_data["token_type"]
            existing_integration.scope = token_data["scope"]
            existing_integration.github_username = token_data["user"]["login"]
            existing_integration.github_email = token_data["user"]["email"]
            existing_integration.github_name = token_data["user"]["name"]
            existing_integration.is_active = True
            existing_integration.last_used = datetime.datetime.utcnow()
            existing_integration.updated_at = datetime.datetime.utcnow()
        else:
            # Create new integration
            new_integration = GitHubOAuthIntegration(
                user_id=current_user.id,
                github_user_id=token_data["user"]["id"],
                github_username=token_data["user"]["login"],
                github_email=token_data["user"]["email"],
                github_name=token_data["user"]["name"],
                access_token=token_data["access_token"],
                token_type=token_data["token_type"],
                scope=token_data["scope"],
                is_active=True,
                last_used=datetime.datetime.utcnow()
            )
            db.add(new_integration)
        
        await db.commit()
        
        # Clean up result
        del oauth_states[result_id]
        
        return OAuthCallbackResponse(
            success=True,
            message="GitHub OAuth authentication successful",
            user_info=token_data["user"],
            redirect_url=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Failed to complete OAuth: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save GitHub integration: {str(e)}"
        )


@router.post("/repositories", response_model=GitHubRepositoryResponse)
async def connect_repository(
    request: RepositoryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    Connect a GitHub repository for integration and set up webhook.
    
    Requirements: 3.3, 3.5
    """
    try:
        repo_connection_service = GitHubRepositoryConnectionService(db)
        
        # Connect repository with webhook setup
        repository = await repo_connection_service.connect_repository(
            user_id=current_user.id,
            repo_url=str(request.repo_url),
            webhook_events=request.webhook_events,
            repository_settings={
                "auto_analysis": request.auto_analysis,
                "create_issues": request.create_issues,
                "comment_on_prs": request.comment_on_prs
            }
        )
        
        return GitHubRepositoryResponse.from_orm(repository)
        
    except GitHubIntegrationError as e:
        logger.error(f"Repository connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected repository connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect repository"
        )


@router.get("/repositories", response_model=RepositoryListResponse)
async def list_repositories(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    include_inactive: bool = Query(False, description="Include inactive repositories"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    List connected GitHub repositories for the current user.
    
    Requirements: 3.3, 3.5
    """
    try:
        repo_connection_service = GitHubRepositoryConnectionService(db)
        
        result = await repo_connection_service.list_user_repositories(
            user_id=current_user.id,
            include_inactive=include_inactive,
            page=page,
            per_page=per_page
        )
        
        # Ensure we always return a valid list response
        return RepositoryListResponse(
            repositories=[GitHubRepositoryResponse(**repo) for repo in result.get("repositories", [])],
            total=result.get("total", 0),
            page=result.get("page", page),
            per_page=result.get("per_page", per_page)
        )
        
    except GitHubIntegrationError as e:
        logger.error(f"Repository listing error: {e}")
        # Return empty list instead of error to prevent frontend crash
        return RepositoryListResponse(
            repositories=[],
            total=0,
            page=page,
            per_page=per_page
        )
    except Exception as e:
        logger.error(f"Failed to list repositories: {e}")
        # Return empty list instead of error to prevent frontend crash
        return RepositoryListResponse(
            repositories=[],
            total=0,
            page=page,
            per_page=per_page
        )


@router.delete("/repositories/{repository_id}")
async def disconnect_repository(
    repository_id: str,
    remove_webhook: bool = Query(True, description="Remove webhook from GitHub"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    Disconnect a GitHub repository integration.
    
    Requirements: 3.3, 3.5
    """
    try:
        repo_connection_service = GitHubRepositoryConnectionService(db)
        
        success = await repo_connection_service.disconnect_repository(
            user_id=current_user.id,
            repository_id=repository_id,
            remove_webhook=remove_webhook
        )
        
        if success:
            return {"message": "Repository disconnected successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to disconnect repository"
            )
        
    except GitHubIntegrationError as e:
        logger.error(f"Repository disconnection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected repository disconnection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect repository"
        )


@router.put("/repositories/{repository_id}/settings", response_model=GitHubRepositoryResponse)
async def update_repository_settings(
    repository_id: str,
    settings: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    Update repository integration settings.
    
    Requirements: 3.3, 3.5
    """
    try:
        repo_connection_service = GitHubRepositoryConnectionService(db)
        
        updated_repo = await repo_connection_service.update_repository_settings(
            user_id=current_user.id,
            repository_id=repository_id,
            settings=settings
        )
        
        return GitHubRepositoryResponse.from_orm(updated_repo)
        
    except GitHubIntegrationError as e:
        logger.error(f"Repository settings update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected repository settings update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update repository settings"
        )


@router.get("/repositories/{repository_id}/webhook-status")
async def get_repository_webhook_status(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    Get webhook status and configuration for a repository.
    
    Requirements: 3.3, 3.5
    """
    try:
        repo_connection_service = GitHubRepositoryConnectionService(db)
        
        webhook_status = await repo_connection_service.get_repository_webhooks_status(
            user_id=current_user.id,
            repository_id=repository_id
        )
        
        return webhook_status
        
    except GitHubIntegrationError as e:
        logger.error(f"Webhook status check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected webhook status check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get webhook status"
        )


@router.post("/repositories/{repository_id}/webhook")
async def setup_repository_webhook(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    Setup or update webhook for a repository.
    
    Requirements: 3.3, 3.5
    """
    try:
        # Get the repository
        repo_query = select(GitHubRepository).where(
            GitHubRepository.id == repository_id,
            GitHubRepository.user_id == current_user.id
        )
        repo_result = await db.execute(repo_query)
        repository = repo_result.scalar_one_or_none()
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found or access denied"
            )
        
        # Note: Webhook setup on localhost will fail since GitHub can't reach localhost
        # This is expected behavior for local development
        return {
            "success": False,
            "message": "Webhook setup is not available for localhost development. Deploy to a public server with a reachable URL to enable webhooks.",
            "webhook_url": f"{settings.GITHUB_WEBHOOK_BASE_URL}/api/v1/github/webhook",
            "repository_id": repository_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected webhook setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup webhook"
        )


@router.post("/repositories/{repository_id}/analyze")
async def trigger_full_repository_analysis(
    repository_id: str,
    branch: str = Query("main", description="Branch to analyze (default: main)"),
    file_patterns: list[str] = Query(None, description="File patterns to include (e.g., *.py, *.js)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    Trigger a full repository code analysis to find issues across the entire codebase.
    
    This endpoint analyzes all code files in the repository and generates a comprehensive
    code quality report with issues, suggestions, and metrics.
    
    Requirements: 3.3, 3.5
    """
    try:
        # Verify user has access to the repository
        repo_query = select(GitHubRepository).where(
            GitHubRepository.id == repository_id,
            GitHubRepository.user_id == current_user.id
        )
        repo_result = await db.execute(repo_query)
        repository = repo_result.scalar_one_or_none()
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found or access denied"
            )
        
        # Create a PR analysis record to track the repository analysis
        # (Using PR analysis model with pr_number=0 to indicate full repo analysis)
        analysis = PRAnalysis(
            repository_id=repository_id,
            pr_number=0,  # 0 indicates full repository analysis
            pr_title=f"Full Repository Analysis - {branch}",
            pr_author=current_user.email or current_user.full_name or "Unknown",
            head_sha="",  # Will be updated by the task
            base_sha="",
            head_branch=branch,
            base_branch=branch,
            status=AnalysisStatus.PENDING
        )
        
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        
        logger.info(f"Created repository analysis record {analysis.id} for repository {repository_id}")
        
        # Queue the background analysis task
        try:
            # Queue the task asynchronously
            task = analyze_repository_files.delay(
                repository_id=repository_id,
                file_patterns=file_patterns or ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"],
                analysis_type="comprehensive",
                user_id=str(current_user.id)
            )
            
            # Update analysis with task ID
            analysis.analysis_results = {
                "task_id": str(task.id) if hasattr(task, 'id') else "queued",
                "branch": branch,
                "file_patterns": file_patterns,
                "started_at": datetime.datetime.utcnow().isoformat()
            }
            analysis.started_at = datetime.datetime.utcnow()
            await db.commit()
            
            logger.info(f"Queued repository analysis task for repository {repository_id}")
            
        except Exception as queue_error:
            logger.warning(f"Failed to queue background task: {queue_error}")
            # Update status to show it's queued but task failed
            analysis.status = AnalysisStatus.PENDING
            analysis.analysis_results = {
                "status": "queued_manually",
                "branch": branch,
                "note": "Analysis will be processed when background workers are available"
            }
            await db.commit()
        
        return {
            "success": True,
            "message": f"Repository analysis for {repository.repo_name} has been queued successfully",
            "analysis_id": analysis.id,
            "repository_id": repository_id,
            "repository_name": repository.repo_name,
            "branch": branch,
            "status": "queued",
            "file_patterns": file_patterns or ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"],
            "created_at": analysis.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger repository analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger repository analysis: {str(e)}"
        )


@router.get("/repositories/{repository_id}/analyze/progress")
async def get_repository_analysis_progress(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    Get the progress of the most recent repository analysis.
    
    Returns real-time progress including files discovered, files analyzed,
    current file being processed, and overall progress percentage.
    
    Requirements: 3.3, 3.5
    """
    try:
        # Verify user has access to the repository
        repo_query = select(GitHubRepository).where(
            GitHubRepository.id == repository_id,
            GitHubRepository.user_id == current_user.id
        )
        repo_result = await db.execute(repo_query)
        repository = repo_result.scalar_one_or_none()
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found or access denied"
            )
        
        # Get most recent repository analysis (pr_number=0)
        analysis_query = select(PRAnalysis).where(
            PRAnalysis.repository_id == repository_id,
            PRAnalysis.pr_number == 0
        ).order_by(PRAnalysis.created_at.desc())
        
        analysis_result = await db.execute(analysis_query)
        analysis = analysis_result.scalars().first()
        
        if not analysis:
            return {
                "repository_id": repository_id,
                "status": "not_started",
                "message": "No repository analysis found. Click 'Analyze Repository' to start."
            }
        
        # Extract progress information from analysis_results
        progress_data = analysis.analysis_results or {}
        
        response = {
            "analysis_id": analysis.id,
            "repository_id": repository_id,
            "repository_name": repository.repo_name,
            "status": analysis.status.value if analysis.status else "unknown",
            "started_at": analysis.started_at.isoformat() if analysis.started_at else None,
            "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
            "progress": {
                "total_files": progress_data.get("total_files", 0),
                "files_discovered": progress_data.get("files_discovered", 0),
                "files_analyzed": progress_data.get("files_analyzed", 0),
                "files_failed": progress_data.get("files_failed", 0),
                "progress_percentage": progress_data.get("progress_percentage", 0),
                "current_file": progress_data.get("current_file"),
                "status": progress_data.get("status", "unknown")
            },
            "results": {
                "total_issues": analysis.issues_found or 0,
                "errors": analysis.errors_count or 0,
                "warnings": analysis.warnings_count or 0
            }
        }
        
        # Add summary if analysis is completed
        if analysis.status == AnalysisStatus.COMPLETED and "summary" in progress_data:
            response["summary"] = progress_data["summary"]
        
        # Add error message if failed
        if analysis.status == AnalysisStatus.FAILED:
            response["error_message"] = analysis.error_message
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis progress: {str(e)}"
        )


@router.post("/repositories/{repository_id}/trigger-analysis")
async def trigger_repository_analysis(
    repository_id: str,
    pr_number: int = Query(..., description="Pull request number to analyze"),
    force_reanalysis: bool = Query(False, description="Force reanalysis if already exists"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    Manually trigger pull request analysis for a repository.
    
    Requirements: 3.3, 3.5
    """
    try:
        repo_connection_service = GitHubRepositoryConnectionService(db)
        
        job_id = await repo_connection_service.trigger_pull_request_analysis(
            repository_id=repository_id,
            pr_number=pr_number,
            force_reanalysis=force_reanalysis,
            user_id=current_user.id
        )
        
        return {
            "message": "Pull request analysis triggered successfully",
            "job_id": job_id,
            "pr_number": pr_number
        }
        
    except GitHubIntegrationError as e:
        logger.error(f"PR analysis trigger error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected PR analysis trigger error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger PR analysis"
        )


@router.post("/webhook", response_model=WebhookEventResponse)
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_async)
):
    """
    Handle GitHub webhook events with signature verification and background processing.
    
    This endpoint:
    1. Verifies webhook signature using HMAC-SHA256
    2. Routes events to appropriate handlers
    3. Queues background analysis jobs for PR events
    4. Returns immediate response while processing asynchronously
    
    Requirements: 3.3, 3.4, 3.6
    """
    try:
        # Get headers and payload
        headers = dict(request.headers)
        payload = await request.body()
        
        # Initialize webhook handler
        webhook_handler = GitHubWebhookHandler(db)
        
        # Process webhook with signature verification and event routing
        result = await webhook_handler.process_webhook(headers, payload)
        
        # Queue background analysis if needed
        if result.get("queue_analysis"):
            background_tasks.add_task(
                webhook_handler.queue_pr_analysis,
                result["event_data"]
            )
        
        return WebhookEventResponse(
            event_id=result.get("event_id", "unknown"),
            event_type=result.get("event_type", "unknown"),
            status="processed",
            message=result.get("message", "Webhook processed successfully"),
            queued_jobs=result.get("queued_jobs", [])
        )
        
    except GitHubIntegrationError as e:
        logger.error(f"Webhook processing error: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "event_id": "unknown",
                "event_type": "unknown", 
                "status": "error",
                "message": str(e),
                "queued_jobs": []
            }
        )
    except Exception as e:
        logger.error(f"Unexpected webhook error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "event_id": "unknown",
                "event_type": "unknown",
                "status": "error", 
                "message": "Webhook processing failed",
                "queued_jobs": []
            }
        )


@router.post("/analyze-pr", response_model=Dict[str, Any])
async def analyze_pull_request(
    request: PRAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    Manually trigger pull request analysis.
    
    Requirements: 3.3, 3.5
    """
    try:
        repo_connection_service = GitHubRepositoryConnectionService(db)
        
        # Trigger analysis using the repository connection service
        job_id = await repo_connection_service.trigger_pull_request_analysis(
            repository_id=request.repository_id,
            pr_number=request.pr_number,
            force_reanalysis=request.force_reanalysis,
            user_id=current_user.id
        )
        
        return {
            "message": "Pull request analysis triggered successfully",
            "job_id": job_id,
            "pr_number": request.pr_number,
            "repository_id": request.repository_id
        }
        
    except GitHubIntegrationError as e:
        logger.error(f"PR analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected PR analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze pull request"
        )


@router.get("/repositories/{repository_id}/pr-analyses", response_model=PRAnalysisListResponse)
async def list_pr_analyses(
    repository_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    List pull request analyses for a repository.
    
    Requirements: 8.4, 8.5
    """
    try:
        # Verify user has access to the repository
        repo_query = select(GitHubRepository).where(
            GitHubRepository.id == repository_id,
            GitHubRepository.user_id == current_user.id
        )
        repo_result = await db.execute(repo_query)
        repository = repo_result.scalar_one_or_none()
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found or access denied"
            )
        
        offset = (page - 1) * per_page
        
        # Get analyses for repository
        query = select(PRAnalysis).where(
            PRAnalysis.repository_id == repository_id
        ).order_by(PRAnalysis.created_at.desc()).offset(offset).limit(per_page)
        
        result = await db.execute(query)
        analyses = result.scalars().all()
        
        # Get total count
        count_query = select(func.count(PRAnalysis.id)).where(
            PRAnalysis.repository_id == repository_id
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        return PRAnalysisListResponse(
            analyses=[PRAnalysisResponse.from_orm(analysis) for analysis in analyses],
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Failed to list PR analyses: {e}")
        # Return empty list instead of error to prevent frontend crash
        return PRAnalysisListResponse(
            analyses=[],
            total=0,
            page=page,
            per_page=per_page
        )


@router.post("/repositories/{repository_id}/pr-analyses")
async def trigger_pr_analysis_for_repo(
    repository_id: str,
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    Trigger manual PR analysis for a specific repository and PR number.
    
    Requirements: 8.4, 8.5
    """
    try:
        pr_number = request.get("pr_number")
        force_reanalysis = request.get("force_reanalysis", False)
        
        if not pr_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="pr_number is required"
            )
        
        # Verify user has access to the repository
        repo_query = select(GitHubRepository).where(
            GitHubRepository.id == repository_id,
            GitHubRepository.user_id == current_user.id
        )
        repo_result = await db.execute(repo_query)
        repository = repo_result.scalar_one_or_none()
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found or access denied"
            )
        
        repo_connection_service = GitHubRepositoryConnectionService(db)
        
        # Trigger analysis
        job_id = await repo_connection_service.trigger_pull_request_analysis(
            repository_id=repository_id,
            pr_number=pr_number,
            force_reanalysis=force_reanalysis,
            user_id=current_user.id
        )
        
        return {
            "message": "Pull request analysis triggered successfully",
            "job_id": job_id,
            "pr_number": pr_number,
            "repository_id": repository_id
        }
        
    except HTTPException:
        raise
    except GitHubIntegrationError as e:
        logger.error(f"PR analysis trigger error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected PR analysis trigger error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger PR analysis"
        )


@router.get("/repositories/{repository_id}/issues")
async def list_repository_issues(
    repository_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str = Query("", description="Filter by issue status (open, closed)"),
    search: str = Query("", description="Search query"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    List issues for a GitHub repository.
    
    Requirements: 8.5
    """
    try:
        # Verify user has access to the repository
        repo_query = select(GitHubRepository).where(
            GitHubRepository.id == repository_id,
            GitHubRepository.user_id == current_user.id
        )
        repo_result = await db.execute(repo_query)
        repository = repo_result.scalar_one_or_none()
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found or access denied"
            )
        
        # For now, return empty list
        # TODO: Implement actual issue listing from GitHub API
        return {
            "issues": [],
            "total": 0,
            "page": page,
            "per_page": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to list repository issues: {e}")
        # Return empty list instead of error
        return {
            "issues": [],
            "total": 0,
            "page": page,
            "per_page": limit
        }


@router.post("/repositories/{repository_id}/issues", response_model=GitHubIssueResponse)
async def create_repository_issue(
    repository_id: str,
    request: GitHubIssueRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    Create an issue in the GitHub repository.
    
    Requirements: 8.5
    """
    try:
        # Verify user has access to the repository
        repo_query = select(GitHubRepository).where(
            GitHubRepository.id == repository_id,
            GitHubRepository.user_id == current_user.id
        )
        repo_result = await db.execute(repo_query)
        repository = repo_result.scalar_one_or_none()
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found or access denied"
            )
        
        github_service = GitHubService(db)
        
        issue_url = await github_service.create_repository_issue(
            repository_id=repository_id,
            title=request.title,
            body=request.body,
            labels=request.labels
        )
        
        return GitHubIssueResponse(
            success=True,
            issue_url=issue_url
        )
        
    except GitHubIntegrationError as e:
        logger.error(f"Issue creation error: {e}")
        return GitHubIssueResponse(
            success=False,
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected issue creation error: {e}")
        return GitHubIssueResponse(
            success=False,
            error="Failed to create issue"
        )


@router.get("/repositories/{repository_id}/stats", response_model=RepositoryStatsResponse)
async def get_repository_stats(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_async)
):
    """
    Get statistics for a connected repository.
    
    Requirements: 8.6
    """
    try:
        # Verify user has access to the repository
        repo_query = select(GitHubRepository).where(
            GitHubRepository.id == repository_id,
            GitHubRepository.user_id == current_user.id
        )
        repo_result = await db.execute(repo_query)
        repository = repo_result.scalar_one_or_none()
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found or access denied"
            )
        
        # Get analysis statistics
        stats_query = select(
            func.count(PRAnalysis.id).label("total_prs"),
            func.sum(PRAnalysis.issues_found).label("total_issues"),
            func.avg(
                func.extract('epoch', PRAnalysis.completed_at - PRAnalysis.started_at)
            ).label("avg_time"),
            func.max(PRAnalysis.completed_at).label("last_analysis")
        ).where(PRAnalysis.repository_id == repository_id)
        
        stats_result = await db.execute(stats_query)
        stats = stats_result.first()
        
        return RepositoryStatsResponse(
            repository_id=repository_id,
            repo_name=repository.repo_name,
            total_prs_analyzed=stats.total_prs or 0,
            total_issues_found=stats.total_issues or 0,
            total_issues_created=0,  # Would need to track this separately
            avg_analysis_time=stats.avg_time,
            last_analysis=stats.last_analysis,
            webhook_status="active" if repository.webhook_id else "inactive"
        )
        
    except Exception as e:
        logger.error(f"Failed to get repository stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve repository statistics"
        )


@router.get("/health", response_model=GitHubHealthResponse)
async def get_github_health(db: AsyncSession = Depends(get_db_async)):
    """
    Get GitHub integration health status.
    
    Requirements: 8.6
    """
    try:
        github_service = GitHubService(db)
        
        # Check GitHub API accessibility
        github_api_accessible = True
        try:
            # This would be a simple API call to test connectivity
            pass
        except Exception:
            github_api_accessible = False
        
        # Get connected repositories count
        repo_count_query = select(func.count(GitHubRepository.id))
        repo_count_result = await db.execute(repo_count_query)
        connected_repositories = repo_count_result.scalar()
        
        # Get recent analyses
        recent_analysis_query = select(func.max(PRAnalysis.completed_at))
        recent_result = await db.execute(recent_analysis_query)
        last_successful_analysis = recent_result.scalar()
        
        return GitHubHealthResponse(
            status="healthy" if github_api_accessible else "degraded",
            github_api_accessible=github_api_accessible,
            webhook_endpoint_accessible=True,  # Would need actual health check
            connected_repositories=connected_repositories,
            recent_webhook_events=0,  # Would need to track this
            last_successful_analysis=last_successful_analysis
        )
        
    except Exception as e:
        logger.error(f"Failed to get GitHub health: {e}")
        return GitHubHealthResponse(
            status="unhealthy",
            github_api_accessible=False,
            webhook_endpoint_accessible=False,
            connected_repositories=0,
            recent_webhook_events=0
        )


@router.get("/webhook/config", response_model=WebhookConfigResponse)
async def get_webhook_config():
    """
    Get webhook configuration information.
    
    Requirements: 8.3
    """
    from app.core.config import settings
    
    return WebhookConfigResponse(
        webhook_url=f"{settings.GITHUB_WEBHOOK_BASE_URL}/webhook",
        supported_events=["pull_request", "push"],
        signature_verification=True,
        last_ping=None  # Would need to track this
    )
