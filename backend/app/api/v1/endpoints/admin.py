from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.rbac import (
    require_admin, 
    require_admin_or_team_lead, 
    RoleChecker, 
    PermissionChecker,
    Permissions
)
from app.models.users import User, UserRole
from app.services.admin_service import AdminService
from app.schemas.user import UserResponse, UserRoleUpdate
from app.schemas.team import (
    TeamCreate, TeamUpdate, TeamResponse, TeamAnalytics, 
    DashboardMetrics, PlatformAnalytics, TeamMemberResponse, FeedbackStatistics
)
from app.schemas.audit_log import AuditLogResponse as AuditLogEntry

router = APIRouter()


# User Management Endpoints

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    team_id: Optional[str] = Query(None, description="Filter by team ID"),
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_team_lead)
):
    """
    Get all users with optional team filtering.
    
    Requirements: 3.2 - Admin views all team members and their roles
    """
    admin_service = AdminService(db)
    
    # Team leads can only see their own team members
    if current_user.role == UserRole.TEAM_LEAD and team_id != current_user.team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Team leads can only view their own team members"
        )
    
    users = await admin_service.get_all_users(team_id=team_id, skip=skip, limit=limit)
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_team_lead)
):
    """Get a specific user by ID."""
    admin_service = AdminService(db)
    user = await admin_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Team leads can only view users in their team
    if (current_user.role == UserRole.TEAM_LEAD and 
        user.team_id != current_user.team_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return user


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update a user's role (admin only).
    
    Requirements: 3.3 - Admin modifies user roles with immediate permission updates
    """
    admin_service = AdminService(db)
    
    # Prevent self-role modification
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own role"
        )
    
    user = await admin_service.update_user_role(
        user_id=user_id,
        role=role_update.role,
        admin_user_id=current_user.id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a user's active status (admin only)."""
    admin_service = AdminService(db)
    
    # Prevent self-status modification
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own status"
        )
    
    user = await admin_service.update_user_status(
        user_id=user_id,
        is_active=is_active,
        admin_user_id=current_user.id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": f"User status updated to {'active' if is_active else 'inactive'}"}


@router.put("/users/{user_id}/team/{team_id}", response_model=UserResponse)
async def assign_user_to_team(
    user_id: int,
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Assign a user to a team (admin only)."""
    admin_service = AdminService(db)
    
    user = await admin_service.assign_user_to_team(
        user_id=user_id,
        team_id=team_id,
        admin_user_id=current_user.id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or team not found"
        )
    
    return user


# Team Management Endpoints

@router.post("/teams", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new team.
    
    Requirements: 3.5 - Admin manages teams (creating, editing, deleting team structures)
    """
    admin_service = AdminService(db)
    team = await admin_service.create_team(team_data, current_user.id)
    return team


@router.get("/teams", response_model=List[TeamResponse])
async def get_all_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_team_lead)
):
    """Get all teams."""
    admin_service = AdminService(db)
    teams = await admin_service.get_all_teams(skip=skip, limit=limit)
    
    # Team leads can only see their own team
    if current_user.role == UserRole.TEAM_LEAD:
        teams = [team for team in teams if team.admin_id == current_user.id]
    
    return teams


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_team_lead)
):
    """Get a specific team by ID."""
    admin_service = AdminService(db)
    team = await admin_service.get_team_by_id(team_id)
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Team leads can only view their own team
    if (current_user.role == UserRole.TEAM_LEAD and 
        team.admin_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return team


@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    team_data: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update team information (admin only)."""
    admin_service = AdminService(db)
    
    team = await admin_service.update_team(
        team_id=team_id,
        team_data=team_data,
        admin_user_id=current_user.id
    )
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    return team


@router.delete("/teams/{team_id}")
async def delete_team(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a team and unassign all users (admin only)."""
    admin_service = AdminService(db)
    
    success = await admin_service.delete_team(
        team_id=team_id,
        admin_user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    return {"message": "Team deleted successfully"}


@router.get("/teams/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_team_members(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_team_lead)
):
    """Get all members of a specific team."""
    admin_service = AdminService(db)
    
    # Verify team exists and user has access
    team = await admin_service.get_team_by_id(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Team leads can only view their own team
    if (current_user.role == UserRole.TEAM_LEAD and 
        team.admin_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    members = await admin_service.get_all_users(team_id=team_id)
    return members


# Analytics Endpoints

@router.get("/analytics/dashboard-metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get dashboard metrics including reviews completed today.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 12.1, 12.2, 12.3, 12.4, 12.5
    """
    admin_service = AdminService(db)
    metrics = await admin_service.get_dashboard_metrics()
    return metrics

@router.get("/analytics/platform", response_model=PlatformAnalytics)
async def get_platform_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get platform-wide analytics.
    
    Requirements: 3.1 - Admin accesses admin dashboard with user management interface
    """
    admin_service = AdminService(db)
    analytics = await admin_service.get_platform_analytics()
    return analytics


@router.get("/analytics/teams", response_model=List[TeamAnalytics])
async def get_all_teams_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_team_lead)
):
    """Get analytics for all teams."""
    admin_service = AdminService(db)
    
    if current_user.role == UserRole.ADMIN:
        analytics = await admin_service.get_all_teams_analytics()
    else:
        # Team leads can only see their own team analytics
        team_analytics = await admin_service.get_team_analytics(current_user.team_id)
        analytics = [team_analytics] if team_analytics else []
    
    return analytics


@router.get("/analytics/teams/{team_id}", response_model=TeamAnalytics)
async def get_team_analytics(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_team_lead)
):
    """
    Get analytics for a specific team.
    
    Requirements: 3.4 - Admin views dashboard showing issues from all team members
    """
    admin_service = AdminService(db)
    
    # Verify team exists and user has access
    team = await admin_service.get_team_by_id(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Team leads can only view their own team
    if (current_user.role == UserRole.TEAM_LEAD and 
        team.admin_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    analytics = await admin_service.get_team_analytics(team_id)
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team analytics not found"
        )
    
    return analytics


@router.get("/analytics/feedback-stats", response_model=FeedbackStatistics)
async def get_feedback_statistics(
    team_id: Optional[str] = Query(None, description="Filter by team ID (null for all users)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get feedback statistics with optional team filtering.
    
    Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
    """
    admin_service = AdminService(db)
    
    # If team_id is provided, verify it exists
    if team_id:
        team = await admin_service.get_team_by_id(team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
    
    statistics = admin_service.get_feedback_statistics(team_id=team_id)
    return statistics


# Audit Logging Endpoints

@router.get("/audit-logs", response_model=List[AuditLogEntry])
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(Permissions.AUDIT_READ))
):
    """
    Get audit logs for admin actions.
    
    Requirements: 3.5 - Implement audit logging for admin actions
    """
    admin_service = AdminService(db)
    logs = await admin_service.get_audit_logs(current_user.id, limit)
    
    return [
        AuditLogEntry(
            timestamp=log["timestamp"],
            action=log["action"],
            target_user_id=log.get("target_user_id"),
            details=log.get("details", {})
        )
        for log in logs
    ]