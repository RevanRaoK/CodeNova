from functools import wraps
from typing import List, Callable, Any
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.models.users import User, UserRole
from app.api.deps import get_current_user, get_db


class RBACError(HTTPException):
    """Custom exception for RBAC authorization errors."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class RoleChecker:
    """
    Role-based access control checker.
    
    Requirements covered: 3.3 - Role-based access control with immediate permission updates
    """
    
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise RBACError(
                detail=f"Access denied. Required roles: {[role.value for role in self.allowed_roles]}"
            )
        
        if not current_user.is_active:
            raise RBACError(detail="Account is inactive")
        
        return current_user


class PermissionChecker:
    """
    Advanced permission checker for specific operations.
    """
    
    def __init__(self, permission: str):
        self.permission = permission
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if not self._has_permission(current_user, self.permission):
            raise RBACError(
                detail=f"Access denied. Missing permission: {self.permission}"
            )
        
        return current_user
    
    def _has_permission(self, user: User, permission: str) -> bool:
        """Check if user has specific permission based on role."""
        role_permissions = {
            UserRole.ADMIN: [
                "user.read", "user.write", "user.delete",
                "team.read", "team.write", "team.delete",
                "analytics.read", "analytics.write",
                "audit.read", "system.admin"
            ],
            UserRole.TEAM_LEAD: [
                "user.read", "team.read", "team.write",
                "analytics.read"
            ],
            UserRole.DEVELOPER: [
                "user.read", "analytics.read"
            ],
            UserRole.REVIEWER: [
                "user.read", "analytics.read"
            ],
            UserRole.USER: [
                "user.read"
            ],
            UserRole.GUEST: []
        }
        
        user_permissions = role_permissions.get(user.role, [])
        return permission in user_permissions


class TeamAccessChecker:
    """
    Check if user has access to team-specific resources.
    """
    
    def __init__(self, require_admin: bool = False):
        self.require_admin = require_admin
    
    def __call__(
        self, 
        team_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Admins have access to all teams
        if current_user.role == UserRole.ADMIN:
            return current_user
        
        # Check if user is team admin (if required)
        if self.require_admin:
            from app.models.team import Team
            team = db.query(Team).filter(Team.id == team_id).first()
            if not team or team.admin_id != current_user.id:
                raise RBACError(detail="Team admin access required")
        
        # Check if user belongs to the team
        elif current_user.team_id != team_id:
            raise RBACError(detail="Access denied. User not in team")
        
        return current_user


# Convenience functions for common role checks

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role."""
    return RoleChecker([UserRole.ADMIN])(current_user)


def require_admin_or_team_lead(current_user: User = Depends(get_current_user)) -> User:
    """Require admin or team lead role."""
    return RoleChecker([UserRole.ADMIN, UserRole.TEAM_LEAD])(current_user)


def require_authenticated(current_user: User = Depends(get_current_user)) -> User:
    """Require any authenticated user."""
    return RoleChecker([
        UserRole.ADMIN, UserRole.TEAM_LEAD, UserRole.DEVELOPER, 
        UserRole.REVIEWER, UserRole.USER
    ])(current_user)


def require_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Require active user (excludes guests)."""
    return RoleChecker([
        UserRole.ADMIN, UserRole.TEAM_LEAD, UserRole.DEVELOPER, 
        UserRole.REVIEWER, UserRole.USER
    ])(current_user)


# Decorator for function-level role checking
def requires_role(*roles: UserRole):
    """
    Decorator to check user roles at the function level.
    
    Usage:
    @requires_role(UserRole.ADMIN, UserRole.TEAM_LEAD)
    def some_function(user: User):
        pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user from kwargs or args
            user = None
            if 'current_user' in kwargs:
                user = kwargs['current_user']
            elif 'user' in kwargs:
                user = kwargs['user']
            elif args and isinstance(args[0], User):
                user = args[0]
            
            if not user or user.role not in roles:
                raise RBACError(
                    detail=f"Access denied. Required roles: {[role.value for role in roles]}"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Permission constants
class Permissions:
    """Constants for permission strings."""
    
    # User permissions
    USER_READ = "user.read"
    USER_WRITE = "user.write"
    USER_DELETE = "user.delete"
    
    # Team permissions
    TEAM_READ = "team.read"
    TEAM_WRITE = "team.write"
    TEAM_DELETE = "team.delete"
    
    # Analytics permissions
    ANALYTICS_READ = "analytics.read"
    ANALYTICS_WRITE = "analytics.write"
    
    # Audit permissions
    AUDIT_READ = "audit.read"
    
    # System permissions
    SYSTEM_ADMIN = "system.admin"