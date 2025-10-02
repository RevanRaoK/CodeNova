"""
Unit tests for validation utilities.

This module tests the validation functions for user permissions,
issue IDs, and other feedback-related validation logic.

Requirements covered: 2.1, 2.2, 2.3
"""

import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from app.utils.validation import FeedbackValidator, ValidationError, PermissionError, create_validator
from app.models.users import User, UserRole
from app.models.feedback import Issue, FeedbackRecord
from app.schemas.feedback import UserPermissionLevel


class TestFeedbackValidator:
    """Test suite for FeedbackValidator class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def validator(self, mock_db):
        """Create a FeedbackValidator instance with mocked database."""
        return FeedbackValidator(mock_db)
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock(spec=User)
        user.id = 1
        user.is_active = True
        user.role = UserRole.DEVELOPER
        return user
    
    @pytest.fixture
    def mock_admin_user(self):
        """Create a mock admin user."""
        user = Mock(spec=User)
        user.id = 2
        user.is_active = True
        user.role = UserRole.ADMIN
        return user
    
    @pytest.fixture
    def mock_issue(self):
        """Create a mock issue."""
        issue = Mock(spec=Issue)
        issue.id = "a" * 64
        issue.status = "active"
        return issue
    
    def test_validate_issue_id_format_valid(self, validator):
        """Test validation of valid issue ID formats."""
        valid_ids = [
            "a" * 64,  # All lowercase
            "A" * 64,  # All uppercase
            "1234567890abcdef" * 4,  # Mixed numbers and letters
            "0123456789ABCDEF" * 4   # Mixed case
        ]
        
        for valid_id in valid_ids:
            assert validator.validate_issue_id_format(valid_id) is True
    
    def test_validate_issue_id_format_invalid(self, validator):
        """Test validation of invalid issue ID formats."""
        invalid_ids = [
            "",  # Empty string
            "abc123",  # Too short
            "a" * 63,  # 63 characters
            "a" * 65,  # 65 characters
            "g" * 64,  # Invalid hex character
            "123-456-789",  # Contains hyphens
            None  # None value
        ]
        
        for invalid_id in invalid_ids:
            assert validator.validate_issue_id_format(invalid_id) is False
    
    def test_validate_issue_exists_true(self, validator, mock_db, mock_issue):
        """Test validation when issue exists."""
        issue_id = "a" * 64
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_issue
        mock_db.query.return_value = mock_query
        
        result = validator.validate_issue_exists(issue_id)
        
        assert result is True
        mock_db.query.assert_called_once_with(Issue)
    
    def test_validate_issue_exists_false(self, validator, mock_db):
        """Test validation when issue doesn't exist."""
        issue_id = "a" * 64
        
        # Mock database query returning None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = validator.validate_issue_exists(issue_id)
        
        assert result is False
    
    def test_validate_issue_exists_invalid_format(self, validator):
        """Test validation with invalid issue ID format."""
        invalid_id = "invalid_id"
        
        result = validator.validate_issue_exists(invalid_id)
        
        assert result is False
    
    def test_validate_user_permission_valid_user(self, validator, mock_db, mock_user):
        """Test user permission validation for valid user."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        result = validator.validate_user_permission(1, 'submit_feedback')
        
        assert result is True
        mock_db.query.assert_called_with(User)
    
    def test_validate_user_permission_user_not_found(self, validator, mock_db):
        """Test user permission validation when user not found."""
        # Mock database query returning None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(ValidationError, match="User with ID 999 not found"):
            validator.validate_user_permission(999, 'submit_feedback')
    
    def test_validate_user_permission_inactive_user(self, validator, mock_db):
        """Test user permission validation for inactive user."""
        inactive_user = Mock(spec=User)
        inactive_user.id = 1
        inactive_user.is_active = False
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = inactive_user
        mock_db.query.return_value = mock_query
        
        with pytest.raises(ValidationError, match="User 1 is not active"):
            validator.validate_user_permission(1, 'submit_feedback')
    
    def test_validate_user_permission_invalid_operation(self, validator, mock_db, mock_user):
        """Test user permission validation with invalid operation."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        with pytest.raises(ValidationError, match="Invalid operation: invalid_op"):
            validator.validate_user_permission(1, 'invalid_op')
    
    def test_validate_user_permission_insufficient_role(self, validator, mock_db, mock_user):
        """Test user permission validation with insufficient role."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        # Regular user trying to validate feedback (admin-only operation)
        result = validator.validate_user_permission(1, 'validate_feedback')
        
        assert result is False
    
    def test_validate_user_permission_admin_operations(self, validator, mock_db, mock_admin_user):
        """Test admin user permissions for admin-only operations."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_admin_user
        mock_db.query.return_value = mock_query
        
        admin_operations = [
            'validate_feedback', 'manage_feedback', 'delete_feedback',
            'export_data', 'manage_users'
        ]
        
        for operation in admin_operations:
            result = validator.validate_user_permission(2, operation)
            assert result is True
    
    def test_validate_feedback_content_valid(self, validator):
        """Test validation of valid feedback content."""
        valid_contents = [
            "This is a helpful suggestion",
            "I disagree with this approach because...",
            "",  # Empty content
            None,  # None content
            "Code looks good: def function(): return True"
        ]
        
        for content in valid_contents:
            if content is not None:
                assert validator.validate_feedback_content(content) is True
    
    def test_validate_feedback_content_malicious(self, validator):
        """Test validation of potentially malicious content."""
        malicious_contents = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "eval('malicious code')",
            "<div onclick='alert()'>click me</div>",
            "<img onerror='alert()' src='x'>",
            "<body onload='alert()'>content</body>"
        ]
        
        for content in malicious_contents:
            assert validator.validate_feedback_content(content) is False
    
    def test_validate_feedback_content_length_limits(self, validator):
        """Test validation of content length limits."""
        # Test comment length limit (1000 chars)
        long_comment = "a" * 1001
        assert validator.validate_feedback_content(long_comment, "comment") is False
        
        valid_comment = "a" * 1000
        assert validator.validate_feedback_content(valid_comment, "comment") is True
        
        # Test suggestion length limit (5000 chars)
        long_suggestion = "a" * 5001
        assert validator.validate_feedback_content(long_suggestion, "suggestion") is False
        
        valid_suggestion = "a" * 5000
        assert validator.validate_feedback_content(valid_suggestion, "suggestion") is True
    
    def test_validate_bulk_operation_valid(self, validator, mock_db, mock_admin_user):
        """Test validation of valid bulk operations."""
        # Mock admin user
        mock_query_user = Mock()
        mock_query_user.filter.return_value.first.return_value = mock_admin_user
        
        # Mock feedback records
        mock_feedback1 = Mock(spec=FeedbackRecord)
        mock_feedback1.id = 1
        mock_feedback2 = Mock(spec=FeedbackRecord)
        mock_feedback2.id = 2
        
        mock_query_feedback = Mock()
        mock_query_feedback.filter.return_value.first.side_effect = [mock_feedback1, mock_feedback2]
        
        # Configure mock_db to return different queries
        def mock_query_side_effect(model):
            if model == User:
                return mock_query_user
            elif model == FeedbackRecord:
                return mock_query_feedback
        
        mock_db.query.side_effect = mock_query_side_effect
        
        result = validator.validate_bulk_operation(2, 'validate_feedback', ['1', '2'])
        
        assert result['valid_ids'] == ['1', '2']
        assert result['invalid_ids'] == []
        assert result['errors'] == []
    
    def test_validate_export_request_admin(self, validator, mock_db, mock_admin_user):
        """Test export request validation for admin user."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_admin_user
        mock_db.query.return_value = mock_query
        
        # Admin can export with personal data
        result = validator.validate_export_request(2, include_personal_data=True)
        assert result is True
        
        # Admin can export without personal data
        result = validator.validate_export_request(2, include_personal_data=False)
        assert result is True
    
    def test_validate_export_request_regular_user(self, validator, mock_db, mock_user):
        """Test export request validation for regular user."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        # Regular user cannot export personal data
        result = validator.validate_export_request(1, include_personal_data=True)
        assert result is False
    
    def test_get_user_permission_level(self, validator, mock_db, mock_user, mock_admin_user):
        """Test getting user permission levels."""
        # Mock database queries
        mock_query = Mock()
        
        # Test regular user
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        level = validator.get_user_permission_level(1)
        assert level == UserPermissionLevel.SUBMIT_FEEDBACK
        
        # Test admin user
        mock_query.filter.return_value.first.return_value = mock_admin_user
        
        level = validator.get_user_permission_level(2)
        assert level == UserPermissionLevel.ADMIN
        
        # Test non-existent user
        mock_query.filter.return_value.first.return_value = None
        
        level = validator.get_user_permission_level(999)
        assert level is None
    
    def test_validate_context_data_structure_valid(self, validator):
        """Test validation of valid context data structures."""
        valid_structures = [
            {},  # Empty dict
            {"key": "value"},  # Simple dict
            {"nested": {"key": "value"}},  # Nested dict
            {"list": [1, 2, 3]},  # Dict with list
            {"complex": {"nested": {"data": [1, 2, {"inner": "value"}]}}}  # Complex but within limits
        ]
        
        for structure in valid_structures:
            assert validator.validate_context_data_structure(structure) is True
    
    def test_validate_context_data_structure_invalid(self, validator):
        """Test validation of invalid context data structures."""
        # Not a dictionary
        assert validator.validate_context_data_structure("not a dict") is False
        assert validator.validate_context_data_structure([1, 2, 3]) is False
        
        # Too large (over 10KB)
        large_data = {"data": "x" * 10001}
        assert validator.validate_context_data_structure(large_data) is False
        
        # Too deeply nested (over 5 levels)
        deeply_nested = {"l1": {"l2": {"l3": {"l4": {"l5": {"l6": "too deep"}}}}}}
        assert validator.validate_context_data_structure(deeply_nested) is False


class TestCreateValidator:
    """Test suite for create_validator factory function."""
    
    def test_create_validator(self):
        """Test creating a validator instance."""
        mock_db = Mock(spec=Session)
        validator = create_validator(mock_db)
        
        assert isinstance(validator, FeedbackValidator)
        assert validator.db == mock_db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])