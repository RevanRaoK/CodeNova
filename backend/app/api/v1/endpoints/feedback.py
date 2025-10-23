"""
Feedback API endpoints for collecting and analyzing user feedback on AI suggestions.

This module provides endpoints for:
- Submitting feedback on AI code suggestions
- Retrieving feedback statistics and analytics
- Managing feedback validation (admin functions)

Requirements covered: 2.1, 2.2, 5.1, 5.2
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.users import User
from app.services.feedback_service import FeedbackService, FeedbackValidationError
from app.schemas.feedback import (
    FeedbackSubmissionRequest, FeedbackResponse, FeedbackStatsResponse,
    FeedbackValidationRequest, DateRange, BulkFeedbackRequest,
    FeedbackHistoryResponse, ExperienceLevel
)
from app.api.v1.endpoints.auth import get_current_active_user, get_current_active_admin

router = APIRouter()


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    feedback_request: FeedbackSubmissionRequest,
) -> Any:
    """
    Submit feedback on an AI code suggestion.
    
    This endpoint allows authenticated users to provide feedback (accept/reject/modify)
    on AI-generated code suggestions. The feedback is used to improve the AI model
    through the learning pipeline.
    
    Requirements: 2.1, 2.2, 5.1
    """
    try:
        feedback_service = FeedbackService(db)
        feedback_record = feedback_service.record_feedback(
            user_id=current_user.id,
            feedback_request=feedback_request
        )
        
        return FeedbackResponse(
            id=feedback_record.id,
            issue_id=feedback_record.issue_id,
            feedback_type=feedback_record.feedback_type,
            feedback_value=feedback_record.feedback_value,
            created_at=feedback_record.created_at,
            is_validated=feedback_record.is_validated
        )
        
    except FeedbackValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/feedback/stats", response_model=FeedbackStatsResponse)
def get_feedback_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    start_date: Optional[str] = Query(None, description="Start date for statistics (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date for statistics (YYYY-MM-DD)"),
    pattern_type: Optional[str] = Query(None, description="Filter by issue pattern type"),
    user_experience_level: Optional[ExperienceLevel] = Query(None, description="Filter by user experience level"),
) -> Any:
    """
    Get comprehensive feedback statistics and analytics.
    
    This endpoint provides aggregated feedback statistics including acceptance rates,
    trends over time, and pattern-specific analytics. Useful for monitoring AI model
    performance and identifying areas for improvement.
    
    Requirements: 2.4, 4.1, 4.2, 5.2
    """
    try:
        feedback_service = FeedbackService(db)
        
        # Parse date range if provided
        date_range = None
        if start_date and end_date:
            try:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_date)
                end_dt = datetime.fromisoformat(end_date)
                date_range = DateRange(start_date=start_dt, end_date=end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD format."
                )
        
        # Get statistics
        stats = feedback_service.get_feedback_statistics(
            date_range=date_range,
            pattern_type=pattern_type,
            user_experience_level=user_experience_level.value if user_experience_level else None
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback statistics: {str(e)}"
        )


@router.get("/feedback/history", response_model=FeedbackHistoryResponse)
def get_user_feedback_history(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of records per page"),
) -> Any:
    """
    Get the current user's feedback history.
    
    Returns a paginated list of all feedback submitted by the current user,
    ordered by most recent first.
    
    Requirements: 5.1, 5.2
    """
    try:
        feedback_service = FeedbackService(db)
        feedback_records, total_count = feedback_service.get_user_feedback_history(
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )
        
        # Convert to response format
        feedback_responses = [
            FeedbackResponse(
                id=record.id,
                issue_id=record.issue_id,
                feedback_type=record.feedback_type,
                feedback_value=record.feedback_value,
                created_at=record.created_at,
                is_validated=record.is_validated
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


@router.post("/feedback/bulk", response_model=dict, status_code=status.HTTP_201_CREATED)
def submit_bulk_feedback(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    bulk_request: BulkFeedbackRequest,
) -> Any:
    """
    Submit multiple feedback records in a single request.
    
    This endpoint allows users to submit feedback for multiple issues at once,
    which is useful for batch processing of code review sessions.
    
    Requirements: 2.1, 2.2, 5.1
    """
    try:
        feedback_service = FeedbackService(db)
        results = []
        errors = []
        
        for i, feedback_request in enumerate(bulk_request.feedback_submissions):
            try:
                feedback_record = feedback_service.record_feedback(
                    user_id=current_user.id,
                    feedback_request=feedback_request
                )
                results.append({
                    "index": i,
                    "feedback_id": feedback_record.id,
                    "issue_id": feedback_record.issue_id,
                    "status": "success"
                })
            except FeedbackValidationError as e:
                errors.append({
                    "index": i,
                    "issue_id": feedback_request.issue_id,
                    "error": str(e),
                    "status": "error"
                })
        
        return {
            "total_submitted": len(bulk_request.feedback_submissions),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process bulk feedback: {str(e)}"
        )


@router.get("/issue/{issue_id}", response_model=list[FeedbackResponse])
def get_feedback_for_issue_alt(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    issue_id: str,
) -> Any:
    """
    Get all feedback records for a specific issue (alternative route).
    
    This endpoint returns all feedback submitted for a particular code issue.
    Alternative route for compatibility with frontend.
    
    Requirements: 5.1, 5.2
    """
    return get_feedback_for_issue(
        db=db,
        current_user=current_user,
        issue_id=issue_id
    )


@router.post("/feedback/{feedback_id}/validate", response_model=FeedbackResponse)
def validate_feedback(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
    feedback_id: int,
    validation_request: FeedbackValidationRequest,
) -> Any:
    """
    Validate feedback quality (admin only).
    
    This endpoint allows administrators to mark feedback as validated and
    assign quality scores, which helps ensure only high-quality feedback
    is used for model training.
    
    Requirements: 3.1, 6.1
    """
    try:
        feedback_service = FeedbackService(db)
        feedback_record = feedback_service.validate_feedback(
            feedback_id=feedback_id,
            validation_request=validation_request
        )
        
        return FeedbackResponse(
            id=feedback_record.id,
            issue_id=feedback_record.issue_id,
            feedback_type=feedback_record.feedback_type,
            feedback_value=feedback_record.feedback_value,
            created_at=feedback_record.created_at,
            is_validated=feedback_record.is_validated
        )
        
    except FeedbackValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate feedback: {str(e)}"
        )


@router.get("/feedback/trends", response_model=dict)
def get_feedback_trends(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    pattern_type: Optional[str] = Query(None, description="Filter by issue pattern type"),
) -> Any:
    """
    Get feedback trends over time.
    
    This endpoint provides trend analysis of feedback patterns over a specified
    time period, which is useful for monitoring model performance improvements
    and identifying patterns in user behavior.
    
    Requirements: 4.1, 4.2, 5.2
    """
    try:
        feedback_service = FeedbackService(db)
        trends = feedback_service.get_feedback_trends(
            days=days,
            pattern_type=pattern_type
        )
        
        return trends
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback trends: {str(e)}"
        )


@router.get("/feedback/statistics", response_model=dict)
def get_feedback_statistics_with_timeframe(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    timeframe: str = Query("week", description="Time period: week, month, quarter, year, all"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (admin only)"),
) -> Any:
    """
    Get comprehensive feedback statistics with timeframe parameter.
    
    This endpoint provides:
    - Aggregation queries for feedback by type (accept/reject/modify)
    - Feedback trends over time periods
    - Model performance metrics based on feedback data
    - Pattern-specific statistics
    
    Requirements: 2.2, 2.3, 2.4, 2.5
    """
    try:
        # Check if user is requesting data for another user (admin only)
        if user_id and user_id != current_user.id:
            if not hasattr(current_user, 'role') or current_user.role != 'admin':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required to view other users' data"
                )
        
        # Use current user ID if not specified or not admin
        target_user_id = user_id if user_id and hasattr(current_user, 'role') and current_user.role == 'admin' else current_user.id
        
        # Validate timeframe parameter
        valid_timeframes = ["week", "month", "quarter", "year", "all"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
            )
        
        feedback_service = FeedbackService(db)
        statistics = feedback_service.get_feedback_statistics_with_timeframe(
            timeframe=timeframe,
            user_id=target_user_id
        )
        
        return statistics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback statistics: {str(e)}"
        )


@router.get("/statistics", response_model=dict)
def get_feedback_statistics_endpoint(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    timeframe: str = Query("week", description="Time period for analysis (week, month, quarter, year)"),
) -> Any:
    """
    Get comprehensive feedback statistics with timeframe parameter.
    
    This endpoint provides:
    - Aggregation queries for feedback by type (accept/reject/modify)
    - Feedback trends over time periods
    - Model performance metrics based on feedback data
    
    Requirements: 2.2, 2.3, 2.4, 2.5
    """
    try:
        print(f"[DEBUG] /statistics endpoint called")
        print(f"[DEBUG] User ID: {current_user.id}")
        print(f"[DEBUG] Timeframe: {timeframe}")
        
        # Validate timeframe parameter
        valid_timeframes = ["week", "month", "quarter", "year"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
            )
        
        feedback_service = FeedbackService(db)
        statistics = feedback_service.get_feedback_statistics_with_timeframe(
            user_id=current_user.id,
            timeframe=timeframe
        )
        
        print(f"[DEBUG] Statistics type: {type(statistics)}")
        print(f"[DEBUG] Statistics keys: {statistics.keys() if isinstance(statistics, dict) else 'Not a dict'}")
        print(f"[DEBUG] Total feedback: {statistics.get('total_feedback') if isinstance(statistics, dict) else 'N/A'}")
        
        return statistics
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback statistics: {str(e)}"
        )


# IMPORTANT: This catch-all route must be at the end to avoid matching specific routes
@router.get("/{issue_id}", response_model=list[FeedbackResponse])
def get_feedback_for_issue(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    issue_id: str,
) -> Any:
    """
    Get all feedback records for a specific issue.
    
    This endpoint returns all feedback submitted for a particular code issue,
    which can be useful for understanding how different users responded to
    the same suggestion.
    
    Requirements: 5.1, 5.2
    
    NOTE: This route uses a path parameter and must be defined AFTER all
    specific routes (like /statistics, /history, etc.) to avoid conflicts.
    """
    try:
        feedback_service = FeedbackService(db)
        feedback_records = feedback_service.get_feedback_for_issue(issue_id)
        
        return [
            FeedbackResponse(
                id=record.id,
                issue_id=record.issue_id,
                feedback_type=record.feedback_type,
                feedback_value=record.feedback_value,
                created_at=record.created_at,
                is_validated=record.is_validated
            )
            for record in feedback_records
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback for issue: {str(e)}"
        )