"""
Integration test for the feedback statistics API endpoint.

Tests the actual endpoint functionality with a real database.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from app.main import app
from app.core.database import get_db, Base
from app.models.users import User, UserRole
from app.models.team import Team
from app.models.feedback import FeedbackRecord, Issue
from app.models.analysis import DirectAnalysis
from app.core.security import create_access_token
import uuid
from datetime import datetime


# Create a temporary SQLite database for testing
@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database."""
    # Create temporary file
    db_fd, db_path = tempfile.mkstemp()
    
    # Create engine with SQLite
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(test_db):
    """Create test client with database override."""
    def override_get_db():
        try:
            db = test_db()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(test_db):
    """Create an admin user."""
    db = test_db()
    try:
        user = User(
            email="admin@test.com",
            hashed_password="hashed_password",
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture
def test_team(test_db, admin_user):
    """Create a test team."""
    db = test_db()
    try:
        team = Team(
            id=str(uuid.uuid4()),
            name="Test Team",
            admin_id=admin_user.id
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        return team
    finally:
        db.close()


@pytest.fixture
def sample_feedback_data(test_db, admin_user, test_team):
    """Create sample feedback data for testing."""
    db = test_db()
    try:
        # Create a user in the team
        user = User(
            email="user@test.com",
            hashed_password="hashed_password",
            full_name="Test User",
            role=UserRole.USER,
            team_id=test_team.id,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create an analysis
        analysis = DirectAnalysis(
            id=str(uuid.uuid4()),
            user_id=user.id,
            code_content="def test(): pass",
            language="python",
            status="completed",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        # Create an issue
        issue = Issue(
            id="a" * 64,  # 64-character hash
            analysis_id=analysis.id,
            pattern_type="unused_variable",
            severity="medium",
            location={"line": 10, "column": 5},
            suggestion_text="Remove unused variable",
            code_context="def test(): unused_var = 1",
            status="active"
        )
        db.add(issue)
        db.commit()
        db.refresh(issue)
        
        # Create feedback records
        feedback_types = ["accept", "reject", "modify", "accept", "accept"]
        for i, feedback_type in enumerate(feedback_types):
            feedback_value = 1 if feedback_type == "accept" else (-1 if feedback_type == "reject" else 0)
            
            feedback = FeedbackRecord(
                issue_id=issue.id,
                user_id=user.id,
                feedback_type=feedback_type,
                feedback_value=feedback_value,
                feedback_comment=f"Test feedback {i}",
                created_at=datetime.utcnow()
            )
            db.add(feedback)
        
        db.commit()
        return {"user": user, "team": test_team, "feedback_count": len(feedback_types)}
    finally:
        db.close()


class TestFeedbackStatisticsEndpoint:
    """Test the feedback statistics API endpoint."""
    
    def test_get_feedback_statistics_success(self, client, admin_user, sample_feedback_data):
        """Test successful feedback statistics retrieval."""
        # Create access token
        token = create_access_token(data={"sub": str(admin_user.id), "email": admin_user.email, "role": admin_user.role.value})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make request
        response = client.get("/api/v1/admin/analytics/feedback-stats", headers=headers)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "total_feedback_count" in data
        assert "acceptance_rate" in data
        assert "rejection_rate" in data
        assert "modification_rate" in data
        assert "ignore_rate" in data
        assert "feedback_breakdown" in data
        
        # Verify data makes sense
        assert data["total_feedback_count"] == 5
        assert data["acceptance_rate"] == 60.0  # 3 accepts out of 5
        assert data["rejection_rate"] == 20.0   # 1 reject out of 5
        assert data["modification_rate"] == 20.0 # 1 modify out of 5
        assert data["ignore_rate"] == 0.0       # 0 ignores out of 5
        
        # Check breakdown
        breakdown = data["feedback_breakdown"]
        assert breakdown["accept"] == 3
        assert breakdown["reject"] == 1
        assert breakdown["modify"] == 1
        assert breakdown["ignore"] == 0
    
    def test_get_feedback_statistics_with_team_filter(self, client, admin_user, sample_feedback_data):
        """Test feedback statistics with team filtering."""
        token = create_access_token(data={"sub": str(admin_user.id), "email": admin_user.email, "role": admin_user.role.value})
        headers = {"Authorization": f"Bearer {token}"}
        
        team_id = sample_feedback_data["team"].id
        response = client.get(
            f"/api/v1/admin/analytics/feedback-stats?team_id={team_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have same results since all feedback is from users in this team
        assert data["total_feedback_count"] == 5
        assert data["acceptance_rate"] == 60.0
    
    def test_get_feedback_statistics_empty_data(self, client, admin_user):
        """Test feedback statistics with no data."""
        token = create_access_token(data={"sub": str(admin_user.id), "email": admin_user.email, "role": admin_user.role.value})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/admin/analytics/feedback-stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_feedback_count"] == 0
        assert data["acceptance_rate"] == 0.0
        assert data["rejection_rate"] == 0.0
        assert data["modification_rate"] == 0.0
        assert data["ignore_rate"] == 0.0
        
        breakdown = data["feedback_breakdown"]
        assert breakdown["accept"] == 0
        assert breakdown["reject"] == 0
        assert breakdown["modify"] == 0
        assert breakdown["ignore"] == 0
    
    def test_get_feedback_statistics_nonexistent_team(self, client, admin_user):
        """Test feedback statistics with nonexistent team."""
        token = create_access_token(data={"sub": str(admin_user.id), "email": admin_user.email, "role": admin_user.role.value})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get(
            "/api/v1/admin/analytics/feedback-stats?team_id=nonexistent-team",
            headers=headers
        )
        
        assert response.status_code == 404
        assert "Team not found" in response.json()["detail"]
    
    def test_get_feedback_statistics_unauthorized(self, client):
        """Test feedback statistics without authentication."""
        response = client.get("/api/v1/admin/analytics/feedback-stats")
        
        # Should return 403 (not authenticated) based on the security setup
        assert response.status_code == 403
    
    def test_get_feedback_statistics_non_admin(self, client, test_db):
        """Test feedback statistics with non-admin user."""
        # Create a regular user
        db = test_db()
        try:
            user = User(
                email="user@test.com",
                hashed_password="hashed_password",
                full_name="Regular User",
                role=UserRole.USER,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role.value})
            headers = {"Authorization": f"Bearer {token}"}
            
            response = client.get("/api/v1/admin/analytics/feedback-stats", headers=headers)
            
            assert response.status_code == 403
        finally:
            db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])