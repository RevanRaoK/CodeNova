"""
Enhanced Feedback API endpoints for AI suggestions with detailed rejection reasons.

This module provides endpoints for:
- Submitting feedback on AI suggestions (accept/reject with reasons)
- Retrieving feedback analytics and statistics
- Managing feedback records

Requirements covered: 1.1, 1.2, 1.3, 1.4, 1.5
"""

from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.users import User
from app.models.enhanced_feedback import FeedbackAction
from app.services.enhanced_feedback_service import EnhancedFeedbackService
from app.repositories.feedback_repository import FeedbackRepository
from app.api.v1.endpoints.auth import get_current_active_user

router = APIRouter()


# Pydantic schemas for request/response
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any


class FeedbackSubmissionRequest(BaseModel):
    """Schema for submitting feedback on AI suggestions."""
    
    suggestion_id: str = Field(..., description="Unique identifier for the AI suggestion")
    action: FeedbackAction = Field(..., description="Accept or reject action")
    rejection_reasons: Optional[List[str]] = Field(None, description="List of predefined rejection reasons")
    custom_reason: Optional[str] = Field(None, max_length=1000, description="Custom reason text")
    suggestion_type: Optional[str] = Field(None, description="Type of AI suggestion")
    confidence_score: Optional[str] = Field(None, description="AI confidence level")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    @field_validator('rejection_reasons')
    @classmethod
    def validate_rejection_reasons(cls, v, info):
        """Validate rejection reasons are provided for reject actions."""
        # Note: We can't access other fields in field_validator, so we'll validate in the endpoint
        return v
    
    @field_validator('custom_reason')
    @classmethod
    def validate_custom_reason(cls, v):
        """Validate custom reason content."""
        if v and len(v.strip()) == 0:
            return None
        return v


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    
    id: str = Field(..., description="Feedback record ID")
    suggestion_id: str = Field(..., description="AI suggestion ID")
    user_id: int = Field(..., description="User ID who provided feedback")
    action: FeedbackAction = Field(..., description="Feedback action")
    rejection_reasons: Optional[List[str]] = Field(None, description="Rejection reasons")
    custom_reason: Optional[str] = Field(None, description="Custom reason")
    suggestion_type: Optional[str] = Field(None, description="Suggestion type")
    timestamp: datetime = Field(..., description="Feedback timestamp")
    
    model_config = {"from_attributes": True}


class FeedbackAnalyticsResponse(BaseModel):
    """Schema for feedback analytics response."""
    
    total_feedback_count: int = Field(..., description="Total feedback count")
    acceptance_rate: float = Field(..., description="Acceptance rate percentage")
    rejection_rate: float = Field(..., description="Rejection rate percentage")
    accept_count: int = Field(..., description="Number of accepts")
    reject_count: int = Field(..., description="Number of rejects")
    rejection_reasons_analysis: Dict[str, Any] = Field(..., description="Rejection reasons analysis")
    feedback_by_date: Dict[str, Dict[str, int]] = Field(..., description="Feedback by date")
    feedback_by_suggestion_type: Dict[str, Dict[str, int]] = Field(..., description="Feedback by type")
    learning_progress: Dict[str, Any] = Field(..., description="Learning progress indicators")


class FeedbackHistoryResponse(BaseModel):
    """Schema for feedback history response."""
    
    feedback_records: List[FeedbackResponse] = Field(..., description="List of feedback records")
    total_count: int = Field(..., description="Total number of records")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Records per page")
    has_next: bool = Field(..., description="Whether there are more records")


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    feedback_request: FeedbackSubmissionRequest,
) -> Any:
    """
    Submit feedback on an AI suggestion.
    
    This endpoint allows authenticated users to provide feedback (accept/reject)
    on AI-generated suggestions. For reject actions, rejection reasons are required.
    
    Requirements: 1.1, 1.2, 1.3
    """
    try:
        # Validate rejection reasons for reject actions
        if (feedback_request.action == FeedbackAction.REJECT and 
            not feedback_request.rejection_reasons):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejection reasons are required when rejecting a suggestion"
            )
        
        feedback_service = EnhancedFeedbackService(db)
        feedback_record = feedback_service.create_feedback(
            suggestion_id=feedback_request.suggestion_id,
            user_id=current_user.id,
            action=feedback_request.action,
            rejection_reasons=feedback_request.rejection_reasons,
            custom_reason=feedback_request.custom_reason,
            suggestion_type=feedback_request.suggestion_type,
            confidence_score=feedback_request.confidence_score,
            context_data=feedback_request.context_data
        )
        
        return FeedbackResponse(
            id=feedback_record.id,
            suggestion_id=feedback_record.suggestion_id,
            user_id=feedback_record.user_id,
            action=feedback_record.action,
            rejection_reasons=feedback_record.rejection_reasons,
            custom_reason=feedback_record.custom_reason,
            suggestion_type=feedback_record.suggestion_type,
            timestamp=feedback_record.timestamp
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/feedback/analytics", response_model=FeedbackAnalyticsResponse)
def get_feedback_analytics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    suggestion_type: Optional[str] = Query(None, description="Filter by suggestion type"),
    user_only: bool = Query(False, description="Show only current user's feedback")
) -> Any:
    """
    Get comprehensive feedback analytics.
    
    This endpoint provides aggregated feedback statistics including acceptance rates,
    rejection patterns, and learning progress indicators.
    
    Requirements: 1.4, 1.5
    """
    try:
        feedback_service = EnhancedFeedbackService(db)
        
        # Parse date parameters
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD."
                )
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD."
                )
        
        # Get analytics
        user_id = current_user.id if user_only else None
        analytics = feedback_service.get_feedback_analytics(
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt,
            suggestion_type=suggestion_type
        )
        
        return FeedbackAnalyticsResponse(**analytics)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback analytics: {str(e)}"
        )


@router.get("/feedback/history", response_model=FeedbackHistoryResponse)
def get_feedback_history(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page"),
    action_filter: Optional[FeedbackAction] = Query(None, description="Filter by action"),
    suggestion_type_filter: Optional[str] = Query(None, description="Filter by suggestion type")
) -> Any:
    """
    Get the current user's feedback history.
    
    Returns a paginated list of all feedback submitted by the current user,
    ordered by most recent first.
    
    Requirements: 1.4
    """
    try:
        feedback_repository = FeedbackRepository(db)
        feedback_records, total_count = feedback_repository.get_user_feedback_paginated(
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            action_filter=action_filter,
            suggestion_type_filter=suggestion_type_filter
        )
        
        # Convert to response format
        feedback_responses = [
            FeedbackResponse(
                id=record.id,
                suggestion_id=record.suggestion_id,
                user_id=record.user_id,
                action=record.action,
                rejection_reasons=record.rejection_reasons,
                custom_reason=record.custom_reason,
                suggestion_type=record.suggestion_type,
                timestamp=record.timestamp
            )
            for record in feedback_records
        ]
        
        return FeedbackHistoryResponse(
            feedback_records=feedback_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback history: {str(e)}"
        )


@router.get("/feedback/suggestion/{suggestion_id}", response_model=List[FeedbackResponse])
def get_feedback_for_suggestion(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    suggestion_id: str,
) -> Any:
    """
    Get all feedback records for a specific suggestion.
    
    This endpoint returns all feedback submitted for a particular AI suggestion,
    which can be useful for understanding how different users responded to
    the same suggestion.
    
    Requirements: 1.4
    """
    try:
        feedback_service = EnhancedFeedbackService(db)
        feedback_records = feedback_service.get_feedback_by_suggestion(suggestion_id)
        
        return [
            FeedbackResponse(
                id=record.id,
                suggestion_id=record.suggestion_id,
                user_id=record.user_id,
                action=record.action,
                rejection_reasons=record.rejection_reasons,
                custom_reason=record.custom_reason,
                suggestion_type=record.suggestion_type,
                timestamp=record.timestamp
            )
            for record in feedback_records
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback for suggestion: {str(e)}"
        )


@router.get("/feedback/rejection-reasons", response_model=Dict[str, Any])
def get_rejection_reasons_analysis(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    user_only: bool = Query(False, description="Show only current user's data")
) -> Any:
    """
    Get detailed analysis of rejection reasons.
    
    This endpoint provides insights into why suggestions are being rejected,
    including common rejection reasons and custom feedback.
    
    Requirements: 1.4, 1.5
    """
    try:
        feedback_repository = FeedbackRepository(db)
        
        # Parse date parameters
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD."
                )
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD."
                )
        
        user_id = current_user.id if user_only else None
        analysis = feedback_repository.get_rejection_reasons_analysis(
            start_date=start_dt,
            end_date=end_dt,
            user_id=user_id
        )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve rejection reasons analysis: {str(e)}"
        )


@router.get("/feedback/daily-stats", response_model=Dict[str, Dict[str, int]])
def get_daily_feedback_stats(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    user_only: bool = Query(False, description="Show only current user's data")
) -> Any:
    """
    Get daily feedback statistics over a specified period.
    
    This endpoint provides day-by-day breakdown of feedback activity,
    useful for tracking engagement and identifying patterns.
    
    Requirements: 1.4
    """
    try:
        feedback_repository = FeedbackRepository(db)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        user_id = current_user.id if user_only else None
        daily_stats = feedback_repository.get_daily_feedback_counts(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        return daily_stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve daily feedback statistics: {str(e)}"
        )


@router.get("/feedback/user-summary", response_model=Dict[str, Any])
def get_user_feedback_summary(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get a summary of the current user's feedback activity.
    
    This endpoint provides an overview of the user's feedback patterns,
    including total counts, rates, and engagement metrics.
    
    Requirements: 1.4
    """
    try:
        feedback_repository = FeedbackRepository(db)
        summary = feedback_repository.get_user_feedback_summary(current_user.id)
        
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user feedback summary: {str(e)}"
        )


@router.post("/feedback/update-learning-patterns", response_model=Dict[str, Any])
def trigger_learning_update(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Trigger an update of AI learning patterns based on recent feedback.
    
    This endpoint initiates a background process to analyze recent feedback
    and update AI learning patterns for model improvement.
    
    Requirements: 1.5
    """
    try:
        feedback_service = EnhancedFeedbackService(db)
        
        # Get recent feedback data for learning
        recent_feedback = feedback_service.get_user_feedback_history(
            user_id=current_user.id,
            page=1,
            page_size=1000  # Get recent feedback for analysis
        )[0]
        
        # Prepare feedback data for learning
        feedback_data = {
            'user_id': current_user.id,
            'feedback_count': len(recent_feedback),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Update learning patterns
        update_result = feedback_service.update_ai_learning_patterns(feedback_data)
        
        return update_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update learning patterns: {str(e)}"
        )