import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
import uuid
from datetime import datetime
from unittest.mock import patch

from app.main import app
from app.core.database import Base, get_db
from app.models.users import User, UserRole
from app.models.team import Team
from app.models.feedback import FeedbackRecord, Issue
from app.models.analysis import DirectAnalysis
from app.services.admin_service import AdminService
from app.core.security import create_access_token


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_admin.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = Session(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class TestAdminWorkflowIntegration:
    """
    Integration tests for admin workflow functionality.
    
    Requirements covered: 3.1, 3.2, 3.3, 3.4, 3.5
    """
    
    @pytest.fixture(scope="class", autouse=True)
    def setup_database(self):
        """Set up test database."""
        Base.metadata.create_all(bind=engine)
        yield
        Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture
    def db_session(self):
        """Get database session for tests."""
        db = TestingSessionLocal
        try:
            yield db
        finally:
            # Clean up after each test
            db.query(FeedbackRecord).delete()
            db.query(DirectAnalysis).delete()
            db.query(User).delete()
            db.query(Team).delete()
            db.commit()
            db.close()
    
    @pytest.fixture
    def client(self):
        """Get test client."""
        return TestClient(app)
    
    @pytest.fixture
    def admin_user(self, db_session):
        """Create admin user for testing."""
        user = User(
            email="admin@test.com",
            full_name="Admin User",
            hashed_password="hashed_password",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            preferences={}
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def team_lead_user(self, db_session):
        """Create team lead user for testing."""
        user = User(
            email="teamlead@test.com",
            full_name="Team Lead User",
            hashed_password="hashed_password",
            role=UserRole.TEAM_LEAD,
            is_active=True,
            is_verified=True,
            team_id="team-1",
            preferences={}
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def regular_users(self, db_session):
        """Create regular users for testing."""
        users = []
        for i in range(3):
            user = User(
                email=f"user{i}@test.com",
                full_name=f"User {i}",
                hashed_password="hashed_password",
                role=UserRole.USER,
                is_active=True,
                is_verified=True,
                team_id="team-1" if i < 2 else "team-2",
                preferences={}
            )
            db_session.add(user)
            users.append(user)
        
        db_session.commit()
        for user in users:
            db_session.refresh(user)
        return users
    
    @pytest.fixture
    def test_team(self, db_session, admin_user):
        """Create test team."""
        team = Team(
            id="team-1",
            name="Test Team",
            admin_id=admin_user.id,
            settings={"test": True}
        )
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)
        return team
    
    @pytest.fixture
    def admin_token(self, admin_user):
        """Create JWT token for admin user."""
        return create_access_token(
            data={"sub": str(admin_user.id), "email": admin_user.email, "role": admin_user.role.value}
        )
    
    @pytest.fixture
    def team_lead_token(self, team_lead_user):
        """Create JWT token for team lead user."""
        return create_access_token(
            data={"sub": str(team_lead_user.id), "email": team_lead_user.email, "role": team_lead_user.role.value}
        )
    
    def test_complete_user_management_workflow(self, client, db_session, admin_user, admin_token):
        """
        Test complete user management workflow.
        
        Requirements: 3.1, 3.2, 3.3 - Admin dashboard, user management, role assignment
        """
        global current_test_user
        current_test_user = admin_user
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 1. Create a new team
        team_data = {"name": "Development Team", "settings": {"department": "engineering"}}
        response = client.post("/api/v1/admin/teams", json=team_data, headers=headers)
        assert response.status_code == 200
        team = response.json()
        team_id = team["id"]
        
        # 2. Create a new user (simulate user registration)
        new_user = User(
            email="newuser@test.com",
            full_name="New User",
            hashed_password="hashed_password",
            role=UserRole.GUEST,
            is_active=True,
            is_verified=False,
            preferences={}
        )
        db_session.add(new_user)
        db_session.commit()
        db_session.refresh(new_user)
        
        # 3. Admin views all users
        response = client.get("/api/v1/admin/users", headers=headers)
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 2  # admin + new user
        
        # 4. Admin updates user role
        role_update = {"role": "developer"}
        response = client.put(f"/api/v1/admin/users/{new_user.id}/role", 
                             json=role_update, headers=headers)
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["role"] == "developer"
        
        # 5. Admin assigns user to team
        response = client.put(f"/api/v1/admin/users/{new_user.id}/team/{team_id}", 
                             headers=headers)
        assert response.status_code == 200
        assigned_user = response.json()
        assert assigned_user["team_id"] == team_id
        
        # 6. Admin views team members
        response = client.get(f"/api/v1/admin/teams/{team_id}/members", headers=headers)
        assert response.status_code == 200
        team_members = response.json()
        assert len(team_members) == 1
        assert team_members[0]["id"] == new_user.id
    
    @patch('app.api.deps.get_current_user')
    def test_team_management_workflow(self, mock_get_user, client, admin_user, admin_token):
        """
        Test complete team management workflow.
        
        Requirements: 3.5 - Team management (creating, editing, deleting)
        """
        current_test_user = admin_user
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 1. Create team
        team_data = {"name": "QA Team", "settings": {"department": "quality"}}
        response = client.post("/api/v1/admin/teams", json=team_data, headers=headers)
        assert response.status_code == 200
        team = response.json()
        team_id = team["id"]
        assert team["name"] == "QA Team"
        
        # 2. Get all teams
        response = client.get("/api/v1/admin/teams", headers=headers)
        assert response.status_code == 200
        teams = response.json()
        assert len(teams) >= 1
        
        # 3. Get specific team
        response = client.get(f"/api/v1/admin/teams/{team_id}", headers=headers)
        assert response.status_code == 200
        retrieved_team = response.json()
        assert retrieved_team["id"] == team_id
        
        # 4. Update team
        update_data = {"name": "Quality Assurance Team", "settings": {"department": "qa", "updated": True}}
        response = client.put(f"/api/v1/admin/teams/{team_id}", 
                             json=update_data, headers=headers)
        assert response.status_code == 200
        updated_team = response.json()
        assert updated_team["name"] == "Quality Assurance Team"
        
        # 5. Delete team
        response = client.delete(f"/api/v1/admin/teams/{team_id}", headers=headers)
        assert response.status_code == 200
        
        # 6. Verify team is deleted
        response = client.get(f"/api/v1/admin/teams/{team_id}", headers=headers)
        assert response.status_code == 404
    
    def test_analytics_workflow(self, client, db_session, admin_user, regular_users, test_team, admin_token):
        """
        Test analytics dashboard workflow.
        
        Requirements: 3.4 - Admin views dashboard showing issues from all team members
        """
        global current_test_user
        current_test_user = admin_user
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create some test data
        for i, user in enumerate(regular_users[:2]):  # Only team-1 users
            # Create analyses
            analysis = DirectAnalysis(
                user_id=user.id,
                code_content="test content",
                language="python",
                filename=f"test_file_{i}.py",
                status="completed",
                results={"issues": [f"issue_{i}"]},
                created_at=datetime.utcnow()
            )
            db_session.add(analysis)
            db_session.flush()  # Get the analysis ID
            
            # Create an issue for the analysis
            issue = Issue(
                id=f"issue_{i}_hash",
                analysis_id=analysis.id,
                pattern_type="test_pattern",
                severity="medium",
                location={"line": 1, "column": 1},
                suggestion_text=f"Test suggestion {i}",
                code_context="test code context",
                created_at=datetime.utcnow()
            )
            db_session.add(issue)
            db_session.flush()  # Get the issue ID
            
            # Create feedback
            feedback = FeedbackRecord(
                issue_id=issue.id,
                user_id=user.id,
                feedback_type="accept" if i % 2 == 0 else "reject",
                feedback_value=1 if i % 2 == 0 else -1,
                created_at=datetime.utcnow()
            )
            db_session.add(feedback)
        
        db_session.commit()
        
        # 1. Get platform analytics
        response = client.get("/api/v1/admin/analytics/platform", headers=headers)
        assert response.status_code == 200
        platform_analytics = response.json()
        assert platform_analytics["total_users"] >= 4  # admin + team_lead + 3 regular users
        assert "role_distribution" in platform_analytics
        
        # 2. Get team analytics
        response = client.get(f"/api/v1/admin/analytics/teams/{test_team.id}", headers=headers)
        assert response.status_code == 200
        team_analytics = response.json()
        assert team_analytics["team_id"] == test_team.id
        assert team_analytics["member_count"] >= 2
        assert team_analytics["total_analyses"] >= 2
        
        # 3. Get all teams analytics
        response = client.get("/api/v1/admin/analytics/teams", headers=headers)
        assert response.status_code == 200
        all_analytics = response.json()
        assert len(all_analytics) >= 1
    
    @patch('app.api.deps.get_current_user')
    def test_team_lead_restricted_access(self, mock_get_user, client, db_session, team_lead_user, regular_users, test_team, team_lead_token):
        """
        Test that team leads have restricted access to their own team only.
        
        Requirements: 3.2, 3.3 - Role-based access control
        """
        # Mock the current user to be the team lead
        mock_get_user.return_value = team_lead_user
        
        headers = {"Authorization": f"Bearer {team_lead_token}"}
        
        # Team lead should be able to view users in their team
        response = client.get("/api/v1/admin/users?team_id=team-1", headers=headers)
        assert response.status_code == 200
        
        # But not users in other teams
        response = client.get("/api/v1/admin/users?team_id=team-2", headers=headers)
        assert response.status_code == 403
        
        # Team lead should be able to view their team
        response = client.get(f"/api/v1/admin/teams/{test_team.id}", headers=headers)
        assert response.status_code == 200
        
        # But not create new teams
        team_data = {"name": "New Team"}
        response = client.post("/api/v1/admin/teams", json=team_data, headers=headers)
        assert response.status_code == 403
        
        # And not access platform analytics
        response = client.get("/api/v1/admin/analytics/platform", headers=headers)
        assert response.status_code == 403
    
    @patch('app.api.deps.get_current_user')
    def test_audit_logging_workflow(self, mock_get_user, client, db_session, admin_user, admin_token):
        """
        Test audit logging for admin actions.
        
        Requirements: 3.5 - Audit logging for admin actions
        """
        # Mock the current user to be the admin
        mock_get_user.return_value = admin_user
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a user to modify
        test_user = User(
            email="audittest@test.com",
            full_name="Audit Test User",
            hashed_password="hashed_password",
            role=UserRole.USER,
            is_active=True,
            preferences={}
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)
        
        # Perform admin actions that should be logged
        
        # 1. Update user role
        role_update = {"role": "developer"}
        response = client.put(f"/api/v1/admin/users/{test_user.id}/role", 
                             json=role_update, headers=headers)
        assert response.status_code == 200
        
        # 2. Create team
        team_data = {"name": "Audit Test Team"}
        response = client.post("/api/v1/admin/teams", json=team_data, headers=headers)
        assert response.status_code == 200
        team = response.json()
        
        # 3. Assign user to team
        response = client.put(f"/api/v1/admin/users/{test_user.id}/team/{team['id']}", 
                             headers=headers)
        assert response.status_code == 200
        
        # 4. Check audit logs
        response = client.get("/api/v1/admin/audit-logs", headers=headers)
        assert response.status_code == 200
        audit_logs = response.json()
        
        # Should have at least 3 log entries
        assert len(audit_logs) >= 3
        
        # Check that different action types are logged
        actions = [log["action"] for log in audit_logs]
        assert "role_update" in actions
        assert "team_create" in actions
        assert "team_assignment" in actions
    
    @patch('app.api.deps.get_current_user')
    def test_error_handling_and_validation(self, mock_get_user, client, admin_user, admin_token):
        """Test error handling and validation in admin endpoints."""
        # Mock the current user to be the admin
        mock_get_user.return_value = admin_user
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 1. Try to get non-existent user
        response = client.get("/api/v1/admin/users/99999", headers=headers)
        assert response.status_code == 404
        
        # 2. Try to update non-existent user role
        role_update = {"role": "admin"}
        response = client.put("/api/v1/admin/users/99999/role", 
                             json=role_update, headers=headers)
        assert response.status_code == 404
        
        # 3. Try to create team with invalid data
        invalid_team_data = {"name": ""}  # Empty name should fail validation
        response = client.post("/api/v1/admin/teams", json=invalid_team_data, headers=headers)
        assert response.status_code == 422  # Validation error
        
        # 4. Try to get non-existent team
        response = client.get("/api/v1/admin/teams/non-existent-team", headers=headers)
        assert response.status_code == 404
        
        # 5. Try to assign user to non-existent team
        response = client.put("/api/v1/admin/users/1/team/non-existent-team", headers=headers)
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])