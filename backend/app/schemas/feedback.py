"""
Pydantic schemas for feedback system API requests and responses.

This module contains the data validation schemas for:
- Feedback submission and validation
- Feedback statistics and aggregation
- Issue tracking and management

Requirements covered: 2.1, 2.2, 2.3, 5.1, 5.2
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class FeedbackType(str, Enum):
    """Valid feedback types for user responses to AI suggestions."""
    ACCEPT = "accept"
    REJECT = "reject"
    MODIFY = "modify"
    IGNORE = "ignore"


class ExperienceLevel(str, Enum):
    """User experience levels for context."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class ReviewContext(str, Enum):
    """Code review context types."""
    PERSONAL = "personal"
    TEAM = "team"
    PRODUCTION = "production"


class FeedbackSubmissionRequest(BaseModel):
    """Schema for submitting feedback on AI suggestions."""
    
    issue_id: str = Field(..., description="Unique identifier for the code issue")
    feedback_type: FeedbackType = Field(..., description="Type of feedback (accept/reject/modify/ignore)")
    feedback_comment: Optional[str] = Field(None, max_length=1000, description="Optional user comment")
    modified_suggestion: Optional[str] = Field(None, max_length=5000, description="User's modified version if applicable")
    
    # Context information
    user_experience_level: Optional[ExperienceLevel] = Field(None, description="User's experience level")
    code_review_context: Optional[ReviewContext] = Field(None, description="Context of the code review")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Additional context information")
    
    @validator('feedback_comment')
    def validate_comment_length(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v
    
    @validator('modified_suggestion')
    def validate_modified_suggestion(cls, v, values):
        if values.get('feedback_type') == FeedbackType.MODIFY and not v:
            raise ValueError("Modified suggestion is required when feedback type is 'modify'")
        return v

    class Config:
        schema_extra = {
            "example": {
                "issue_id": "abc123def456...",
                "feedback_type": "accept",
                "feedback_comment": "This suggestion helped improve code readability",
                "user_experience_level": "intermediate",
                "code_review_context": "team"
            }
        }


class FeedbackResponse(BaseModel):
    """Schema for feedback submission response."""
    
    id: int = Field(..., description="Feedback record ID")
    issue_id: str = Field(..., description="Issue ID that was given feedback")
    feedback_type: FeedbackType = Field(..., description="Type of feedback submitted")
    feedback_value: int = Field(..., description="Numeric feedback value (1=positive, -1=negative, 0=neutral)")
    created_at: datetime = Field(..., description="Timestamp when feedback was created")
    is_validated: bool = Field(..., description="Whether the feedback has been validated")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 123,
                "issue_id": "abc123def456...",
                "feedback_type": "accept",
                "feedback_value": 1,
                "created_at": "2024-01-15T10:30:00Z",
                "is_validated": False
            }
        }


class IssueResponse(BaseModel):
    """Schema for issue information response."""
    
    id: str = Field(..., description="Unique issue identifier")
    analysis_id: str = Field(..., description="Analysis ID this issue belongs to")
    pattern_type: str = Field(..., description="Type of code pattern detected")
    severity: str = Field(..., description="Issue severity level")
    suggestion_text: str = Field(..., description="AI-generated suggestion")
    location: Dict[str, Any] = Field(..., description="Location information in the code")
    status: str = Field(..., description="Current issue status")
    created_at: datetime = Field(..., description="Issue creation timestamp")
    
    class Config:
        orm_mode = True


class FeedbackStatsResponse(BaseModel):
    """Schema for feedback statistics response."""
    
    total_feedback_count: int = Field(..., description="Total number of feedback records")
    acceptance_rate: float = Field(..., description="Percentage of accepted suggestions")
    rejection_rate: float = Field(..., description="Percentage of rejected suggestions")
    modification_rate: float = Field(..., description="Percentage of modified suggestions")
    
    # Breakdown by feedback type
    feedback_breakdown: Dict[str, int] = Field(..., description="Count of each feedback type")
    
    # Time-based statistics
    feedback_by_date: Dict[str, int] = Field(..., description="Feedback count by date")
    
    # User experience breakdown
    feedback_by_experience: Dict[str, int] = Field(..., description="Feedback count by user experience level")
    
    # Issue pattern statistics
    pattern_feedback_stats: Dict[str, Dict[str, float]] = Field(..., description="Feedback rates by pattern type")
    
    # Performance metrics
    average_response_time_hours: Optional[float] = Field(None, description="Average time to receive feedback")
    most_common_patterns: List[str] = Field(..., description="Most frequently occurring issue patterns")
    
    class Config:
        schema_extra = {
            "example": {
                "total_feedback_count": 1250,
                "acceptance_rate": 72.5,
                "rejection_rate": 18.2,
                "modification_rate": 9.3,
                "feedback_breakdown": {
                    "accept": 906,
                    "reject": 228,
                    "modify": 116
                },
                "feedback_by_date": {
                    "2024-01-15": 45,
                    "2024-01-14": 38
                },
                "feedback_by_experience": {
                    "beginner": 320,
                    "intermediate": 680,
                    "expert": 250
                },
                "pattern_feedback_stats": {
                    "unused_variable": {
                        "acceptance_rate": 85.2,
                        "rejection_rate": 14.8
                    }
                },
                "average_response_time_hours": 2.4,
                "most_common_patterns": ["unused_variable", "code_complexity", "naming_convention"]
            }
        }


class FeedbackValidationRequest(BaseModel):
    """Schema for validating feedback quality (admin use)."""
    
    feedback_id: int = Field(..., description="Feedback record ID to validate")
    is_valid: bool = Field(..., description="Whether the feedback is considered valid")
    validation_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality score for the feedback")
    validation_comment: Optional[str] = Field(None, max_length=500, description="Validation notes")


class BulkFeedbackRequest(BaseModel):
    """Schema for submitting multiple feedback records at once."""
    
    feedback_submissions: List[FeedbackSubmissionRequest] = Field(..., max_items=50, description="List of feedback submissions")
    
    @validator('feedback_submissions')
    def validate_submissions_not_empty(cls, v):
        if not v:
            raise ValueError("At least one feedback submission is required")
        return v


class FeedbackHistoryResponse(BaseModel):
    """Schema for user's feedback history."""
    
    feedback_records: List[FeedbackResponse] = Field(..., description="List of user's feedback records")
    total_count: int = Field(..., description="Total number of feedback records")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of records per page")
    has_next: bool = Field(..., description="Whether there are more records")


class DateRange(BaseModel):
    """Schema for date range filters."""
    
    start_date: datetime = Field(..., description="Start date for the range")
    end_date: datetime = Field(..., description="End date for the range")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError("End date must be after start date")
        return v