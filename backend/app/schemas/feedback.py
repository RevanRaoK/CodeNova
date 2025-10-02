"""
Pydantic schemas for feedback system API requests and responses.

This module contains the data validation schemas for:
- Feedback submission and validation
- Feedback statistics and aggregation
- Issue tracking and management

Requirements covered: 2.1, 2.2, 2.3, 5.1, 5.2
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import re


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
    
    @field_validator('issue_id')
    @classmethod
    def validate_issue_id(cls, v):
        """Validate issue ID format - must be 64-character hexadecimal string (SHA-256)."""
        if not v:
            raise ValueError("Issue ID is required")
        
        # Check if it's a valid 64-character hexadecimal string (SHA-256 hash)
        if not re.match(r'^[a-fA-F0-9]{64}$', v):
            raise ValueError("Issue ID must be a 64-character hexadecimal string")
        
        return v.lower()  # Normalize to lowercase
    
    @field_validator('feedback_comment')
    @classmethod
    def validate_comment_length(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        
        # Check for potentially malicious content
        if v and any(char in v for char in ['<script', 'javascript:', 'data:']):
            raise ValueError("Feedback comment contains potentially unsafe content")
        
        return v
    
    @field_validator('modified_suggestion')
    @classmethod
    def validate_modified_suggestion_content(cls, v):
        # Validate modified suggestion length and content
        if v and len(v.strip()) == 0:
            return None
            
        # Check for potentially malicious content in code suggestions
        if v and any(char in v for char in ['<script', 'javascript:', 'eval(']):
            raise ValueError("Modified suggestion contains potentially unsafe content")
        
        return v
    
    @model_validator(mode='after')
    def validate_modify_requires_suggestion(self):
        """Validate that modified suggestion is required when feedback type is MODIFY."""
        if self.feedback_type == FeedbackType.MODIFY and not self.modified_suggestion:
            raise ValueError("Modified suggestion is required when feedback type is 'modify'")
        return self
    
    @field_validator('context_data')
    @classmethod
    def validate_context_data(cls, v):
        """Validate context data structure and content."""
        if v is None:
            return v
        
        if not isinstance(v, dict):
            raise ValueError("Context data must be a dictionary")
        
        # Limit the size of context data
        if len(str(v)) > 10000:  # 10KB limit
            raise ValueError("Context data is too large (max 10KB)")
        
        # Check for nested depth (prevent deeply nested objects)
        def check_depth(obj, current_depth=0, max_depth=5):
            if current_depth > max_depth:
                raise ValueError("Context data is too deeply nested")
            if isinstance(obj, dict):
                for value in obj.values():
                    check_depth(value, current_depth + 1, max_depth)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, current_depth + 1, max_depth)
        
        check_depth(v)
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "issue_id": "abc123def456...",
                "feedback_type": "accept",
                "feedback_comment": "This suggestion helped improve code readability",
                "user_experience_level": "intermediate",
                "code_review_context": "team"
            }
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
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 123,
                "issue_id": "abc123def456...",
                "feedback_type": "accept",
                "feedback_value": 1,
                "created_at": "2024-01-15T10:30:00Z",
                "is_validated": False
            }
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
    
    model_config = {"from_attributes": True}


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
    
    model_config = {
        "json_schema_extra": {
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
    }


class FeedbackValidationRequest(BaseModel):
    """Schema for validating feedback quality (admin use)."""
    
    feedback_id: int = Field(..., description="Feedback record ID to validate")
    is_valid: bool = Field(..., description="Whether the feedback is considered valid")
    validation_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality score for the feedback")
    validation_comment: Optional[str] = Field(None, max_length=500, description="Validation notes")


class BulkFeedbackRequest(BaseModel):
    """Schema for submitting multiple feedback records at once."""
    
    feedback_submissions: List[FeedbackSubmissionRequest] = Field(..., max_length=50, description="List of feedback submissions")
    
    @field_validator('feedback_submissions')
    @classmethod
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
    
    @model_validator(mode='after')
    def validate_date_range(self):
        if self.end_date < self.start_date:
            raise ValueError("End date must be after start date")
        
        # Prevent excessively large date ranges (more than 1 year)
        max_range = timedelta(days=365)
        if self.end_date - self.start_date > max_range:
            raise ValueError("Date range cannot exceed 365 days")
        
        return self


class UserPermissionLevel(str, Enum):
    """User permission levels for feedback operations."""
    READ_ONLY = "read_only"
    SUBMIT_FEEDBACK = "submit_feedback"
    VALIDATE_FEEDBACK = "validate_feedback"
    ADMIN = "admin"


class FeedbackPermissionRequest(BaseModel):
    """Schema for validating user permissions for feedback operations."""
    
    user_id: int = Field(..., gt=0, description="User ID requesting permission")
    operation: str = Field(..., description="Operation being requested")
    resource_id: Optional[str] = Field(None, description="Resource ID (issue_id, feedback_id, etc.)")
    
    @field_validator('operation')
    @classmethod
    def validate_operation(cls, v):
        """Validate that the operation is one of the allowed operations."""
        allowed_operations = {
            'submit_feedback', 'view_feedback', 'validate_feedback', 
            'view_statistics', 'manage_feedback', 'delete_feedback',
            'export_data', 'manage_users'
        }
        
        if v not in allowed_operations:
            raise ValueError(f"Invalid operation: {v}. Must be one of {allowed_operations}")
        
        return v
    
    @model_validator(mode='after')
    def validate_resource_id(self):
        """Validate resource ID format based on operation type."""
        if self.resource_id is None:
            return self
        
        # For feedback-related operations, validate issue ID format
        if self.operation in ['submit_feedback', 'view_feedback'] and self.resource_id:
            if not re.match(r'^[a-fA-F0-9]{64}$', self.resource_id):
                raise ValueError("Resource ID must be a valid 64-character hexadecimal string for feedback operations")
        
        # For validation operations, allow numeric feedback IDs
        elif self.operation in ['validate_feedback', 'manage_feedback'] and self.resource_id:
            if not (self.resource_id.isdigit() or re.match(r'^[a-fA-F0-9]{64}$', self.resource_id)):
                raise ValueError("Resource ID must be a numeric feedback ID or 64-character issue ID")
        
        return self


class BulkFeedbackValidationRequest(BaseModel):
    """Schema for bulk validation of feedback records."""
    
    feedback_ids: List[int] = Field(..., min_length=1, max_length=100, description="List of feedback IDs to validate")
    validation_action: str = Field(..., description="Validation action to perform")
    validation_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality score for bulk validation")
    validation_comment: Optional[str] = Field(None, max_length=500, description="Bulk validation notes")
    
    @field_validator('validation_action')
    @classmethod
    def validate_action(cls, v):
        """Validate bulk validation action."""
        allowed_actions = {'approve', 'reject', 'flag_for_review', 'mark_invalid'}
        
        if v not in allowed_actions:
            raise ValueError(f"Invalid validation action: {v}. Must be one of {allowed_actions}")
        
        return v
    
    @field_validator('feedback_ids')
    @classmethod
    def validate_feedback_ids(cls, v):
        """Validate feedback ID list."""
        if not v:
            raise ValueError("At least one feedback ID is required")
        
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Duplicate feedback IDs are not allowed")
        
        # Validate each ID is positive
        for feedback_id in v:
            if feedback_id <= 0:
                raise ValueError(f"Invalid feedback ID: {feedback_id}. Must be positive integer")
        
        return v


class FeedbackExportRequest(BaseModel):
    """Schema for exporting feedback data."""
    
    export_format: str = Field(..., description="Export format (json, csv, xlsx)")
    date_range: Optional[DateRange] = Field(None, description="Date range for export")
    pattern_types: Optional[List[str]] = Field(None, max_length=50, description="Filter by pattern types")
    feedback_types: Optional[List[FeedbackType]] = Field(None, description="Filter by feedback types")
    user_experience_levels: Optional[List[ExperienceLevel]] = Field(None, description="Filter by experience levels")
    include_validated_only: bool = Field(False, description="Include only validated feedback")
    include_personal_data: bool = Field(False, description="Include user personal data (admin only)")
    
    @field_validator('export_format')
    @classmethod
    def validate_export_format(cls, v):
        """Validate export format."""
        allowed_formats = {'json', 'csv', 'xlsx'}
        
        if v.lower() not in allowed_formats:
            raise ValueError(f"Invalid export format: {v}. Must be one of {allowed_formats}")
        
        return v.lower()
    
    @field_validator('pattern_types')
    @classmethod
    def validate_pattern_types(cls, v):
        """Validate pattern types list."""
        if v is None:
            return v
        
        # Check for empty strings
        if any(not pattern.strip() for pattern in v):
            raise ValueError("Pattern types cannot be empty strings")
        
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Duplicate pattern types are not allowed")
        
        return v


class FeedbackAnalyticsRequest(BaseModel):
    """Schema for requesting feedback analytics and insights."""
    
    analysis_type: str = Field(..., description="Type of analysis to perform")
    date_range: Optional[DateRange] = Field(None, description="Date range for analysis")
    group_by: Optional[str] = Field(None, description="Grouping dimension")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    
    @field_validator('analysis_type')
    @classmethod
    def validate_analysis_type(cls, v):
        """Validate analysis type."""
        allowed_types = {
            'acceptance_trends', 'pattern_performance', 'user_behavior', 
            'model_improvement', 'feedback_quality', 'response_time_analysis'
        }
        
        if v not in allowed_types:
            raise ValueError(f"Invalid analysis type: {v}. Must be one of {allowed_types}")
        
        return v
    
    @field_validator('group_by')
    @classmethod
    def validate_group_by(cls, v):
        """Validate grouping dimension."""
        if v is None:
            return v
        
        allowed_dimensions = {
            'date', 'week', 'month', 'pattern_type', 'user_experience', 
            'feedback_type', 'severity', 'user_id'
        }
        
        if v not in allowed_dimensions:
            raise ValueError(f"Invalid group_by dimension: {v}. Must be one of {allowed_dimensions}")
        
        return v