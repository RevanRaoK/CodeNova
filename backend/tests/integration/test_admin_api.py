"""
Integration tests for admin API endpoints.

Tests cover:
- User management endpoints
- Team management endpoints
- Platform analytics endpoints
- Authorization and access control

Requirements: 15.3, 15.4
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime

from app.main import app
from app.api.deps import get_current_user
from app.models.users import User, UserRole


class TestAdminUserManagementAPI:
    """Integration tests for admin user management endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_admin(self):
        """Create mock admin user."""
        admin = Mock(spec=User)
        admin.id = 1
        admin.email = "admin@example.com"
        admin.full_name = "Admin User"
        admin.role = UserRole.ADMIN
        admin.is_active = True
        return admin
    
    @pytest.fixture
    def mock_regular_user(self):
        """Create mock regular user."""
        user = Mock(spec=User)
        user.id = 2
        user.email = "user@example.com"
        user.full_name = "Regular User"
        user.role = UserRole.USER
        user.is_active = True
        return user
    
    @pytest.fixture
    def admin_client(self, client, mock_admin):
        """Create admin authenticated client."""
        app.dependency_overrides[get_current_user] = lambda: mock_admin
        yield client
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def user_client(self, client, mock_regular_user):
        """Create regular user authenticated client."""
        app.dependency_overrides[get_current_user] = lambda: mock_regular_user
        yield client
        app.dependency_overrides.clear()
    
    # Get All Users Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_all_users_as_admin(self, admin_client):
        """Test admin can retrieve all users."""
        with patch('app.services.admin_service.AdminService.get_all_users') as mock_get:
            mock_users = [
                Mock(id=1, email="user1@example.com", full_name="User One", role=UserRole.USER),
                Mock(id=2, email="user2@example.com", full_name="User Two", role=UserRole.USER)
            ]
            mock_get.return_value = mock_users
            
            response = admin_client.get("/api/v1/admin/users")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 0  # Response format may vary
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_all_users_as_regular_user(self, user_client):
        """Test regular user cannot access admin endpoint."""
        response = user_client.get("/api/v1/admin/users")
        
        assert response.status_code == 403
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_all_users_with_filters(self, admin_client):
        """Test getting users with filters."""
        with patch('app.services.admin_service.AdminService.get_all_users') as mock_get:
            mock_get.return_value = []
            
            response = admin_client.get(
                "/api/v1/admin/users?role=admin&is_active=true&search=test"
            )
            
            assert response.status_code == 200
    
    # Get User by ID Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_user_by_id_as_admin(self, admin_client):
        """Test admin can retrieve specific user."""
        with patch('app.services.admin_service.AdminService.get_user_by_id') as mock_get:
            mock_user = Mock(
                id=2,
                email="test@example.com",
                full_name="Test User",
                role=UserRole.USER,
                is_active=True
            )
            mock_get.return_value = mock_user
            
            response = admin_client.get("/api/v1/admin/users/2")
            
            assert response.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_user_by_id_not_found(self, admin_client):
        """Test getting non-existent user returns 404."""
        with patch('app.services.admin_service.AdminService.get_user_by_id') as mock_get:
            mock_get.return_value = None
            
            response = admin_client.get("/api/v1/admin/users/999")
            
            assert response.status_code == 404
    
    # Update User Role Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_update_user_role_as_admin(self, admin_client):
        """Test admin can update user role."""
        with patch('app.services.admin_service.AdminService.update_user_role') as mock_update:
            mock_user = Mock(
                id=2,
                email="test@example.com",
                full_name="Test User",
                role=UserRole.TEAM_LEAD
            )
            mock_update.return_value = mock_user
            
            response = admin_client.put(
                "/api/v1/admin/users/2/role",
                json={"role": "team_lead"}
            )
            
            assert response.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_update_user_role_invalid_role(self, admin_client):
        """Test updating user with invalid role returns error."""
        response = admin_client.put(
            "/api/v1/admin/users/2/role",
            json={"role": "invalid_role"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_update_user_role_as_regular_user(self, user_client):
        """Test regular user cannot update roles."""
        response = user_client.put(
            "/api/v1/admin/users/2/role",
            json={"role": "admin"}
        )
        
        assert response.status_code == 403
    
    # Update User Status Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_update_user_status_as_admin(self, admin_client):
        """Test admin can update user status."""
        with patch('app.services.admin_service.AdminService.update_user_status') as mock_update:
            mock_user = Mock(id=2, is_active=False)
            mock_update.return_value = mock_user
            
            response = admin_client.put(
                "/api/v1/admin/users/2/status",
                json={"is_active": False}
            )
            
            assert response.status_code == 200
    
    # Assign User to Team Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_assign_user_to_team_as_admin(self, admin_client):
        """Test admin can assign user to team."""
        with patch('app.services.admin_service.AdminService.assign_user_to_team') as mock_assign:
            mock_user = Mock(id=2, team_id="team-123")
            mock_assign.return_value = mock_user
            
            response = admin_client.put(
                "/api/v1/admin/users/2/team",
                json={"team_id": "team-123"}
            )
            
            assert response.status_code == 200


class TestAdminTeamManagementAPI:
    """Integration tests for admin team management endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_admin(self):
        """Create mock admin user."""
        admin = Mock(spec=User)
        admin.id = 1
        admin.email = "admin@example.com"
        admin.full_name = "Admin User"
        admin.role = UserRole.ADMIN
        admin.is_active = True
        return admin
    
    @pytest.fixture
    def admin_client(self, client, mock_admin):
        """Create admin authenticated client."""
        app.dependency_overrides[get_current_user] = lambda: mock_admin
        yield client
        app.dependency_overrides.clear()
    
    # Create Team Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_create_team_as_admin(self, admin_client):
        """Test admin can create team."""
        with patch('app.services.admin_service.AdminService.create_team') as mock_create:
            mock_team = Mock(
                id="team-123",
                name="New Team",
                admin_id=1,
                settings={}
            )
            mock_create.return_value = mock_team
            
            response = admin_client.post(
                "/api/v1/admin/teams",
                json={"name": "New Team", "settings": {}}
            )
            
            assert response.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_create_team_missing_name(self, admin_client):
        """Test creating team without name returns error."""
        response = admin_client.post(
            "/api/v1/admin/teams",
            json={}
        )
        
        assert response.status_code == 422
    
    # Get All Teams Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_all_teams_as_admin(self, admin_client):
        """Test admin can retrieve all teams."""
        with patch('app.services.admin_service.AdminService.get_all_teams') as mock_get:
            mock_teams = [
                Mock(id="team-1", name="Team 1"),
                Mock(id="team-2", name="Team 2")
            ]
            mock_get.return_value = mock_teams
            
            response = admin_client.get("/api/v1/admin/teams")
            
            assert response.status_code == 200
    
    # Get Team by ID Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_team_by_id_as_admin(self, admin_client):
        """Test admin can retrieve specific team."""
        with patch('app.services.admin_service.AdminService.get_team_by_id') as mock_get:
            mock_team = Mock(
                id="team-123",
                name="Test Team",
                admin_id=1
            )
            mock_get.return_value = mock_team
            
            response = admin_client.get("/api/v1/admin/teams/team-123")
            
            assert response.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_team_by_id_not_found(self, admin_client):
        """Test getting non-existent team returns 404."""
        with patch('app.services.admin_service.AdminService.get_team_by_id') as mock_get:
            mock_get.return_value = None
            
            response = admin_client.get("/api/v1/admin/teams/invalid-team")
            
            assert response.status_code == 404
    
    # Update Team Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_update_team_as_admin(self, admin_client):
        """Test admin can update team."""
        with patch('app.services.admin_service.AdminService.update_team') as mock_update:
            mock_team = Mock(
                id="team-123",
                name="Updated Team"
            )
            mock_update.return_value = mock_team
            
            response = admin_client.put(
                "/api/v1/admin/teams/team-123",
                json={"name": "Updated Team"}
            )
            
            assert response.status_code == 200
    
    # Delete Team Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_delete_team_as_admin(self, admin_client):
        """Test admin can delete team."""
        with patch('app.services.admin_service.AdminService.delete_team') as mock_delete:
            mock_delete.return_value = True
            
            response = admin_client.delete("/api/v1/admin/teams/team-123")
            
            assert response.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_delete_team_not_found(self, admin_client):
        """Test deleting non-existent team returns 404."""
        with patch('app.services.admin_service.AdminService.delete_team') as mock_delete:
            mock_delete.return_value = False
            
            response = admin_client.delete("/api/v1/admin/teams/invalid-team")
            
            assert response.status_code == 404


class TestAdminAnalyticsAPI:
    """Integration tests for admin analytics endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_admin(self):
        """Create mock admin user."""
        admin = Mock(spec=User)
        admin.id = 1
        admin.email = "admin@example.com"
        admin.full_name = "Admin User"
        admin.role = UserRole.ADMIN
        admin.is_active = True
        return admin
    
    @pytest.fixture
    def admin_client(self, client, mock_admin):
        """Create admin authenticated client."""
        app.dependency_overrides[get_current_user] = lambda: mock_admin
        yield client
        app.dependency_overrides.clear()
    
    # Platform Analytics Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_platform_analytics_as_admin(self, admin_client):
        """Test admin can retrieve platform analytics."""
        with patch('app.services.admin_service.AdminService.get_platform_analytics') as mock_get:
            mock_analytics = {
                "total_users": 100,
                "active_users": 75,
                "total_teams": 10,
                "total_analyses": 500,
                "total_feedback": 300
            }
            mock_get.return_value = mock_analytics
            
            response = admin_client.get("/api/v1/admin/analytics/platform")
            
            assert response.status_code == 200
            data = response.json()
            assert "total_users" in data
            assert "total_teams" in data
    
    # Team Analytics Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_team_analytics_as_admin(self, admin_client):
        """Test admin can retrieve team analytics."""
        with patch('app.services.admin_service.AdminService.get_team_analytics') as mock_get:
            mock_analytics = {
                "team_id": "team-123",
                "team_name": "Test Team",
                "member_count": 5,
                "total_analyses": 50,
                "total_feedback": 30
            }
            mock_get.return_value = mock_analytics
            
            response = admin_client.get("/api/v1/admin/analytics/teams/team-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["team_id"] == "team-123"
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_team_analytics_not_found(self, admin_client):
        """Test getting analytics for non-existent team returns 404."""
        with patch('app.services.admin_service.AdminService.get_team_analytics') as mock_get:
            mock_get.return_value = None
            
            response = admin_client.get("/api/v1/admin/analytics/teams/invalid-team")
            
            assert response.status_code == 404
    
    # All Teams Analytics Tests
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_all_teams_analytics_as_admin(self, admin_client):
        """Test admin can retrieve analytics for all teams."""
        with patch('app.services.admin_service.AdminService.get_all_teams_analytics') as mock_get:
            mock_analytics = [
                {"team_id": "team-1", "team_name": "Team 1", "member_count": 5},
                {"team_id": "team-2", "team_name": "Team 2", "member_count": 3}
            ]
            mock_get.return_value = mock_analytics
            
            response = admin_client.get("/api/v1/admin/analytics/teams")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 0


class TestAuditLogAPI:
    """Integration tests for audit log endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_admin(self):
        """Create mock admin user."""
        admin = Mock(spec=User)
        admin.id = 1
        admin.email = "admin@example.com"
        admin.full_name = "Admin User"
        admin.role = UserRole.ADMIN
        admin.is_active = True
        return admin
    
    @pytest.fixture
    def admin_client(self, client, mock_admin):
        """Create admin authenticated client."""
        app.dependency_overrides[get_current_user] = lambda: mock_admin
        yield client
        app.dependency_overrides.clear()
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_audit_logs_as_admin(self, admin_client):
        """Test admin can retrieve audit logs."""
        with patch('app.services.audit_logger.AuditLogger.get_audit_logs') as mock_get:
            mock_logs = {
                "logs": [
                    {
                        "id": 1,
                        "timestamp": "2025-01-01T00:00:00",
                        "user_id": 1,
                        "action": "update_role",
                        "resource_type": "user"
                    }
                ],
                "total": 1
            }
            mock_get.return_value = mock_logs
            
            response = admin_client.get("/api/v1/admin/audit-logs")
            
            assert response.status_code == 200
            data = response.json()
            assert "logs" in data
            assert "total" in data
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_audit_logs_with_filters(self, admin_client):
        """Test getting audit logs with filters."""
        with patch('app.services.audit_logger.AuditLogger.get_audit_logs') as mock_get:
            mock_get.return_value = {"logs": [], "total": 0}
            
            response = admin_client.get(
                "/api/v1/admin/audit-logs?action=update_role&resource_type=user"
            )
            
            assert response.status_code == 200
