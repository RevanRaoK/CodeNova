"""
Unit tests for feedback schema validation.

This module tests the Pydantic schemas for feedback requests and responses,
including validation for feedback types, issue IDs, and user permissions.

Requirements covered: 2.1, 2.2, 2.3
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from app.schemas.feedback import (
    FeedbackSubmissionRequest, FeedbackResponse, FeedbackType, ExperienceLevel,
    ReviewContext, FeedbackPermissionRequest, BulkFeedbackValidationRequest,
    FeedbackExportRequest, FeedbackAnalyticsRequest, DateRange,
    BulkFeedbackRequest, FeedbackValidationRequest, UserPermissionLevel
)


class TestFeedbackSubmissionRequest:
    """Test suite for FeedbackSubmissionRequest schema validation."""
    
    def test_valid_feedback_submission(self):
        """Test valid feedback submission request."""
        valid_issue_id = "a" * 64  # 64-character hex string
        
        request = FeedbackSubmissionRequest(
            issue_id=valid_issue_id,
            feedback_type=FeedbackType.ACCEPT,
            feedback_comment="This suggestion was helpful",
            user_experience_level=ExperienceLevel.INTERMEDIATE,
            code_review_context=ReviewContext.TEAM
        )
        
        assert request.issue_id == valid_issue_id
        assert request.feedback_type == FeedbackType.ACCEPT
        assert request.feedback_comment == "This suggestion was helpful"
        assert request.user_experience_level == ExperienceLevel.INTERMEDIATE
        assert request.code_review_context == ReviewContext.TEAM
    
    def test_invalid_issue_id_format(self):
        """Test validation of invalid issue ID formats."""
        invalid_issue_ids = [
            "",  # Empty string
            "abc123",  # Too short
            "a" * 63,  # 63 characters (too short)
            "a" * 65,  # 65 characters (too long)
            "g" * 64,  # Invalid hex character
            "ABC123" + "z" * 58,  # Contains invalid character
            "123-456-789",  # Contains hyphens
            None  # None value
        ]
        
        for invalid_id in invalid_issue_ids:
            with pytest.raises(ValidationError) as exc_info:
                FeedbackSubmissionRequest(
                    issue_id=invalid_id,
                    feedback_type=FeedbackType.ACCEPT
                )
            
            error_messages = str(exc_info.value)
            # Check that we get a validation error - the specific message may vary
            assert len(error_messages) > 0
            # For None values, check for "string_type" error
            if invalid_id is None:
                assert any(keyword in error_messages.lower() for keyword in 
                          ['input should be a valid string', 'string_type'])
            else:
                # For other invalid formats, check for our custom validation messages
                assert any(keyword in error_messages.lower() for keyword in 
                          ['issue id', '64-character hexadecimal string', 'required'])
    
    def test_valid_issue_id_normalization(self):
        """Test that issue IDs are normalized to lowercase."""
        uppercase_id = "A" * 64
        
        request = FeedbackSubmissionRequest(
            issue_id=uppercase_id,
            feedback_type=FeedbackType.ACCEPT
        )
        
        assert request.issue_id == "a" * 64  # Should be normalized to lowercase
    
    def test_feedback_type_validation(self):
        """Test validation of feedback types."""
        valid_issue_id = "a" * 64
        
        # Test all valid feedback types
        for feedback_type in FeedbackType:
            # For MODIFY type, we need to provide modified_suggestion
            kwargs = {
                "issue_id": valid_issue_id,
                "feedback_type": feedback_type
            }
            if feedback_type == FeedbackType.MODIFY:
                kwargs["modified_suggestion"] = "def improved_function():\n    return 'better'"
            
            request = FeedbackSubmissionRequest(**kwargs)
            assert request.feedback_type == feedback_type
        
        # Test invalid feedback type
        with pytest.raises(ValidationError):
            FeedbackSubmissionRequest(
                issue_id=valid_issue_id,
                feedback_type="invalid_type"
            )
    
    def test_modified_suggestion_required_for_modify(self):
        """Test that modified suggestion is required when feedback type is MODIFY."""
        valid_issue_id = "a" * 64
        
        # Should fail without modified_suggestion
        with pytest.raises(ValidationError) as exc_info:
            FeedbackSubmissionRequest(
                issue_id=valid_issue_id,
                feedback_type=FeedbackType.MODIFY
            )
        
        assert "modified suggestion is required" in str(exc_info.value).lower()
        
        # Should succeed with modified_suggestion
        request = FeedbackSubmissionRequest(
            issue_id=valid_issue_id,
            feedback_type=FeedbackType.MODIFY,
            modified_suggestion="def improved_function():\n    return 'better code'"
        )
        
        assert request.modified_suggestion is not None
    
    def test_feedback_comment_validation(self):
        """Test feedback comment validation."""
        valid_issue_id = "a" * 64
        
        # Valid comments
        valid_comments = [
            "This is a helpful suggestion",
            "I disagree with this approach",
            None,  # Optional field
            ""  # Empty string should be converted to None
        ]
        
        for comment in valid_comments:
            request = FeedbackSubmissionRequest(
                issue_id=valid_issue_id,
                feedback_type=FeedbackType.ACCEPT,
                feedback_comment=comment
            )
            # Empty string should be converted to None by the validator
            expected = None if comment == "" else comment
            assert request.feedback_comment == expected
        
        # Invalid comments (potentially malicious content)
        malicious_comments = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>"
        ]
        
        for malicious_comment in malicious_comments:
            with pytest.raises(ValidationError) as exc_info:
                FeedbackSubmissionRequest(
                    issue_id=valid_issue_id,
                    feedback_type=FeedbackType.ACCEPT,
                    feedback_comment=malicious_comment
                )
            
            assert "unsafe content" in str(exc_info.value).lower()
        
        # Test maximum length
        long_comment = "a" * 1001  # Exceeds 1000 character limit
        with pytest.raises(ValidationError):
            FeedbackSubmissionRequest(
                issue_id=valid_issue_id,
                feedback_type=FeedbackType.ACCEPT,
                feedback_comment=long_comment
            )
    
    def test_modified_suggestion_validation(self):
        """Test modified suggestion validation."""
        valid_issue_id = "a" * 64
        
        # Valid modified suggestions
        valid_suggestions = [
            "def improved_function():\n    return 'better'",
            "// This is a better approach\nfunction test() { return true; }",
            "# Python code\nresult = [x for x in range(10)]"
        ]
        
        for suggestion in valid_suggestions:
            request = FeedbackSubmissionRequest(
                issue_id=valid_issue_id,
                feedback_type=FeedbackType.MODIFY,
                modified_suggestion=suggestion
            )
            assert request.modified_suggestion == suggestion
        
        # Invalid suggestions (potentially malicious content)
        malicious_suggestions = [
            "<script>alert('xss')</script>",
            "eval('malicious code')",
            "javascript:alert('xss')"
        ]
        
        for malicious_suggestion in malicious_suggestions:
            with pytest.raises(ValidationError) as exc_info:
                FeedbackSubmissionRequest(
                    issue_id=valid_issue_id,
                    feedback_type=FeedbackType.MODIFY,
                    modified_suggestion=malicious_suggestion
                )
            
            assert "unsafe content" in str(exc_info.value).lower()
        
        # Test maximum length
        long_suggestion = "a" * 5001  # Exceeds 5000 character limit
        with pytest.raises(ValidationError):
            FeedbackSubmissionRequest(
                issue_id=valid_issue_id,
                feedback_type=FeedbackType.MODIFY,
                modified_suggestion=long_suggestion
            )
    
    def test_context_data_validation(self):
        """Test context data validation."""
        valid_issue_id = "a" * 64
        
        # Valid context data
        valid_context_data = [
            None,  # Optional field
            {},  # Empty dict
            {"ide": "vscode", "project_type": "web"},
            {"user_settings": {"theme": "dark", "font_size": 14}},
            {"metrics": [1, 2, 3, 4, 5]}
        ]
        
        for context_data in valid_context_data:
            request = FeedbackSubmissionRequest(
                issue_id=valid_issue_id,
                feedback_type=FeedbackType.ACCEPT,
                context_data=context_data
            )
            assert request.context_data == context_data
        
        # Invalid context data types
        with pytest.raises(ValidationError) as exc_info:
            FeedbackSubmissionRequest(
                issue_id=valid_issue_id,
                feedback_type=FeedbackType.ACCEPT,
                context_data="not a dict"
            )
        
        assert any(keyword in str(exc_info.value).lower() for keyword in 
                  ['must be a dictionary', 'should be a valid dictionary', 'dict_type'])
        
        # Test size limit (10KB)
        large_context = {"data": "x" * 10001}  # Exceeds 10KB
        with pytest.raises(ValidationError) as exc_info:
            FeedbackSubmissionRequest(
                issue_id=valid_issue_id,
                feedback_type=FeedbackType.ACCEPT,
                context_data=large_context
            )
        
        assert "too large" in str(exc_info.value).lower()
        
        # Test depth limit
        deeply_nested = {"level1": {"level2": {"level3": {"level4": {"level5": {"level6": "too deep"}}}}}}
        with pytest.raises(ValidationError) as exc_info:
            FeedbackSubmissionRequest(
                issue_id=valid_issue_id,
                feedback_type=FeedbackType.ACCEPT,
                context_data=deeply_nested
            )
        
        assert "too deeply nested" in str(exc_info.value).lower()


class TestFeedbackPermissionRequest:
    """Test suite for FeedbackPermissionRequest schema validation."""
    
    def test_valid_permission_request(self):
        """Test valid permission request."""
        request = FeedbackPermissionRequest(
            user_id=123,
            operation="submit_feedback",
            resource_id="a" * 64
        )
        
        assert request.user_id == 123
        assert request.operation == "submit_feedback"
        assert request.resource_id == "a" * 64
    
    def test_invalid_user_id(self):
        """Test validation of invalid user IDs."""
        invalid_user_ids = [0, -1, -100]
        
        for invalid_id in invalid_user_ids:
            with pytest.raises(ValidationError) as exc_info:
                FeedbackPermissionRequest(
                    user_id=invalid_id,
                    operation="submit_feedback"
                )
            
            assert "greater than 0" in str(exc_info.value).lower()
    
    def test_operation_validation(self):
        """Test validation of operations."""
        valid_operations = [
            'submit_feedback', 'view_feedback', 'validate_feedback',
            'view_statistics', 'manage_feedback', 'delete_feedback',
            'export_data', 'manage_users'
        ]
        
        for operation in valid_operations:
            request = FeedbackPermissionRequest(
                user_id=123,
                operation=operation
            )
            assert request.operation == operation
        
        # Test invalid operation
        with pytest.raises(ValidationError) as exc_info:
            FeedbackPermissionRequest(
                user_id=123,
                operation="invalid_operation"
            )
        
        assert "invalid operation" in str(exc_info.value).lower()
    
    def test_resource_id_validation(self):
        """Test resource ID validation based on operation type."""
        # For feedback operations, should accept 64-char hex strings
        request = FeedbackPermissionRequest(
            user_id=123,
            operation="submit_feedback",
            resource_id="a" * 64
        )
        assert request.resource_id == "a" * 64
        
        # For validation operations, should accept numeric IDs
        request = FeedbackPermissionRequest(
            user_id=123,
            operation="validate_feedback",
            resource_id="12345"
        )
        assert request.resource_id == "12345"
        
        # Invalid resource ID for feedback operation
        with pytest.raises(ValidationError) as exc_info:
            FeedbackPermissionRequest(
                user_id=123,
                operation="submit_feedback",
                resource_id="invalid_id"
            )
        
        assert "64-character hexadecimal" in str(exc_info.value).lower()


class TestBulkFeedbackValidationRequest:
    """Test suite for BulkFeedbackValidationRequest schema validation."""
    
    def test_valid_bulk_validation_request(self):
        """Test valid bulk validation request."""
        request = BulkFeedbackValidationRequest(
            feedback_ids=[1, 2, 3, 4, 5],
            validation_action="approve",
            validation_score=0.8,
            validation_comment="Bulk approval of high-quality feedback"
        )
        
        assert request.feedback_ids == [1, 2, 3, 4, 5]
        assert request.validation_action == "approve"
        assert request.validation_score == 0.8
    
    def test_feedback_ids_validation(self):
        """Test validation of feedback IDs list."""
        # Empty list should fail
        with pytest.raises(ValidationError) as exc_info:
            BulkFeedbackValidationRequest(
                feedback_ids=[],
                validation_action="approve"
            )
        
        assert any(keyword in str(exc_info.value).lower() for keyword in 
                  ['at least one feedback id', 'at least 1 item', 'too_short'])
        
        # Too many IDs should fail
        with pytest.raises(ValidationError):
            BulkFeedbackValidationRequest(
                feedback_ids=list(range(1, 102)),  # 101 items, exceeds max of 100
                validation_action="approve"
            )
        
        # Duplicate IDs should fail
        with pytest.raises(ValidationError) as exc_info:
            BulkFeedbackValidationRequest(
                feedback_ids=[1, 2, 3, 2, 4],  # Duplicate ID: 2
                validation_action="approve"
            )
        
        assert "duplicate" in str(exc_info.value).lower()
        
        # Invalid (non-positive) IDs should fail
        with pytest.raises(ValidationError) as exc_info:
            BulkFeedbackValidationRequest(
                feedback_ids=[1, 2, 0, 4],  # Invalid ID: 0
                validation_action="approve"
            )
        
        assert "positive integer" in str(exc_info.value).lower()
    
    def test_validation_action_validation(self):
        """Test validation of validation actions."""
        valid_actions = ['approve', 'reject', 'flag_for_review', 'mark_invalid']
        
        for action in valid_actions:
            request = BulkFeedbackValidationRequest(
                feedback_ids=[1, 2, 3],
                validation_action=action
            )
            assert request.validation_action == action
        
        # Invalid action should fail
        with pytest.raises(ValidationError) as exc_info:
            BulkFeedbackValidationRequest(
                feedback_ids=[1, 2, 3],
                validation_action="invalid_action"
            )
        
        assert "invalid validation action" in str(exc_info.value).lower()


class TestFeedbackExportRequest:
    """Test suite for FeedbackExportRequest schema validation."""
    
    def test_valid_export_request(self):
        """Test valid export request."""
        date_range = DateRange(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        request = FeedbackExportRequest(
            export_format="json",
            date_range=date_range,
            pattern_types=["unused_variable", "code_complexity"],
            feedback_types=[FeedbackType.ACCEPT, FeedbackType.REJECT],
            include_validated_only=True
        )
        
        assert request.export_format == "json"
        assert request.pattern_types == ["unused_variable", "code_complexity"]
        assert request.include_validated_only is True
    
    def test_export_format_validation(self):
        """Test export format validation."""
        valid_formats = ['json', 'csv', 'xlsx']
        
        for format_type in valid_formats:
            request = FeedbackExportRequest(export_format=format_type)
            assert request.export_format == format_type.lower()
        
        # Test case insensitive
        request = FeedbackExportRequest(export_format="JSON")
        assert request.export_format == "json"
        
        # Invalid format should fail
        with pytest.raises(ValidationError) as exc_info:
            FeedbackExportRequest(export_format="pdf")
        
        assert "invalid export format" in str(exc_info.value).lower()
    
    def test_pattern_types_validation(self):
        """Test pattern types validation."""
        # Valid pattern types
        request = FeedbackExportRequest(
            export_format="json",
            pattern_types=["type1", "type2", "type3"]
        )
        assert request.pattern_types == ["type1", "type2", "type3"]
        
        # Empty strings should fail
        with pytest.raises(ValidationError) as exc_info:
            FeedbackExportRequest(
                export_format="json",
                pattern_types=["valid_type", "", "another_type"]
            )
        
        assert "cannot be empty" in str(exc_info.value).lower()
        
        # Duplicates should fail
        with pytest.raises(ValidationError) as exc_info:
            FeedbackExportRequest(
                export_format="json",
                pattern_types=["type1", "type2", "type1"]
            )
        
        assert "duplicate" in str(exc_info.value).lower()
        
        # Too many pattern types should fail
        with pytest.raises(ValidationError):
            FeedbackExportRequest(
                export_format="json",
                pattern_types=[f"type_{i}" for i in range(51)]  # Exceeds max of 50
            )


class TestDateRange:
    """Test suite for DateRange schema validation."""
    
    def test_valid_date_range(self):
        """Test valid date range."""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        date_range = DateRange(start_date=start_date, end_date=end_date)
        
        assert date_range.start_date == start_date
        assert date_range.end_date == end_date
    
    def test_invalid_date_range(self):
        """Test invalid date range (end before start)."""
        start_date = datetime.now()
        end_date = datetime.now() - timedelta(days=1)  # End before start
        
        with pytest.raises(ValidationError) as exc_info:
            DateRange(start_date=start_date, end_date=end_date)
        
        assert "end date must be after start date" in str(exc_info.value).lower()
    
    def test_excessive_date_range(self):
        """Test excessively large date range."""
        start_date = datetime.now() - timedelta(days=400)  # More than 365 days
        end_date = datetime.now()
        
        with pytest.raises(ValidationError) as exc_info:
            DateRange(start_date=start_date, end_date=end_date)
        
        assert "cannot exceed 365 days" in str(exc_info.value).lower()


class TestFeedbackAnalyticsRequest:
    """Test suite for FeedbackAnalyticsRequest schema validation."""
    
    def test_valid_analytics_request(self):
        """Test valid analytics request."""
        request = FeedbackAnalyticsRequest(
            analysis_type="acceptance_trends",
            group_by="date",
            filters={"pattern_type": "unused_variable"}
        )
        
        assert request.analysis_type == "acceptance_trends"
        assert request.group_by == "date"
        assert request.filters == {"pattern_type": "unused_variable"}
    
    def test_analysis_type_validation(self):
        """Test analysis type validation."""
        valid_types = [
            'acceptance_trends', 'pattern_performance', 'user_behavior',
            'model_improvement', 'feedback_quality', 'response_time_analysis'
        ]
        
        for analysis_type in valid_types:
            request = FeedbackAnalyticsRequest(analysis_type=analysis_type)
            assert request.analysis_type == analysis_type
        
        # Invalid analysis type should fail
        with pytest.raises(ValidationError) as exc_info:
            FeedbackAnalyticsRequest(analysis_type="invalid_analysis")
        
        assert "invalid analysis type" in str(exc_info.value).lower()
    
    def test_group_by_validation(self):
        """Test group_by dimension validation."""
        valid_dimensions = [
            'date', 'week', 'month', 'pattern_type', 'user_experience',
            'feedback_type', 'severity', 'user_id'
        ]
        
        for dimension in valid_dimensions:
            request = FeedbackAnalyticsRequest(
                analysis_type="acceptance_trends",
                group_by=dimension
            )
            assert request.group_by == dimension
        
        # Invalid dimension should fail
        with pytest.raises(ValidationError) as exc_info:
            FeedbackAnalyticsRequest(
                analysis_type="acceptance_trends",
                group_by="invalid_dimension"
            )
        
        assert "invalid group_by dimension" in str(exc_info.value).lower()


class TestBulkFeedbackRequest:
    """Test suite for BulkFeedbackRequest schema validation."""
    
    def test_valid_bulk_feedback_request(self):
        """Test valid bulk feedback request."""
        valid_issue_id = "a" * 64
        
        submissions = [
            FeedbackSubmissionRequest(
                issue_id=valid_issue_id,
                feedback_type=FeedbackType.ACCEPT
            ),
            FeedbackSubmissionRequest(
                issue_id="b" * 64,
                feedback_type=FeedbackType.REJECT
            )
        ]
        
        request = BulkFeedbackRequest(feedback_submissions=submissions)
        
        assert len(request.feedback_submissions) == 2
        assert request.feedback_submissions[0].feedback_type == FeedbackType.ACCEPT
        assert request.feedback_submissions[1].feedback_type == FeedbackType.REJECT
    
    def test_empty_submissions_validation(self):
        """Test validation of empty submissions list."""
        with pytest.raises(ValidationError) as exc_info:
            BulkFeedbackRequest(feedback_submissions=[])
        
        assert "at least one feedback submission" in str(exc_info.value).lower()
    
    def test_max_submissions_validation(self):
        """Test validation of maximum submissions limit."""
        valid_issue_id = "a" * 64
        
        # Create 51 submissions (exceeds max of 50)
        submissions = [
            FeedbackSubmissionRequest(
                issue_id=valid_issue_id,
                feedback_type=FeedbackType.ACCEPT
            ) for _ in range(51)
        ]
        
        with pytest.raises(ValidationError):
            BulkFeedbackRequest(feedback_submissions=submissions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])