# app/api/v1/endpoints/admin_analytics.py

"""
Global analytics endpoints for admin dashboard.
Requirements: 9.1, 9.2, 9.3, 10.1, 10.2, 10.3
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.rbac import require_admin
from app.models.users import User
from app.services.global_analytics_service import GlobalAnalyticsService
from pydantic import BaseModel, Field

router = APIRouter()


class PlatformStatsResponse(BaseModel):
    total_users: int
    total_teams: int
    total_reviews: int
    active_users_30d: int
    total_issues_found: int
    avg_issues_per_review: float
    feedback_participation_rate: float
    timestamp: datetime


class GlobalTrendsDataPoint(BaseModel):
    date: str
    reviews: int
    errors: int
    warnings: int
    security_issues: int
    total_issues: int


class GlobalTrendsResponse(BaseModel):
    timeframe: str
    data_points: List[GlobalTrendsDataPoint]
    summary: dict


class TeamComparisonItem(BaseModel):
    team_id: str
    team_name: str
    total_reviews: int
    avg_issues_per_review: float
    feedback_acceptance_rate: float
    active_members: int


class ReviewItem(BaseModel):
    analysis_id: str
    user_id: int
    username: str
    team_name: Optional[str]
    filename: str
    created_at: datetime
    issues_count: int
    feedback_count: int


class ReviewsResponse(BaseModel):
    reviews: List[ReviewItem]
    total: int
    page: int
    page_size: int


class FeedbackItem(BaseModel):
    feedback_id: str
    user_id: int
    username: str
    issue_id: str
    feedback_type: str
    created_at: datetime
    comment: Optional[str]


class FeedbackResponse(BaseModel):
    feedback: List[FeedbackItem]
    summary: dict
    total: int
    page: int
    page_size: int


@router.get("/platform", response_model=PlatformStatsResponse)
async def get_platform_stats(
    team_id: Optional[str] = Query(None, description="Filter by team ID. If null, shows all users."),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get platform-wide statistics.
    
    Requirements: 9.1, 9.2, 9.3, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6 - Platform metrics with team filtering
    """
    analytics_service = GlobalAnalyticsService(db)
    stats = await analytics_service.get_platform_stats(team_id=team_id)
    
    return PlatformStatsResponse(
        total_users=stats["total_users"],
        total_teams=stats["total_teams"],
        total_reviews=stats["total_reviews"],
        active_users_30d=stats["active_users_30d"],
        total_issues_found=stats["total_issues_found"],
        avg_issues_per_review=stats["avg_issues_per_review"],
        feedback_participation_rate=stats["feedback_participation_rate"],
        timestamp=datetime.utcnow()
    )


@router.get("/global-trends", response_model=GlobalTrendsResponse)
async def get_global_trends(
    timeframe: str = Query("30d", regex="^(7d|30d|90d)$", description="Time range"),
    team_id: Optional[str] = Query(None, description="Filter by team"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get global issue trends over time.
    
    Requirements: 9.1, 9.2 - Global trends visualization
    """
    analytics_service = GlobalAnalyticsService(db)
    trends = await analytics_service.get_global_issue_trends(
        timeframe=timeframe,
        team_id=team_id
    )
    
    data_points = []
    for point in trends["data_points"]:
        data_points.append(GlobalTrendsDataPoint(
            date=point["date"],
            reviews=point["reviews"],
            errors=point["errors"],
            warnings=point["warnings"],
            security_issues=point["security_issues"],
            total_issues=point["total_issues"]
        ))
    
    return GlobalTrendsResponse(
        timeframe=timeframe,
        data_points=data_points,
        summary=trends["summary"]
    )


@router.get("/team-comparison", response_model=List[TeamComparisonItem])
async def get_team_comparison(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get comparison metrics across all teams.
    
    Requirements: 9.3 - Team comparison analytics
    """
    analytics_service = GlobalAnalyticsService(db)
    comparison = await analytics_service.get_team_comparison()
    
    items = []
    for team_data in comparison:
        items.append(TeamComparisonItem(
            team_id=team_data["team_id"],
            team_name=team_data["team_name"],
            total_reviews=team_data["total_reviews"],
            avg_issues_per_review=team_data["avg_issues_per_review"],
            feedback_acceptance_rate=team_data["feedback_acceptance_rate"],
            active_members=team_data["active_members"]
        ))
    
    return items


@router.get("/all-reviews", response_model=ReviewsResponse)
async def get_all_reviews(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    team_id: Optional[str] = Query(None, description="Filter by team"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get all code reviews across the platform.
    
    Requirements: 10.1 - View all code reviews
    """
    analytics_service = GlobalAnalyticsService(db)
    
    result = await analytics_service.get_all_reviews(
        page=page,
        page_size=page_size,
        team_id=team_id,
        date_from=date_from,
        date_to=date_to
    )
    
    reviews = []
    for review in result["reviews"]:
        reviews.append(ReviewItem(
            analysis_id=review["analysis_id"],
            user_id=review["user_id"],
            username=review["username"],
            team_name=review.get("team_name"),
            filename=review["filename"],
            created_at=review["created_at"],
            issues_count=review["issues_count"],
            feedback_count=review["feedback_count"]
        ))
    
    return ReviewsResponse(
        reviews=reviews,
        total=result["total"],
        page=page,
        page_size=page_size
    )


@router.get("/all-feedback", response_model=FeedbackResponse)
async def get_all_feedback(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    feedback_type: Optional[str] = Query(None, description="Filter by type"),
    team_id: Optional[str] = Query(None, description="Filter by team"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get all feedback data across the platform.
    
    Requirements: 10.2, 10.3 - View aggregated feedback data
    """
    analytics_service = GlobalAnalyticsService(db)
    
    result = await analytics_service.get_all_feedback(
        page=page,
        page_size=page_size,
        feedback_type=feedback_type,
        team_id=team_id
    )
    
    feedback_items = []
    for feedback in result["feedback"]:
        feedback_items.append(FeedbackItem(
            feedback_id=feedback["feedback_id"],
            user_id=feedback["user_id"],
            username=feedback["username"],
            issue_id=feedback["issue_id"],
            feedback_type=feedback["feedback_type"],
            created_at=feedback["created_at"],
            comment=feedback.get("comment")
        ))
    
    return FeedbackResponse(
        feedback=feedback_items,
        summary=result["summary"],
        total=result["total"],
        page=page,
        page_size=page_size
    )


class CriticalityDistributionResponse(BaseModel):
    timeframe: str
    team_id: Optional[str]
    distribution: dict
    total_issues: int
    generated_at: str


@router.get("/criticality-distribution", response_model=CriticalityDistributionResponse)
async def get_criticality_distribution(
    timeframe: str = Query("30d", regex="^(7d|30d|90d|1y)$", description="Time range"),
    team_id: Optional[str] = Query(None, description="Filter by team"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get global criticality distribution of issues.
    
    Requirements: 9.3, 10.3 - Issue severity distribution with team filtering
    """
    analytics_service = GlobalAnalyticsService(db)
    distribution = await analytics_service.get_criticality_distribution(
        timeframe=timeframe,
        team_id=team_id
    )
    
    return CriticalityDistributionResponse(
        timeframe=distribution["timeframe"],
        team_id=distribution["team_id"],
        distribution=distribution["distribution"],
        total_issues=distribution["total_issues"],
        generated_at=distribution["generated_at"]
    )
