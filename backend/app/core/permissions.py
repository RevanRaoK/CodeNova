"""
Enhanced RBAC (Role-Based Access Control) system with granular permissions.

This module provides a comprehensive permission system for the CodeNova platform,
including role definitions, permission checks, and decorators for endpoint protection.

Requirements covered: 12.1, 12.2, 12.3, 14.1, 14.5
"""

from enum import Enum
from typing import List, Callable, Optional
from functools import wraps

from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session

from app.models.users import User, UserRole
from app.api.deps import get_current_user, get_db
from app.core.monitoring import get_service_logger, ServiceType

logger = get_service_logger(ServiceType.API, "permissions")


class Permission(str, Enum):
    """Granular permissions for platform operations."""
    
    # Code Analysis Permissions
    ANALYZE_CODE = "analyze_code"
    VIEW_OWN_ANALYSES = "view_own_analyses"
    DELETE_OWN_ANALYSES = "delete_own_analyses"
    
    # File Upload Permissions
    UPLOAD_FILES = "upload_files"
    VIEW_OWN_FILES = "view_own_files"
    DELETE_OWN_FILES = "delete_own_files"
    
    # Feedback Permissions
    PROVIDE_FEEDBACK = "provide_feedback"
    VIEW_OWN_FEEDBACK = "view_own_feedback"
    
    # Team Permissions
    VIEW_TEAM_ANALYSES = "view_team_analyses"
    VIEW_TEAM_STATS = "view_team_stats"
    VIEW_TEAM_MEMBERS = "view_team_members"
    
    # Team Lead Permissions
    MANAGE_TEAM_MEMBERS = "manage_team_members"
    VIEW_TEAM_FEEDBACK = "view_team_feedback"
    
    # Admin User Management Permissions
    VIEW_ALL_USERS = "view_all_users"
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    UPDATE_USER_ROLE = "update_user_role"
    UPDATE_USER_STATUS = "update_user_status"
    ASSIGN_USER_TEAM = "assign_user_team"
    
    # Admin Team Management Permissions
    VIEW_ALL_TEAMS = "view_all_teams"
    CREATE_TEAM = "create_team"
    UPDATE_TEAM = "update_team"
    DELETE_TEAM = "delete_team"
    MANAGE_TEAM_MEMBERS_ADMIN = "manage_team_members_admin"
    
    # Admin Analytics Permissions
    VIEW_PLATFORM_STATS = "view_platform_stats"
    VIEW_ALL_ANALYSES = "view_all_analyses"
    VIEW_ALL_FEEDBACK = "view_all_feedback"
    VIEW_GLOBAL_TRENDS = "view_global_trends"
    VIEW_TEAM_COMPARISON = "view_team_comparison"
    
    # Audit Permissions
    VIEW_AUDIT_LOGS = "view_audit_logs"
    EXPORT_AUDIT_LOGS = "export_audit_logs"
    
    # System Permissions
    MANAGE_SYSTEM_SETTINGS = "manage_system_settings"
    VIEW_SYSTEM_HEALTH = "view_system_health"


# Role-Permission Mapping
ROLE_PERMISSIONS: dict[UserRole, List[Permission]] = {
    UserRole.USER: [
        Permission.ANALYZE_CODE,
        Permission.VIEW_OWN_ANALYSES,
        Permission.DELETE_OWN_ANALYSES,
        Permission.UPLOAD_FILES,
        Permission.VIEW_OWN_FILES,
        Permission.DELETE_OWN_FILES,
        Permission.PROVIDE_FEEDBACK,
        Permission.VIEW_OWN_FEEDBACK,
    ],
    
    UserRole.DEVELOPER: [
        # All USER permissions plus:
        Permission.ANALYZE_CODE,
        Permission.VIEW_OWN_ANALYSES,
        Permission.DELETE_OWN_ANALYSES,
        Permission.UPLOAD_FILES,
        Permission.VIEW_OWN_FILES,
        Permission.DELETE_OWN_FILES,
        Permission.PROVIDE_FEEDBACK,
        Permission.VIEW_OWN_FEEDBACK,
        Permission.VIEW_TEAM_ANALYSES,
        Permission.VIEW_TEAM_STATS,
        Permission.VIEW_TEAM_MEMBERS,
    ],
    
    UserRole.TEAM_LEAD: [
        # All DEVELOPER permissions plus:
        Permission.ANALYZE_CODE,
        Permission.VIEW_OWN_ANALYSES,
        Permission.DELETE_OWN_ANALYSES,
        Permission.UPLOAD_FILES,
        Permission.VIEW_OWN_FILES,
        Permission.DELETE_OWN_FILES,
        Permission.PROVIDE_FEEDBACK,
        Permission.VIEW_OWN_FEEDBACK,
        Permission.VIEW_TEAM_ANALYSES,
        Permission.VIEW_TEAM_STATS,
        Permission.VIEW_TEAM_MEMBERS,
        Permission.MANAGE_TEAM_MEMBERS,
        Permission.VIEW_TEAM_FEEDBACK,
    ],
    
    UserRole.REVIEWER: [
        # Specialized role for code reviewers
        Permission.VIEW_OWN_ANALYSES,
        Permission.VIEW_TEAM_ANALYSES,
        Permission.VIEW_TEAM_STATS,
        Permission.PROVIDE_FEEDBACK,
        Permission.VIEW_OWN_FEEDBACK,
        Permission.VIEW_TEAM_FEEDBACK,
    ],
    
    UserRole.ADMIN: [
        # All permissions
        *list(Permission)
    ],
    
    UserRole.GUEST: [
        # Minimal permissions for guest users
        Permission.ANALYZE_CODE,
        Permission.VIEW_OWN_ANALYSES,
    ],
}


class PermissionChecker:
    """Service for checking user permissions."""
    
    @staticmethod
    def has_permission(user: User, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        if not user or not user.is_active:
            return False
        
        user_permissions = ROLE_PERMISSIONS.get(user.role, [])
        return permission in user_permissions
    
    @staticmethod
    def has_any_permission(user: User, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(PermissionChecker.has_permission(user, perm) for perm in permissions)
    
    @staticmethod
    def has_all_permissions(user: User, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions."""
        return all(PermissionChecker.has_permission(user, perm) for perm in permissions)
    
    @staticmethod
    def get_user_permissions(user: User) -> List[Permission]:
        """Get all permissions for a user."""
        if not user or not user.is_active:
            return []
        
        return ROLE_PERMISSIONS.get(user.role, [])
    
    @staticmethod
    def can_access_resource(user: User, resource_owner_id: int, permission: Permission) -> bool:
        """
        Check if user can access a resource.
        
        Users can access their own resources or team resources if they have team permissions.
        Admins can access all resources.
        """
        # Check if user has the permission
        if not PermissionChecker.has_permission(user, permission):
            return False
        
        # Admins can access everything
        if user.role == UserRole.ADMIN:
            return True
        
        # Users can access their own resources
        if user.id == resource_owner_id:
            return True
        
        # Team leads and developers can access team resources
        if permission in [Permission.VIEW_TEAM_ANALYSES, Permission.VIEW_TEAM_STATS]:
            # Would need to check if resource owner is in same team
            # This requires additional database query
            return False
        
        return False


def require_permission(permission: Permission):
    """
    Decorator to require a specific permission for an endpoint.
    
    Usage:
        @router.get("/admin/users")
        @require_permission(Permission.VIEW_ALL_USERS)
        async def get_all_users(current_user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if not PermissionChecker.has_permission(current_user, permission):
                logger.warning(
                    "Permission denied",
                    user_id=current_user.id,
                    user_role=current_user.role.value,
                    required_permission=permission.value,
                    endpoint=func.__name__
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {permission.value} required"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator


def require_any_permission(*permissions: Permission):
    """
    Decorator to require any of the specified permissions.
    
    Usage:
        @router.get("/analyses")
        @require_any_permission(Permission.VIEW_OWN_ANALYSES, Permission.VIEW_ALL_ANALYSES)
        async def get_analyses(current_user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if not PermissionChecker.has_any_permission(current_user, list(permissions)):
                logger.warning(
                    "Permission denied",
                    user_id=current_user.id,
                    user_role=current_user.role.value,
                    required_permissions=[p.value for p in permissions],
                    endpoint=func.__name__
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: one of {[p.value for p in permissions]} required"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator


def require_all_permissions(*permissions: Permission):
    """
    Decorator to require all of the specified permissions.
    
    Usage:
        @router.post("/admin/teams/{team_id}/members")
        @require_all_permissions(Permission.VIEW_ALL_TEAMS, Permission.MANAGE_TEAM_MEMBERS_ADMIN)
        async def add_team_member(current_user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if not PermissionChecker.has_all_permissions(current_user, list(permissions)):
                logger.warning(
                    "Permission denied",
                    user_id=current_user.id,
                    user_role=current_user.role.value,
                    required_permissions=[p.value for p in permissions],
                    endpoint=func.__name__
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: all of {[p.value for p in permissions]} required"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator


def require_role(role: UserRole):
    """
    Decorator to require a specific role.
    
    Usage:
        @router.get("/admin/dashboard")
        @require_role(UserRole.ADMIN)
        async def admin_dashboard(current_user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if current_user.role != role:
                logger.warning(
                    "Role check failed",
                    user_id=current_user.id,
                    user_role=current_user.role.value,
                    required_role=role.value,
                    endpoint=func.__name__
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Role {role.value} required"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator


# Dependency functions for FastAPI
async def require_permission_dependency(permission: Permission):
    """Dependency function to check permission."""
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not PermissionChecker.has_permission(current_user, permission):
            logger.warning(
                "Permission denied",
                user_id=current_user.id,
                user_role=current_user.role.value,
                required_permission=permission.value
            )
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission.value} required"
            )
        return current_user
    
    return permission_checker


# Convenience dependency functions
async def require_admin_permission(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require admin role."""
    if current_user.role != UserRole.ADMIN:
        logger.warning(
            "Admin permission denied",
            user_id=current_user.id,
            user_role=current_user.role.value
        )
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return current_user


async def require_team_lead_or_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require team lead or admin role."""
    if current_user.role not in [UserRole.TEAM_LEAD, UserRole.ADMIN]:
        logger.warning(
            "Team lead or admin permission denied",
            user_id=current_user.id,
            user_role=current_user.role.value
        )
        raise HTTPException(
            status_code=403,
            detail="Team lead or admin privileges required"
        )
    return current_user
