import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.users import User, UserRole
from app.models.team import Team
from app.models.feedback import FeedbackRecord
from app.models.analysis import DirectAnalysis
from app.services.admin_service import AdminService
from app.schemas.team import TeamCreate, TeamUpdate


class TestAdminServiceIntegration:
    """
    Simplified integration tests for AdminService functionality.
    
    Requirements covered: 3.1, 3.2, 3.3, 3.4, 3.5
    """
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def admin_service(self, mock_db):
        return AdminService(mock_db)
    
    @pytest.fixture
    def admin_user(self):
        user = Mock(spec=User)
        user.id = 1
        user.email = "admin@test.com"
        user.role = UserRole.ADMIN
        user.is_active = True
        # Use a real dictionary instead of Mock for preferences
        user.preferences = {}
        return user
    
    @pytest.fixture
    def regular_user(self):
        user = Mock(spec=User)
        user.id = 2
        user.email = "user@test.com"
        user.role = UserRole.USER
        user.is_active = True
        user.team_id = "team-1"
        user.updated_at = datetime.utcnow()
        return user
    
    @pytest.fixture
    def test_team(self):
        team = Mock(spec=Team)
        team.id = "team-1"
        team.name = "Test Team"
        team.admin_id = 1
        team.settings = {}
        team.updated_at = datetime.utcnow()
        return team
    
    @pytest.mark.asyncio
    async def test_user_management_workflow(self, admin_service, mock_db, admin_user, regular_user):
        """
        Test complete user management workflow.
        
        Requirements: 3.2, 3.3 - User management and role assignment
        """
        # Mock database responses
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Test getting all users
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [regular_user]
        users = await admin_service.get_all_users()
        assert len(users) == 1
        assert users[0] == regular_user
        
        # Set up mock for update_user_role - first call gets the user, second gets admin for audit
        mock_db.query.return_value.filter.return_value.first.side_effect = [regular_user, admin_user]
        
        # Test updating user role
        updated_user = await admin_service.update_user_role(
            user_id=regular_user.id,
            role=UserRole.DEVELOPER,
            admin_user_id=admin_user.id
        )
        assert updated_user == regular_user
        assert regular_user.role == UserRole.DEVELOPER
        
        # Verify audit logging
        assert "audit_logs" in admin_user.preferences
        assert len(admin_user.preferences["audit_logs"]) > 0
        
        log_entry = admin_user.preferences["audit_logs"][-1]
        assert log_entry["action"] == "role_update"
        assert log_entry["target_user_id"] == regular_user.id
    
    @pytest.mark.asyncio
    async def test_team_management_workflow(self, admin_service, mock_db, admin_user, test_team):
        """
        Test complete team management workflow.
        
        Requirements: 3.5 - Team management (creating, editing, deleting)
        """
        # Test creating team
        team_data = TeamCreate(name="New Team", settings={"test": True})
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        # Mock for audit logging
        mock_db.query.return_value.filter.return_value.first.return_value = admin_user
        
        with patch('uuid.uuid4', return_value=Mock(hex='test-uuid-123')):
            created_team = await admin_service.create_team(team_data, admin_user.id)
            assert created_team is not None
            assert created_team.name == "New Team"
            assert created_team.admin_id == admin_user.id
            assert created_team.settings == {"test": True}
        
        # Test getting all teams
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [test_team]
        teams = await admin_service.get_all_teams()
        assert len(teams) == 1
        assert teams[0] == test_team
        
        # Test updating team
        mock_db.query.return_value.filter.return_value.first.side_effect = [test_team, admin_user]
        update_data = TeamUpdate(name="Updated Team")
        
        updated_team = await admin_service.update_team(
            team_id=test_team.id,
            team_data=update_data,
            admin_user_id=admin_user.id
        )
        assert updated_team == test_team
        assert test_team.name == "Updated Team"
        
        # Test deleting team
        mock_db.query.return_value.filter.return_value.first.side_effect = [test_team, admin_user]
        mock_db.query.return_value.filter.return_value.update.return_value = None
        mock_db.delete.return_value = None
        
        success = await admin_service.delete_team(test_team.id, admin_user.id)
        assert success is True
    
    @pytest.mark.asyncio
    async def test_team_analytics_workflow(self, admin_service, mock_db, test_team):
        """
        Test team analytics functionality.
        
        Requirements: 3.4 - Admin views dashboard showing issues from all team members
        """
        # Mock team and users
        mock_users = [Mock(id=1), Mock(id=2)]
        mock_db.query.return_value.filter.return_value.first.return_value = test_team
        mock_db.query.return_value.filter.return_value.all.return_value = mock_users
        
        # Mock analytics data
        mock_db.query.return_value.filter.return_value.scalar.return_value = 10
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        analytics = await admin_service.get_team_analytics(test_team.id)
        
        assert analytics is not None
        assert analytics["team_id"] == test_team.id
        assert analytics["team_name"] == test_team.name
        assert analytics["member_count"] == 2
        assert "total_analyses" in analytics
        assert "acceptance_rate" in analytics
    
    @pytest.mark.asyncio
    async def test_platform_analytics_workflow(self, admin_service, mock_db):
        """
        Test platform-wide analytics.
        
        Requirements: 3.1 - Admin accesses admin dashboard with user management interface
        """
        # Mock platform statistics
        mock_db.query.return_value.scalar.return_value = 100
        
        analytics = await admin_service.get_platform_analytics()
        
        assert analytics is not None
        assert "total_users" in analytics
        assert "active_users" in analytics
        assert "total_teams" in analytics
        assert "role_distribution" in analytics
        assert "recent_activity" in analytics
    
    @pytest.mark.asyncio
    async def test_audit_logging_functionality(self, admin_service, mock_db, admin_user, regular_user):
        """
        Test audit logging for admin actions.
        
        Requirements: 3.5 - Implement audit logging for admin actions
        """
        # Mock database responses for both operations and audit logging
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            regular_user, admin_user,  # First operation
            regular_user, admin_user,  # Second operation
            admin_user                 # get_audit_logs operation
        ]
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Perform multiple admin actions
        await admin_service.update_user_role(
            user_id=regular_user.id,
            role=UserRole.DEVELOPER,
            admin_user_id=admin_user.id
        )
        
        await admin_service.update_user_status(
            user_id=regular_user.id,
            is_active=False,
            admin_user_id=admin_user.id
        )
        
        # Check audit logs
        logs = await admin_service.get_audit_logs(admin_user.id)
        
        assert len(logs) >= 2
        
        # Verify log entries
        actions = [log["action"] for log in logs]
        assert "role_update" in actions
        assert "status_update" in actions
        
        # Verify log details
        role_log = next(log for log in logs if log["action"] == "role_update")
        assert role_log["target_user_id"] == regular_user.id
        assert "old_role" in role_log["details"]
        assert "new_role" in role_log["details"]
    
    @pytest.mark.asyncio
    async def test_user_team_assignment(self, admin_service, mock_db, admin_user, regular_user, test_team):
        """
        Test user team assignment functionality.
        
        Requirements: 3.2 - Admin views all team members and their roles
        """
        # Mock database responses - user, team, then admin for audit logging
        mock_db.query.return_value.filter.return_value.first.side_effect = [regular_user, test_team, admin_user]
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Test assigning user to team
        assigned_user = await admin_service.assign_user_to_team(
            user_id=regular_user.id,
            team_id=test_team.id,
            admin_user_id=admin_user.id
        )
        
        assert assigned_user == regular_user
        assert regular_user.team_id == test_team.id
        
        # Verify audit logging
        assert "audit_logs" in admin_user.preferences
        log_entry = admin_user.preferences["audit_logs"][-1]
        assert log_entry["action"] == "team_assignment"
        assert log_entry["target_user_id"] == regular_user.id
    
    @pytest.mark.asyncio
    async def test_error_handling(self, admin_service, mock_db, admin_user):
        """Test error handling in admin service methods."""
        # Test with non-existent user
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await admin_service.update_user_role(
            user_id=999,
            role=UserRole.DEVELOPER,
            admin_user_id=admin_user.id
        )
        assert result is None
        
        # Test with non-existent team
        result = await admin_service.get_team_analytics("non-existent-team")
        assert result is None
        
        # Test deleting non-existent team
        success = await admin_service.delete_team("non-existent-team", admin_user.id)
        assert success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])