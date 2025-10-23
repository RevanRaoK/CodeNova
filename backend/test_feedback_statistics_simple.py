"""
Simple unit tests for feedback statistics functionality.

Tests the core feedback statistics calculation without complex database setup.
"""

import pytest
from unittest.mock import Mock, patch
from app.services.admin_service import AdminService
from app.models.feedback import FeedbackRecord


def test_feedback_statistics_calculation_logic():
    """Test the core logic of feedback statistics calculation."""
    
    # Mock database session
    mock_db = Mock()
    
    # Create admin service
    admin_service = AdminService(mock_db)
    
    # Mock the query results for empty case
    mock_query = Mock()
    mock_query.count.return_value = 0
    mock_db.query.return_value = mock_query
    
    # Test empty case
    stats = admin_service.get_feedback_statistics()
    
    assert stats["total_feedback_count"] == 0
    assert stats["acceptance_rate"] == 0.0
    assert stats["rejection_rate"] == 0.0
    assert stats["modification_rate"] == 0.0
    assert stats["ignore_rate"] == 0.0
    
    # Verify the breakdown
    breakdown = stats["feedback_breakdown"]
    assert breakdown["accept"] == 0
    assert breakdown["reject"] == 0
    assert breakdown["modify"] == 0
    assert breakdown["ignore"] == 0


def test_feedback_statistics_with_mock_data():
    """Test feedback statistics with mocked data."""
    
    # Mock database session
    mock_db = Mock()
    
    # Create admin service
    admin_service = AdminService(mock_db)
    
    # Mock the query chain for total count
    mock_query = Mock()
    mock_query.count.return_value = 10  # Total feedback count
    mock_db.query.return_value = mock_query
    
    # Mock the filter chains for each feedback type
    def mock_filter_side_effect(condition):
        mock_filtered_query = Mock()
        # Simulate different counts based on feedback type
        if "accept" in str(condition):
            mock_filtered_query.count.return_value = 7
        elif "reject" in str(condition):
            mock_filtered_query.count.return_value = 2
        elif "modify" in str(condition):
            mock_filtered_query.count.return_value = 1
        else:  # ignore
            mock_filtered_query.count.return_value = 0
        return mock_filtered_query
    
    mock_query.filter.side_effect = mock_filter_side_effect
    
    # Test with mocked data
    stats = admin_service.get_feedback_statistics()
    
    assert stats["total_feedback_count"] == 10
    assert stats["acceptance_rate"] == 70.0  # 7/10 * 100
    assert stats["rejection_rate"] == 20.0   # 2/10 * 100
    assert stats["modification_rate"] == 10.0 # 1/10 * 100
    assert stats["ignore_rate"] == 0.0       # 0/10 * 100
    
    # Verify the breakdown
    breakdown = stats["feedback_breakdown"]
    assert breakdown["accept"] == 7
    assert breakdown["reject"] == 2
    assert breakdown["modify"] == 1
    assert breakdown["ignore"] == 0


def test_feedback_statistics_team_filtering():
    """Test that team filtering is applied correctly."""
    
    # Mock database session
    mock_db = Mock()
    
    # Create admin service
    admin_service = AdminService(mock_db)
    
    # Mock the query chain
    mock_query = Mock()
    mock_query.count.return_value = 5  # Filtered count
    mock_db.query.return_value = mock_query
    
    # Mock the filter method to track calls
    mock_filtered_query = Mock()
    mock_filtered_query.count.return_value = 0
    mock_query.filter.return_value = mock_filtered_query
    
    # Test with team filtering
    team_id = "test-team-id"
    stats = admin_service.get_feedback_statistics(team_id=team_id)
    
    # Verify that filter was called (indicating team filtering was applied)
    assert mock_query.filter.called
    assert stats["total_feedback_count"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])