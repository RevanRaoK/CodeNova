import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.main import app
from app.models.users import User, UserRole
from app.models.team import Team
from app.core.rbac import RBACError, RoleChecker, PermissionChecker, Permissions
from app.services.admin_service import AdminService


class TestRBACAuthorization:
    """
    Test role-based access control authorization.
    
    Requirements covered: 3.3 - Role-based access control with immediate permission updates
    """
    
    def test_role_checker_admin_access(self):
        """Test that admin users can access admin-only resources."""
        admin_user = Mock(spec=User)
        admin_user.role = UserRole.ADMIN
        admin_user.is_active = True
        
        checker = RoleChecker([UserRole.ADMIN])
        result = checker(admin_user)
        
        assert result == admin_user
    
    def test_role_checker_unauthorized_access(self):
        """Test that non-admin users cannot access admin-only resources."""
        regular_user = Mock(spec=User)
        regular_user.role = UserRole.USER
        regular_user.is_active = True
        
        checker = RoleChecker([UserRole.ADMIN])
        
        with pytest.raises(RBACError) as exc_info:
            checker(regular_user)
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in str(exc_info.value.detail)
    
    def test_role_checker_inactive_user(self):
        """Test that inactive users cannot access resources."""
        inactive_admin = Mock(spec=User)
        inactive_admin.role = UserRole.ADMIN
        inactive_admin.is_active = False
        
        checker = RoleChecker([UserRole.ADMIN])
        
        with pytest.raises(RBACError) as exc_info:
            checker(inactive_admin)
        
        assert "Account is inactive" in str(exc_info.value.detail)
    
    def test_role_checker_multiple_roles(self):
        """Test role checker with multiple allowed roles."""
        team_lead = Mock(spec=User)
        team_lead.role = UserRole.TEAM_LEAD
        team_lead.is_active = True
        
        checker = RoleChecker([UserRole.ADMIN, UserRole.TEAM_LEAD])
        result = checker(team_lead)
        
        assert result == team_lead
    
    def test_permission_checker_admin_permissions(self):
        """Test that admin users have all permissions."""
        admin_user = Mock(spec=User)
        admin_user.role = UserRole.ADMIN
        admin_user.is_active = True
        
        checker = PermissionChecker(Permissions.USER_WRITE)
        result = checker(admin_user)
        
        assert result == admin_user
    
    def test_permission_checker_insufficient_permissions(self):
        """Test that users without permissions are denied access."""
        regular_user = Mock(spec=User)
        regular_user.role = UserRole.USER
        regular_user.is_active = True
        
        checker = PermissionChecker(Permissions.USER_WRITE)
        
        with pytest.raises(RBACError) as exc_info:
            checker(regular_user)
        
        assert "Missing permission" in str(exc_info.value.detail)
    
    def test_team_lead_permissions(self):
        """Test that team leads have appropriate permissions."""
        team_lead = Mock(spec=User)
        team_lead.role = UserRole.TEAM_LEAD
        team_lead.is_active = True
        
        # Team leads should have team read/write permissions
        checker = PermissionChecker(Permissions.TEAM_READ)
        result = checker(team_lead)
        assert result == team_lead
        
        checker = PermissionChecker(Permissions.TEAM_WRITE)
        result = checker(team_lead)
        assert result == team_lead
        
        # But not user delete permissions
        checker = PermissionChecker(Permissions.USER_DELETE)
        with pytest.raises(RBACError):
            checker(team_lead)


class TestAdminServiceAuthorization:
    """Test authorization in AdminService methods."""
    
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
        user.role = UserRole.ADMIN
        user.is_active = True
        user.preferences = {"audit_logs": []}
        return user
    
    @pytest.fixture
    def regular_user(self):
        user = Mock(spec=User)
        user.id = 2
        user.role = UserRole.USER
        user.is_active = True
        user.team_id = "team-1"
        user.preferences = {}
        return user
    
    @pytest.fixture
    def team_lead_user(self):
        user = Mock(spec=User)
        user.id = 3
        user.role = UserRole.TEAM_LEAD
        user.is_active = True
        user.team_id = "team-1"
        user.preferences = {}
        return user
    
    @pytest.mark.asyncio
    async def test_update_user_role_authorization(self, admin_service, mock_db, admin_user, regular_user):
        """Test that only admins can update user roles."""
        # Setup mock to return different users for different queries
        def mock_query_side_effect(*args):
            mock_query = Mock()
            mock_filter = Mock()
            mock_query.filter.return_value = mock_filter
            
            # First call is for the user being updated, second is for admin user in audit log
            if hasattr(mock_query_side_effect, 'call_count'):
                mock_query_side_effect.call_count += 1
            else:
                mock_query_side_effect.call_count = 1
            
            if mock_query_side_effect.call_count == 1:
                mock_filter.first.return_value = regular_user
            else:
                mock_filter.first.return_value = admin_user
            
            return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Admin should be able to update roles
        result = await admin_service.update_user_role(
            user_id=regular_user.id,
            role=UserRole.DEVELOPER,
            admin_user_id=admin_user.id
        )
        
        assert result == regular_user
        assert regular_user.role == UserRole.DEVELOPER
    
    @pytest.mark.asyncio
    async def test_create_team_authorization(self, admin_service, mock_db, admin_user):
        """Test that teams can be created by admins."""
        from app.schemas.team import TeamCreate
        
        team_data = TeamCreate(name="Test Team", settings={})
        
        # Mock the database operations
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Mock the query for audit logging
        mock_db.query.return_value.filter.return_value.first.return_value = admin_user
        
        # Mock uuid generation
        with patch('uuid.uuid4', return_value=type('MockUUID', (), {'__str__': lambda self: 'team-123'})()):
            result = await admin_service.create_team(team_data, admin_user.id)
            
            assert result is not None
            assert hasattr(result, 'name')
            assert result.name == "Test Team"
    
    @pytest.mark.asyncio
    async def test_audit_logging(self, admin_service, mock_db, admin_user, regular_user):
        """Test that admin actions are properly logged."""
        # Setup mock to return different users for different queries
        def mock_query_side_effect(*args):
            mock_query = Mock()
            mock_filter = Mock()
            mock_query.filter.return_value = mock_filter
            
            # First call is for the user being updated, second is for admin user in audit log
            if hasattr(mock_query_side_effect, 'call_count'):
                mock_query_side_effect.call_count += 1
            else:
                mock_query_side_effect.call_count = 1
            
            if mock_query_side_effect.call_count == 1:
                mock_filter.first.return_value = regular_user
            else:
                mock_filter.first.return_value = admin_user
            
            return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Update user role (should trigger audit log)
        await admin_service.update_user_role(
            user_id=regular_user.id,
            role=UserRole.DEVELOPER,
            admin_user_id=admin_user.id
        )
        
        # Check that audit log was created
        assert "audit_logs" in admin_user.preferences
        assert len(admin_user.preferences["audit_logs"]) > 0
        
        log_entry = admin_user.preferences["audit_logs"][-1]
        assert log_entry["action"] == "role_update"
        assert log_entry["target_user_id"] == regular_user.id
        assert "old_role" in log_entry["details"]
        assert "new_role" in log_entry["details"]


class TestAdminAPIAuthorization:
    """Test authorization for admin API endpoints."""
    
    def test_role_checker_integration(self):
        """Test role checker integration with admin endpoints."""
        from app.core.rbac import require_admin, require_admin_or_team_lead
        
        # Test admin access
        admin_user = Mock(spec=User)
        admin_user.role = UserRole.ADMIN
        admin_user.is_active = True
        
        result = require_admin(admin_user)
        assert result == admin_user
        
        # Test team lead access
        team_lead = Mock(spec=User)
        team_lead.role = UserRole.TEAM_LEAD
        team_lead.is_active = True
        
        result = require_admin_or_team_lead(team_lead)
        assert result == team_lead
        
        # Test unauthorized access
        regular_user = Mock(spec=User)
        regular_user.role = UserRole.USER
        regular_user.is_active = True
        
        with pytest.raises(RBACError):
            require_admin(regular_user)
    
    def test_permission_based_access_control(self):
        """Test permission-based access control."""
        from app.core.rbac import PermissionChecker, Permissions
        
        # Admin should have all permissions
        admin_user = Mock(spec=User)
        admin_user.role = UserRole.ADMIN
        admin_user.is_active = True
        
        checker = PermissionChecker(Permissions.USER_WRITE)
        result = checker(admin_user)
        assert result == admin_user
        
        # Regular user should not have admin permissions
        regular_user = Mock(spec=User)
        regular_user.role = UserRole.USER
        regular_user.is_active = True
        
        with pytest.raises(RBACError):
            checker(regular_user)
    
    def test_team_access_control(self):
        """Test team-based access control."""
        from app.core.rbac import TeamAccessChecker
        
        # Mock database session
        mock_db = Mock()
        mock_team = Mock()
        mock_team.admin_id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_team
        
        # Team admin should have access
        team_admin = Mock(spec=User)
        team_admin.id = 1
        team_admin.role = UserRole.TEAM_LEAD
        team_admin.is_active = True
        team_admin.team_id = "team-1"
        
        checker = TeamAccessChecker(require_admin=True)
        result = checker("team-1", team_admin, mock_db)
        assert result == team_admin
        
        # Non-team member should not have access
        other_user = Mock(spec=User)
        other_user.id = 2
        other_user.role = UserRole.USER
        other_user.is_active = True
        other_user.team_id = "team-2"
        
        with pytest.raises(RBACError):
            checker("team-1", other_user, mock_db)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])