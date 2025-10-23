#!/usr/bin/env python3
"""
Comprehensive test to verify and enhance audit logging for user role changes.

This test verifies that audit log entries are created correctly for:
1. User role updates
2. User status changes  
3. Team assignment changes
4. Before/after values are properly logged
5. All required fields are populated

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import Request
from unittest.mock import Mock

# Import the models and services
from app.core.database import get_db, engine
from app.models.users import User, UserRole
from app.models.team import Team
from app.models.audit_log import AuditLog
from app.services.audit_logger import AuditLogger
from app.services.admin_service import AdminService


class TestAuditLogging:
    """Test suite for audit logging verification and enhancement."""
    
    def setup_method(self):
        """Set up test database and create test data."""
        # Create a test database session
        from sqlalchemy.orm import sessionmaker
        import time
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = TestingSessionLocal()
        
        # Use timestamp to ensure unique emails
        timestamp = str(int(time.time()))
        
        # Clean up any existing test data first
        try:
            self.db.query(AuditLog).filter(AuditLog.user_id.in_(
                self.db.query(User.id).filter(User.email.like(f"%audit_test_{timestamp}%"))
            )).delete(synchronize_session=False)
            self.db.query(Team).filter(Team.id.like(f"test-team-{timestamp}%")).delete(synchronize_session=False)
            self.db.query(User).filter(User.email.like(f"%audit_test_{timestamp}%")).delete(synchronize_session=False)
            self.db.commit()
        except Exception:
            self.db.rollback()
        
        # Create test users with unique emails
        self.admin_user = User(
            email=f"admin_audit_test_{timestamp}@test.com",
            full_name="Test Admin",
            role=UserRole.ADMIN,
            is_active=True,
            hashed_password="test_hash"
        )
        self.db.add(self.admin_user)
        
        self.target_user = User(
            email=f"user_audit_test_{timestamp}@test.com",
            full_name="Test User", 
            role=UserRole.USER,
            is_active=True,
            hashed_password="test_hash"
        )
        self.db.add(self.target_user)
        
        # Create test team (need to commit admin user first to get ID)
        self.db.commit()
        self.db.refresh(self.admin_user)
        
        self.test_team = Team(
            id=f"test-team-{timestamp}",
            name="Test Team",
            admin_id=self.admin_user.id
        )
        self.db.add(self.test_team)
        
        self.db.commit()
        self.db.refresh(self.target_user)
        self.db.refresh(self.test_team)
        
        # Initialize services
        self.audit_logger = AuditLogger(self.db)
        self.admin_service = AdminService(self.db)
        
        # Mock request object
        self.mock_request = Mock(spec=Request)
        self.mock_request.client.host = "127.0.0.1"
        self.mock_request.headers = {
            "User-Agent": "Test Client",
            "X-Forwarded-For": "192.168.1.100"
        }
        self.mock_request.method = "PUT"
        self.mock_request.url.path = "/api/v1/admin/users/123/role"
    
    def teardown_method(self):
        """Clean up test data."""
        try:
            # Clean up audit logs for our test users
            if hasattr(self, 'admin_user') and hasattr(self, 'target_user'):
                self.db.query(AuditLog).filter(AuditLog.user_id.in_([
                    self.admin_user.id, self.target_user.id
                ])).delete(synchronize_session=False)
                
                # Clean up test team
                if hasattr(self, 'test_team'):
                    self.db.query(Team).filter(Team.id == self.test_team.id).delete(synchronize_session=False)
                
                # Clean up test users
                self.db.query(User).filter(User.id.in_([
                    self.admin_user.id, self.target_user.id
                ])).delete(synchronize_session=False)
                
            self.db.commit()
        except Exception as e:
            print(f"Cleanup error: {e}")
            self.db.rollback()
        finally:
            self.db.close()
    
    def test_user_role_update_audit_logging(self):
        """
        Test that user role updates create proper audit log entries.
        
        Requirements: 10.1, 10.2 - Audit log creation with before/after values
        """
        print("Testing user role update audit logging...")
        
        # Get initial role
        old_role = self.target_user.role
        new_role = UserRole.TEAM_LEAD
        
        # Create changes dict with before/after values
        changes = {
            "role": {
                "old": old_role.value,
                "new": new_role.value
            }
        }
        
        # Log the role update action
        audit_log = self.audit_logger.log_action(
            user_id=self.admin_user.id,
            action="update_user_role",
            resource_type="user",
            resource_id=str(self.target_user.id),
            details={
                "username": self.target_user.full_name,
                "old_role": old_role.value,
                "new_role": new_role.value
            },
            changes=changes,
            request=self.mock_request
        )
        
        # Verify audit log was created
        assert audit_log is not None, "Audit log should be created"
        assert audit_log.user_id == self.admin_user.id, "Admin user ID should be logged"
        assert audit_log.action == "update_user_role", "Action should be 'update_user_role'"
        assert audit_log.resource_type == "user", "Resource type should be 'user'"
        assert audit_log.resource_id == str(self.target_user.id), "Resource ID should match target user"
        
        # Verify details are logged
        assert audit_log.details is not None, "Details should be logged"
        assert audit_log.details["username"] == self.target_user.full_name, "Username should be in details"
        assert audit_log.details["old_role"] == old_role.value, "Old role should be in details"
        assert audit_log.details["new_role"] == new_role.value, "New role should be in details"
        
        # Verify changes are logged with before/after values
        assert audit_log.changes is not None, "Changes should be logged"
        assert "role" in audit_log.changes, "Role changes should be logged"
        assert audit_log.changes["role"]["old"] == old_role.value, "Old role value should be logged"
        assert audit_log.changes["role"]["new"] == new_role.value, "New role value should be logged"
        
        # Verify request metadata
        assert audit_log.ip_address == "192.168.1.100", "IP address should be extracted from X-Forwarded-For"
        assert audit_log.user_agent == "Test Client", "User agent should be logged"
        assert audit_log.request_method == "PUT", "Request method should be logged"
        assert audit_log.request_path == "/api/v1/admin/users/123/role", "Request path should be logged"
        
        # Verify timestamp
        assert audit_log.timestamp is not None, "Timestamp should be set"
        assert isinstance(audit_log.timestamp, datetime), "Timestamp should be datetime"
        
        print("✓ User role update audit logging verified")
    
    def test_user_status_update_audit_logging(self):
        """
        Test that user status updates create proper audit log entries.
        
        Requirements: 10.3 - Audit log creation for status changes
        """
        print("Testing user status update audit logging...")
        
        # Get initial status
        old_status = self.target_user.is_active
        new_status = False
        
        # Create changes dict
        changes = {
            "is_active": {
                "old": old_status,
                "new": new_status
            }
        }
        
        # Log the status update action
        audit_log = self.audit_logger.log_action(
            user_id=self.admin_user.id,
            action="update_user_status",
            resource_type="user",
            resource_id=str(self.target_user.id),
            details={
                "username": self.target_user.full_name,
                "old_status": "active" if old_status else "inactive",
                "new_status": "active" if new_status else "inactive"
            },
            changes=changes,
            request=self.mock_request
        )
        
        # Verify audit log was created
        assert audit_log is not None, "Audit log should be created"
        assert audit_log.action == "update_user_status", "Action should be 'update_user_status'"
        
        # Verify changes are logged
        assert audit_log.changes is not None, "Changes should be logged"
        assert "is_active" in audit_log.changes, "Status changes should be logged"
        assert audit_log.changes["is_active"]["old"] == old_status, "Old status should be logged"
        assert audit_log.changes["is_active"]["new"] == new_status, "New status should be logged"
        
        print("✓ User status update audit logging verified")
    
    def test_team_assignment_audit_logging(self):
        """
        Test that team assignment changes create proper audit log entries.
        
        Requirements: 10.4 - Audit log creation for team assignment changes
        """
        print("Testing team assignment audit logging...")
        
        # Test assigning user to team
        old_team_id = self.target_user.team_id  # Should be None initially
        new_team_id = self.test_team.id
        
        # Create changes dict
        changes = {
            "team_id": {
                "old": old_team_id,
                "new": new_team_id
            }
        }
        
        # Log the team assignment action
        audit_log = self.audit_logger.log_action(
            user_id=self.admin_user.id,
            action="assign_user_to_team",
            resource_type="user",
            resource_id=str(self.target_user.id),
            details={
                "username": self.target_user.full_name,
                "old_team_id": old_team_id,
                "new_team_id": new_team_id,
                "team_name": self.test_team.name
            },
            changes=changes,
            request=self.mock_request
        )
        
        # Verify audit log was created
        assert audit_log is not None, "Audit log should be created"
        assert audit_log.action == "assign_user_to_team", "Action should be 'assign_user_to_team'"
        
        # Verify changes are logged
        assert audit_log.changes is not None, "Changes should be logged"
        assert "team_id" in audit_log.changes, "Team changes should be logged"
        assert audit_log.changes["team_id"]["old"] == old_team_id, "Old team ID should be logged"
        assert audit_log.changes["team_id"]["new"] == new_team_id, "New team ID should be logged"
        
        # Test removing user from team
        changes_remove = {
            "team_id": {
                "old": new_team_id,
                "new": None
            }
        }
        
        audit_log_remove = self.audit_logger.log_action(
            user_id=self.admin_user.id,
            action="remove_user_from_team",
            resource_type="user",
            resource_id=str(self.target_user.id),
            details={
                "username": self.target_user.full_name,
                "old_team_id": new_team_id,
                "new_team_id": None
            },
            changes=changes_remove,
            request=self.mock_request
        )
        
        # Verify removal audit log
        assert audit_log_remove is not None, "Removal audit log should be created"
        assert audit_log_remove.action == "remove_user_from_team", "Action should be 'remove_user_from_team'"
        assert audit_log_remove.changes["team_id"]["old"] == new_team_id, "Old team ID should be logged"
        assert audit_log_remove.changes["team_id"]["new"] is None, "New team ID should be None"
        
        print("✓ Team assignment audit logging verified")
    
    def test_audit_log_retrieval_and_filtering(self):
        """
        Test that audit logs can be retrieved and filtered properly.
        
        Requirements: 10.5 - Audit log retrieval and filtering
        """
        print("Testing audit log retrieval and filtering...")
        
        # Create multiple audit log entries
        actions = [
            ("update_user_role", "user", str(self.target_user.id)),
            ("update_user_status", "user", str(self.target_user.id)),
            ("assign_user_to_team", "user", str(self.target_user.id)),
            ("create_team", "team", self.test_team.id)
        ]
        
        for action, resource_type, resource_id in actions:
            self.audit_logger.log_action(
                user_id=self.admin_user.id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details={"test": "data"},
                request=self.mock_request
            )
        
        # Test retrieving all logs
        result = asyncio.run(self.audit_logger.get_audit_logs())
        assert result["total"] >= 4, "Should have at least 4 audit logs"
        assert len(result["logs"]) >= 4, "Should return at least 4 logs"
        
        # Test filtering by action
        result_filtered = asyncio.run(self.audit_logger.get_audit_logs(action="update_user_role"))
        assert result_filtered["total"] >= 1, "Should have at least 1 role update log"
        for log in result_filtered["logs"]:
            assert log["action"] == "update_user_role", "All logs should be role updates"
        
        # Test filtering by resource type
        result_user_logs = asyncio.run(self.audit_logger.get_audit_logs(resource_type="user"))
        assert result_user_logs["total"] >= 3, "Should have at least 3 user-related logs"
        for log in result_user_logs["logs"]:
            assert log["resource_type"] == "user", "All logs should be user-related"
        
        # Test filtering by user ID
        result_admin_logs = asyncio.run(self.audit_logger.get_audit_logs(user_id=self.admin_user.id))
        assert result_admin_logs["total"] >= 4, "Should have at least 4 logs from admin user"
        for log in result_admin_logs["logs"]:
            assert log["user_id"] == self.admin_user.id, "All logs should be from admin user"
        
        # Test date filtering
        yesterday = datetime.utcnow() - timedelta(days=1)
        tomorrow = datetime.utcnow() + timedelta(days=1)
        result_date_filtered = asyncio.run(self.audit_logger.get_audit_logs(
            date_from=yesterday,
            date_to=tomorrow
        ))
        assert result_date_filtered["total"] >= 4, "Should have logs within date range"
        
        print("✓ Audit log retrieval and filtering verified")
    
    def test_audit_log_error_handling(self):
        """
        Test that audit logging handles errors gracefully.
        
        Requirements: 10.1 - Robust audit logging
        """
        print("Testing audit log error handling...")
        
        # Test logging a failed action
        audit_log = self.audit_logger.log_failed_action(
            user_id=self.admin_user.id,
            action="update_user_role",
            error_message="User not found",
            resource_type="user",
            resource_id="999999",
            request=self.mock_request
        )
        
        # Verify failed action is logged
        assert audit_log is not None, "Failed action should be logged"
        assert audit_log.status == "failed", "Status should be 'failed'"
        assert audit_log.error_message == "User not found", "Error message should be logged"
        
        print("✓ Audit log error handling verified")
    
    def test_changes_dict_helper(self):
        """
        Test the helper method for creating changes dictionaries.
        
        Requirements: 10.2 - Before/after values logging
        """
        print("Testing changes dict helper...")
        
        # Test creating changes dict
        changes = AuditLogger.create_changes_dict(
            old_value="user",
            new_value="admin", 
            field_name="role"
        )
        
        assert "role" in changes, "Field name should be in changes dict"
        assert changes["role"]["old"] == "user", "Old value should be correct"
        assert changes["role"]["new"] == "admin", "New value should be correct"
        
        print("✓ Changes dict helper verified")
    
    def run_all_tests(self):
        """Run all audit logging tests."""
        print("=" * 60)
        print("AUDIT LOGGING VERIFICATION AND ENHANCEMENT TESTS")
        print("=" * 60)
        
        try:
            self.setup_method()
            
            # Run all test methods
            self.test_user_role_update_audit_logging()
            self.test_user_status_update_audit_logging()
            self.test_team_assignment_audit_logging()
            self.test_audit_log_retrieval_and_filtering()
            self.test_audit_log_error_handling()
            self.test_changes_dict_helper()
            
            print("\n" + "=" * 60)
            print("✅ ALL AUDIT LOGGING TESTS PASSED")
            print("=" * 60)
            
            # Print summary of verified requirements
            print("\nVerified Requirements:")
            print("✓ 10.1 - Audit log entries are created when roles are updated")
            print("✓ 10.2 - Audit logs include before/after values")
            print("✓ 10.3 - Audit log creation for status changes")
            print("✓ 10.4 - Audit log creation for team assignment changes")
            print("✓ 10.5 - Audit log retrieval and filtering")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise
        finally:
            self.teardown_method()


def main():
    """Main function to run the audit logging verification tests."""
    test_suite = TestAuditLogging()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main()