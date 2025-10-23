# app/api/v1/endpoints/audit_logs.py

"""
Audit log endpoints for tracking admin actions.
Requirements: 14.4
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.rbac import require_admin, PermissionChecker, Permissions
from app.models.users import User
from app.services.audit_logger import AuditLogger
from pydantic import BaseModel

router = APIRouter()


class AuditLogEntry(BaseModel):
    id: int
    timestamp: datetime
    user_id: int
    username: str
    action: str
    resource_type: str
    resource_id: str
    details: dict
    ip_address: Optional[str]
    user_agent: Optional[str]


class AuditLogsResponse(BaseModel):
    logs: List[AuditLogEntry]
    total: int
    page: int
    page_size: int


@router.get("/audit-logs", response_model=AuditLogsResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get audit logs with filtering.
    
    Requirements: 14.4 - Audit logging with filtering
    """
    audit_logger = AuditLogger(db)
    
    result = await audit_logger.get_audit_logs(
        page=page,
        page_size=page_size,
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to
    )
    
    logs = []
    for log in result["logs"]:
        logs.append(AuditLogEntry(
            id=log["id"],
            timestamp=log["timestamp"],
            user_id=log["user_id"],
            username=log["username"],
            action=log["action"],
            resource_type=log["resource_type"],
            resource_id=log["resource_id"],
            details=log["details"],
            ip_address=log.get("ip_address"),
            user_agent=log.get("user_agent")
        ))
    
    return AuditLogsResponse(
        logs=logs,
        total=result["total"],
        page=page,
        page_size=page_size
    )


@router.get("/audit-logs/actions", response_model=List[str])
async def get_audit_log_actions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get list of all available audit log action types.
    
    Requirements: 14.4 - Audit log filtering support
    """
    audit_logger = AuditLogger(db)
    actions = await audit_logger.get_available_actions()
    return actions


@router.get("/audit-logs/resource-types", response_model=List[str])
async def get_audit_log_resource_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get list of all available audit log resource types.
    
    Requirements: 14.4 - Audit log filtering support
    """
    audit_logger = AuditLogger(db)
    resource_types = await audit_logger.get_available_resource_types()
    return resource_types
