"""
Unit tests for AuditLogger service.

Tests cover:
- Action logging
- User action logging
- Team action logging
- Analytics access logging
- Failed action logging
- Audit log retrieval

Requirements: 15.1, 15.3, 15.4
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from fastapi import Request
from sqlalchemy.orm import Session

from app.services.audit_logger import AuditLogger, AuditLogContext
from app.models.audit_log import AuditLog
from app.models.users import User


class TestAuditLogger:
    """Test suite for AuditLogger."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock(spec=Session)
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.query = Mock()
        return db
    
    @pytest.fixture
    def logger(self, mock_db):
        """Create an AuditLogger instance."""
        return AuditLogger(mock_db)
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI Request."""
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/v1/admin/users/1/role"
        request.headers = {"User-Agent": "TestClient/1.0"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        return request
    
    # Basic Logging Tests
    
    @pytest.mark.unit
    def test_log_action_basic(self, logger, mock_db):
        """Test basic action logging."""
        with patch.object(AuditLog, 'create_log', return_value=Mock(spec=AuditLog)) as mock_create:
            result = logger.log_action(
                user_id=1,
                action="test_action",
                resource_type="test_resource",
                resource_id="123"
            )
        
        assert result is not None
        mock_create.assert_called_once()
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.unit
    def test_log_action_with_details(self, logger, mock_db):
        """Test logging action with details."""
        details = {"key": "value", "count": 5}
        
        with patch.object(AuditLog, 'create_log', return_value=Mock(spec=AuditLog)) as mock_create:
            result = logger.log_action(
                user_id=1,
                action="test_action",
                details=details
            )
        
        assert result is not None
        call_args = mock_create.call_args[1]
        assert call_args["details"] == details
    
    @pytest.mark.unit
    def test_log_action_with_changes(self, logger, mock_db):
        """Test logging action with before/after changes."""
        changes = {
            "role": {"old": "user", "new": "admin"}
        }
        
        with patch.object(AuditLog, 'create_log', return_value=Mock(spec=AuditLog)) as mock_create:
            result = logger.log_action(
                user_id=1,
                action="update_role",
                changes=changes
            )
        
        assert result is not None
        call_args = mock_create.call_args[1]
        assert call_args["changes"] == changes
    
    @pytest.mark.unit
    def test_log_action_with_request(self, logger, mock_db, mock_request):
        """Test logging action with request metadata."""
        with patch.object(AuditLog, 'create_log', return_value=Mock(spec=AuditLog)) as mock_create:
            result = logger.log_action(
                user_id=1,
                action="test_action",
                request=mock_request
            )
        
        assert result is not None
        call_args = mock_create.call_args[1]
        assert call_args["ip_address"] == "192.168.1.1"
        assert call_args["user_agent"] == "TestClient/1.0"
        assert call_args["request_method"] == "POST"
        assert "/admin/users/" in call_args["request_path"]
    
    @pytest.mark.unit
    def test_log_action_failed_status(self, logger, mock_db):
        """Test logging failed action."""
        with patch.object(AuditLog, 'create_log', return_value=Mock(spec=AuditLog)) as mock_create:
            result = logger.log_action(
                user_id=1,
                action="test_action",
                status="failed",
                error_message="Something went wrong"
            )
        
        assert result is not None
        call_args = mock_create.call_args[1]
        assert call_args["status"] == "failed"
        assert call_args["error_message"] == "Something went wrong"
    
    @pytest.mark.unit
    def test_log_action_with_duration(self, logger, mock_db):
        """Test logging action with duration."""
        with patch.object(AuditLog, 'create_log', return_value=Mock(spec=AuditLog)) as mock_create:
            result = logger.log_action(
                user_id=1,
                action="test_action",
                duration_ms=150
            )
        
        assert result is not None
        call_args = mock_create.call_args[1]
        assert call_args["duration_ms"] == 150
    
    @pytest.mark.unit
    def test_log_action_exception_handling(self, logger, mock_db):
        """Test that logging exceptions don't break the main flow."""
        mock_db.add.side_effect = Exception("Database error")
        
        # Should not raise exception
        result = logger.log_action(
            user_id=1,
            action="test_action"
        )
        
        assert result is None  # Returns None on error
    
    # Specialized Logging Methods Tests
    
    @pytest.mark.unit
    def test_log_user_action(self, logger, mock_db):
        """Test logging user management action."""
        changes = {"role": {"old": "user", "new": "admin"}}
        
        with patch.object(logger, 'log_action') as mock_log:
            logger.log_user_action(
                admin_user_id=2,
                target_user_id=1,
                action="update_role",
                changes=changes
            )
        
        mock_log.assert_called_once()
        call_args = mock_log.call_args[1]
        assert call_args["user_id"] == 2
        assert call_args["action"] == "user_update_role"
        assert call_args["resource_type"] == "user"
        assert call_args["resource_id"] == "1"
        assert call_args["changes"] == changes
    
    @pytest.mark.unit
    def test_log_team_action_create(self, logger, mock_db):
        """Test logging team creation action."""
        details = {"team_name": "New Team"}
        
        with patch.object(logger, 'log_action') as mock_log:
            logger.log_team_action(
                admin_user_id=2,
                team_id="team-123",
                action="create",
                details=details
            )
        
        mock_log.assert_called_once()
        call_args = mock_log.call_args[1]
        assert call_args["action"] == "team_create"
        assert call_args["resource_type"] == "team"
        assert call_args["resource_id"] == "team-123"
        assert call_args["details"] == details
    
    @pytest.mark.unit
    def test_log_team_action_delete(self, logger, mock_db):
        """Test logging team deletion action."""
        details = {"team_name": "Old Team", "member_count": 5}
        
        with patch.object(logger, 'log_action') as mock_log:
            logger.log_team_action(
                admin_user_id=2,
                team_id="team-123",
                action="delete",
                details=details
            )
        
        mock_log.assert_called_once()
        call_args = mock_log.call_args[1]
        assert call_args["action"] == "team_delete"
        assert call_args["details"]["member_count"] == 5
    
    @pytest.mark.unit
    def test_log_analytics_access(self, logger, mock_db):
        """Test logging analytics access."""
        filters = {"team_id": "team-123", "date_range": "30d"}
        
        with patch.object(logger, 'log_action') as mock_log:
            logger.log_analytics_access(
                user_id=2,
                analytics_type="platform_stats",
                filters=filters
            )
        
        mock_log.assert_called_once()
        call_args = mock_log.call_args[1]
        assert call_args["action"] == "analytics_access_platform_stats"
        assert call_args["resource_type"] == "analytics"
        assert call_args["details"]["filters"] == filters
    
    @pytest.mark.unit
    def test_log_failed_action(self, logger, mock_db):
        """Test logging failed action."""
        with patch.object(logger, 'log_action') as mock_log:
            logger.log_failed_action(
                user_id=1,
                action="delete_team",
                error_message="Team has active members",
                resource_type="team",
                resource_id="team-123"
            )
        
        mock_log.assert_called_once()
        call_args = mock_log.call_args[1]
        assert call_args["status"] == "failed"
        assert call_args["error_message"] == "Team has active members"
    
    # IP Address Extraction Tests
    
    @pytest.mark.unit
    def test_get_client_ip_direct(self, logger):
        """Test extracting IP from direct client."""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        ip = logger._get_client_ip(request)
        
        assert ip == "192.168.1.1"
    
    @pytest.mark.unit
    def test_get_client_ip_forwarded(self, logger):
        """Test extracting IP from X-Forwarded-For header."""
        request = Mock(spec=Request)
        request.headers = {"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        ip = logger._get_client_ip(request)
        
        assert ip == "10.0.0.1"  # Should take first IP
    
    @pytest.mark.unit
    def test_get_client_ip_real_ip(self, logger):
        """Test extracting IP from X-Real-IP header."""
        request = Mock(spec=Request)
        request.headers = {"X-Real-IP": "10.0.0.1"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        ip = logger._get_client_ip(request)
        
        assert ip == "10.0.0.1"
    
    @pytest.mark.unit
    def test_get_client_ip_no_client(self, logger):
        """Test extracting IP when no client info available."""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = None
        
        ip = logger._get_client_ip(request)
        
        assert ip is None
    
    # Utility Methods Tests
    
    @pytest.mark.unit
    def test_create_changes_dict(self):
        """Test creating changes dictionary."""
        changes = AuditLogger.create_changes_dict("user", "admin", "role")
        
        assert changes == {
            "role": {
                "old": "user",
                "new": "admin"
            }
        }
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_audit_logs_no_filters(self, logger, mock_db):
        """Test retrieving audit logs without filters."""
        mock_log = Mock(spec=AuditLog)
        mock_log.id = 1
        mock_log.timestamp = datetime.utcnow()
        mock_log.user_id = 1
        mock_log.action = "test_action"
        mock_log.resource_type = "test"
        mock_log.resource_id = "123"
        mock_log.details = {}
        mock_log.ip_address = "192.168.1.1"
        mock_log.user_agent = "TestClient"
        
        mock_user = Mock(spec=User)
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        
        mock_query = Mock()
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_log]
        
        def query_side_effect(model):
            if model == AuditLog:
                return mock_query
            elif model == User:
                user_query = Mock()
                user_query.filter.return_value.first.return_value = mock_user
                return user_query
        
        mock_db.query.side_effect = query_side_effect
        
        result = await logger.get_audit_logs()
        
        assert result["total"] == 1
        assert len(result["logs"]) == 1
        assert result["logs"][0]["username"] == "Test User"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_audit_logs_with_filters(self, logger, mock_db):
        """Test retrieving audit logs with filters."""
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 0
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        
        result = await logger.get_audit_logs(
            action="update_role",
            resource_type="user",
            user_id=2
        )
        
        assert result["total"] == 0
        assert len(result["logs"]) == 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_available_actions(self, logger, mock_db):
        """Test getting available action types."""
        mock_query = Mock()
        mock_query.distinct.return_value.all.return_value = [
            ("update_role",),
            ("create_team",),
            ("delete_user",)
        ]
        mock_db.query.return_value = mock_query
        
        actions = await logger.get_available_actions()
        
        assert len(actions) == 3
        assert "update_role" in actions
        assert "create_team" in actions
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_available_resource_types(self, logger, mock_db):
        """Test getting available resource types."""
        mock_query = Mock()
        mock_query.distinct.return_value.all.return_value = [
            ("user",),
            ("team",),
            ("analytics",)
        ]
        mock_db.query.return_value = mock_query
        
        resource_types = await logger.get_available_resource_types()
        
        assert len(resource_types) == 3
        assert "user" in resource_types
        assert "team" in resource_types


class TestAuditLogContext:
    """Test suite for AuditLogContext context manager."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def logger(self, mock_db):
        """Create an AuditLogger instance."""
        return AuditLogger(mock_db)
    
    @pytest.mark.unit
    def test_context_manager_success(self, logger):
        """Test context manager for successful operation."""
        with patch.object(logger, 'log_action') as mock_log:
            with AuditLogContext(logger, 1, "test_action") as ctx:
                ctx.set_resource("test", "123")
                ctx.set_details({"key": "value"})
        
        mock_log.assert_called_once()
        call_args = mock_log.call_args[1]
        assert call_args["status"] == "success"
        assert call_args["resource_id"] == "123"
        assert call_args["details"]["key"] == "value"
        assert call_args["duration_ms"] is not None
    
    @pytest.mark.unit
    def test_context_manager_failure(self, logger):
        """Test context manager for failed operation."""
        with patch.object(logger, 'log_action') as mock_log:
            try:
                with AuditLogContext(logger, 1, "test_action") as ctx:
                    raise ValueError("Test error")
            except ValueError:
                pass
        
        mock_log.assert_called_once()
        call_args = mock_log.call_args[1]
        assert call_args["status"] == "failed"
        assert "Test error" in call_args["error_message"]
    
    @pytest.mark.unit
    def test_context_manager_set_changes(self, logger):
        """Test setting changes in context manager."""
        with patch.object(logger, 'log_action') as mock_log:
            with AuditLogContext(logger, 1, "test_action") as ctx:
                ctx.set_changes({"field": {"old": "a", "new": "b"}})
        
        mock_log.assert_called_once()
        call_args = mock_log.call_args[1]
        assert call_args["changes"] is not None
        assert call_args["changes"]["field"]["old"] == "a"
    
    @pytest.mark.unit
    def test_context_manager_with_request(self, logger):
        """Test context manager with request object."""
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.headers = {}
        mock_request.client = None
        
        with patch.object(logger, 'log_action') as mock_log:
            with AuditLogContext(logger, 1, "test_action", request=mock_request):
                pass
        
        mock_log.assert_called_once()
        call_args = mock_log.call_args[1]
        assert call_args["request"] == mock_request
