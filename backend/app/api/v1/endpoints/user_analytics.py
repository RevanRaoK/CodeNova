# app/api/v1/endpoints/user_analytics.py

"""
User analytics endpoints for data visualizations.
Requirements: 4.1, 4.2, 5.1, 5.2
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.services.analytics_service import AnalyticsService
from pydantic import BaseModel

router = APIRouter()


class IssueTrendsDataPoint(BaseModel):
    date: str
    errors: int
    security_issues: int
    warnings: int
    total: int


class IssueTrendsResponse(BaseModel):
    timeframe: str
    data_points: List[IssueTrendsDataPoint]
    summary: dict


class CriticalityDistributionItem(BaseModel):
    severity: str
    count: int
    percentage: float


class CriticalityDistributionResponse(BaseModel):
    timeframe: str
    distribution: List[CriticalityDistributionItem]
    total_issues: int


@router.get("/issue-trends", response_model=IssueTrendsResponse)
async def get_issue_trends(
    timeframe: str = Query("30d", regex="^(7d|30d|90d)$", description="Time range"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get issue trends over time for the current user.
    
    Requirements: 4.1, 4.2 - Issue trends visualization
    """
    analytics_service = AnalyticsService(db)
    
    trends = await analytics_service.get_issue_trends(
        user_id=current_user.id,
        timeframe=timeframe
    )
    
    data_points = []
    for point in trends["data_points"]:
        data_points.append(IssueTrendsDataPoint(
            date=point["date"],
            errors=point["errors"],
            security_issues=point["security_issues"],
            warnings=point["warnings"],
            total=point["total"]
        ))
    
    return IssueTrendsResponse(
        timeframe=timeframe,
        data_points=data_points,
        summary=trends["summary"]
    )


@router.get("/criticality-distribution", response_model=CriticalityDistributionResponse)
async def get_criticality_distribution(
    timeframe: str = Query("30d", regex="^(7d|30d|90d)$", description="Time range"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get criticality distribution for the current user.
    
    Requirements: 5.1, 5.2 - Criticality distribution visualization
    """
    analytics_service = AnalyticsService(db)
    
    distribution = await analytics_service.get_criticality_distribution(
        user_id=current_user.id,
        timeframe=timeframe
    )
    
    items = []
    for severity, data in distribution["distribution"].items():
        items.append(CriticalityDistributionItem(
            severity=severity,
            count=data["count"],
            percentage=data["percentage"]
        ))
    
    return CriticalityDistributionResponse(
        timeframe=timeframe,
        distribution=items,
        total_issues=distribution["total_issues"]
    )
