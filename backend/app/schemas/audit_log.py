"""
Pydantic schemas for audit logging.

These schemas handle validation and serialization for audit log entries
and queries.

Requirements covered: 14.4
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AuditActionEnum(str, Enum):
    """Common audit action types."""
    # User management
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    UPDATE_USER_ROLE = "update_user_role"
    UPDATE_USER_STATUS = "update_user_status"
    ASSIGN_USER_TO_TEAM = "assign_user_to_team"
    REMOVE_USER_FROM_TEAM = "remove_user_from_team"
    
    # Team management
    CREATE_TEAM = "create_team"
    UPDATE_TEAM = "update_team"
    DELETE_TEAM = "delete_team"
    ADD_TEAM_MEMBER = "add_team_member"
    REMOVE_TEAM_MEMBER = "remove_team_member"
    
    # Analysis operations
    CREATE_ANALYSIS = "create_analysis"
    DELETE_ANALYSIS = "delete_analysis"
    VIEW_ANALYSIS = "view_analysis"
    
    # Admin operations
    VIEW_PLATFORM_ANALYTICS = "view_platform_analytics"
    VIEW_USER_DATA = "view_user_data"
    EXPORT_DATA = "export_data"
    
    # Security events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    
    # System events
    SYSTEM_ERROR = "system_error"
    CONFIGURATION_CHANGE = "configuration_change"


class AuditStatusEnum(str, Enum):
    """Audit log status enumeration."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ResourceTypeEnum(str, Enum):
    """Resource type enumeration."""
    USER = "user"
    TEAM = "team"
    ANALYSIS = "analysis"
    FEEDBACK = "feedback"
    FILE = "file"
    BATCH = "batch"
    SYSTEM = "system"


# Base Schemas

class AuditLogBase(BaseModel):
    """Base schema for audit log."""
    action: str = Field(..., max_length=100)
    resource_type: Optional[str] = Field(None, max_length=50)
    resource_id: Optional[str] = Field(None, max_length=100)
    details: Optional[Dict[str, Any]] = None
    changes: Optional[Dict[str, Any]] = None


class AuditLogCreate(AuditLogBase):
    """Schema for creating an audit log entry."""
    user_id: int
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None
    request_method: Optional[str] = Field(None, max_length=10)
    request_path: Optional[str] = Field(None, max_length=512)
    status: str = Field(default="success", max_length=20)
    error_message: Optional[str] = None
    duration_ms: Optional[int] = Field(None, ge=0)


class AuditLogResponse(AuditLogBase):
    """Schema for audit log response."""
    id: int
    event_id: str
    user_id: int
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    changes: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    timestamp: datetime
    duration_ms: Optional[int] = None
    
    class Config:
        from_attributes = True


class AuditLogDetailResponse(AuditLogResponse):
    """Detailed schema for audit log with user information."""
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Query Schemas

class AuditLogQuery(BaseModel):
    """Schema for querying audit logs."""
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    ip_address: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    sort_by: str = Field(default="timestamp")
    sort_order: str = Field(default="desc")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list response."""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Statistics Schemas

class AuditLogStatistics(BaseModel):
    """Schema for audit log statistics."""
    total_logs: int
    logs_by_action: Dict[str, int]
    logs_by_user: Dict[int, int]
    logs_by_status: Dict[str, int]
    logs_by_resource_type: Dict[str, int]
    recent_activity: List[AuditLogResponse]
    failed_actions_count: int
    success_rate: float


class UserActivitySummary(BaseModel):
    """Schema for user activity summary."""
    user_id: int
    user_email: str
    total_actions: int
    actions_by_type: Dict[str, int]
    last_activity: Optional[datetime] = None
    failed_actions: int
    success_rate: float


class TeamActivitySummary(BaseModel):
    """Schema for team activity summary."""
    team_id: str
    team_name: str
    total_actions: int
    actions_by_type: Dict[str, int]
    member_activity: List[UserActivitySummary]
    last_activity: Optional[datetime] = None


# Helper Schemas

class AuditLogExportRequest(BaseModel):
    """Schema for audit log export request."""
    query: AuditLogQuery
    format: str = Field(default="json")  # json, csv, pdf
    include_details: bool = True
    
    @validator('format')
    def validate_format(cls, v):
        if v not in ['json', 'csv', 'pdf']:
            raise ValueError('format must be "json", "csv", or "pdf"')
        return v


class AuditLogExportResponse(BaseModel):
    """Schema for audit log export response."""
    export_id: str
    status: str
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    total_records: int
