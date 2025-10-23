"""
End-to-End Tests for Admin Workflows

Tests complete admin journeys including:
- Team management workflow
- User management workflow
- Analytics viewing workflow
- Audit log tracking
"""

import pytest
import time
from unittest.mock import Mock

from app.models.users import User, UserRole
from app.models.team import Team
from app.models.audit_log import AuditLog


@pytest.mark.e2e
class TestAdminTeamManagementWorkflow:
    """Test complete team management workflow."""
    
    def test_create_and_manage_team(self, admin_client, db_session, mock_admin_user):
        """Test creating a team and managing its members."""
        # Step 1: Create a team
        team_data = {
            "name": "Engineering Team"
        }
        
        response = admin_client.post(
            "/api/v1/admin/teams",
            json=team_data
        )
        
        assert response.status_code == 200
        team = response.json()
        assert team["name"] == "Engineering Team"
        team_id = team["id"]
        
        # Step 2: Create test users
        user1 = User(
            email="user1@example.com",
            first_name="User",
            last_name="One",
            hashed_password="hashed",
            role=UserRole.USER
        )
        user2 = User(
            email="user2@example.com",
            first_name="User",
            last_name="Two",
            hashed_password="hashed",
            role=UserRole.USER
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)
        
        # Step 3: Add users to team
        response = admin_client.put(
            f"/api/v1/admin/users/{user1.id}/team/{team_id}"
        )
        assert response.status_code == 200
        
        response = admin_client.put(
            f"/api/v1/admin/users/{user2.id}/team/{team_id}"
        )
        assert response.status_code == 200
        
        # Step 4: Verify team members
        response = admin_client.get(
            f"/api/v1/admin/teams/{team_id}/members"
        )
        
        assert response.status_code == 200
        members = response.json()
        assert len(members) == 2
        member_emails = [m["email"] for m in members]
        assert "user1@example.com" in member_emails
        assert "user2@example.com" in member_emails
        
        # Step 5: Remove a user from team
        response = admin_client.delete(
            f"/api/v1/admin/users/{user1.id}/team"
        )
        assert response.status_code == 200
        
        # Step 6: Verify member removed
        response = admin_client.get(
            f"/api/v1/admin/teams/{team_id}/members"
        )
        members = response.json()
        assert len(members) == 1
        
        # Step 7: Update team details
        update_data = {
            "name": "Updated Engineering Team"
        }
        response = admin_client.put(
            f"/api/v1/admin/teams/{team_id}",
            json=update_data
        )
        assert response.status_code == 200
        
        # Step 8: Delete team
        response = admin_client.delete(
            f"/api/v1/admin/teams/{team_id}"
        )
        assert response.status_code == 200
        
        # Step 9: Verify team deleted
        response = admin_client.get(
            f"/api/v1/admin/teams/{team_id}"
        )
        assert response.status_code == 404
    
    def test_team_management_with_audit_logging(self, admin_client, db_session, mock_admin_user):
        """Test that team management actions are logged."""
        # Create team
        team_data = {"name": "Test Team"}
        response = admin_client.post("/api/v1/admin/teams", json=team_data)
        assert response.status_code == 200
        team_id = response.json()["id"]
        
        # Check audit logs
        response = admin_client.get("/api/v1/admin/audit-logs")
        assert response.status_code == 200
        logs = response.json()
        
        # Should have log for team creation
        create_log = next(
            (log for log in logs["logs"] if log["action"] == "create_team"),
            None
        )
        assert create_log is not None
        assert create_log["resource_id"] == team_id


@pytest.mark.e2e
class TestAdminUserManagementWorkflow:
    """Test complete user management workflow."""
    
    def test_manage_user_roles_and_status(self, admin_client, db_session):
        """Test managing user roles and status."""
        # Step 1: Create test user
        user = User(
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed",
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Step 2: View user list
        response = admin_client.get("/api/v1/admin/users")
        assert response.status_code == 200
        users = response.json()
        assert len(users["users"]) > 0
        
        # Step 3: Get user details
        response = admin_client.get(f"/api/v1/admin/users/{user.id}")
        assert response.status_code == 200
        user_detail = response.json()
        assert user_detail["email"] == "testuser@example.com"
        
        # Step 4: Update user role
        role_data = {"role": "team_lead"}
        response = admin_client.put(
            f"/api/v1/admin/users/{user.id}/role",
            json=role_data
        )
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["role"] == "team_lead"
        
        # Step 5: Deactivate user
        status_data = {"is_active": False}
        response = admin_client.put(
            f"/api/v1/admin/users/{user.id}/status",
            json=status_data
        )
        assert response.status_code == 200
        
        # Step 6: Verify user is deactivated
        response = admin_client.get(f"/api/v1/admin/users/{user.id}")
        user_detail = response.json()
        assert user_detail["is_active"] is False
        
        # Step 7: Reactivate user
        status_data = {"is_active": True}
        response = admin_client.put(
            f"/api/v1/admin/users/{user.id}/status",
            json=status_data
        )
        assert response.status_code == 200
    
    def test_search_and_filter_users(self, admin_client, db_session):
        """Test searching and filtering users."""
        # Create multiple test users
        users = [
            User(email=f"user{i}@example.com", first_name=f"User{i}", 
                 last_name="Test", hashed_password="hashed", role=UserRole.USER)
            for i in range(5)
        ]
        db_session.add_all(users)
        db_session.commit()
        
        # Test pagination
        response = admin_client.get("/api/v1/admin/users?page=1&page_size=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) <= 3
        
        # Test search
        response = admin_client.get("/api/v1/admin/users?search=user1")
        assert response.status_code == 200
        data = response.json()
        assert any("user1" in u["email"] for u in data["users"])
        
        # Test filter by role
        response = admin_client.get("/api/v1/admin/users?role=user")
        assert response.status_code == 200
        data = response.json()
        assert all(u["role"] == "user" for u in data["users"])


@pytest.mark.e2e
class TestAdminAnalyticsWorkflow:
    """Test complete analytics viewing workflow."""
    
    def test_view_platform_analytics(self, admin_client, db_session):
        """Test viewing platform-wide analytics."""
        # Step 1: Get platform overview
        response = admin_client.get("/api/v1/admin/analytics/platform")
        assert response.status_code == 200
        stats = response.json()
        
        assert "total_users" in stats
        assert "total_teams" in stats
        assert "total_reviews" in stats
        assert "active_users_30d" in stats
        
        # Step 2: Get global trends
        response = admin_client.get(
            "/api/v1/admin/analytics/global-trends?timeframe=30d"
        )
        assert response.status_code == 200
        trends = response.json()
        assert "data_points" in trends
        
        # Step 3: Get team comparison
        response = admin_client.get("/api/v1/admin/analytics/team-comparison")
        assert response.status_code == 200
        comparison = response.json()
        assert "teams" in comparison
        
        # Step 4: View all reviews
        response = admin_client.get(
            "/api/v1/admin/analytics/all-reviews?page=1&page_size=10"
        )
        assert response.status_code == 200
        reviews = response.json()
        assert "reviews" in reviews
        assert "total" in reviews
        
        # Step 5: View all feedback
        response = admin_client.get(
            "/api/v1/admin/analytics/all-feedback?page=1&page_size=10"
        )
        assert response.status_code == 200
        feedback = response.json()
        assert "feedback" in feedback
        assert "summary" in feedback
    
    def test_filter_analytics_by_team(self, admin_client, db_session, mock_admin_user):
        """Test filtering analytics by team."""
        # Create test team
        team = Team(name="Test Team", admin_id=mock_admin_user.id)
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)
        
        # Get trends for specific team
        response = admin_client.get(
            f"/api/v1/admin/analytics/global-trends?team_id={team.id}"
        )
        assert response.status_code == 200
        
        # Get reviews for specific team
        response = admin_client.get(
            f"/api/v1/admin/analytics/all-reviews?team_id={team.id}"
        )
        assert response.status_code == 200


@pytest.mark.e2e
class TestCompleteAdminJourney:
    """Test complete end-to-end admin journey."""
    
    def test_admin_daily_workflow(self, admin_client, db_session, mock_admin_user):
        """Test typical daily admin workflow."""
        # Morning: Check platform stats
        response = admin_client.get("/api/v1/admin/analytics/platform")
        assert response.status_code == 200
        
        # Create new team for new project
        team_data = {"name": "New Project Team"}
        response = admin_client.post("/api/v1/admin/teams", json=team_data)
        assert response.status_code == 200
        team_id = response.json()["id"]
        
        # Add users to team
        user = User(
            email="developer@example.com",
            first_name="Dev",
            last_name="User",
            hashed_password="hashed",
            role=UserRole.USER
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        response = admin_client.put(
            f"/api/v1/admin/users/{user.id}/team/{team_id}"
        )
        assert response.status_code == 200
        
        # Promote user to team lead
        response = admin_client.put(
            f"/api/v1/admin/users/{user.id}/role",
            json={"role": "team_lead"}
        )
        assert response.status_code == 200
        
        # Check team analytics
        response = admin_client.get(
            f"/api/v1/admin/analytics/global-trends?team_id={team_id}"
        )
        assert response.status_code == 200
        
        # Review audit logs
        response = admin_client.get("/api/v1/admin/audit-logs")
        assert response.status_code == 200
        logs = response.json()
        
        # Should have logs for all actions
        actions = [log["action"] for log in logs["logs"]]
        assert "create_team" in actions
        assert "assign_user_to_team" in actions
        assert "update_user_role" in actions
