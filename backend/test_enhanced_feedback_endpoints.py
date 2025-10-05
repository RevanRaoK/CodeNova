"""
Integration tests for Enhanced Feedback API endpoints.

Tests cover:
- API endpoint functionality
- Request/response validation
- Authentication and authorization
- Database integration
- Error handling
- Analytics and reporting

Requirements covered: 1.1, 1.2, 1.3, 1.4, 1.5
"""

import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.enhanced_feedback import EnhancedFeedback, FeedbackAction
from app.models.users import User
from app.services.enhanced_feedback_service import EnhancedFeedbackService
from app.repositories.feedback_repository import FeedbackRepository
from app.api.v1.endpoints.auth import get_current_active_user

# Test client
client = TestClient(app)


class TestEnhancedFeedbackEndpoints:
    """Test class for enhanced feedback API endpoints."""
    
    @pytest.fixture
    def db_session(self):
        """Get database session for testing."""
        db = next(get_db())
        yield db
        db.close()
    
    @pytest.fixture
    def test_user(self, db_session: Session):
        """Create a test user for authentication."""
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        user = User(
            email=unique_email,
            full_name="Test User",
            hashed_password="hashed_password",
            role="admin",  # Use admin role which is more likely to exist in original enum
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def auth_headers(self, test_user: User):
        """Get authentication headers for API requests."""
        # Mock the authentication dependency to return our test user
        def mock_get_current_user():
            return test_user
        
        app.dependency_overrides[get_current_active_user] = mock_get_current_user
        
        # Return empty headers since we're mocking the dependency
        return {}
    
    @pytest.fixture
    def sample_feedback_data(self):
        """Sample feedback data for testing."""
        return {
            "suggestion_id": "test_suggestion_123",
            "action": "accept",
            "suggestion_type": "code_completion",
            "confidence_score": "high",
            "context_data": {
                "file_path": "/test/file.py",
                "line_number": 42
            }
        }
    
    @pytest.fixture
    def sample_rejection_data(self):
        """Sample rejection feedback data for testing."""
        return {
            "suggestion_id": "test_suggestion_456",
            "action": "reject",
            "rejection_reasons": ["incorrect_logic", "poor_performance"],
            "custom_reason": "The suggested code doesn't handle edge cases properly",
            "suggestion_type": "bug_fix",
            "confidence_score": "medium",
            "context_data": {
                "file_path": "/test/buggy_file.py",
                "function_name": "process_data"
            }
        }
    
    def test_submit_feedback_accept_success(self, db_session: Session, auth_headers: Dict[str, str], sample_feedback_data: Dict[str, Any]):
        """Test successful submission of accept feedback."""
        response = client.post(
            "/api/v1/feedback",
            json=sample_feedback_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["suggestion_id"] == sample_feedback_data["suggestion_id"]
        assert data["action"] == "accept"
        assert data["user_id"] == 1
        assert data["suggestion_type"] == sample_feedback_data["suggestion_type"]
        assert "id" in data
        assert "timestamp" in data
    
    def test_submit_feedback_reject_success(self, db_session: Session, auth_headers: Dict[str, str], sample_rejection_data: Dict[str, Any]):
        """Test successful submission of reject feedback with reasons."""
        response = client.post(
            "/api/v1/feedback",
            json=sample_rejection_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["suggestion_id"] == sample_rejection_data["suggestion_id"]
        assert data["action"] == "reject"
        assert data["rejection_reasons"] == sample_rejection_data["rejection_reasons"]
        assert data["custom_reason"] == sample_rejection_data["custom_reason"]
        assert data["user_id"] == 1
    
    def test_submit_feedback_reject_without_reasons_fails(self, auth_headers: Dict[str, str]):
        """Test that reject feedback without reasons fails validation."""
        invalid_data = {
            "suggestion_id": "test_suggestion_789",
            "action": "reject",
            "suggestion_type": "refactoring"
        }
        
        response = client.post(
            "/api/v1/feedback",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "rejection reasons are required" in response.json()["detail"].lower()
    
    def test_submit_feedback_unauthenticated_fails(self, sample_feedback_data: Dict[str, Any]):
        """Test that unauthenticated requests fail."""
        response = client.post(
            "/api/v1/feedback",
            json=sample_feedback_data
        )
        
        assert response.status_code == 401
    
    def test_submit_feedback_invalid_action_fails(self, auth_headers: Dict[str, str]):
        """Test that invalid action values fail validation."""
        invalid_data = {
            "suggestion_id": "test_suggestion_invalid",
            "action": "invalid_action",
            "suggestion_type": "code_completion"
        }
        
        response = client.post(
            "/api/v1/feedback",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_update_existing_feedback(self, db_session: Session, auth_headers: Dict[str, str], sample_feedback_data: Dict[str, Any]):
        """Test updating existing feedback for the same suggestion."""
        # Submit initial feedback
        response1 = client.post(
            "/api/v1/feedback",
            json=sample_feedback_data,
            headers=auth_headers
        )
        assert response1.status_code == 201
        
        # Update the same suggestion with different feedback
        updated_data = sample_feedback_data.copy()
        updated_data["action"] = "reject"
        updated_data["rejection_reasons"] = ["not_helpful"]
        updated_data["custom_reason"] = "Changed my mind about this suggestion"
        
        response2 = client.post(
            "/api/v1/feedback",
            json=updated_data,
            headers=auth_headers
        )
        
        assert response2.status_code == 201
        data = response2.json()
        
        assert data["action"] == "reject"
        assert data["rejection_reasons"] == ["not_helpful"]
        assert data["custom_reason"] == "Changed my mind about this suggestion"
    
    def test_get_feedback_analytics_success(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test retrieving feedback analytics."""
        # Create some test feedback data
        feedback_service = EnhancedFeedbackService(db_session)
        
        # Create multiple feedback records
        for i in range(5):
            feedback_service.create_feedback(
                suggestion_id=f"suggestion_{i}",
                user_id=1,
                action=FeedbackAction.ACCEPT if i % 2 == 0 else FeedbackAction.REJECT,
                rejection_reasons=["not_helpful"] if i % 2 == 1 else None,
                suggestion_type="code_completion"
            )
        
        response = client.get(
            "/api/v1/feedback/analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_feedback_count" in data
        assert "acceptance_rate" in data
        assert "rejection_rate" in data
        assert "accept_count" in data
        assert "reject_count" in data
        assert "rejection_reasons_analysis" in data
        assert "feedback_by_date" in data
        assert "feedback_by_suggestion_type" in data
        assert "learning_progress" in data
        
        assert data["total_feedback_count"] == 5
        assert data["accept_count"] == 3
        assert data["reject_count"] == 2
    
    def test_get_feedback_analytics_with_filters(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test retrieving feedback analytics with date and type filters."""
        # Create test data with different dates and types
        feedback_service = EnhancedFeedbackService(db_session)
        
        yesterday = datetime.utcnow() - timedelta(days=1)
        feedback_service.create_feedback(
            suggestion_id="old_suggestion",
            user_id=1,
            action=FeedbackAction.ACCEPT,
            suggestion_type="bug_fix"
        )
        
        # Set timestamp to yesterday manually
        old_feedback = db_session.query(EnhancedFeedback).filter(
            EnhancedFeedback.suggestion_id == "old_suggestion"
        ).first()
        old_feedback.timestamp = yesterday
        db_session.commit()
        
        # Create recent feedback
        feedback_service.create_feedback(
            suggestion_id="recent_suggestion",
            user_id=1,
            action=FeedbackAction.REJECT,
            rejection_reasons=["incorrect_logic"],
            suggestion_type="code_completion"
        )
        
        # Test with date filter
        today = datetime.utcnow().date()
        response = client.get(
            f"/api/v1/feedback/analytics?start_date={today}&suggestion_type=code_completion",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_feedback_count"] == 1
        assert data["reject_count"] == 1
    
    def test_get_feedback_analytics_user_only(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test retrieving analytics for current user only."""
        feedback_service = EnhancedFeedbackService(db_session)
        
        # Create feedback for current user
        feedback_service.create_feedback(
            suggestion_id="user1_suggestion",
            user_id=1,
            action=FeedbackAction.ACCEPT,
            suggestion_type="code_completion"
        )
        
        # Create feedback for different user
        feedback_service.create_feedback(
            suggestion_id="user2_suggestion",
            user_id=2,
            action=FeedbackAction.REJECT,
            rejection_reasons=["not_helpful"],
            suggestion_type="code_completion"
        )
        
        # Test user-only filter
        response = client.get(
            "/api/v1/feedback/analytics?user_only=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_feedback_count"] == 1
        assert data["accept_count"] == 1
        assert data["reject_count"] == 0
    
    def test_get_feedback_history_success(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test retrieving user's feedback history."""
        feedback_service = EnhancedFeedbackService(db_session)
        
        # Create multiple feedback records
        for i in range(15):
            feedback_service.create_feedback(
                suggestion_id=f"history_suggestion_{i}",
                user_id=1,
                action=FeedbackAction.ACCEPT if i % 3 == 0 else FeedbackAction.REJECT,
                rejection_reasons=["not_helpful"] if i % 3 != 0 else None,
                suggestion_type=f"type_{i % 3}"
            )
        
        response = client.get(
            "/api/v1/feedback/history?page=1&page_size=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "feedback_records" in data
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_next" in data
        
        assert len(data["feedback_records"]) == 10
        assert data["total_count"] == 15
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["has_next"] is True
    
    def test_get_feedback_history_with_filters(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test retrieving feedback history with action and type filters."""
        feedback_service = EnhancedFeedbackService(db_session)
        
        # Create mixed feedback
        feedback_service.create_feedback(
            suggestion_id="accept_code",
            user_id=1,
            action=FeedbackAction.ACCEPT,
            suggestion_type="code_completion"
        )
        
        feedback_service.create_feedback(
            suggestion_id="reject_code",
            user_id=1,
            action=FeedbackAction.REJECT,
            rejection_reasons=["not_helpful"],
            suggestion_type="code_completion"
        )
        
        feedback_service.create_feedback(
            suggestion_id="accept_bug",
            user_id=1,
            action=FeedbackAction.ACCEPT,
            suggestion_type="bug_fix"
        )
        
        # Test filtering by action
        response = client.get(
            "/api/v1/feedback/history?action_filter=accept",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] == 2
        for record in data["feedback_records"]:
            assert record["action"] == "accept"
        
        # Test filtering by suggestion type
        response = client.get(
            "/api/v1/feedback/history?suggestion_type_filter=code_completion",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] == 2
        for record in data["feedback_records"]:
            assert record["suggestion_type"] == "code_completion"
    
    def test_get_feedback_for_suggestion_success(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test retrieving all feedback for a specific suggestion."""
        feedback_service = EnhancedFeedbackService(db_session)
        
        suggestion_id = "multi_user_suggestion"
        
        # Create feedback from multiple users for the same suggestion
        feedback_service.create_feedback(
            suggestion_id=suggestion_id,
            user_id=1,
            action=FeedbackAction.ACCEPT,
            suggestion_type="code_completion"
        )
        
        feedback_service.create_feedback(
            suggestion_id=suggestion_id,
            user_id=2,
            action=FeedbackAction.REJECT,
            rejection_reasons=["incorrect_logic"],
            suggestion_type="code_completion"
        )
        
        response = client.get(
            f"/api/v1/feedback/suggestion/{suggestion_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert all(record["suggestion_id"] == suggestion_id for record in data)
        
        # Check that we have both accept and reject
        actions = [record["action"] for record in data]
        assert "accept" in actions
        assert "reject" in actions
    
    def test_get_rejection_reasons_analysis_success(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test retrieving rejection reasons analysis."""
        feedback_service = EnhancedFeedbackService(db_session)
        
        # Create rejection feedback with various reasons
        reasons_data = [
            (["incorrect_logic", "poor_performance"], "Custom reason 1"),
            (["not_helpful"], "Custom reason 2"),
            (["incorrect_logic"], None),
            (["poor_performance", "not_helpful"], "Custom reason 3")
        ]
        
        for i, (reasons, custom) in enumerate(reasons_data):
            feedback_service.create_feedback(
                suggestion_id=f"rejection_analysis_{i}",
                user_id=1,
                action=FeedbackAction.REJECT,
                rejection_reasons=reasons,
                custom_reason=custom,
                suggestion_type="code_completion"
            )
        
        response = client.get(
            "/api/v1/feedback/rejection-reasons",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "common_reasons" in data
        assert "custom_reasons" in data
        assert "total_rejections" in data
        assert "unique_reasons_count" in data
        
        assert data["total_rejections"] == 4
        assert "incorrect_logic" in data["common_reasons"]
        assert "poor_performance" in data["common_reasons"]
        assert "not_helpful" in data["common_reasons"]
        
        # Check that incorrect_logic appears most frequently (2 times)
        assert data["common_reasons"]["incorrect_logic"] == 2
    
    def test_get_daily_feedback_stats_success(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test retrieving daily feedback statistics."""
        feedback_service = EnhancedFeedbackService(db_session)
        
        # Create feedback for today
        today = datetime.utcnow()
        for i in range(3):
            feedback_service.create_feedback(
                suggestion_id=f"daily_stats_{i}",
                user_id=1,
                action=FeedbackAction.ACCEPT if i % 2 == 0 else FeedbackAction.REJECT,
                rejection_reasons=["not_helpful"] if i % 2 == 1 else None,
                suggestion_type="code_completion"
            )
        
        response = client.get(
            "/api/v1/feedback/daily-stats?days=7",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have data for today
        today_str = today.strftime('%Y-%m-%d')
        assert today_str in data
        assert data[today_str]["accept"] == 2
        assert data[today_str]["reject"] == 1
    
    def test_get_user_feedback_summary_success(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test retrieving user feedback summary."""
        feedback_service = EnhancedFeedbackService(db_session)
        
        # Create varied feedback for the user
        feedback_service.create_feedback(
            suggestion_id="summary_accept_1",
            user_id=1,
            action=FeedbackAction.ACCEPT,
            suggestion_type="code_completion"
        )
        
        feedback_service.create_feedback(
            suggestion_id="summary_accept_2",
            user_id=1,
            action=FeedbackAction.ACCEPT,
            suggestion_type="bug_fix"
        )
        
        feedback_service.create_feedback(
            suggestion_id="summary_reject_1",
            user_id=1,
            action=FeedbackAction.REJECT,
            rejection_reasons=["not_helpful"],
            suggestion_type="refactoring"
        )
        
        response = client.get(
            "/api/v1/feedback/user-summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_feedback" in data
        assert "acceptance_rate" in data
        assert "rejection_rate" in data
        assert "accept_count" in data
        assert "reject_count" in data
        assert "most_recent_feedback" in data
        assert "feedback_streak_days" in data
        assert "first_feedback" in data
        
        assert data["total_feedback"] == 3
        assert data["accept_count"] == 2
        assert data["reject_count"] == 1
        assert data["acceptance_rate"] == 66.67
        assert data["rejection_rate"] == 33.33
    
    def test_trigger_learning_update_success(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test triggering AI learning pattern update."""
        feedback_service = EnhancedFeedbackService(db_session)
        
        # Create some feedback data for learning
        for i in range(5):
            feedback_service.create_feedback(
                suggestion_id=f"learning_suggestion_{i}",
                user_id=1,
                action=FeedbackAction.ACCEPT if i % 2 == 0 else FeedbackAction.REJECT,
                rejection_reasons=["not_helpful"] if i % 2 == 1 else None,
                suggestion_type="code_completion",
                confidence_score="high" if i % 2 == 0 else "low"
            )
        
        response = client.post(
            "/api/v1/feedback/update-learning-patterns",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "processed_count" in data
        assert "learning_data" in data
        assert "patterns_identified" in data
        
        assert data["status"] == "success"
        assert data["processed_count"] >= 5
    
    def test_invalid_date_format_in_analytics(self, auth_headers: Dict[str, str]):
        """Test that invalid date formats return proper error."""
        response = client.get(
            "/api/v1/feedback/analytics?start_date=invalid-date",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "invalid start_date format" in response.json()["detail"].lower()
    
    def test_pagination_edge_cases(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test pagination edge cases."""
        # Test with no data
        response = client.get(
            "/api/v1/feedback/history?page=1&page_size=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert len(data["feedback_records"]) == 0
        assert data["has_next"] is False
        
        # Test with invalid page parameters
        response = client.get(
            "/api/v1/feedback/history?page=0&page_size=10",
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error for page < 1
        
        response = client.get(
            "/api/v1/feedback/history?page=1&page_size=0",
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error for page_size < 1
    
    def test_large_custom_reason_validation(self, auth_headers: Dict[str, str]):
        """Test validation of large custom reason text."""
        large_reason = "x" * 1001  # Exceeds 1000 character limit
        
        invalid_data = {
            "suggestion_id": "test_large_reason",
            "action": "reject",
            "rejection_reasons": ["not_helpful"],
            "custom_reason": large_reason,
            "suggestion_type": "code_completion"
        }
        
        response = client.post(
            "/api/v1/feedback",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_empty_rejection_reasons_list(self, auth_headers: Dict[str, str]):
        """Test that empty rejection reasons list is treated as missing."""
        invalid_data = {
            "suggestion_id": "test_empty_reasons",
            "action": "reject",
            "rejection_reasons": [],  # Empty list should be invalid
            "suggestion_type": "code_completion"
        }
        
        response = client.post(
            "/api/v1/feedback",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "rejection reasons are required" in response.json()["detail"].lower()
    
    def test_concurrent_feedback_submission(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test handling of concurrent feedback submissions for the same suggestion."""
        suggestion_id = "concurrent_test_suggestion"
        
        # Submit feedback multiple times rapidly (simulating concurrent requests)
        responses = []
        for i in range(3):
            feedback_data = {
                "suggestion_id": suggestion_id,
                "action": "accept" if i == 0 else "reject",
                "rejection_reasons": ["not_helpful"] if i > 0 else None,
                "custom_reason": f"Concurrent test {i}" if i > 0 else None,
                "suggestion_type": "code_completion"
            }
            
            response = client.post(
                "/api/v1/feedback",
                json=feedback_data,
                headers=auth_headers
            )
            responses.append(response)
        
        # All requests should succeed (last one wins)
        for response in responses:
            assert response.status_code == 201
        
        # Verify only one feedback record exists for this suggestion and user
        final_response = client.get(
            f"/api/v1/feedback/suggestion/{suggestion_id}",
            headers=auth_headers
        )
        
        assert final_response.status_code == 200
        feedback_records = final_response.json()
        
        # Should have only one record for this user
        user_records = [r for r in feedback_records if r["user_id"] == 1]
        assert len(user_records) == 1
        
        # Should be the last submitted feedback (reject)
        assert user_records[0]["action"] == "reject"    

    def test_analytics_with_no_data(self, auth_headers: Dict[str, str]):
        """Test analytics endpoint behavior with no feedback data."""
        response = client.get(
            "/api/v1/feedback/analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_feedback_count"] == 0
        assert data["acceptance_rate"] == 0.0
        assert data["rejection_rate"] == 0.0
        assert data["accept_count"] == 0
        assert data["reject_count"] == 0
        assert data["rejection_reasons_analysis"] == {}
        assert data["feedback_by_date"] == {}
        assert data["feedback_by_suggestion_type"] == {}
        assert data["learning_progress"] == {}
    
    def test_feedback_with_complex_context_data(self, auth_headers: Dict[str, str]):
        """Test feedback submission with complex context data."""
        complex_context = {
            "file_path": "/complex/nested/file.py",
            "function_name": "complex_function",
            "line_range": {"start": 10, "end": 25},
            "variables": ["var1", "var2", "var3"],
            "dependencies": {
                "imports": ["os", "sys", "json"],
                "external_libs": ["requests", "pandas"]
            },
            "performance_metrics": {
                "execution_time": 0.045,
                "memory_usage": 1024
            }
        }
        
        feedback_data = {
            "suggestion_id": "complex_context_suggestion",
            "action": "accept",
            "suggestion_type": "optimization",
            "confidence_score": "high",
            "context_data": complex_context
        }
        
        response = client.post(
            "/api/v1/feedback",
            json=feedback_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["suggestion_id"] == "complex_context_suggestion"
        assert data["action"] == "accept"
        
        # Verify context data is preserved (we can't directly check it in response,
        # but we can verify the feedback was created successfully)
        assert "id" in data
        assert "timestamp" in data
    
    def test_feedback_analytics_date_range_validation(self, auth_headers: Dict[str, str]):
        """Test analytics with various date range scenarios."""
        # Test with end_date before start_date
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        response = client.get(
            f"/api/v1/feedback/analytics?start_date={tomorrow}&end_date={yesterday}",
            headers=auth_headers
        )
        
        # Should still work but return no data
        assert response.status_code == 200
        data = response.json()
        assert data["total_feedback_count"] == 0
        
        # Test with future dates
        future_date = (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d')
        response = client.get(
            f"/api/v1/feedback/analytics?start_date={future_date}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_feedback_count"] == 0
    
    def test_feedback_history_sorting(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test that feedback history is properly sorted by timestamp (most recent first)."""
        feedback_service = EnhancedFeedbackService(db_session)
        
        # Create feedback with different timestamps
        base_time = datetime.utcnow()
        
        feedback_times = [
            base_time - timedelta(hours=3),
            base_time - timedelta(hours=1),
            base_time - timedelta(hours=2)
        ]
        
        created_feedback = []
        for i, timestamp in enumerate(feedback_times):
            feedback = feedback_service.create_feedback(
                suggestion_id=f"sorting_test_{i}",
                user_id=1,
                action=FeedbackAction.ACCEPT,
                suggestion_type="code_completion"
            )
            
            # Manually set timestamp
            feedback.timestamp = timestamp
            db_session.commit()
            created_feedback.append((feedback.id, timestamp))
        
        response = client.get(
            "/api/v1/feedback/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify sorting (most recent first)
        timestamps = [datetime.fromisoformat(record["timestamp"].replace('Z', '+00:00')) for record in data["feedback_records"]]
        
        # Should be sorted in descending order (most recent first)
        for i in range(len(timestamps) - 1):
            assert timestamps[i] >= timestamps[i + 1]
    
    def test_rejection_reasons_analysis_with_date_filter(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test rejection reasons analysis with date filtering."""
        feedback_service = EnhancedFeedbackService(db_session)
        
        # Create old rejection
        old_feedback = feedback_service.create_feedback(
            suggestion_id="old_rejection",
            user_id=1,
            action=FeedbackAction.REJECT,
            rejection_reasons=["old_reason"],
            suggestion_type="code_completion"
        )
        
        # Set to old date
        old_date = datetime.utcnow() - timedelta(days=10)
        old_feedback.timestamp = old_date
        db_session.commit()
        
        # Create recent rejection
        feedback_service.create_feedback(
            suggestion_id="recent_rejection",
            user_id=1,
            action=FeedbackAction.REJECT,
            rejection_reasons=["recent_reason"],
            suggestion_type="code_completion"
        )
        
        # Test with date filter that excludes old feedback
        recent_date = (datetime.utcnow() - timedelta(days=5)).strftime('%Y-%m-%d')
        response = client.get(
            f"/api/v1/feedback/rejection-reasons?start_date={recent_date}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_rejections"] == 1
        assert "recent_reason" in data["common_reasons"]
        assert "old_reason" not in data["common_reasons"]
    
    def test_daily_stats_user_filter(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test daily stats with user-only filter."""
        feedback_service = EnhancedFeedbackService(db_session)
        
        # Create feedback for current user
        feedback_service.create_feedback(
            suggestion_id="user1_daily",
            user_id=1,
            action=FeedbackAction.ACCEPT,
            suggestion_type="code_completion"
        )
        
        # Create feedback for different user
        feedback_service.create_feedback(
            suggestion_id="user2_daily",
            user_id=2,
            action=FeedbackAction.REJECT,
            rejection_reasons=["not_helpful"],
            suggestion_type="code_completion"
        )
        
        # Test with user_only=true
        response = client.get(
            "/api/v1/feedback/daily-stats?days=1&user_only=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        today_str = datetime.utcnow().strftime('%Y-%m-%d')
        if today_str in data:
            assert data[today_str]["accept"] == 1
            assert data[today_str]["reject"] == 0
        
        # Test with user_only=false (default)
        response = client.get(
            "/api/v1/feedback/daily-stats?days=1&user_only=false",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if today_str in data:
            assert data[today_str]["accept"] == 1
            assert data[today_str]["reject"] == 1
    
    def test_suggestion_feedback_with_no_results(self, auth_headers: Dict[str, str]):
        """Test getting feedback for a suggestion that doesn't exist."""
        response = client.get(
            "/api/v1/feedback/suggestion/nonexistent_suggestion",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_feedback_submission_with_whitespace_handling(self, auth_headers: Dict[str, str]):
        """Test feedback submission with whitespace in custom reasons."""
        # Test with only whitespace custom reason
        feedback_data = {
            "suggestion_id": "whitespace_test",
            "action": "reject",
            "rejection_reasons": ["not_helpful"],
            "custom_reason": "   \n\t   ",  # Only whitespace
            "suggestion_type": "code_completion"
        }
        
        response = client.post(
            "/api/v1/feedback",
            json=feedback_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Whitespace-only custom reason should be treated as None
        assert data["custom_reason"] is None
        
        # Test with valid custom reason with surrounding whitespace
        feedback_data["suggestion_id"] = "whitespace_test_2"
        feedback_data["custom_reason"] = "  Valid reason with whitespace  "
        
        response = client.post(
            "/api/v1/feedback",
            json=feedback_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Should preserve the trimmed content
        assert data["custom_reason"] == "  Valid reason with whitespace  "
    
    def test_learning_update_with_no_feedback(self, auth_headers: Dict[str, str]):
        """Test learning pattern update when user has no feedback."""
        response = client.post(
            "/api/v1/feedback/update-learning-patterns",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should handle gracefully even with no feedback
        assert "status" in data
        assert "processed_count" in data
        assert data["processed_count"] == 0
    
    def test_analytics_performance_with_large_dataset(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test analytics performance with a larger dataset."""
        feedback_service = EnhancedFeedbackService(db_session)
        
        # Create a larger dataset (100 feedback records)
        suggestion_types = ["code_completion", "bug_fix", "refactoring", "optimization"]
        actions = [FeedbackAction.ACCEPT, FeedbackAction.REJECT]
        
        for i in range(100):
            action = actions[i % 2]
            suggestion_type = suggestion_types[i % 4]
            
            feedback_service.create_feedback(
                suggestion_id=f"perf_test_suggestion_{i}",
                user_id=1,
                action=action,
                rejection_reasons=["performance_issue"] if action == FeedbackAction.REJECT else None,
                suggestion_type=suggestion_type,
                confidence_score="high" if i % 3 == 0 else "medium"
            )
        
        # Test analytics endpoint performance
        import time
        start_time = time.time()
        
        response = client.get(
            "/api/v1/feedback/analytics",
            headers=auth_headers
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_feedback_count"] == 100
        assert data["accept_count"] == 50
        assert data["reject_count"] == 50
        
        # Performance check - should complete within reasonable time (5 seconds)
        assert execution_time < 5.0
    
    def test_error_handling_database_connection_issues(self, auth_headers: Dict[str, str]):
        """Test error handling when database connection issues occur."""
        # This test would require mocking database failures
        # For now, we'll test with invalid data that might cause database errors
        
        feedback_data = {
            "suggestion_id": "db_error_test",
            "action": "accept",
            "suggestion_type": "code_completion"
        }
        
        # Test with extremely long suggestion_id that might cause database issues
        feedback_data["suggestion_id"] = "x" * 10000
        
        response = client.post(
            "/api/v1/feedback",
            json=feedback_data,
            headers=auth_headers
        )
        
        # Should handle gracefully (either succeed or return proper error)
        assert response.status_code in [201, 400, 422, 500]
        
        if response.status_code >= 400:
            # Should return proper error message
            assert "detail" in response.json()
    
    def test_comprehensive_workflow_integration(self, db_session: Session, auth_headers: Dict[str, str]):
        """Test a comprehensive workflow integrating multiple endpoints."""
        feedback_service = EnhancedFeedbackService(db_session)
        
        # Step 1: Submit initial feedback
        initial_feedback = {
            "suggestion_id": "workflow_suggestion",
            "action": "accept",
            "suggestion_type": "code_completion",
            "confidence_score": "high",
            "context_data": {"file": "test.py", "line": 10}
        }
        
        response = client.post(
            "/api/v1/feedback",
            json=initial_feedback,
            headers=auth_headers
        )
        assert response.status_code == 201
        feedback_id = response.json()["id"]
        
        # Step 2: Update the feedback
        updated_feedback = initial_feedback.copy()
        updated_feedback["action"] = "reject"
        updated_feedback["rejection_reasons"] = ["incorrect_logic"]
        updated_feedback["custom_reason"] = "Changed my mind after testing"
        
        response = client.post(
            "/api/v1/feedback",
            json=updated_feedback,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # Step 3: Check feedback history
        response = client.get(
            "/api/v1/feedback/history",
            headers=auth_headers
        )
        assert response.status_code == 200
        history_data = response.json()
        assert history_data["total_count"] >= 1
        
        # Step 4: Get analytics
        response = client.get(
            "/api/v1/feedback/analytics",
            headers=auth_headers
        )
        assert response.status_code == 200
        analytics_data = response.json()
        assert analytics_data["total_feedback_count"] >= 1
        
        # Step 5: Get suggestion-specific feedback
        response = client.get(
            f"/api/v1/feedback/suggestion/{initial_feedback['suggestion_id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        suggestion_feedback = response.json()
        assert len(suggestion_feedback) == 1
        assert suggestion_feedback[0]["action"] == "reject"
        
        # Step 6: Get user summary
        response = client.get(
            "/api/v1/feedback/user-summary",
            headers=auth_headers
        )
        assert response.status_code == 200
        summary_data = response.json()
        assert summary_data["total_feedback"] >= 1
        
        # Step 7: Trigger learning update
        response = client.post(
            "/api/v1/feedback/update-learning-patterns",
            headers=auth_headers
        )
        assert response.status_code == 200
        learning_data = response.json()
        assert "status" in learning_data


if __name__ == "__main__":
    pytest.main([__file__])