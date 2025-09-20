"""
Analysis-related Pydantic schemas for API responses and requests.

This module contains enhanced schemas for code analysis results,
including CodeIssue and CodeMetrics models as specified in the design.

Requirements covered: 2.1, 5.1, 5.2
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class IssueSeverity(str, Enum):
    """Enumeration of issue severity levels."""
    ERROR = "error"
    WARNING = "warning" 
    INFO = "info"
    SUGGESTION = "suggestion"

class IssueCategory(str, Enum):
    """Enumeration of issue categories."""
    AI_REVIEW = "ai-review"
    SYNTAX = "syntax"
    STYLE = "style"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    COMPLEXITY = "complexity"
    DOCUMENTATION = "documentation"

class CodeIssue(BaseModel):
    """
    Represents a single code issue found during analysis.
    
    This model provides structured information about code issues
    including location, severity, and suggested improvements.
    """
    id: str = Field(description="Unique identifier for this issue")
    line: int = Field(ge=1, description="Line number where issue occurs")
    column: int = Field(ge=1, default=1, description="Column number where issue occurs")
    severity: IssueSeverity = Field(description="Issue severity level")
    message: str = Field(min_length=1, description="Human-readable issue description")
    rule: str = Field(description="Rule or check that triggered this issue")
    category: IssueCategory = Field(default=IssueCategory.AI_REVIEW, description="Issue category")
    suggestion: Optional[str] = Field(default=None, description="Suggested fix or improvement")
    
    # Additional metadata
    start_line: Optional[int] = Field(default=None, ge=1, description="Start line for multi-line issues")
    end_line: Optional[int] = Field(default=None, ge=1, description="End line for multi-line issues")
    start_column: Optional[int] = Field(default=None, ge=1, description="Start column for precise location")
    end_column: Optional[int] = Field(default=None, ge=1, description="End column for precise location")
    
    # Code context
    code_snippet: Optional[str] = Field(default=None, description="Relevant code snippet")
    suggested_fix: Optional[str] = Field(default=None, description="Suggested code replacement")
    
    @validator('end_line')
    def validate_end_line(cls, v, values):
        if v is not None and 'start_line' in values and values['start_line'] is not None:
            if v < values['start_line']:
                raise ValueError('end_line must be >= start_line')
        return v

class CodeMetrics(BaseModel):
    """
    Represents code quality metrics calculated during analysis.
    
    This model provides quantitative measures of code quality
    including complexity, maintainability, and other metrics.
    """
    lines_of_code: int = Field(ge=0, description="Total lines of code (excluding empty lines)")
    total_lines: int = Field(ge=0, description="Total lines including empty lines and comments")
    complexity: int = Field(ge=0, default=0, description="Cyclomatic complexity score")
    maintainability_index: int = Field(ge=0, le=100, default=0, description="Maintainability index (0-100)")
    duplicate_lines: int = Field(ge=0, default=0, description="Number of duplicate lines detected")
    test_coverage: Optional[float] = Field(ge=0, le=100, default=None, description="Test coverage percentage")
    
    # Additional metrics
    comment_lines: int = Field(ge=0, default=0, description="Number of comment lines")
    blank_lines: int = Field(ge=0, default=0, description="Number of blank lines")
    function_count: int = Field(ge=0, default=0, description="Number of functions/methods")
    class_count: int = Field(ge=0, default=0, description="Number of classes")
    
    # Ratios and derived metrics
    comment_ratio: float = Field(ge=0, le=1, default=0, description="Ratio of comment lines to total lines")
    complexity_per_function: Optional[float] = Field(ge=0, default=None, description="Average complexity per function")
    
    @validator('comment_ratio')
    def validate_comment_ratio(cls, v, values):
        if 'total_lines' in values and values['total_lines'] > 0:
            max_ratio = values['comment_lines'] / values['total_lines'] if 'comment_lines' in values else 0
            if v > max_ratio + 0.01:  # Small tolerance for floating point
                raise ValueError('comment_ratio cannot exceed actual ratio of comment lines')
        return v

class AnalysisStatus(str, Enum):
    """Enumeration of analysis status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class DirectAnalysisResponse(BaseModel):
    """
    Response model for direct code analysis results.
    
    This model represents the complete response from a direct code analysis,
    including all issues, metrics, and metadata.
    """
    analysis_id: str = Field(description="Unique identifier for this analysis")
    status: AnalysisStatus = Field(description="Current analysis status")
    issues: List[CodeIssue] = Field(description="List of code issues found")
    metrics: CodeMetrics = Field(description="Code quality metrics")
    summary: str = Field(description="Human-readable analysis summary")
    
    # Timing information
    created_at: datetime = Field(description="When the analysis was created")
    completed_at: Optional[datetime] = Field(default=None, description="When the analysis was completed")
    
    # Input metadata
    language: str = Field(description="Programming language analyzed")
    filename: Optional[str] = Field(default=None, description="Original filename if provided")
    file_size_bytes: int = Field(ge=0, description="Size of analyzed code in bytes")
    
    # Analysis metadata
    processing_time_ms: Optional[int] = Field(default=None, ge=0, description="Analysis processing time in milliseconds")
    ai_model_used: Optional[str] = Field(default=None, description="AI model used for analysis")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DirectAnalysisHistoryItem(BaseModel):
    """
    Simplified model for analysis history listings.
    
    Used for displaying user's analysis history without full details.
    """
    analysis_id: str = Field(description="Unique identifier for this analysis")
    status: AnalysisStatus = Field(description="Analysis status")
    language: str = Field(description="Programming language")
    filename: Optional[str] = Field(default=None, description="Original filename")
    issues_count: int = Field(ge=0, description="Total number of issues found")
    errors_count: int = Field(ge=0, description="Number of error-level issues")
    warnings_count: int = Field(ge=0, description="Number of warning-level issues")
    lines_of_code: Optional[int] = Field(default=None, ge=0, description="Lines of code analyzed")
    created_at: datetime = Field(description="When the analysis was created")
    completed_at: Optional[datetime] = Field(default=None, description="When the analysis was completed")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AnalysisHistoryResponse(BaseModel):
    """Response model for analysis history listings."""
    analyses: List[DirectAnalysisHistoryItem] = Field(description="List of user's analyses")
    total_count: int = Field(ge=0, description="Total number of analyses for the user")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Number of items per page")
    has_next: bool = Field(description="Whether there are more pages")
    has_previous: bool = Field(description="Whether there are previous pages")

class AnalysisStatsResponse(BaseModel):
    """Response model for user analysis statistics."""
    total_analyses: int = Field(ge=0, description="Total number of analyses performed")
    completed_analyses: int = Field(ge=0, description="Number of completed analyses")
    failed_analyses: int = Field(ge=0, description="Number of failed analyses")
    total_issues_found: int = Field(ge=0, description="Total issues found across all analyses")
    total_lines_analyzed: int = Field(ge=0, description="Total lines of code analyzed")
    languages_used: List[str] = Field(description="List of programming languages analyzed")
    avg_issues_per_analysis: float = Field(ge=0, description="Average issues per analysis")
    most_common_issue_types: List[Dict[str, Any]] = Field(description="Most common issue categories and counts")
    
    # Time-based statistics
    analyses_this_week: int = Field(ge=0, description="Analyses performed this week")
    analyses_this_month: int = Field(ge=0, description="Analyses performed this month")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }