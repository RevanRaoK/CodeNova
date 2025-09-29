"""
Unit tests for FeedbackService class.

Tests cover:
- Feedback recording and validation
- Feedback statistics and aggregation
- Training data preparation
- Error handling and edge cases

Requirements covered: 2.1, 2.2, 2.3, 2.4
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.feedback_service import FeedbackService, FeedbackValidationError
from app.models.feedback import FeedbackRecord, Issue, ModelVersion
from app.models.users import User
from app.schemas.feedback import (
    FeedbackSubmissionRequest, FeedbackType, ExperienceLevel, 
    ReviewContext, DateRange, FeedbackValidationRequest
)


class TestFeedbackService:
    """Test suite for FeedbackService functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def feedback_service(self, mock_db):
        """Create FeedbackService instance with mock database."""
        return FeedbackService(mock_db)
    
    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        return User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            is_active=True
        )
    
    @pytest.fixture
    def sample_issue(self):
        """Create a sample issue for testing."""
        return Issue(
            id="test_issue_123",
            analysis_id="analysis_456",
            pattern_type="unused_variable",
            severity="medium",
            suggestion_text="Remove unused variable 'x'",
            code_context="def func():\n    x = 1\n    return 2",
            location={"line": 2, "column": 4},
            status="active",
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_feedback_request(self):
        """Create a sample feedback submission request."""
        return FeedbackSubmissionRequest(
            issue_id="test_issue_123",
            feedback_type=FeedbackType.ACCEPT,
            feedback_comment="Good suggestion",
            user_experience_level=ExperienceLevel.INTERMEDIATE,
            code_review_context=ReviewContext.TEAM
        )
    
    def test_record_feedback_success(self, feedback_service, mock_db, sample_issue, sample_feedback_request):
        """Test successful feedback recording."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_issue
        mock_db.query.return_value.filter.return_value.first.side_effect = [sample_issue, None]  # Issue exists, no existing feedback
        
        # Execute
        result = feedback_service.record_feedback(1, sample_feedback_request)
        
        # Verify
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_record_feedback_issue_not_found(self, feedback_service, mock_db, sample_feedback_request):
        """Test feedback recording when issue doesn't exist."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute and verify
        with pytest.raises(FeedbackValidationError, match="Issue with ID test_issue_123 not found"):
            feedback_service.record_feedback(1, sample_feedback_request)
    
    def test_record_feedback_update_existing(self, feedback_service, mock_db, sample_issue, sample_feedback_request):
        """Test updating existing feedback instead of creating duplicate."""
        # Setup existing feedback
        existing_feedback = FeedbackRecord(
            id=1,
            issue_id="test_issue_123",
            user_id=1,
            feedback_type="reject",
            feedback_value=-1
        )
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.side_effect = [sample_issue, existing_feedback]
        
        # Execute
        result = feedback_service.record_feedback(1, sample_feedback_request)
        
        # Verify update occurred
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert not mock_db.add.called  # Should not add new record
    
    def test_get_feedback_value_mapping(self, feedback_service):
        """Test feedback type to numeric value conversion."""
        assert feedback_service._get_feedback_value(FeedbackType.ACCEPT) == 1
        assert feedback_service._get_feedback_value(FeedbackType.REJECT) == -1
        assert feedback_service._get_feedback_value(FeedbackType.MODIFY) == 0
        assert feedback_service._get_feedback_value(FeedbackType.IGNORE) == 0
    
    def test_get_feedback_by_id(self, feedback_service, mock_db):
        """Test retrieving feedback by ID."""
        # Setup mock
        expected_feedback = FeedbackRecord(id=1, issue_id="test", user_id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = expected_feedback
        
        # Execute
        result = feedback_service.get_feedback_by_id(1)
        
        # Verify
        assert result == expected_feedback
        mock_db.query.assert_called_with(FeedbackRecord)
    
    def test_get_feedback_for_issue(self, feedback_service, mock_db):
        """Test retrieving all feedback for a specific issue."""
        # Setup mock
        expected_feedback = [
            FeedbackRecord(id=1, issue_id="test_issue", user_id=1),
            FeedbackRecord(id=2, issue_id="test_issue", user_id=2)
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = expected_feedback
        
        # Execute
        result = feedback_service.get_feedback_for_issue("test_issue")
        
        # Verify
        assert result == expected_feedback
        mock_db.query.assert_called_with(FeedbackRecord)
    
    def test_get_user_feedback_history_pagination(self, feedback_service, mock_db):
        """Test paginated user feedback history."""
        # Setup mock chain
        mock_query = Mock()
        mock_order_by = Mock()
        mock_offset = Mock()
        mock_limit = Mock()
        
        mock_db.query.return_value.filter.return_value = mock_query
        mock_query.count.return_value = 25
        mock_query.order_by.return_value = mock_order_by
        mock_order_by.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        mock_limit.all.return_value = [
            FeedbackRecord(id=1, user_id=1),
            FeedbackRecord(id=2, user_id=1)
        ]
        
        # Execute
        feedback_records, total_count = feedback_service.get_user_feedback_history(1, page=2, page_size=10)
        
        # Verify
        assert total_count == 25
        assert len(feedback_records) == 2
        mock_order_by.offset.assert_called_with(10)  # (page-1) * page_size
        mock_offset.limit.assert_called_with(10)
    
    def test_get_feedback_statistics_empty_data(self, feedback_service, mock_db):
        """Test statistics generation with no data."""
        # Setup mock for empty result
        mock_db.query.return_value.join.return_value.all.return_value = []
        
        # Execute
        result = feedback_service.get_feedback_statistics()
        
        # Verify empty response
        assert result.total_feedback_count == 0
        assert result.acceptance_rate == 0.0
        assert result.rejection_rate == 0.0
        assert result.modification_rate == 0.0
        assert result.feedback_breakdown == {}
    
    def test_get_feedback_statistics_with_data(self, feedback_service, mock_db, sample_issue):
        """Test statistics generation with sample data."""
        # Create sample feedback records
        feedback_records = [
            FeedbackRecord(
                id=1, issue_id="test1", user_id=1, feedback_type="accept",
                created_at=datetime.utcnow(), issue=sample_issue
            ),
            FeedbackRecord(
                id=2, issue_id="test2", user_id=2, feedback_type="accept",
                created_at=datetime.utcnow(), issue=sample_issue
            ),
            FeedbackRecord(
                id=3, issue_id="test3", user_id=3, feedback_type="reject",
                created_at=datetime.utcnow(), issue=sample_issue
            )
        ]
        
        # Setup mock
        mock_db.query.return_value.join.return_value.all.return_value = feedback_records
        
        # Execute
        result = feedback_service.get_feedback_statistics()
        
        # Verify calculations
        assert result.total_feedback_count == 3
        assert result.acceptance_rate == 66.67  # 2/3 * 100
        assert result.rejection_rate == 33.33   # 1/3 * 100
        assert result.modification_rate == 0.0
        assert result.feedback_breakdown == {'accept': 2, 'reject': 1}
    
    def test_get_feedback_statistics_with_date_filter(self, feedback_service, mock_db):
        """Test statistics with date range filter."""
        # Setup date range
        date_range = DateRange(
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        
        # Setup mock
        mock_query = Mock()
        mock_db.query.return_value.join.return_value = mock_query
        mock_query.filter.return_value.all.return_value = []
        
        # Execute
        feedback_service.get_feedback_statistics(date_range=date_range)
        
        # Verify filter was applied
        mock_query.filter.assert_called_once()
    
    def test_validate_feedback_success(self, feedback_service, mock_db):
        """Test successful feedback validation."""
        # Setup existing feedback
        feedback_record = FeedbackRecord(
            id=1, issue_id="test", user_id=1, is_validated=False
        )
        mock_db.query.return_value.filter.return_value.first.return_value = feedback_record
        
        # Setup validation request
        validation_request = FeedbackValidationRequest(
            feedback_id=1,
            is_valid=True,
            validation_score=0.8
        )
        
        # Execute
        result = feedback_service.validate_feedback(1, validation_request)
        
        # Verify
        assert result.is_validated == True
        assert result.validation_score == 0.8
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_validate_feedback_not_found(self, feedback_service, mock_db):
        """Test feedback validation when record doesn't exist."""
        # Setup mock
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        validation_request = FeedbackValidationRequest(
            feedback_id=999,
            is_valid=True
        )
        
        # Execute and verify
        with pytest.raises(FeedbackValidationError, match="Feedback record with ID 999 not found"):
            feedback_service.validate_feedback(999, validation_request)
    
    def test_prepare_training_data_success(self, feedback_service, mock_db, sample_issue):
        """Test training data preparation with sufficient feedback."""
        # Create validated feedback records
        validated_feedback = [
            FeedbackRecord(
                id=1, issue_id="test1", user_id=1, feedback_type="accept",
                feedback_value=1, is_validated=True, validation_score=0.8,
                issue=sample_issue
            ),
            FeedbackRecord(
                id=2, issue_id="test2", user_id=2, feedback_type="reject",
                feedback_value=-1, is_validated=True, validation_score=0.9,
                issue=sample_issue
            )
        ]
        
        # Setup mock
        mock_query = Mock()
        mock_db.query.return_value.filter.return_value.join.return_value = mock_query
        mock_query.all.return_value = validated_feedback
        
        # Execute
        result = feedback_service.prepare_training_data(feedback_threshold=1)
        
        # Verify structure
        assert 'training_data' in result
        assert 'metadata' in result
        assert result['metadata']['total_examples'] == 2
        assert result['metadata']['positive_examples'] == 1
        assert result['metadata']['negative_examples'] == 1
        assert 'unused_variable' in result['training_data']
    
    def test_prepare_training_data_insufficient_feedback(self, feedback_service, mock_db, sample_issue):
        """Test training data preparation with insufficient feedback per pattern."""
        # Create single feedback record (below threshold)
        validated_feedback = [
            FeedbackRecord(
                id=1, issue_id="test1", user_id=1, feedback_type="accept",
                feedback_value=1, is_validated=True, issue=sample_issue
            )
        ]
        
        # Setup mock
        mock_query = Mock()
        mock_db.query.return_value.filter.return_value.join.return_value = mock_query
        mock_query.all.return_value = validated_feedback
        
        # Execute with high threshold
        result = feedback_service.prepare_training_data(feedback_threshold=10)
        
        # Verify no training data due to insufficient feedback
        assert result['training_data'] == {}
        assert result['metadata']['total_examples'] == 0
        assert result['metadata']['pattern_count'] == 0
    
    def test_get_feedback_trends(self, feedback_service, mock_db, sample_issue):
        """Test feedback trends calculation."""
        # Create feedback records over time
        base_date = datetime.utcnow()
        feedback_records = [
            FeedbackRecord(
                id=1, feedback_type="accept", 
                created_at=base_date - timedelta(days=1),
                issue=sample_issue
            ),
            FeedbackRecord(
                id=2, feedback_type="reject",
                created_at=base_date - timedelta(days=1),
                issue=sample_issue
            ),
            FeedbackRecord(
                id=3, feedback_type="accept",
                created_at=base_date - timedelta(days=2),
                issue=sample_issue
            )
        ]
        
        # Setup mock
        mock_query = Mock()
        mock_db.query.return_value.filter.return_value.join.return_value = mock_query
        mock_query.all.return_value = feedback_records
        
        # Execute
        result = feedback_service.get_feedback_trends(days=7)
        
        # Verify structure
        assert 'daily_feedback_counts' in result
        assert 'acceptance_rate_trend' in result
        assert 'total_feedback_period' in result
        assert result['total_feedback_period'] == 3
        assert result['period_days'] == 7
    
    def test_calculate_pattern_feedback_stats(self, feedback_service):
        """Test pattern-specific feedback statistics calculation."""
        # Create mock feedback records with different patterns
        issue1 = Mock()
        issue1.pattern_type = "unused_variable"
        
        issue2 = Mock()
        issue2.pattern_type = "code_complexity"
        
        feedback_records = [
            Mock(feedback_type="accept", issue=issue1),
            Mock(feedback_type="accept", issue=issue1),
            Mock(feedback_type="reject", issue=issue1),
            Mock(feedback_type="accept", issue=issue2),
            Mock(feedback_type="reject", issue=issue2)
        ]
        
        # Execute
        result = feedback_service._calculate_pattern_feedback_stats(feedback_records)
        
        # Verify calculations
        assert "unused_variable" in result
        assert "code_complexity" in result
        assert result["unused_variable"]["acceptance_rate"] == 66.67  # 2/3 * 100
        assert result["unused_variable"]["rejection_rate"] == 33.33   # 1/3 * 100
        assert result["code_complexity"]["acceptance_rate"] == 50.0   # 1/2 * 100
    
    def test_calculate_average_response_time(self, feedback_service):
        """Test average response time calculation."""
        # Create mock feedback with different response times
        base_time = datetime.utcnow()
        
        issue1 = Mock()
        issue1.created_at = base_time - timedelta(hours=2)
        
        issue2 = Mock()
        issue2.created_at = base_time - timedelta(hours=4)
        
        feedback_records = [
            Mock(created_at=base_time, issue=issue1),  # 2 hours response time
            Mock(created_at=base_time, issue=issue2)   # 4 hours response time
        ]
        
        # Execute
        result = feedback_service._calculate_average_response_time(feedback_records)
        
        # Verify average (2 + 4) / 2 = 3 hours
        assert result == 3.0
    
    def test_get_most_common_patterns(self, feedback_service):
        """Test most common patterns identification."""
        # Create mock feedback with pattern frequency
        patterns = ["unused_variable", "unused_variable", "code_complexity", "naming_convention"]
        feedback_records = []
        
        for pattern in patterns:
            issue = Mock()
            issue.pattern_type = pattern
            feedback_records.append(Mock(issue=issue))
        
        # Execute
        result = feedback_service._get_most_common_patterns(feedback_records, limit=2)
        
        # Verify most common patterns (unused_variable should be first with 2 occurrences)
        assert len(result) == 2
        assert result[0] == "unused_variable"
        assert "code_complexity" in result or "naming_convention" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])