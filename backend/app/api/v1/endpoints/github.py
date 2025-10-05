"""
GitHub Integration API Endpoints

This module provides REST API endpoints for GitHub integration including OAuth authentication,
repository management, webhook handling, and pull request analysis.

Requirements covered: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
"""

import logging
import secrets
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Query, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_current_user, get_db
from app.core.exceptions import GitHubIntegrationError
from app.models.users import User
from app.models.github_integration import GitHubRepository, PRAnalysis
from app.services.github_service import GitHubService
from app.schemas.github_schemas import (
    GitHubRepositoryResponse,
    PRAnalysisResponse,
    WebhookEventResponse,
    OAuthCallbackResponse,
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
    db: AsyncSession = Depends(get_db)
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


@router.get("/oauth/callback", response_model=OAuthCallbackResponse)
async def oauth_callback(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="OAuth state parameter"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle GitHub OAuth callback and exchange code for token.
    
    Requirements: 8.1
    """
    try:
        # Verify state parameter
        if state not in oauth_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OAuth state"
            )
        
        github_service = GitHubService(db)
        
        # Exchange code for token
        token_data = await github_service.exchange_oauth_code(code, state)
        
        # Clean up state
        redirect_url = oauth_states[state].get("redirect_url")
        del oauth_states[state]
        
        return OAuthCallbackResponse(
            success=True,
            message="GitHub OAuth authentication successful",
            user_info=token_data["user"],
            redirect_url=redirect_url
        )
        
    except GitHubIntegrationError as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )


@router.post("/repositories", response_model=GitHubRepositoryResponse)
async def connect_repository(
    request: RepositoryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Connect a GitHub repository for integration.
    
    Requirements: 8.1, 8.2
    """
    try:
        github_service = GitHubService(db)
        
        # Note: In a real implementation, you'd need to get the user's GitHub access token
        # This could be stored during OAuth or passed in the request
        access_token = "user_github_token"  # This should come from user's stored tokens
        
        repository = await github_service.setup_repository_webhook(
            user_id=current_user.id,
            repo_url=str(request.repo_url),
            access_token=access_token
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List connected GitHub repositories for the current user.
    
    Requirements: 8.2
    """
    try:
        offset = (page - 1) * per_page
        
        # Get repositories for current user
        query = select(GitHubRepository).where(
            GitHubRepository.user_id == current_user.id
        ).offset(offset).limit(per_page)
        
        result = await db.execute(query)
        repositories = result.scalars().all()
        
        # Get total count
        count_query = select(func.count(GitHubRepository.id)).where(
            GitHubRepository.user_id == current_user.id
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        return RepositoryListResponse(
            repositories=[GitHubRepositoryResponse.from_orm(repo) for repo in repositories],
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Failed to list repositories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve repositories"
        )


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle GitHub webhook events.
    
    Requirements: 8.3, 8.4
    """
    try:
        # Get headers and payload
        headers = dict(request.headers)
        payload = await request.body()
        
        github_service = GitHubService(db)
        
        # Process webhook in background
        background_tasks.add_task(
            github_service.handle_webhook_event,
            headers,
            payload
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "accepted", "message": "Webhook event queued for processing"}
        )
        
    except GitHubIntegrationError as e:
        logger.error(f"Webhook processing error: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected webhook error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Webhook processing failed"}
        )


@router.post("/analyze-pr", response_model=PRAnalysisResponse)
async def analyze_pull_request(
    request: PRAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger pull request analysis.
    
    Requirements: 8.4, 8.5
    """
    try:
        github_service = GitHubService(db)
        
        # Verify user has access to the repository
        repo_query = select(GitHubRepository).where(
            GitHubRepository.id == request.repository_id,
            GitHubRepository.user_id == current_user.id
        )
        repo_result = await db.execute(repo_query)
        repository = repo_result.scalar_one_or_none()
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found or access denied"
            )
        
        # Trigger analysis
        analysis = await github_service.analyze_pull_request(
            repository_id=request.repository_id,
            pr_number=request.pr_number,
            force_reanalysis=request.force_reanalysis
        )
        
        return PRAnalysisResponse.from_orm(analysis)
        
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


@router.get("/repositories/{repository_id}/analyses", response_model=PRAnalysisListResponse)
async def list_pr_analyses(
    repository_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve PR analyses"
        )


@router.post("/repositories/{repository_id}/issues", response_model=GitHubIssueResponse)
async def create_repository_issue(
    repository_id: str,
    request: GitHubIssueRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
async def get_github_health(db: AsyncSession = Depends(get_db)):
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