"""
Unit tests for Enhanced Feedback Service.

Tests cover:
- Feedback creation and validation
- Analytics generation
- Learning pattern updates
- Error handling

Requirements covered: 1.1, 1.2, 1.3, 1.4, 1.5
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
import uuid

from app.services.enhanced_feedback_service import EnhancedFeedbackService
from app.models.enhanced_feedback import EnhancedFeedback, FeedbackAction
from app.models.users import User


class TestEnhancedFeedbackService:
    """Test cases for EnhancedFeedbackService."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def feedback_service(self, mock_db):
        """Create feedback service instance."""
        return EnhancedFeedbackService(mock_db)
    
    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing."""
        return User(id=1, email="test@example.com")
    
    @pytest.fixture
    def sample_feedback_data(self):
        """Sample feedback data for testing."""
        return {
            'suggestion_id': 'test-suggestion-123',
            'user_id': 1,
            'action': FeedbackAction.ACCEPT,
            'suggestion_type': 'code_improvement',
            'confidence_score': 'high',
            'context_data': {'file_type': 'python', 'line_count': 50}
        }
    
    def test_create_feedback_accept(self, feedback_service, mock_db, sample_feedback_data):
        """Test creating accept feedback."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Execute
        result = feedback_service.create_feedback(**sample_feedback_data)
        
        # Verify
        assert result.suggestion_id == sample_feedback_data['suggestion_id']
        assert result.user_id == sample_feedback_data['user_id']
        assert result.action == FeedbackAction.ACCEPT
        assert result.suggestion_type == sample_feedback_data['suggestion_type']
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_create_feedback_reject_with_reasons(self, feedback_service, mock_db):
        """Test creating reject feedback with rejection reasons."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        feedback_data = {
            'suggestion_id': 'test-suggestion-123',
            'user_id': 1,
            'action': FeedbackAction.REJECT,
            'rejection_reasons': ['incorrect', 'not_applicable'],
            'custom_reason': 'The suggestion does not fit our coding standards'
        }
        
        # Execute
        result = feedback_service.create_feedback(**feedback_data)
        
        # Verify
        assert result.action == FeedbackAction.REJECT
        assert result.rejection_reasons == ['incorrect', 'not_applicable']
        assert result.custom_reason == 'The suggestion does not fit our coding standards'
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_create_feedback_reject_without_reasons_raises_error(self, feedback_service, mock_db):
        """Test that rejecting without reasons raises an error."""
        feedback_data = {
            'suggestion_id': 'test-suggestion-123',
            'user_id': 1,
            'action': FeedbackAction.REJECT,
            'rejection_reasons': None
        }
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Rejection reasons are required"):
            feedback_service.create_feedback(**feedback_data)
    
    def test_update_existing_feedback(self, feedback_service, mock_db):
        """Test updating existing feedback record."""
        # Setup existing feedback
        existing_feedback = EnhancedFeedback(
            id=str(uuid.uuid4()),
            suggestion_id='test-suggestion-123',
            user_id=1,
            action=FeedbackAction.ACCEPT,
            timestamp=datetime.utcnow()
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_feedback
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Execute
        result = feedback_service.create_feedback(
            suggestion_id='test-suggestion-123',
            user_id=1,
            action=FeedbackAction.REJECT,
            rejection_reasons=['changed_mind']
        )
        
        # Verify
        assert result.action == FeedbackAction.REJECT
        assert result.rejection_reasons == ['changed_mind']
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_get_feedback_analytics_empty_data(self, feedback_service, mock_db):
        """Test analytics with no feedback data."""
        # Setup
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Execute
        result = feedback_service.get_feedback_analytics()
        
        # Verify
        assert result['total_feedback_count'] == 0
        assert result['acceptance_rate'] == 0.0
        assert result['rejection_rate'] == 0.0
        assert result['feedback_by_date'] == {}
    
    def test_get_feedback_analytics_with_data(self, feedback_service, mock_db):
        """Test analytics with sample feedback data."""
        # Setup sample feedback records
        feedback_records = [
            Mock(
                action=FeedbackAction.ACCEPT,
                timestamp=datetime(2024, 1, 15, 10, 0, 0),
                suggestion_type='code_improvement',
                rejection_reasons=None,
                custom_reason=None
            ),
            Mock(
                action=FeedbackAction.REJECT,
                timestamp=datetime(2024, 1, 15, 11, 0, 0),
                suggestion_type='code_improvement',
                rejection_reasons=['incorrect'],
                custom_reason='Not suitable'
            ),
            Mock(
                action=FeedbackAction.ACCEPT,
                timestamp=datetime(2024, 1, 16, 9, 0, 0),
                suggestion_type='bug_fix',
                rejection_reasons=None,
                custom_reason=None
            )
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = feedback_records
        
        # Execute
        result = feedback_service.get_feedback_analytics()
        
        # Verify
        assert result['total_feedback_count'] == 3
        assert result['acceptance_rate'] == 66.67  # 2 out of 3
        assert result['rejection_rate'] == 33.33   # 1 out of 3
        assert result['accept_count'] == 2
        assert result['reject_count'] == 1
        
        # Check rejection reasons analysis
        rejection_analysis = result['rejection_reasons_analysis']
        assert rejection_analysis['total_rejections'] == 1
        assert 'incorrect' in rejection_analysis['common_reasons']
        
        # Check feedback by date
        feedback_by_date = result['feedback_by_date']
        assert '2024-01-15' in feedback_by_date
        assert '2024-01-16' in feedback_by_date
        assert feedback_by_date['2024-01-15']['accept'] == 1
        assert feedback_by_date['2024-01-15']['reject'] == 1
        assert feedback_by_date['2024-01-16']['accept'] == 1
    
    def test_get_user_feedback_history(self, feedback_service, mock_db):
        """Test retrieving user feedback history."""
        # Setup
        mock_feedback_records = [
            Mock(id='1', suggestion_id='s1', timestamp=datetime.utcnow()),
            Mock(id='2', suggestion_id='s2', timestamp=datetime.utcnow() - timedelta(hours=1))
        ]
        
        mock_query = Mock()
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_feedback_records
        
        mock_db.query.return_value.filter.return_value = mock_query
        
        # Execute
        records, total_count = feedback_service.get_user_feedback_history(user_id=1, page=1, page_size=10)
        
        # Verify
        assert len(records) == 2
        assert total_count == 2
        assert records[0].id == '1'
        assert records[1].id == '2'
    
    def test_update_ai_learning_patterns(self, feedback_service, mock_db):
        """Test updating AI learning patterns."""
        # Setup recent feedback
        recent_feedback = [
            Mock(
                action=FeedbackAction.REJECT,
                suggestion_id='s1',
                suggestion_type='code_improvement',
                rejection_reasons=['incorrect'],
                custom_reason=None,
                confidence_score='high',
                context_data={},
                timestamp=datetime.utcnow()
            ),
            Mock(
                action=FeedbackAction.ACCEPT,
                suggestion_id='s2',
                suggestion_type='bug_fix',
                rejection_reasons=None,
                custom_reason=None,
                confidence_score='medium',
                context_data={},
                timestamp=datetime.utcnow()
            )
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = recent_feedback
        
        # Execute
        feedback_data = {'test': 'data'}
        result = feedback_service.update_ai_learning_patterns(feedback_data)
        
        # Verify
        assert result['status'] == 'success'
        assert result['processed_count'] == 2
        assert 'learning_data' in result
        assert 'patterns_identified' in result
        
        learning_data = result['learning_data']
        assert 'rejection_patterns' in learning_data
        assert 'acceptance_patterns' in learning_data
        assert 'confidence_adjustments' in learning_data
    
    def test_update_ai_learning_patterns_no_data(self, feedback_service, mock_db):
        """Test learning pattern update with no recent feedback."""
        # Setup
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Execute
        result = feedback_service.update_ai_learning_patterns({})
        
        # Verify
        assert result['status'] == 'no_recent_feedback'
        assert result['processed_count'] == 0
    
    def test_analyze_rejection_reasons(self, feedback_service):
        """Test rejection reasons analysis."""
        # Setup feedback records with various rejection reasons
        feedback_records = [
            Mock(
                action=FeedbackAction.REJECT,
                rejection_reasons=['incorrect', 'not_applicable'],
                custom_reason='Custom reason 1',
                timestamp=datetime.utcnow(),
                suggestion_type='type1'
            ),
            Mock(
                action=FeedbackAction.REJECT,
                rejection_reasons=['incorrect'],
                custom_reason='Custom reason 2',
                timestamp=datetime.utcnow(),
                suggestion_type='type2'
            ),
            Mock(
                action=FeedbackAction.ACCEPT,
                rejection_reasons=None,
                custom_reason=None,
                timestamp=datetime.utcnow(),
                suggestion_type='type1'
            )
        ]
        
        # Execute
        result = feedback_service._analyze_rejection_reasons(feedback_records)
        
        # Verify
        assert result['total_rejections'] == 2
        assert result['common_reasons']['incorrect'] == 2
        assert result['common_reasons']['not_applicable'] == 1
        assert len(result['custom_reasons']) == 2
        assert result['reasons_distribution']['incorrect'] == 100.0  # 2 out of 2 rejections
        assert result['reasons_distribution']['not_applicable'] == 50.0  # 1 out of 2 rejections
    
    def test_calculate_learning_progress_insufficient_data(self, feedback_service):
        """Test learning progress calculation with insufficient data."""
        # Setup with less than 10 records
        feedback_records = [Mock() for _ in range(5)]
        
        # Execute
        result = feedback_service._calculate_learning_progress(feedback_records)
        
        # Verify
        assert result['insufficient_data'] is True
    
    def test_calculate_learning_progress_with_data(self, feedback_service):
        """Test learning progress calculation with sufficient data."""
        # Setup with 15 records over 3 weeks
        base_date = datetime(2024, 1, 1)
        feedback_records = []
        
        # Week 1: 5 records, 3 accepts (60% acceptance)
        for i in range(5):
            action = FeedbackAction.ACCEPT if i < 3 else FeedbackAction.REJECT
            feedback_records.append(Mock(
                action=action,
                timestamp=base_date + timedelta(days=i)
            ))
        
        # Week 2: 5 records, 4 accepts (80% acceptance)
        for i in range(5):
            action = FeedbackAction.ACCEPT if i < 4 else FeedbackAction.REJECT
            feedback_records.append(Mock(
                action=action,
                timestamp=base_date + timedelta(days=7 + i)
            ))
        
        # Week 3: 5 records, 5 accepts (100% acceptance)
        for i in range(5):
            feedback_records.append(Mock(
                action=FeedbackAction.ACCEPT,
                timestamp=base_date + timedelta(days=14 + i)
            ))
        
        # Execute
        result = feedback_service._calculate_learning_progress(feedback_records)
        
        # Verify
        assert 'insufficient_data' not in result
        assert result['trend'] == 'improving'
        assert len(result['weekly_acceptance_rates']) == 3
        assert result['weekly_acceptance_rates'][0]['acceptance_rate'] == 60.0
        assert result['weekly_acceptance_rates'][1]['acceptance_rate'] == 80.0
        assert result['weekly_acceptance_rates'][2]['acceptance_rate'] == 100.0
        assert result['latest_acceptance_rate'] == 100.0
    
    def test_suggest_confidence_adjustment(self, feedback_service):
        """Test confidence adjustment suggestions."""
        # Test high confidence with low accuracy
        result = feedback_service._suggest_confidence_adjustment('high', 70.0)
        assert result == 'lower_confidence'
        
        # Test low confidence with high accuracy
        result = feedback_service._suggest_confidence_adjustment('low', 95.0)
        assert result == 'raise_confidence'
        
        # Test medium confidence with appropriate accuracy
        result = feedback_service._suggest_confidence_adjustment('medium', 75.0)
        assert result == 'maintain_confidence'
        
        # Test medium confidence with low accuracy
        result = feedback_service._suggest_confidence_adjustment('medium', 50.0)
        assert result == 'lower_confidence'
        
        # Test medium confidence with very high accuracy
        result = feedback_service._suggest_confidence_adjustment('medium', 98.0)
        assert result == 'raise_confidence'


class TestFeedbackServiceIntegration:
    """Integration tests for feedback service with database."""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session."""
        # This would be implemented with a test database
        # For now, we'll mock it
        return Mock(spec=Session)
    
    def test_end_to_end_feedback_workflow(self, db_session):
        """Test complete feedback workflow from creation to analytics."""
        # This would test the complete workflow with a real database
        # Including creating feedback, retrieving it, and generating analytics
        pass
    
    def test_concurrent_feedback_creation(self, db_session):
        """Test handling concurrent feedback creation for the same suggestion."""
        # This would test race conditions and database constraints
        pass
    
    def test_large_dataset_analytics(self, db_session):
        """Test analytics performance with large datasets."""
        # This would test performance with thousands of feedback records
        pass


if __name__ == '__main__':
    pytest.main([__file__])