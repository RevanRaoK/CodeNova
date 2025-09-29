"""
Integration tests for feedback API endpoints.

Tests cover:
- POST /api/v1/feedback endpoint for submitting feedback
- GET /api/v1/feedback/stats endpoint for statistics
- Authentication and input validation
- Error handling

Requirements covered: 2.1, 2.2, 5.1, 5.2
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime

from app.main import app
from app.schemas.feedback import FeedbackType, ExperienceLevel, ReviewContext
from app.api.v1.endpoints.auth import get_current_active_user, get_current_active_admin

# Create test client
client = TestClient(app)


class TestFeedbackEndpoints:
    """Test suite for feedback API endpoints."""
    
    @pytest.fixture
    def sample_feedback_payload(self):
        """Sample feedback submission payload."""
        return {
            "issue_id": "test_issue_123",
            "feedback_type": "accept",
            "feedback_comment": "Good suggestion",
            "user_experience_level": "intermediate",
            "code_review_context": "team"
        }
    
    def test_submit_feedback_success(self, sample_feedback_payload):
        """Test successful feedback submission."""
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        
        # Mock feedback record
        mock_feedback_record = Mock()
        mock_feedback_record.id = 123
        mock_feedback_record.issue_id = "test_issue_123"
        mock_feedback_record.feedback_type = "accept"
        mock_feedback_record.feedback_value = 1
        mock_feedback_record.created_at = datetime.utcnow()
        mock_feedback_record.is_validated = False
        
        # Override dependencies
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        with patch('app.services.feedback_service.FeedbackService.record_feedback') as mock_record_feedback:
            mock_record_feedback.return_value = mock_feedback_record
            
            # Execute
            response = client.post(
                "/api/v1/feedback",
                json=sample_feedback_payload
            )
            
            # Verify
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == 123
            assert data["issue_id"] == "test_issue_123"
            assert data["feedback_type"] == "accept"
            assert data["feedback_value"] == 1
            assert data["is_validated"] == False
        
        # Clean up
        app.dependency_overrides.clear()
    
    def test_submit_feedback_unauthenticated(self, sample_feedback_payload):
        """Test feedback submission without authentication."""
        response = client.post("/api/v1/feedback", json=sample_feedback_payload)
        assert response.status_code == 401
    
    def test_submit_feedback_invalid_payload(self):
        """Test feedback submission with invalid payload."""
        mock_user = Mock()
        mock_user.id = 1
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        invalid_payload = {
            "issue_id": "",  # Empty issue ID
            "feedback_type": "invalid_type"  # Invalid feedback type
        }
        
        response = client.post(
            "/api/v1/feedback",
            json=invalid_payload
        )
        
        assert response.status_code == 422  # Validation error
        app.dependency_overrides.clear()
    
    def test_submit_feedback_service_error(self, sample_feedback_payload):
        """Test feedback submission when service raises an error."""
        mock_user = Mock()
        mock_user.id = 1
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        with patch('app.services.feedback_service.FeedbackService.record_feedback') as mock_record_feedback:
            from app.services.feedback_service import FeedbackValidationError
            mock_record_feedback.side_effect = FeedbackValidationError("Issue not found")
            
            # Execute
            response = client.post(
                "/api/v1/feedback",
                json=sample_feedback_payload
            )
            
            # Verify
            assert response.status_code == 400
            assert "Issue not found" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_get_feedback_stats_success(self):
        """Test successful feedback statistics retrieval."""
        mock_user = Mock()
        mock_user.id = 1
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        from app.schemas.feedback import FeedbackStatsResponse
        mock_stats = FeedbackStatsResponse(
            total_feedback_count=100,
            acceptance_rate=75.0,
            rejection_rate=20.0,
            modification_rate=5.0,
            feedback_breakdown={"accept": 75, "reject": 20, "modify": 5},
            feedback_by_date={"2024-01-15": 50, "2024-01-14": 50},
            feedback_by_experience={"intermediate": 60, "expert": 40},
            pattern_feedback_stats={},
            average_response_time_hours=2.5,
            most_common_patterns=["unused_variable", "code_complexity"]
        )
        
        with patch('app.services.feedback_service.FeedbackService.get_feedback_statistics') as mock_get_stats:
            mock_get_stats.return_value = mock_stats
            
            # Execute
            response = client.get("/api/v1/feedback/stats")
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["total_feedback_count"] == 100
            assert data["acceptance_rate"] == 75.0
            assert data["rejection_rate"] == 20.0
            assert data["modification_rate"] == 5.0
            assert len(data["most_common_patterns"]) == 2
        
        app.dependency_overrides.clear()
    
    def test_get_feedback_stats_with_filters(self):
        """Test feedback statistics with query parameters."""
        mock_user = Mock()
        mock_user.id = 1
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        from app.schemas.feedback import FeedbackStatsResponse
        mock_stats = FeedbackStatsResponse(
            total_feedback_count=50,
            acceptance_rate=80.0,
            rejection_rate=15.0,
            modification_rate=5.0,
            feedback_breakdown={"accept": 40, "reject": 7, "modify": 3},
            feedback_by_date={},
            feedback_by_experience={},
            pattern_feedback_stats={},
            average_response_time_hours=1.8,
            most_common_patterns=["unused_variable"]
        )
        
        with patch('app.services.feedback_service.FeedbackService.get_feedback_statistics') as mock_get_stats:
            mock_get_stats.return_value = mock_stats
            
            # Execute with query parameters
            response = client.get(
                "/api/v1/feedback/stats?start_date=2024-01-01&end_date=2024-01-31&pattern_type=unused_variable&user_experience_level=expert"
            )
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["total_feedback_count"] == 50
            
            # Verify service was called with filters
            mock_get_stats.assert_called_once()
            call_args = mock_get_stats.call_args[1]
            assert call_args["pattern_type"] == "unused_variable"
            assert call_args["user_experience_level"] == "expert"
            assert call_args["date_range"] is not None
        
        app.dependency_overrides.clear()
    
    def test_get_feedback_stats_unauthenticated(self):
        """Test feedback statistics without authentication."""
        response = client.get("/api/v1/feedback/stats")
        assert response.status_code == 401
    
    def test_get_feedback_stats_invalid_date_format(self):
        """Test feedback statistics with invalid date format."""
        mock_user = Mock()
        mock_user.id = 1
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        response = client.get(
            "/api/v1/feedback/stats?start_date=invalid-date&end_date=2024-01-31"
        )
        
        assert response.status_code == 400
        assert "Invalid date format" in response.json()["detail"]
        app.dependency_overrides.clear()
    
    def test_get_user_feedback_history(self):
        """Test user feedback history retrieval."""
        mock_user = Mock()
        mock_user.id = 1
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        mock_feedback_records = [
            Mock(
                id=1, issue_id="issue1", feedback_type="accept",
                feedback_value=1, created_at=datetime.utcnow(), is_validated=False
            ),
            Mock(
                id=2, issue_id="issue2", feedback_type="reject",
                feedback_value=-1, created_at=datetime.utcnow(), is_validated=True
            )
        ]
        
        with patch('app.services.feedback_service.FeedbackService.get_user_feedback_history') as mock_get_history:
            mock_get_history.return_value = (mock_feedback_records, 25)
            
            # Execute
            response = client.get("/api/v1/feedback/history?page=2&page_size=10")
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 25
            assert data["page"] == 2
            assert data["page_size"] == 10
            assert data["has_next"] == True  # (2 * 10) < 25
            assert len(data["feedback_records"]) == 2
            
            # Verify service was called with correct parameters
            mock_get_history.assert_called_once_with(user_id=1, page=2, page_size=10)
        
        app.dependency_overrides.clear()
    
    def test_get_feedback_for_issue(self):
        """Test retrieving feedback for a specific issue."""
        mock_user = Mock()
        mock_user.id = 1
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        mock_feedback_records = [
            Mock(
                id=1, issue_id="test_issue", feedback_type="accept",
                feedback_value=1, created_at=datetime.utcnow(), is_validated=False
            )
        ]
        
        with patch('app.services.feedback_service.FeedbackService.get_feedback_for_issue') as mock_get_feedback:
            mock_get_feedback.return_value = mock_feedback_records
            
            # Execute
            response = client.get("/api/v1/feedback/test_issue")
            
            # Verify
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["issue_id"] == "test_issue"
            assert data[0]["feedback_type"] == "accept"
            
            # Verify service was called with correct issue ID
            mock_get_feedback.assert_called_once_with("test_issue")
        
        app.dependency_overrides.clear()
    
    def test_submit_bulk_feedback(self):
        """Test bulk feedback submission."""
        mock_user = Mock()
        mock_user.id = 1
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        mock_feedback_record = Mock()
        mock_feedback_record.id = 123
        mock_feedback_record.issue_id = "test_issue"
        
        # Prepare bulk request
        bulk_payload = {
            "feedback_submissions": [
                {
                    "issue_id": "issue1",
                    "feedback_type": "accept",
                    "feedback_comment": "Good"
                },
                {
                    "issue_id": "issue2",
                    "feedback_type": "reject",
                    "feedback_comment": "Not helpful"
                }
            ]
        }
        
        with patch('app.services.feedback_service.FeedbackService.record_feedback') as mock_record_feedback:
            mock_record_feedback.return_value = mock_feedback_record
            
            # Execute
            response = client.post(
                "/api/v1/feedback/bulk",
                json=bulk_payload
            )
            
            # Verify
            assert response.status_code == 201
            data = response.json()
            assert data["total_submitted"] == 2
            assert data["successful"] == 2
            assert data["failed"] == 0
            assert len(data["results"]) == 2
            
            # Verify service was called twice
            assert mock_record_feedback.call_count == 2
        
        app.dependency_overrides.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])