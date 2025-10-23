# app/api/v1/endpoints/admin_teams.py

"""
Admin team management endpoints.
Requirements: 7.1, 7.2, 7.3, 8.1, 8.2, 8.3
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.rbac import require_admin
from app.models.users import User
from app.services.admin_service import AdminService
from app.services.audit_logger import AuditLogger
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse, TeamMemberResponse
from pydantic import BaseModel

router = APIRouter()


@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new team.
    
    Requirements: 8.1, 8.2 - Team creation with audit logging
    """
    admin_service = AdminService(db)
    audit_logger = AuditLogger(db)
    
    try:
        team = await admin_service.create_team(team_data, current_user.id)
        
        # Log the action
        audit_logger.log_action(
            user_id=current_user.id,
            action="create_team",
            resource_type="team",
            resource_id=team.id,
            details={
                "team_name": team.name,
                "description": team.description
            },
            request=request
        )
        
        return team
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/teams", response_model=List[TeamResponse])
async def get_all_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get all teams.
    
    Requirements: 7.1 - View all teams
    """
    admin_service = AdminService(db)
    teams = await admin_service.get_all_teams(skip=skip, limit=limit)
    return teams


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get a specific team by ID.
    
    Requirements: 7.1 - View team details
    """
    admin_service = AdminService(db)
    team = await admin_service.get_team_by_id(team_id)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return team


@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    team_data: TeamUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update team information.
    
    Requirements: 8.2 - Team editing with audit logging
    """
    admin_service = AdminService(db)
    audit_logger = AuditLogger(db)
    
    # Get old team data for audit
    old_team = await admin_service.get_team_by_id(team_id)
    if not old_team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = await admin_service.update_team(
        team_id=team_id,
        team_data=team_data,
        admin_user_id=current_user.id
    )
    
    # Log the action
    audit_logger.log_action(
        user_id=current_user.id,
        action="update_team",
        resource_type="team",
        resource_id=team_id,
        details={
            "old_name": old_team.name,
            "new_name": team.name,
            "old_description": old_team.description,
            "new_description": team.description
        },
        request=request
    )
    
    return team


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete a team and unassign all users.
    
    Requirements: 8.3 - Team deletion with audit logging
    """
    admin_service = AdminService(db)
    audit_logger = AuditLogger(db)
    
    # Get team data before deletion for audit
    team = await admin_service.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    success = await admin_service.delete_team(
        team_id=team_id,
        admin_user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Log the action
    audit_logger.log_action(
        user_id=current_user.id,
        action="delete_team",
        resource_type="team",
        resource_id=team_id,
        details={
            "team_name": team.name,
            "member_count": len(team.members) if hasattr(team, 'members') else 0
        },
        request=request
    )
    
    return None


@router.get("/teams/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_team_members(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get all members of a specific team.
    
    Requirements: 8.4 - View team members
    """
    admin_service = AdminService(db)
    
    # Verify team exists
    team = await admin_service.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    members = await admin_service.get_all_users(team_id=team_id)
    return members


@router.post("/teams/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
async def add_team_member(
    team_id: str,
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Add a user to a team.
    
    Requirements: 8.5 - Team member management with audit logging
    """
    admin_service = AdminService(db)
    audit_logger = AuditLogger(db)
    
    user = await admin_service.assign_user_to_team(
        user_id=user_id,
        team_id=team_id,
        admin_user_id=current_user.id
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User or team not found")
    
    # Log the action
    audit_logger.log_action(
        user_id=current_user.id,
        action="add_team_member",
        resource_type="team",
        resource_id=team_id,
        details={
            "user_id": user_id,
            "username": user.username
        },
        request=request
    )
    
    return user


@router.delete("/teams/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: str,
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Remove a user from a team.
    
    Requirements: 8.6 - Team member management with audit logging
    """
    admin_service = AdminService(db)
    audit_logger = AuditLogger(db)
    
    # Get user data before removal for audit
    user = await admin_service.get_user_by_id(user_id)
    if not user or user.team_id != team_id:
        raise HTTPException(status_code=404, detail="User not found in team")
    
    # Remove from team by setting team_id to None
    updated_user = await admin_service.assign_user_to_team(
        user_id=user_id,
        team_id=None,
        admin_user_id=current_user.id
    )
    
    # Log the action
    audit_logger.log_action(
        user_id=current_user.id,
        action="remove_team_member",
        resource_type="team",
        resource_id=team_id,
        details={
            "user_id": user_id,
            "username": user.username
        },
        request=request
    )
    
    return None
