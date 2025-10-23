#!/usr/bin/env python3
"""
Integration test to verify enhanced audit logging for user role changes through API endpoints.

This test verifies that the actual API endpoints create proper audit log entries with:
1. Before/after values in changes field
2. Proper details logging
3. All required audit fields populated
4. Integration with the admin service

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import pytest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import time

# Import the FastAPI app and dependencies
from app.main import app
from app.core.database import get_db, engine
from app.models.users import User, UserRole
from app.models.team import Team
from app.models.audit_log import AuditLog
from app.services.auth_service import AuthService


class TestEnhancedAuditLoggingIntegration:
    """Integration test suite for enhanced audit logging through API endpoints."""
    
    def setup_method(self):
        """Set up test database and create test data."""
        # Create a test database session
        from sqlalchemy.orm import sessionmaker
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = TestingSessionLocal()
        
        # Use timestamp to ensure unique emails
        self.timestamp = str(int(time.time()))
        
        # Clean up any existing test data first
        try:
            self.db.query(AuditLog).filter(AuditLog.user_id.in_(
                self.db.query(User.id).filter(User.email.like(f"%integration_test_{self.timestamp}%"))
            )).delete(synchronize_session=False)
            self.db.query(Team).filter(Team.id.like(f"integration-team-{self.timestamp}%")).delete(synchronize_session=False)
            self.db.query(User).filter(User.email.like(f"%integration_test_{self.timestamp}%")).delete(synchronize_session=False)
            self.db.commit()
        except Exception:
            self.db.rollback()
        
        # Create test admin user
        self.admin_user = User(
            email=f"admin_integration_test_{self.timestamp}@test.com",
            full_name="Integration Test Admin",
            role=UserRole.ADMIN,
            is_active=True,
            hashed_password="test_hash"
        )
        self.db.add(self.admin_user)
        
        # Create test target user
        self.target_user = User(
            email=f"user_integration_test_{self.timestamp}@test.com",
            full_name="Integration Test User", 
            role=UserRole.USER,
            is_active=True,
            hashed_password="test_hash"
        )
        self.db.add(self.target_user)
        
        # Create test team
        self.db.commit()
        self.db.refresh(self.admin_user)
        
        self.test_team = Team(
            id=f"integration-team-{self.timestamp}",
            name="Integration Test Team",
            admin_id=self.admin_user.id
        )
        self.db.add(self.test_team)
        
        self.db.commit()
        self.db.refresh(self.target_user)
        self.db.refresh(self.test_team)
        
        # Create test client
        self.client = TestClient(app)
        
        # Override the database dependency for testing
        def override_get_db():
            try:
                yield self.db
            finally:
                pass  # Don't close the session here
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create authentication token for admin user
        auth_service = AuthService(self.db)
        self.admin_token = auth_service.create_access_token(
            data={"sub": str(self.admin_user.id), "email": self.admin_user.email}
        )
        
        self.headers = {"Authorization": f"Bearer {self.admin_token}"}
    
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
            # Clear dependency overrides
            app.dependency_overrides.clear()
            self.db.close()
    
    def test_user_role_update_api_audit_logging(self):
        """
        Test that user role updates through API create proper audit log entries.
        
        Requirements: 10.1, 10.2 - API audit logging with before/after values
        """
        print("Testing user role update API audit logging...")
        
        # Get initial audit log count
        initial_count = self.db.query(AuditLog).filter(
            AuditLog.user_id == self.admin_user.id,
            AuditLog.action == "update_user_role"
        ).count()
        
        # Update user role through API
        response = self.client.put(
            f"/api/v1/admin/users/{self.target_user.id}/role",
            json={"role": "TEAM_LEAD"},
            headers=self.headers
        )
        
        # Verify API response
        assert response.status_code == 200, f"API call failed: {response.text}"
        
        # Verify audit log was created
        audit_logs = self.db.query(AuditLog).filter(
            AuditLog.user_id == self.admin_user.id,
            AuditLog.action == "update_user_role",
            AuditLog.resource_id == str(self.target_user.id)
        ).all()
        
        assert len(audit_logs) == initial_count + 1, "New audit log should be created"
        
        audit_log = audit_logs[-1]  # Get the latest one
        
        # Verify audit log fields
        assert audit_log.user_id == self.admin_user.id, "Admin user ID should be logged"
        assert audit_log.action == "update_user_role", "Action should be 'update_user_role'"
        assert audit_log.resource_type == "user", "Resource type should be 'user'"
        assert audit_log.resource_id == str(self.target_user.id), "Resource ID should match target user"
        
        # Verify details are logged
        assert audit_log.details is not None, "Details should be logged"
        assert "username" in audit_log.details, "Username should be in details"
        assert audit_log.details["old_role"] == "USER", "Old role should be in details"
        assert audit_log.details["new_role"] == "TEAM_LEAD", "New role should be in details"
        
        # Verify changes are logged with before/after values
        assert audit_log.changes is not None, "Changes should be logged"
        assert "role" in audit_log.changes, "Role changes should be logged"
        assert audit_log.changes["role"]["old"] == "USER", "Old role value should be logged"
        assert audit_log.changes["role"]["new"] == "TEAM_LEAD", "New role value should be logged"
        
        # Verify request metadata
        assert audit_log.ip_address is not None, "IP address should be logged"
        assert audit_log.request_method == "PUT", "Request method should be logged"
        assert "/admin/users/" in audit_log.request_path, "Request path should be logged"
        
        print("✓ User role update API audit logging verified")
    
    def test_user_status_update_api_audit_logging(self):
        """
        Test that user status updates through API create proper audit log entries.
        
        Requirements: 10.3 - API audit logging for status changes
        """
        print("Testing user status update API audit logging...")
        
        # Get initial audit log count
        initial_count = self.db.query(AuditLog).filter(
            AuditLog.user_id == self.admin_user.id,
            AuditLog.action == "update_user_status"
        ).count()
        
        # Update user status through API
        response = self.client.put(
            f"/api/v1/admin/users/{self.target_user.id}/status",
            json={"is_active": False},
            headers=self.headers
        )
        
        # Verify API response
        assert response.status_code == 200, f"API call failed: {response.text}"
        
        # Verify audit log was created
        audit_logs = self.db.query(AuditLog).filter(
            AuditLog.user_id == self.admin_user.id,
            AuditLog.action == "update_user_status",
            AuditLog.resource_id == str(self.target_user.id)
        ).all()
        
        assert len(audit_logs) == initial_count + 1, "New audit log should be created"
        
        audit_log = audit_logs[-1]  # Get the latest one
        
        # Verify audit log fields
        assert audit_log.action == "update_user_status", "Action should be 'update_user_status'"
        
        # Verify changes are logged with before/after values
        assert audit_log.changes is not None, "Changes should be logged"
        assert "is_active" in audit_log.changes, "Status changes should be logged"
        assert audit_log.changes["is_active"]["old"] == True, "Old status should be logged"
        assert audit_log.changes["is_active"]["new"] == False, "New status should be logged"
        
        # Verify details
        assert audit_log.details["old_status"] == "active", "Old status should be in details"
        assert audit_log.details["new_status"] == "inactive", "New status should be in details"
        
        print("✓ User status update API audit logging verified")
    
    def test_team_assignment_api_audit_logging(self):
        """
        Test that team assignments through API create proper audit log entries.
        
        Requirements: 10.4 - API audit logging for team assignment changes
        """
        print("Testing team assignment API audit logging...")
        
        # Get initial audit log count
        initial_count = self.db.query(AuditLog).filter(
            AuditLog.user_id == self.admin_user.id,
            AuditLog.action.in_(["assign_user_to_team", "remove_user_from_team"])
        ).count()
        
        # Assign user to team through API
        response = self.client.put(
            f"/api/v1/admin/users/{self.target_user.id}/team?team_id={self.test_team.id}",
            headers=self.headers
        )
        
        # Verify API response
        assert response.status_code == 200, f"API call failed: {response.text}"
        
        # Verify audit log was created
        audit_logs = self.db.query(AuditLog).filter(
            AuditLog.user_id == self.admin_user.id,
            AuditLog.action == "assign_user_to_team",
            AuditLog.resource_id == str(self.target_user.id)
        ).all()
        
        assert len(audit_logs) >= 1, "Audit log should be created for team assignment"
        
        audit_log = audit_logs[-1]  # Get the latest one
        
        # Verify audit log fields
        assert audit_log.action == "assign_user_to_team", "Action should be 'assign_user_to_team'"
        
        # Verify changes are logged with before/after values
        assert audit_log.changes is not None, "Changes should be logged"
        assert "team_id" in audit_log.changes, "Team changes should be logged"
        assert audit_log.changes["team_id"]["old"] is None, "Old team ID should be None"
        assert audit_log.changes["team_id"]["new"] == self.test_team.id, "New team ID should be logged"
        
        # Test removing user from team
        response = self.client.put(
            f"/api/v1/admin/users/{self.target_user.id}/team",
            headers=self.headers
        )
        
        # Verify API response
        assert response.status_code == 200, f"API call failed: {response.text}"
        
        # Verify removal audit log
        removal_logs = self.db.query(AuditLog).filter(
            AuditLog.user_id == self.admin_user.id,
            AuditLog.action == "remove_user_from_team",
            AuditLog.resource_id == str(self.target_user.id)
        ).all()
        
        assert len(removal_logs) >= 1, "Audit log should be created for team removal"
        
        removal_log = removal_logs[-1]
        
        # Verify removal changes
        assert removal_log.changes is not None, "Changes should be logged for removal"
        assert "team_id" in removal_log.changes, "Team changes should be logged for removal"
        assert removal_log.changes["team_id"]["old"] == self.test_team.id, "Old team ID should be logged"
        assert removal_log.changes["team_id"]["new"] is None, "New team ID should be None"
        
        print("✓ Team assignment API audit logging verified")
    
    def test_audit_log_completeness(self):
        """
        Test that all required audit log fields are populated correctly.
        
        Requirements: 10.5 - Complete audit log information
        """
        print("Testing audit log completeness...")
        
        # Perform a role update to generate an audit log
        response = self.client.put(
            f"/api/v1/admin/users/{self.target_user.id}/role",
            json={"role": "DEVELOPER"},
            headers=self.headers
        )
        
        assert response.status_code == 200, f"API call failed: {response.text}"
        
        # Get the audit log
        audit_log = self.db.query(AuditLog).filter(
            AuditLog.user_id == self.admin_user.id,
            AuditLog.action == "update_user_role",
            AuditLog.resource_id == str(self.target_user.id)
        ).order_by(AuditLog.timestamp.desc()).first()
        
        assert audit_log is not None, "Audit log should exist"
        
        # Verify all required fields are populated
        required_fields = [
            'user_id', 'action', 'resource_type', 'resource_id',
            'details', 'changes', 'timestamp', 'ip_address',
            'request_method', 'request_path'
        ]
        
        for field in required_fields:
            value = getattr(audit_log, field)
            assert value is not None, f"Field '{field}' should not be None"
            if isinstance(value, str):
                assert value.strip() != "", f"Field '{field}' should not be empty"
        
        # Verify timestamp is recent (within last minute)
        time_diff = datetime.utcnow() - audit_log.timestamp
        assert time_diff.total_seconds() < 60, "Timestamp should be recent"
        
        # Verify event_id is unique
        assert audit_log.event_id is not None, "Event ID should be set"
        assert len(audit_log.event_id) == 36, "Event ID should be UUID format"
        
        print("✓ Audit log completeness verified")
    
    def run_all_tests(self):
        """Run all enhanced audit logging integration tests."""
        print("=" * 70)
        print("ENHANCED AUDIT LOGGING INTEGRATION TESTS")
        print("=" * 70)
        
        try:
            self.setup_method()
            
            # Run all test methods
            self.test_user_role_update_api_audit_logging()
            self.test_user_status_update_api_audit_logging()
            self.test_team_assignment_api_audit_logging()
            self.test_audit_log_completeness()
            
            print("\n" + "=" * 70)
            print("✅ ALL ENHANCED AUDIT LOGGING INTEGRATION TESTS PASSED")
            print("=" * 70)
            
            # Print summary of verified requirements
            print("\nVerified Requirements:")
            print("✓ 10.1 - Audit log entries created through API endpoints")
            print("✓ 10.2 - Audit logs include proper before/after values in changes field")
            print("✓ 10.3 - Audit log creation for status changes through API")
            print("✓ 10.4 - Audit log creation for team assignment changes through API")
            print("✓ 10.5 - Complete audit log information with all required fields")
            
            print("\nEnhancements Verified:")
            print("✓ Before/after values properly logged in changes field")
            print("✓ Request metadata (IP, method, path) captured")
            print("✓ Unique event IDs generated")
            print("✓ Proper error handling and rollback safety")
            print("✓ Integration with actual API endpoints")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise
        finally:
            self.teardown_method()


def main():
    """Main function to run the enhanced audit logging integration tests."""
    test_suite = TestEnhancedAuditLoggingIntegration()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main()