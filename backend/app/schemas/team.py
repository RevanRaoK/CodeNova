"""
Pydantic schemas for team management.

These schemas handle validation and serialization for team operations,
member management, and team analytics.

Requirements covered: 7.1, 7.2, 7.3, 8.1, 8.2, 8.3
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class TeamBase(BaseModel):
    """Base schema for team."""
    name: str = Field(..., min_length=2, max_length=255)
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Team name cannot be empty or whitespace')
        return v.strip()


class TeamCreate(TeamBase):
    """Schema for creating a team."""
    admin_id: Optional[int] = None  # Will be set from current user if not provided


class TeamUpdate(BaseModel):
    """Schema for updating a team."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    settings: Optional[Dict[str, Any]] = None
    admin_id: Optional[int] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Team name cannot be empty or whitespace')
        return v.strip() if v else v


class AdminInfo(BaseModel):
    """Schema for admin information in team response."""
    id: int
    full_name: Optional[str] = None
    username: Optional[str] = None
    email: str
    
    class Config:
        from_attributes = True


class TeamResponse(TeamBase):
    """Schema for team response."""
    id: str
    admin_id: int
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = 0
    admin: Optional[AdminInfo] = None
    
    class Config:
        from_attributes = True


class TeamDetailResponse(TeamResponse):
    """Detailed schema for team with members."""
    members: List['TeamMemberResponse'] = []
    admin_email: Optional[str] = None
    admin_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class TeamMemberResponse(BaseModel):
    """Schema for team member response."""
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TeamMemberAdd(BaseModel):
    """Schema for adding a member to a team."""
    user_id: int


class TeamMemberRemove(BaseModel):
    """Schema for removing a member from a team."""
    user_id: int


class TeamMemberUpdate(BaseModel):
    """Schema for updating a team member."""
    role: Optional[str] = None
    is_active: Optional[bool] = None


# Analytics Schemas

class TeamAnalytics(BaseModel):
    """Schema for team analytics."""
    team_id: str
    team_name: str
    member_count: int
    active_members: int
    total_analyses: int
    total_feedback: int
    acceptance_rate: float
    rejection_rate: float
    avg_issues_per_analysis: float
    recent_activity: List[Dict[str, Any]] = []
    top_contributors: List[Dict[str, Any]] = []


class TeamComparisonMetrics(BaseModel):
    """Schema for comparing teams."""
    team_id: str
    team_name: str
    member_count: int
    total_reviews: int
    avg_issues_per_review: float
    feedback_acceptance_rate: float
    code_quality_score: float
    activity_score: float


class TeamPerformanceMetrics(BaseModel):
    """Schema for team performance metrics."""
    team_id: str
    team_name: str
    time_period: str
    total_analyses: int
    total_issues_found: int
    issues_by_severity: Dict[str, int]
    issues_by_type: Dict[str, int]
    feedback_metrics: Dict[str, Any]
    quality_trends: List[Dict[str, Any]]


# Platform Analytics Schemas

class DashboardMetrics(BaseModel):
    """Schema for admin dashboard metrics."""
    total_users: int
    active_teams: int
    reviews_today: int
    recent_activities: List[Dict[str, Any]] = []

class PlatformAnalytics(BaseModel):
    """Schema for platform-wide analytics."""
    total_users: int
    active_users: int
    inactive_users: int
    total_teams: int
    total_analyses: int
    total_feedback: int
    total_issues_found: int
    role_distribution: Dict[str, int]
    recent_activity: Dict[str, int]
    avg_issues_per_review: float
    feedback_acceptance_rate: float
    reviews_today: int
    active_users_30d: int
    top_languages: List[Dict[str, Any]] = []
    growth_metrics: Dict[str, Any] = {}
    issue_breakdown: List[Dict[str, Any]] = []


class PlatformStatistics(BaseModel):
    """Schema for detailed platform statistics."""
    overview: PlatformAnalytics
    team_comparison: List[TeamComparisonMetrics]
    user_activity: Dict[str, Any]
    code_quality_trends: List[Dict[str, Any]]
    system_health: Dict[str, Any]


class FeedbackStatistics(BaseModel):
    """Schema for feedback statistics response."""
    total_feedback_count: int = Field(..., description="Total number of feedback records")
    acceptance_rate: float = Field(..., description="Percentage of accepted suggestions")
    rejection_rate: float = Field(..., description="Percentage of rejected suggestions")
    modification_rate: float = Field(..., description="Percentage of modified suggestions")
    ignore_rate: float = Field(..., description="Percentage of ignored suggestions")
    feedback_breakdown: Dict[str, int] = Field(..., description="Count of each feedback type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_feedback_count": 1250,
                "acceptance_rate": 72.5,
                "rejection_rate": 18.2,
                "modification_rate": 9.3,
                "ignore_rate": 0.0,
                "feedback_breakdown": {
                    "accept": 906,
                    "reject": 228,
                    "modify": 116,
                    "ignore": 0
                }
            }
        }


# Query Schemas

class TeamListQuery(BaseModel):
    """Schema for querying teams."""
    search: Optional[str] = None
    admin_id: Optional[int] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v


class TeamListResponse(BaseModel):
    """Schema for paginated team list response."""
    teams: List[TeamResponse]
    total: int
    page: int
    page_size: int
    total_pages: int