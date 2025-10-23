# app/api/v1/endpoints/admin_users.py

"""
Admin user management endpoints.
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.rbac import require_admin
from app.models.users import User, UserRole
from app.services.admin_service import AdminService
from app.services.audit_logger import AuditLogger
from app.schemas.user import UserResponse, UserRoleUpdate, UserStatusUpdate
from pydantic import BaseModel

router = APIRouter()


class UserDetailResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    team_id: Optional[str]
    team_name: Optional[str]
    created_at: str
    last_login: Optional[str]
    # Activity statistics
    total_analyses: int
    total_feedback: int
    avg_issues_per_analysis: float


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    team_id: Optional[str] = Query(None, description="Filter by team ID"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get all users with filtering and search.
    
    Requirements: 7.1, 7.3 - List all users with search and filter
    """
    admin_service = AdminService(db)
    
    users = await admin_service.get_all_users(
        team_id=team_id,
        role=role,
        is_active=is_active,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return users


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get detailed information about a specific user.
    
    Requirements: 7.4 - View detailed user information and activity
    """
    admin_service = AdminService(db)
    
    user = await admin_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user statistics
    from app.models.analysis import DirectAnalysis
    from app.models.feedback import Feedback
    
    total_analyses = db.query(DirectAnalysis).filter(
        DirectAnalysis.user_id == user_id
    ).count()
    
    total_feedback = db.query(Feedback).filter(
        Feedback.user_id == user_id
    ).count()
    
    # Calculate average issues per analysis
    analyses_with_issues = db.query(DirectAnalysis).filter(
        DirectAnalysis.user_id == user_id,
        DirectAnalysis.issues_count.isnot(None)
    ).all()
    
    avg_issues = 0
    if analyses_with_issues:
        total_issues = sum(a.issues_count for a in analyses_with_issues if a.issues_count)
        avg_issues = total_issues / len(analyses_with_issues)
    
    # Get team name if user is in a team
    team_name = None
    if user.team_id:
        from app.models.team import Team
        team = db.query(Team).filter(Team.id == user.team_id).first()
        if team:
            team_name = team.name
    
    return UserDetailResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        team_id=user.team_id,
        team_name=team_name,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None,
        total_analyses=total_analyses,
        total_feedback=total_feedback,
        avg_issues_per_analysis=round(avg_issues, 2)
    )


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update a user's role.
    
    Requirements: 7.2 - Update user roles with audit logging
    """
    admin_service = AdminService(db)
    audit_logger = AuditLogger(db)
    
    # Prevent self-role modification
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify your own role"
        )
    
    # Get old role for audit
    old_user = await admin_service.get_user_by_id(user_id)
    if not old_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = await admin_service.update_user_role(
        user_id=user_id,
        role=role_update.role,
        admin_user_id=current_user.id
    )
    
    # Log the action with before/after values
    changes = AuditLogger.create_changes_dict(
        old_value=old_user.role.value,
        new_value=role_update.role.value,
        field_name="role"
    )
    
    audit_logger.log_action(
        user_id=current_user.id,
        action="update_user_role",
        resource_type="user",
        resource_id=str(user_id),
        details={
            "username": user.full_name or user.email,
            "old_role": old_user.role.value,
            "new_role": role_update.role.value
        },
        changes=changes,
        request=request
    )
    
    return user


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update a user's active status.
    
    Requirements: 7.2 - Update user status with audit logging
    """
    admin_service = AdminService(db)
    audit_logger = AuditLogger(db)
    
    # Prevent self-status modification
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify your own status"
        )
    
    # Get old status for audit
    old_user = await admin_service.get_user_by_id(user_id)
    if not old_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = await admin_service.update_user_status(
        user_id=user_id,
        is_active=status_update.is_active,
        admin_user_id=current_user.id
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log the action with before/after values
    changes = AuditLogger.create_changes_dict(
        old_value=old_user.is_active,
        new_value=status_update.is_active,
        field_name="is_active"
    )
    
    audit_logger.log_action(
        user_id=current_user.id,
        action="update_user_status",
        resource_type="user",
        resource_id=str(user_id),
        details={
            "username": user.full_name or user.email,
            "old_status": "active" if old_user.is_active else "inactive",
            "new_status": "active" if status_update.is_active else "inactive"
        },
        changes=changes,
        request=request
    )
    
    return {
        "message": f"User status updated to {'active' if status_update.is_active else 'inactive'}",
        "user_id": user_id,
        "is_active": status_update.is_active
    }


@router.put("/users/{user_id}/team", response_model=UserResponse)
async def assign_user_team(
    user_id: int,
    team_id: Optional[str],
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Assign a user to a team or remove from team.
    
    Requirements: 7.5 - Team assignment with audit logging
    """
    admin_service = AdminService(db)
    audit_logger = AuditLogger(db)
    
    # Get old team for audit
    old_user = await admin_service.get_user_by_id(user_id)
    if not old_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = await admin_service.assign_user_to_team(
        user_id=user_id,
        team_id=team_id,
        admin_user_id=current_user.id
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User or team not found")
    
    # Log the action with before/after values
    action = "assign_user_to_team" if team_id else "remove_user_from_team"
    changes = AuditLogger.create_changes_dict(
        old_value=old_user.team_id,
        new_value=team_id,
        field_name="team_id"
    )
    
    audit_logger.log_action(
        user_id=current_user.id,
        action=action,
        resource_type="user",
        resource_id=str(user_id),
        details={
            "username": user.full_name or user.email,
            "old_team_id": old_user.team_id,
            "new_team_id": team_id
        },
        changes=changes,
        request=request
    )
    
    return user
