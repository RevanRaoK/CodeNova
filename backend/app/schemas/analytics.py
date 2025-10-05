"""
Pydantic schemas for analytics API requests and responses.

This module contains the data validation schemas for:
- Analytics dashboard data
- Real-time analytics updates
- Data export functionality
- Performance metrics

Requirements covered: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TimeframeEnum(str, Enum):
    """Valid timeframes for analytics queries."""
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"
    NINETY_DAYS = "90d"
    ONE_YEAR = "1y"


class ExportFormatEnum(str, Enum):
    """Valid export formats for analytics data."""
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"


class AnalyticsRequest(BaseModel):
    """Base schema for analytics requests."""
    
    user_id: Optional[int] = Field(None, description="Optional filter by specific user")
    timeframe: TimeframeEnum = Field(TimeframeEnum.THIRTY_DAYS, description="Time period for analysis")
    pattern_type: Optional[str] = Field(None, description="Optional filter by pattern type")
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("User ID must be positive")
        return v


class AcceptanceRatesResponse(BaseModel):
    """Schema for acceptance rates analytics response."""
    
    total_feedback: int = Field(..., description="Total number of feedback records")
    acceptance_rate: float = Field(..., description="Overall acceptance rate percentage")
    rejection_rate: float = Field(..., description="Overall rejection rate percentage")
    daily_rates: Dict[str, float] = Field(..., description="Daily acceptance rates")
    pattern_breakdown: Dict[str, Dict[str, Any]] = Field(..., description="Acceptance rates by pattern type")
    timeframe: str = Field(..., description="Time period analyzed")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_feedback": 1250,
                "acceptance_rate": 72.5,
                "rejection_rate": 18.2,
                "daily_rates": {
                    "2024-01-15": 75.0,
                    "2024-01-14": 68.5
                },
                "pattern_breakdown": {
                    "unused_variable": {
                        "acceptance_rate": 85.2,
                        "total_feedback": 150,
                        "accept_count": 128,
                        "reject_count": 22
                    }
                },
                "timeframe": "30d"
            }
        }
    }


class RejectionPatternsResponse(BaseModel):
    """Schema for rejection patterns analytics response."""
    
    total_rejections: int = Field(..., description="Total number of rejections")
    rejection_reasons: Dict[str, int] = Field(..., description="Count of each rejection reason")
    custom_reasons: List[str] = Field(..., description="Recent custom rejection reasons")
    pattern_rejections: Dict[str, int] = Field(..., description="Rejections by pattern type")
    timeframe: str = Field(..., description="Time period analyzed")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_rejections": 228,
                "rejection_reasons": {
                    "incorrect": 85,
                    "not_applicable": 62,
                    "too_complex": 45,
                    "others": 36
                },
                "custom_reasons": [
                    "Doesn't fit our coding style",
                    "Performance concerns",
                    "Already implemented differently"
                ],
                "pattern_rejections": {
                    "unused_variable": 45,
                    "code_complexity": 38,
                    "naming_convention": 32
                },
                "timeframe": "30d"
            }
        }
    }


class UsageStatisticsResponse(BaseModel):
    """Schema for usage statistics analytics response."""
    
    total_interactions: int = Field(..., description="Total number of user interactions")
    unique_users: int = Field(..., description="Number of unique users")
    daily_activity: Dict[str, int] = Field(..., description="Daily interaction counts")
    most_active_users: Dict[int, int] = Field(..., description="Most active users and their interaction counts")
    suggestion_types_usage: Dict[str, int] = Field(..., description="Usage count by suggestion type")
    average_daily_interactions: float = Field(..., description="Average interactions per day")
    timeframe: str = Field(..., description="Time period analyzed")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_interactions": 1250,
                "unique_users": 45,
                "daily_activity": {
                    "2024-01-15": 85,
                    "2024-01-14": 72
                },
                "most_active_users": {
                    "123": 45,
                    "456": 38,
                    "789": 32
                },
                "suggestion_types_usage": {
                    "unused_variable": 320,
                    "code_complexity": 280,
                    "naming_convention": 250
                },
                "average_daily_interactions": 41.7,
                "timeframe": "30d"
            }
        }
    }


class ModelVersionInfo(BaseModel):
    """Schema for model version information."""
    
    version: str = Field(..., description="Model version name")
    accuracy: Optional[float] = Field(None, description="Model accuracy score")
    acceptance_rate: Optional[float] = Field(None, description="User acceptance rate")
    created_at: Optional[str] = Field(None, description="Version creation timestamp")
    is_active: bool = Field(..., description="Whether this version is currently active")


class LearningProgressResponse(BaseModel):
    """Schema for learning progress analytics response."""
    
    model_versions: List[ModelVersionInfo] = Field(..., description="Recent model versions and performance")
    recent_acceptance_rate: float = Field(..., description="Recent acceptance rate percentage")
    total_training_data: int = Field(..., description="Total validated training data count")
    recent_feedback_count: int = Field(..., description="Recent feedback count")
    learning_indicators: Dict[str, str] = Field(..., description="Learning quality indicators")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "model_versions": [
                    {
                        "version": "v1.2.3",
                        "accuracy": 0.85,
                        "acceptance_rate": 72.5,
                        "created_at": "2024-01-15T10:30:00Z",
                        "is_active": True
                    }
                ],
                "recent_acceptance_rate": 74.2,
                "total_training_data": 2500,
                "recent_feedback_count": 450,
                "learning_indicators": {
                    "data_quality": "good",
                    "feedback_volume": "high",
                    "model_performance": "improving"
                }
            }
        }
    }


class AnalyticsDashboardResponse(BaseModel):
    """Schema for comprehensive analytics dashboard response."""
    
    acceptance_rates: AcceptanceRatesResponse = Field(..., description="Acceptance rates analytics")
    rejection_patterns: RejectionPatternsResponse = Field(..., description="Rejection patterns analytics")
    usage_statistics: UsageStatisticsResponse = Field(..., description="Usage statistics")
    learning_progress: LearningProgressResponse = Field(..., description="Learning progress indicators")
    generated_at: str = Field(..., description="Timestamp when analytics were generated")
    timeframe: str = Field(..., description="Time period analyzed")
    user_id: Optional[int] = Field(None, description="User ID if filtered by user")


class AnalyticsExportRequest(BaseModel):
    """Schema for analytics data export requests."""
    
    export_format: ExportFormatEnum = Field(ExportFormatEnum.JSON, description="Export format")
    start_date: Optional[datetime] = Field(None, description="Start date for export range")
    end_date: Optional[datetime] = Field(None, description="End date for export range")
    user_id: Optional[int] = Field(None, description="Optional filter by user")
    include_raw_data: bool = Field(False, description="Include raw feedback data")
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if v and info.data.get('start_date') and v < info.data['start_date']:
            raise ValueError("End date must be after start date")
        return v
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("User ID must be positive")
        return v


class AnalyticsExportResponse(BaseModel):
    """Schema for analytics export response."""
    
    data: List[Dict[str, Any]] = Field(..., description="Exported analytics data")
    format: str = Field(..., description="Export format used")
    total_records: int = Field(..., description="Total number of records exported")
    exported_at: str = Field(..., description="Export timestamp")
    filters: Dict[str, Any] = Field(..., description="Filters applied during export")


class RealTimeAnalyticsUpdate(BaseModel):
    """Schema for real-time analytics updates via WebSocket."""
    
    update_type: str = Field(..., description="Type of update (acceptance_rate, new_feedback, etc.)")
    data: Dict[str, Any] = Field(..., description="Updated analytics data")
    timestamp: str = Field(..., description="Update timestamp")
    user_id: Optional[int] = Field(None, description="User ID if user-specific update")
    
    @field_validator('update_type')
    @classmethod
    def validate_update_type(cls, v):
        allowed_types = {
            "acceptance_rate", "new_feedback", "rejection_pattern", 
            "usage_stats", "learning_progress", "dashboard_refresh"
        }
        if v not in allowed_types:
            raise ValueError(f"Invalid update type: {v}. Must be one of {allowed_types}")
        return v


class AnalyticsMetrics(BaseModel):
    """Schema for performance metrics of analytics queries."""
    
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")
    cache_hit: bool = Field(..., description="Whether data was served from cache")
    data_freshness_minutes: Optional[float] = Field(None, description="Age of cached data in minutes")
    total_records_processed: int = Field(..., description="Total records processed for analytics")


class AnalyticsHealthCheck(BaseModel):
    """Schema for analytics service health check."""
    
    status: str = Field(..., description="Service status (healthy, degraded, unhealthy)")
    cache_status: str = Field(..., description="Cache service status")
    database_status: str = Field(..., description="Database connection status")
    last_update: str = Field(..., description="Last successful analytics update")
    metrics: AnalyticsMetrics = Field(..., description="Performance metrics")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        allowed_statuses = {"healthy", "degraded", "unhealthy"}
        if v not in allowed_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of {allowed_statuses}")
        return v


class AnalyticsAlert(BaseModel):
    """Schema for analytics-based alerts and notifications."""
    
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(..., description="Alert severity level")
    message: str = Field(..., description="Alert message")
    data: Dict[str, Any] = Field(..., description="Alert-specific data")
    triggered_at: str = Field(..., description="Alert trigger timestamp")
    
    @field_validator('alert_type')
    @classmethod
    def validate_alert_type(cls, v):
        allowed_types = {
            "low_acceptance_rate", "high_rejection_rate", "unusual_pattern",
            "data_quality_issue", "performance_degradation"
        }
        if v not in allowed_types:
            raise ValueError(f"Invalid alert type: {v}. Must be one of {allowed_types}")
        return v
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        allowed_severities = {"low", "medium", "high", "critical"}
        if v not in allowed_severities:
            raise ValueError(f"Invalid severity: {v}. Must be one of {allowed_severities}")
        return v