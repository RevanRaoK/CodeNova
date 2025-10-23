"""
Unit tests for AdminService.

Tests cover:
- User management operations
- Team management operations
- Platform analytics
- Audit logging integration

Requirements: 15.1, 15.3, 15.4
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.admin_service import AdminService
from app.models.users import User, UserRole
from app.models.team import Team
from app.models.analysis import DirectAnalysis
from app.models.feedback import FeedbackRecord
from app.schemas.team import TeamCreate, TeamUpdate


class TestAdminService:
    """Test suite for AdminService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock(spec=Session)
        db.query = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.delete = Mock()
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create an AdminService instance with mocked dependencies."""
        with patch('app.services.admin_service.AuditLogger'):
            return AdminService(mock_db)
    
    @pytest.fixture
    def sample_user(self):
        """Create a sample user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.first_name = "Test"
        user.last_name = "User"
        user.role = UserRole.USER
        user.is_active = True
        user.team_id = None
        user.created_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        return user
    
    @pytest.fixture
    def sample_admin(self):
        """Create a sample admin user."""
        admin = Mock(spec=User)
        admin.id = 2
        admin.email = "admin@example.com"
        admin.full_name = "Admin User"
        admin.first_name = "Admin"
        admin.last_name = "User"
        admin.role = UserRole.ADMIN
        admin.is_active = True
        admin.team_id = None
        return admin
    
    @pytest.fixture
    def sample_team(self):
        """Create a sample team."""
        team = Mock(spec=Team)
        team.id = "team-123"
        team.name = "Test Team"
        team.admin_id = 2
        team.settings = {}
        team.created_at = datetime.utcnow()
        team.updated_at = datetime.utcnow()
        return team
    
    # User Management Tests
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_all_users_no_filters(self, service, mock_db, sample_user):
        """Test getting all users without filters."""
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = [sample_user]
        mock_db.query.return_value = mock_query
        
        users = await service.get_all_users()
        
        assert len(users) == 1
        assert users[0].id == sample_user.id
        mock_db.query.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_all_users_with_team_filter(self, service, mock_db, sample_user):
        """Test getting users filtered by team."""
        sample_user.team_id = "team-123"
        mock_query = Mock()
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = [sample_user]
        mock_db.query.return_value = mock_query
        
        users = await service.get_all_users(team_id="team-123")
        
        assert len(users) == 1
        assert users[0].team_id == "team-123"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_all_users_with_role_filter(self, service, mock_db, sample_admin):
        """Test getting users filtered by role."""
        mock_query = Mock()
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = [sample_admin]
        mock_db.query.return_value = mock_query
        
        users = await service.get_all_users(role=UserRole.ADMIN)
        
        assert len(users) == 1
        assert users[0].role == UserRole.ADMIN
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_all_users_with_search(self, service, mock_db, sample_user):
        """Test getting users with search query."""
        mock_query = Mock()
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = [sample_user]
        mock_db.query.return_value = mock_query
        
        users = await service.get_all_users(search="test")
        
        assert len(users) == 1
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_by_id_exists(self, service, mock_db, sample_user):
        """Test getting user by ID when user exists."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_user
        mock_db.query.return_value = mock_query
        
        user = await service.get_user_by_id(1)
        
        assert user is not None
        assert user.id == 1
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_exists(self, service, mock_db):
        """Test getting user by ID when user doesn't exist."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        user = await service.get_user_by_id(999)
        
        assert user is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_user_role_success(self, service, mock_db, sample_user):
        """Test successful user role update."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_user
        mock_db.query.return_value = mock_query
        
        updated_user = await service.update_user_role(1, UserRole.TEAM_LEAD, 2)
        
        assert updated_user is not None
        assert updated_user.role == UserRole.TEAM_LEAD
        mock_db.commit.assert_called_once()
        service.audit_logger.log_user_action.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_user_role_user_not_found(self, service, mock_db):
        """Test role update when user doesn't exist."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        updated_user = await service.update_user_role(999, UserRole.ADMIN, 2)
        
        assert updated_user is None
        mock_db.commit.assert_not_called()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_user_status_activate(self, service, mock_db, sample_user):
        """Test activating a user."""
        sample_user.is_active = False
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_user
        mock_db.query.return_value = mock_query
        
        updated_user = await service.update_user_status(1, True, 2)
        
        assert updated_user.is_active is True
        mock_db.commit.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_user_status_deactivate(self, service, mock_db, sample_user):
        """Test deactivating a user."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_user
        mock_db.query.return_value = mock_query
        
        updated_user = await service.update_user_status(1, False, 2)
        
        assert updated_user.is_active is False
        service.audit_logger.log_user_action.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_assign_user_to_team_success(self, service, mock_db, sample_user, sample_team):
        """Test successful user team assignment."""
        def query_side_effect(model):
            mock_query = Mock()
            if model == User:
                mock_query.filter.return_value.first.return_value = sample_user
            elif model == Team:
                mock_query.filter.return_value.first.return_value = sample_team
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        updated_user = await service.assign_user_to_team(1, "team-123", 2)
        
        assert updated_user is not None
        assert updated_user.team_id == "team-123"
        mock_db.commit.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_assign_user_to_team_user_not_found(self, service, mock_db, sample_team):
        """Test team assignment when user doesn't exist."""
        def query_side_effect(model):
            mock_query = Mock()
            if model == User:
                mock_query.filter.return_value.first.return_value = None
            elif model == Team:
                mock_query.filter.return_value.first.return_value = sample_team
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        updated_user = await service.assign_user_to_team(999, "team-123", 2)
        
        assert updated_user is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_assign_user_to_team_team_not_found(self, service, mock_db, sample_user):
        """Test team assignment when team doesn't exist."""
        def query_side_effect(model):
            mock_query = Mock()
            if model == User:
                mock_query.filter.return_value.first.return_value = sample_user
            elif model == Team:
                mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        updated_user = await service.assign_user_to_team(1, "invalid-team", 2)
        
        assert updated_user is None
    
    # Team Management Tests
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_team_success(self, service, mock_db):
        """Test successful team creation."""
        team_data = TeamCreate(name="New Team", settings={"key": "value"})
        
        created_team = await service.create_team(team_data, 2)
        
        assert created_team is not None
        assert created_team.name == "New Team"
        assert created_team.admin_id == 2
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        service.audit_logger.log_team_action.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_all_teams(self, service, mock_db, sample_team):
        """Test getting all teams."""
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = [sample_team]
        mock_db.query.return_value = mock_query
        
        teams = await service.get_all_teams()
        
        assert len(teams) == 1
        assert teams[0].id == sample_team.id
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_team_by_id_exists(self, service, mock_db, sample_team):
        """Test getting team by ID when team exists."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_team
        mock_db.query.return_value = mock_query
        
        team = await service.get_team_by_id("team-123")
        
        assert team is not None
        assert team.id == "team-123"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_team_by_id_not_exists(self, service, mock_db):
        """Test getting team by ID when team doesn't exist."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        team = await service.get_team_by_id("invalid-team")
        
        assert team is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_team_success(self, service, mock_db, sample_team):
        """Test successful team update."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_team
        mock_db.query.return_value = mock_query
        
        team_data = TeamUpdate(name="Updated Team", settings={"new": "settings"})
        updated_team = await service.update_team("team-123", team_data, 2)
        
        assert updated_team is not None
        assert updated_team.name == "Updated Team"
        mock_db.commit.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_team_not_found(self, service, mock_db):
        """Test team update when team doesn't exist."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        team_data = TeamUpdate(name="Updated Team")
        updated_team = await service.update_team("invalid-team", team_data, 2)
        
        assert updated_team is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_team_success(self, service, mock_db, sample_team):
        """Test successful team deletion."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_team
        mock_query.filter.return_value.count.return_value = 3
        mock_query.filter.return_value.update.return_value = None
        mock_db.query.return_value = mock_query
        
        result = await service.delete_team("team-123", 2)
        
        assert result is True
        mock_db.delete.assert_called_once_with(sample_team)
        mock_db.commit.assert_called_once()
        service.audit_logger.log_team_action.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_team_not_found(self, service, mock_db):
        """Test team deletion when team doesn't exist."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = await service.delete_team("invalid-team", 2)
        
        assert result is False
        mock_db.delete.assert_not_called()
    
    # Analytics Tests
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_team_analytics_success(self, service, mock_db, sample_team, sample_user):
        """Test getting team analytics."""
        # Setup mocks for different queries
        def query_side_effect(model):
            mock_query = Mock()
            if model == Team:
                mock_query.filter.return_value.first.return_value = sample_team
            elif model == User:
                mock_query.filter.return_value.all.return_value = [sample_user]
            elif model == DirectAnalysis:
                mock_query.filter.return_value.scalar.return_value = 10
                mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
            elif model == FeedbackRecord:
                mock_query.filter.return_value.scalar.return_value = 5
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        # Mock func.count
        with patch('app.services.admin_service.func'):
            analytics = await service.get_team_analytics("team-123")
        
        assert analytics is not None
        assert analytics["team_id"] == "team-123"
        assert "member_count" in analytics
        assert "total_analyses" in analytics
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_team_analytics_team_not_found(self, service, mock_db):
        """Test getting analytics for non-existent team."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        analytics = await service.get_team_analytics("invalid-team")
        
        assert analytics is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_platform_analytics(self, service, mock_db):
        """Test getting platform-wide analytics."""
        mock_query = Mock()
        mock_query.scalar.return_value = 100
        mock_query.filter.return_value.scalar.return_value = 50
        mock_db.query.return_value = mock_query
        
        with patch('app.services.admin_service.func'):
            analytics = await service.get_platform_analytics()
        
        assert analytics is not None
        assert "total_users" in analytics
        assert "total_teams" in analytics
        assert "total_analyses" in analytics
        assert "role_distribution" in analytics
    
    # Audit Log Tests
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_audit_logs_no_filters(self, service, mock_db):
        """Test getting audit logs without filters."""
        mock_query = Mock()
        mock_query.count.return_value = 10
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        logs, total = await service.get_audit_logs()
        
        assert total == 10
        assert isinstance(logs, list)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_audit_logs_with_filters(self, service, mock_db):
        """Test getting audit logs with filters."""
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 5
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        logs, total = await service.get_audit_logs(
            admin_user_id=2,
            action="update_role",
            resource_type="user"
        )
        
        assert total == 5
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_audit_logs_with_date_range(self, service, mock_db):
        """Test getting audit logs with date range filter."""
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 3
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        logs, total = await service.get_audit_logs(
            start_date=start_date,
            end_date=end_date
        )
        
        assert total == 3
