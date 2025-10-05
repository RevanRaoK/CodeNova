from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class TeamBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    settings: Optional[Dict[str, Any]] = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    settings: Optional[Dict[str, Any]] = None


class TeamResponse(TeamBase):
    id: str
    admin_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TeamAnalytics(BaseModel):
    team_id: str
    team_name: str
    member_count: int
    total_analyses: int
    total_feedback: int
    acceptance_rate: float
    recent_activity: List[Dict[str, Any]]


class TeamMemberResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class PlatformAnalytics(BaseModel):
    total_users: int
    active_users: int
    total_teams: int
    total_analyses: int
    total_feedback: int
    role_distribution: Dict[str, int]
    recent_activity: Dict[str, int]


class AuditLogEntry(BaseModel):
    timestamp: str
    action: str
    target_user_id: Optional[int]
    details: Dict[str, Any]