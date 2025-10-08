"""
Integration API endpoints for end-to-end workflows
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.security import require_admin
from app.models import User
from app.services.integration_service import integration_service
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.feedback import FeedbackCreate
from app.schemas.github_schemas import RepositoryCreateRequest as GitHubRepositoryCreate
from pydantic import BaseModel

router = APIRouter()

class OnboardingRequest(BaseModel):
    """Request model for user onboarding"""
    user_data: UserCreate

class GitHubIntegrationRequest(BaseModel):
    """Request model for GitHub integration"""
    repository_data: GitHubRepositoryCreate

class FileAnalysisRequest(BaseModel):
    """Request model for file analysis workflow"""
    files: List[Dict[str, Any]]

class AdminUserManagementRequest(BaseModel):
    """Request model for admin user management"""
    user_data: UserCreate
    team_id: str = None
    role: str = "user"

class FeedbackAnalysisRequest(BaseModel):
    """Request model for feedback analysis"""
    feedback_data: FeedbackCreate

@router.post("/workflows/onboarding", response_model=Dict[str, Any])
async def start_user_onboarding_workflow(
    request: OnboardingRequest,
    db: Session = Depends(get_db)
):
    """
    Start user onboarding workflow
    Creates user account, initializes profile, and sets up analytics
    """
    try:
        result = await integration_service.complete_user_onboarding(
            request.user_data, 
            db
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Onboarding workflow failed: {str(e)}"
        )

@router.post("/workflows/github-integration", response_model=Dict[str, Any])
async def start_github_integration_workflow(
    request: GitHubIntegrationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start GitHub integration workflow
    Connects repository, sets up webhook, and performs initial scan
    """
    try:
        result = await integration_service.complete_github_integration(
            str(current_user.id),
            request.repository_data,
            db
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GitHub integration workflow failed: {str(e)}"
        )

@router.post("/workflows/file-analysis", response_model=Dict[str, Any])
async def start_file_analysis_workflow(
    request: FileAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start file analysis workflow
    Uploads files, triggers analysis, and updates analytics
    """
    try:
        result = await integration_service.complete_file_analysis_workflow(
            str(current_user.id),
            request.files,
            db
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File analysis workflow failed: {str(e)}"
        )

@router.post("/workflows/admin-user-management", response_model=Dict[str, Any])
async def start_admin_user_management_workflow(
    request: AdminUserManagementRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Start admin user management workflow
    Creates user, assigns team and role, initializes analytics
    """
    try:
        result = await integration_service.complete_admin_user_management(
            str(current_admin.id),
            request.user_data,
            request.team_id,
            request.role,
            db
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Admin user management workflow failed: {str(e)}"
        )

@router.post("/workflows/feedback-analysis", response_model=Dict[str, Any])
async def start_feedback_analysis_workflow(
    request: FeedbackAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start feedback analysis workflow
    Submits feedback, updates analytics, and triggers AI model updates
    """
    try:
        result = await integration_service.complete_feedback_analysis_workflow(
            str(current_user.id),
            request.feedback_data,
            db
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Feedback analysis workflow failed: {str(e)}"
        )

@router.get("/dashboard/initialize", response_model=Dict[str, Any])
async def initialize_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize dashboard with all necessary data
    Fetches user profile, analytics, files, repositories, and feedback
    """
    try:
        dashboard_data = await integration_service.initialize_dashboard_data(
            str(current_user.id),
            db
        )
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard initialization failed: {str(e)}"
        )

@router.get("/workflows/{workflow_id}/status", response_model=Dict[str, Any])
async def get_workflow_status(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a specific workflow
    """
    workflow = integration_service.get_workflow_status(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    return workflow

@router.get("/workflows", response_model=List[Dict[str, Any]])
async def get_all_workflows(
    current_user: User = Depends(get_current_user)
):
    """
    Get all workflows for monitoring
    """
    workflows = integration_service.get_all_workflows()
    return workflows

@router.post("/workflows/{workflow_id}/retry", response_model=Dict[str, Any])
async def retry_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Retry a failed workflow
    """
    try:
        result = await integration_service.retry_workflow(workflow_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow retry failed: {str(e)}"
        )

@router.get("/health", response_model=Dict[str, Any])
async def integration_health_check():
    """
    Health check for integration service
    """
    return {
        "status": "healthy",
        "service": "integration",
        "timestamp": "2024-01-01T00:00:00Z",
        "active_workflows": len(integration_service.get_all_workflows())
    }