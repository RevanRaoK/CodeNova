"""
Audit log model for tracking administrative actions and system events.

This model provides comprehensive audit logging for security, compliance,
and troubleshooting purposes.

Requirements covered: 14.4
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class AuditLog(Base):
    """
    Model for tracking administrative actions and sensitive operations.
    
    This model logs all administrative actions, user management operations,
    and other security-relevant events for audit and compliance purposes.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Event identification
    event_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # User and action information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., 'create_team', 'update_user_role'
    
    # Resource information
    resource_type = Column(String(50), nullable=True, index=True)  # e.g., 'user', 'team', 'analysis'
    resource_id = Column(String(100), nullable=True, index=True)  # ID of the affected resource
    
    # Action details
    details = Column(JSON, nullable=True)  # Additional context about the action
    changes = Column(JSON, nullable=True)  # Before/after values for updates
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)  # Browser/client information
    request_method = Column(String(10), nullable=True)  # HTTP method (GET, POST, etc.)
    request_path = Column(String(512), nullable=True)  # API endpoint path
    
    # Status and result
    status = Column(String(20), default="success")  # success, failed, partial
    error_message = Column(Text, nullable=True)  # Error details if action failed
    
    # Timing
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    duration_ms = Column(Integer, nullable=True)  # Action duration in milliseconds
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_action_timestamp', 'action', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action}, timestamp={self.timestamp})>"
    
    @classmethod
    def create_log(
        cls,
        user_id: int,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        details: dict = None,
        changes: dict = None,
        ip_address: str = None,
        user_agent: str = None,
        request_method: str = None,
        request_path: str = None,
        status: str = "success",
        error_message: str = None,
        duration_ms: int = None
    ):
        """
        Factory method to create an audit log entry.
        
        Args:
            user_id: ID of the user performing the action
            action: Action being performed (e.g., 'create_team')
            resource_type: Type of resource affected (e.g., 'team')
            resource_id: ID of the affected resource
            details: Additional context about the action
            changes: Before/after values for updates
            ip_address: Client IP address
            user_agent: Client user agent string
            request_method: HTTP method
            request_path: API endpoint path
            status: Action status (success, failed, partial)
            error_message: Error details if action failed
            duration_ms: Action duration in milliseconds
            
        Returns:
            AuditLog instance
        """
        return cls(
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
