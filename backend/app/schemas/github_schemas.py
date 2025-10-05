"""
GitHub Integration Schemas

Pydantic schemas for GitHub integration API endpoints including OAuth, repositories,
and pull request analysis.

Requirements covered: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, HttpUrl, Field
from enum import Enum


class AnalysisStatus(str, Enum):
    """Analysis status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class GitHubUserInfo(BaseModel):
    """GitHub user information from OAuth."""
    id: int
    login: str
    email: Optional[str] = None
    name: Optional[str] = None


class OAuthTokenResponse(BaseModel):
    """OAuth token exchange response."""
    access_token: str
    token_type: str = "bearer"
    scope: str
    user: GitHubUserInfo


class OAuthCallbackResponse(BaseModel):
    """OAuth callback response."""
    success: bool
    message: str
    user_info: Optional[GitHubUserInfo] = None
    redirect_url: Optional[str] = None


class RepositoryCreateRequest(BaseModel):
    """Request to connect a GitHub repository."""
    repo_url: HttpUrl = Field(..., description="GitHub repository URL")
    webhook_events: List[str] = Field(
        default=["pull_request", "push"],
        description="Webhook events to subscribe to"
    )
    auto_analysis: bool = Field(
        default=True,
        description="Enable automatic analysis on PR events"
    )
    create_issues: bool = Field(
        default=True,
        description="Create GitHub issues for analysis results"
    )
    comment_on_prs: bool = Field(
        default=True,
        description="Post comments on pull requests"
    )


class GitHubRepositoryResponse(BaseModel):
    """GitHub repository integration response."""
    id: str
    repo_url: str
    repo_name: str
    default_branch: str
    webhook_id: Optional[str] = None
    webhook_status: str = "active"
    repository_settings: Dict[str, Any]
    permissions: Dict[str, str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PRAnalysisRequest(BaseModel):
    """Request to analyze a pull request."""
    repository_id: str = Field(..., description="Repository integration ID")
    pr_number: int = Field(..., description="Pull request number")
    force_reanalysis: bool = Field(
        default=False,
        description="Force reanalysis even if already analyzed"
    )


class IssueInfo(BaseModel):
    """Code analysis issue information."""
    line: int
    message: str
    severity: str
    rule: str
    file: str


class FileAnalysisResult(BaseModel):
    """Analysis result for a single file."""
    filename: str
    language: str
    issues: List[IssueInfo]
    status: str
    error: Optional[str] = None


class AnalysisSummary(BaseModel):
    """Analysis summary statistics."""
    total_files: int
    total_issues: int
    total_errors: int
    total_warnings: int
    analyzed_at: datetime


class PRAnalysisResponse(BaseModel):
    """Pull request analysis response."""
    id: str
    repository_id: str
    pr_number: int
    pr_title: str
    pr_author: str
    head_sha: str
    base_sha: str
    head_branch: str
    base_branch: str
    status: AnalysisStatus
    issues_found: int
    errors_count: int
    warnings_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    analysis_results: Optional[Dict[str, Any]] = None
    issues_created: Optional[List[str]] = None
    comments_posted: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class WebhookEventResponse(BaseModel):
    """Webhook event processing response."""
    status: str
    message: str
    event_type: Optional[str] = None
    repository: Optional[str] = None
    pr_number: Optional[int] = None
    analysis_triggered: bool = False


class RepositoryListResponse(BaseModel):
    """List of connected repositories."""
    repositories: List[GitHubRepositoryResponse]
    total: int
    page: int
    per_page: int


class PRAnalysisListResponse(BaseModel):
    """List of PR analyses."""
    analyses: List[PRAnalysisResponse]
    total: int
    page: int
    per_page: int


class GitHubIssueRequest(BaseModel):
    """Request to create a GitHub issue."""
    repository_id: str = Field(..., description="Repository integration ID")
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    labels: List[str] = Field(default_factory=list)


class GitHubIssueResponse(BaseModel):
    """GitHub issue creation response."""
    success: bool
    issue_url: Optional[str] = None
    error: Optional[str] = None


class RepositoryStatsResponse(BaseModel):
    """Repository integration statistics."""
    repository_id: str
    repo_name: str
    total_prs_analyzed: int
    total_issues_found: int
    total_issues_created: int
    avg_analysis_time: Optional[float] = None
    last_analysis: Optional[datetime] = None
    webhook_status: str


class GitHubHealthResponse(BaseModel):
    """GitHub integration health status."""
    status: str
    github_api_accessible: bool
    webhook_endpoint_accessible: bool
    connected_repositories: int
    recent_webhook_events: int
    last_successful_analysis: Optional[datetime] = None


class OAuthStateRequest(BaseModel):
    """OAuth state generation request."""
    redirect_url: Optional[str] = None


class OAuthStateResponse(BaseModel):
    """OAuth state generation response."""
    authorization_url: str
    state: str


class WebhookConfigResponse(BaseModel):
    """Webhook configuration status."""
    webhook_url: str
    supported_events: List[str]
    signature_verification: bool
    last_ping: Optional[datetime] = None