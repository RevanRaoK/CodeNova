"""
Audit Logger Service for automatic logging of admin actions and sensitive operations.

This service provides a centralized way to log all administrative actions,
user management operations, and security-relevant events.

Requirements covered: 14.4, 14.5
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Request
from datetime import datetime
import logging
import time

from app.models.audit_log import AuditLog
from app.models.users import User

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Service for automatic audit logging of administrative actions.
    
    This service provides methods to log various types of actions with
    comprehensive context information for security and compliance.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_action(
        self,
        user_id: int,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> Optional[AuditLog]:
        """
        Log an administrative action with full context.
        
        Args:
            user_id: ID of the user performing the action
            action: Action being performed (e.g., 'create_team', 'update_user_role')
            resource_type: Type of resource affected (e.g., 'user', 'team')
            resource_id: ID of the affected resource
            details: Additional context about the action
            changes: Before/after values for updates
            request: FastAPI Request object for extracting metadata
            status: Action status (success, failed, partial)
            error_message: Error details if action failed
            duration_ms: Action duration in milliseconds
            
        Returns:
            Created AuditLog instance or None if logging failed
        """
        try:
            # Extract request metadata if available
            ip_address = None
            user_agent = None
            request_method = None
            request_path = None
            
            if request:
                ip_address = self._get_client_ip(request)
                user_agent = request.headers.get("User-Agent")
                request_method = request.method
                request_path = str(request.url.path)
            
            # Create audit log entry
            audit_log = AuditLog.create_log(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                changes=changes,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request_method,
                request_path=request_path,
                status=status,
                error_message=error_message,
                duration_ms=duration_ms
            )
            
            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)
            
            logger.info(
                f"Audit log created: action={action}, user_id={user_id}, "
                f"resource={resource_type}:{resource_id}, status={status}"
            )
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
            # Don't fail the main operation if audit logging fails
            return None
    
    def log_user_action(
        self,
        admin_user_id: int,
        target_user_id: int,
        action: str,
        changes: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> Optional[AuditLog]:
        """
        Log a user management action.
        
        Args:
            admin_user_id: ID of the admin performing the action
            target_user_id: ID of the user being modified
            action: Action type (e.g., 'update_role', 'deactivate')
            changes: Before/after values
            request: FastAPI Request object
            
        Returns:
            Created AuditLog instance or None
        """
        return self.log_action(
            user_id=admin_user_id,
            action=f"user_{action}",
            resource_type="user",
            resource_id=str(target_user_id),
            changes=changes,
            request=request
        )
    
    def log_team_action(
        self,
        admin_user_id: int,
        team_id: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> Optional[AuditLog]:
        """
        Log a team management action.
        
        Args:
            admin_user_id: ID of the admin performing the action
            team_id: ID of the team being modified
            action: Action type (e.g., 'create', 'update', 'delete')
            details: Additional context
            changes: Before/after values
            request: FastAPI Request object
            
        Returns:
            Created AuditLog instance or None
        """
        return self.log_action(
            user_id=admin_user_id,
            action=f"team_{action}",
            resource_type="team",
            resource_id=team_id,
            details=details,
            changes=changes,
            request=request
        )
    
    def log_analytics_access(
        self,
        user_id: int,
        analytics_type: str,
        filters: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> Optional[AuditLog]:
        """
        Log access to analytics data.
        
        Args:
            user_id: ID of the user accessing analytics
            analytics_type: Type of analytics accessed
            filters: Filters applied to the analytics query
            request: FastAPI Request object
            
        Returns:
            Created AuditLog instance or None
        """
        return self.log_action(
            user_id=user_id,
            action=f"analytics_access_{analytics_type}",
            resource_type="analytics",
            details={"filters": filters} if filters else None,
            request=request
        )
    
    def log_failed_action(
        self,
        user_id: int,
        action: str,
        error_message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None
    ) -> Optional[AuditLog]:
        """
        Log a failed action attempt.
        
        Args:
            user_id: ID of the user attempting the action
            action: Action that failed
            error_message: Error details
            resource_type: Type of resource
            resource_id: ID of the resource
            request: FastAPI Request object
            
        Returns:
            Created AuditLog instance or None
        """
        return self.log_action(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status="failed",
            error_message=error_message,
            request=request
        )
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """
        Extract client IP address from request, handling proxies.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Client IP address or None
        """
        # Check for forwarded IP (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP in the chain
            return forwarded.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return None
    
    @staticmethod
    def create_changes_dict(old_value: Any, new_value: Any, field_name: str) -> Dict[str, Any]:
        """
        Create a changes dictionary for audit logging.
        
        Args:
            old_value: Previous value
            new_value: New value
            field_name: Name of the field being changed
            
        Returns:
            Dictionary with before/after values
        """
        return {
            field_name: {
                "old": old_value,
                "new": new_value
            }
        }
    
    async def get_audit_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get audit logs with filtering and pagination.
        
        Requirements: 14.4 - Audit log retrieval with filtering
        """
        try:
            query = self.db.query(AuditLog)
            
            # Apply filters
            if action:
                query = query.filter(AuditLog.action == action)
            
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            if date_from:
                query = query.filter(AuditLog.timestamp >= date_from)
            
            if date_to:
                query = query.filter(AuditLog.timestamp <= date_to)
            
            # Get total count
            total = query.count()
            
            # Paginate
            skip = (page - 1) * page_size
            logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(page_size).all()
            
            # Format logs
            logs_data = []
            for log in logs:
                # Get username
                user = self.db.query(User).filter(User.id == log.user_id).first()
                username = user.full_name if user and user.full_name else (user.email if user else f"User {log.user_id}")
                
                logs_data.append({
                    "id": log.id,
                    "timestamp": log.timestamp,
                    "user_id": log.user_id,
                    "username": username,
                    "action": log.action,
                    "resource_type": log.resource_type or "",
                    "resource_id": log.resource_id or "",
                    "details": log.details or {},
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent
                })
            
            return {
                "logs": logs_data,
                "total": total
            }
            
        except Exception as e:
            logger.error(f"Error fetching audit logs: {e}", exc_info=True)
            return {
                "logs": [],
                "total": 0
            }
    
    async def get_available_actions(self) -> list:
        """
        Get list of all available audit log action types.
        
        Requirements: 14.4 - Audit log filtering support
        """
        try:
            actions = self.db.query(AuditLog.action).distinct().all()
            return [action[0] for action in actions if action[0]]
        except Exception as e:
            logger.error(f"Error fetching available actions: {e}", exc_info=True)
            return []
    
    async def get_available_resource_types(self) -> list:
        """
        Get list of all available audit log resource types.
        
        Requirements: 14.4 - Audit log filtering support
        """
        try:
            resource_types = self.db.query(AuditLog.resource_type).distinct().all()
            return [rt[0] for rt in resource_types if rt[0]]
        except Exception as e:
            logger.error(f"Error fetching available resource types: {e}", exc_info=True)
            return []


class AuditLogContext:
    """
    Context manager for timing and logging actions.
    
    Usage:
        with AuditLogContext(audit_logger, user_id, "create_team") as ctx:
            # Perform action
            team = create_team(...)
            ctx.set_resource("team", team.id)
            ctx.set_details({"team_name": team.name})
    """
    
    def __init__(
        self,
        audit_logger: AuditLogger,
        user_id: int,
        action: str,
        resource_type: Optional[str] = None,
        request: Optional[Request] = None
    ):
        self.audit_logger = audit_logger
        self.user_id = user_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = None
        self.details = {}
        self.changes = None
        self.request = request
        self.start_time = None
        self.status = "success"
        self.error_message = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = int((time.time() - self.start_time) * 1000)
        
        if exc_type is not None:
            self.status = "failed"
            self.error_message = str(exc_val)
        
        self.audit_logger.log_action(
            user_id=self.user_id,
            action=self.action,
            resource_type=self.resource_type,
            resource_id=self.resource_id,
            details=self.details,
            changes=self.changes,
            request=self.request,
            status=self.status,
            error_message=self.error_message,
            duration_ms=duration_ms
        )
        
        # Don't suppress exceptions
        return False
    
    def set_resource(self, resource_type: str, resource_id: str):
        """Set the resource being acted upon."""
        self.resource_type = resource_type
        self.resource_id = resource_id
    
    def set_details(self, details: Dict[str, Any]):
        """Set additional details about the action."""
        self.details.update(details)
    
    def set_changes(self, changes: Dict[str, Any]):
        """Set before/after values for the action."""
        self.changes = changes
