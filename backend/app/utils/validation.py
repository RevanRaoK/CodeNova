"""
Validation utilities for feedback system.

This module provides validation functions for user permissions,
issue IDs, and other feedback-related validation logic.

Requirements covered: 2.1, 2.2, 2.3
"""

import re
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.users import User, UserRole
from app.models.feedback import Issue, FeedbackRecord
from app.schemas.feedback import UserPermissionLevel


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class PermissionError(Exception):
    """Custom exception for permission-related errors."""
    pass


class FeedbackValidator:
    """Utility class for feedback system validation."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_issue_id_format(self, issue_id: str) -> bool:
        """
        Validate issue ID format.
        
        Args:
            issue_id: The issue ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not issue_id:
            return False
        
        # Check if it's a valid 64-character hexadecimal string (SHA-256 hash)
        return bool(re.match(r'^[a-fA-F0-9]{64}$', issue_id))
    
    def validate_issue_exists(self, issue_id: str) -> bool:
        """
        Validate that an issue exists in the database.
        
        Args:
            issue_id: The issue ID to check
            
        Returns:
            True if issue exists, False otherwise
        """
        if not self.validate_issue_id_format(issue_id):
            return False
        
        issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
        return issue is not None
    
    def validate_user_permission(
        self, 
        user_id: int, 
        operation: str, 
        resource_id: Optional[str] = None
    ) -> bool:
        """
        Validate user permissions for feedback operations.
        
        Args:
            user_id: ID of the user requesting permission
            operation: Operation being requested
            resource_id: Optional resource ID (issue_id, feedback_id, etc.)
            
        Returns:
            True if user has permission, False otherwise
            
        Raises:
            ValidationError: If user or operation is invalid
        """
        # Get user from database
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValidationError(f"User with ID {user_id} not found")
        
        if not user.is_active:
            raise ValidationError(f"User {user_id} is not active")
        
        # Define permission mappings
        permission_map = {
            'submit_feedback': [UserRole.DEVELOPER, UserRole.REVIEWER, UserRole.ADMIN],
            'view_feedback': [UserRole.DEVELOPER, UserRole.REVIEWER, UserRole.ADMIN],
            'validate_feedback': [UserRole.ADMIN],
            'view_statistics': [UserRole.DEVELOPER, UserRole.REVIEWER, UserRole.ADMIN],
            'manage_feedback': [UserRole.ADMIN],
            'delete_feedback': [UserRole.ADMIN],
            'export_data': [UserRole.ADMIN],
            'manage_users': [UserRole.ADMIN]
        }
        
        # Check if operation is valid
        if operation not in permission_map:
            raise ValidationError(f"Invalid operation: {operation}")
        
        # Check if user has required role
        required_roles = permission_map[operation]
        if user.role not in required_roles:
            return False
        
        # Additional checks for specific operations
        if operation == 'submit_feedback' and resource_id:
            # Check if issue exists and is active
            if not self.validate_issue_exists(resource_id):
                raise ValidationError(f"Issue {resource_id} not found or invalid")
            
            # Check if user already provided feedback for this issue
            existing_feedback = self.db.query(FeedbackRecord).filter(
                FeedbackRecord.issue_id == resource_id,
                FeedbackRecord.user_id == user_id
            ).first()
            
            # Allow updating existing feedback
            return True
        
        elif operation in ['validate_feedback', 'manage_feedback'] and resource_id:
            # For feedback management, check if feedback record exists
            if resource_id.isdigit():
                # Numeric ID - feedback record
                feedback = self.db.query(FeedbackRecord).filter(
                    FeedbackRecord.id == int(resource_id)
                ).first()
                return feedback is not None
            else:
                # Hex ID - issue ID
                return self.validate_issue_exists(resource_id)
        
        return True
    
    def validate_feedback_content(self, content: str, content_type: str = "comment") -> bool:
        """
        Validate feedback content for security and quality.
        
        Args:
            content: The content to validate
            content_type: Type of content ("comment" or "suggestion")
            
        Returns:
            True if content is valid, False otherwise
        """
        if not content:
            return True  # Empty content is allowed
        
        # Check for potentially malicious content
        malicious_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'data:text/html',
            r'eval\s*\(',
            r'onclick\s*=',
            r'onerror\s*=',
            r'onload\s*='
        ]
        
        content_lower = content.lower()
        for pattern in malicious_patterns:
            if re.search(pattern, content_lower):
                return False
        
        # Check content length based on type
        max_lengths = {
            "comment": 1000,
            "suggestion": 5000
        }
        
        max_length = max_lengths.get(content_type, 1000)
        if len(content) > max_length:
            return False
        
        return True
    
    def validate_bulk_operation(
        self, 
        user_id: int, 
        operation: str, 
        resource_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Validate bulk operations on feedback records.
        
        Args:
            user_id: ID of the user requesting the operation
            operation: Bulk operation type
            resource_ids: List of resource IDs to operate on
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid_ids': [],
            'invalid_ids': [],
            'permission_denied': [],
            'errors': []
        }
        
        # Check user permission for bulk operations
        try:
            if not self.validate_user_permission(user_id, operation):
                results['errors'].append(f"User {user_id} lacks permission for {operation}")
                return results
        except ValidationError as e:
            results['errors'].append(str(e))
            return results
        
        # Validate each resource ID
        for resource_id in resource_ids:
            try:
                if operation in ['validate_feedback', 'manage_feedback']:
                    if resource_id.isdigit():
                        # Feedback record ID
                        feedback = self.db.query(FeedbackRecord).filter(
                            FeedbackRecord.id == int(resource_id)
                        ).first()
                        if feedback:
                            results['valid_ids'].append(resource_id)
                        else:
                            results['invalid_ids'].append(resource_id)
                    else:
                        results['invalid_ids'].append(resource_id)
                
                elif operation == 'submit_feedback':
                    if self.validate_issue_exists(resource_id):
                        results['valid_ids'].append(resource_id)
                    else:
                        results['invalid_ids'].append(resource_id)
                
                else:
                    results['invalid_ids'].append(resource_id)
                    
            except Exception as e:
                results['errors'].append(f"Error validating {resource_id}: {str(e)}")
        
        return results
    
    def validate_export_request(
        self, 
        user_id: int, 
        include_personal_data: bool = False
    ) -> bool:
        """
        Validate export request permissions.
        
        Args:
            user_id: ID of the user requesting export
            include_personal_data: Whether personal data is requested
            
        Returns:
            True if export is allowed, False otherwise
        """
        try:
            # Basic export permission
            if not self.validate_user_permission(user_id, 'export_data'):
                return False
            
            # Additional check for personal data
            if include_personal_data:
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user or user.role != UserRole.ADMIN:
                    return False
            
            return True
            
        except ValidationError:
            return False
    
    def get_user_permission_level(self, user_id: int) -> Optional[UserPermissionLevel]:
        """
        Get the permission level for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            UserPermissionLevel enum value or None if user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return None
        
        # Map user roles to permission levels
        role_to_permission = {
            UserRole.GUEST: UserPermissionLevel.READ_ONLY,
            UserRole.DEVELOPER: UserPermissionLevel.SUBMIT_FEEDBACK,
            UserRole.REVIEWER: UserPermissionLevel.SUBMIT_FEEDBACK,
            UserRole.ADMIN: UserPermissionLevel.ADMIN
        }
        
        return role_to_permission.get(user.role, UserPermissionLevel.READ_ONLY)
    
    def validate_context_data_structure(self, context_data: Dict[str, Any]) -> bool:
        """
        Validate the structure and content of context data.
        
        Args:
            context_data: Context data dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(context_data, dict):
            return False
        
        # Check size limit (10KB)
        if len(str(context_data)) > 10000:
            return False
        
        # Check nesting depth (max 5 levels)
        def check_depth(obj, current_depth=0, max_depth=5):
            if current_depth > max_depth:
                return False
            
            if isinstance(obj, dict):
                for value in obj.values():
                    if not check_depth(value, current_depth + 1, max_depth):
                        return False
            elif isinstance(obj, list):
                for item in obj:
                    if not check_depth(item, current_depth + 1, max_depth):
                        return False
            
            return True
        
        return check_depth(context_data)


def create_validator(db: Session) -> FeedbackValidator:
    """
    Factory function to create a FeedbackValidator instance.
    
    Args:
        db: Database session
        
    Returns:
        FeedbackValidator instance
    """
    return FeedbackValidator(db)