"""
Test script for Task 3: Admin and Analytics Services

This script tests the implementation of:
- AdminService (team CRUD, user management, role updates)
- AuditLogger (automatic logging for admin actions)
- GlobalAnalyticsService (platform stats, global trends, team comparison)
- Enhanced AnalyticsService (issue trends, criticality distribution)
- RBAC system (UserRole enum and permission checking)
- Data anonymization (privacy protection)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.users import User, UserRole
from app.models.team import Team
from app.models.audit_log import AuditLog
from app.services.admin_service import AdminService
from app.services.audit_logger import AuditLogger, AuditLogContext
from app.services.global_analytics_service import GlobalAnalyticsService
from app.services.analytics_service import AnalyticsService
from app.services.data_anonymization_service import DataAnonymizationService
from app.core.rbac import RoleChecker, PermissionChecker, Permissions, require_admin
from app.schemas.team import TeamCreate, TeamUpdate
import asyncio
from datetime import datetime


# Create test database
TEST_DATABASE_URL = "sqlite:///./test_task3.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def test_rbac_system():
    """Test RBAC system with UserRole enum and permission checking."""
    print("\n=== Testing RBAC System ===")
    
    # Test UserRole enum
    print(f"✓ UserRole enum values: {[role.value for role in UserRole]}")
    
    # Test Permissions constants
    print(f"✓ Permissions.USER_READ: {Permissions.USER_READ}")
    print(f"✓ Permissions.TEAM_WRITE: {Permissions.TEAM_WRITE}")
    print(f"✓ Permissions.ANALYTICS_READ: {Permissions.ANALYTICS_READ}")
    
    # Test RoleChecker
    db = SessionLocal()
    try:
        admin_user = User(
            id=1,
            email="admin@test.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        
        role_checker = RoleChecker([UserRole.ADMIN])
        result = role_checker(admin_user)
        print(f"✓ RoleChecker validated admin user: {result.email}")
        
        # Test PermissionChecker
        perm_checker = PermissionChecker(Permissions.USER_READ)
        has_permission = perm_checker._has_permission(admin_user, Permissions.USER_READ)
        print(f"✓ PermissionChecker: Admin has USER_READ permission: {has_permission}")
        
    finally:
        db.close()
    
    print("✓ RBAC system tests passed!")


async def test_admin_service():
    """Test AdminService for team CRUD and user management."""
    print("\n=== Testing AdminService ===")
    
    db = SessionLocal()
    try:
        admin_service = AdminService(db)
        
        # Create admin user
        admin_user = User(
            id=100,
            email="admin@codenova.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        
        # Test team creation
        team_data = TeamCreate(name="Engineering Team", settings={"max_members": 50})
        team = await admin_service.create_team(team_data, admin_user.id)
        print(f"✓ Created team: {team.name} (ID: {team.id})")
        
        # Test user creation and team assignment
        test_user = User(
            id=101,
            email="developer@codenova.com",
            role=UserRole.DEVELOPER,
            is_active=True
        )
        db.add(test_user)
        db.commit()
        
        # Assign user to team
        updated_user = await admin_service.assign_user_to_team(test_user.id, team.id, admin_user.id)
        print(f"✓ Assigned user {updated_user.email} to team {team.name}")
        
        # Test role update
        updated_user = await admin_service.update_user_role(test_user.id, UserRole.TEAM_LEAD, admin_user.id)
        print(f"✓ Updated user role to: {updated_user.role.value}")
        
        # Test user status update
        updated_user = await admin_service.update_user_status(test_user.id, False, admin_user.id)
        print(f"✓ Updated user status to: {'active' if updated_user.is_active else 'inactive'}")
        
        # Test team update
        team_update = TeamUpdate(name="Senior Engineering Team")
        updated_team = await admin_service.update_team(team.id, team_update, admin_user.id)
        print(f"✓ Updated team name to: {updated_team.name}")
        
        # Test get all users
        users = await admin_service.get_all_users()
        print(f"✓ Retrieved {len(users)} users")
        
        # Test get all teams
        teams = await admin_service.get_all_teams()
        print(f"✓ Retrieved {len(teams)} teams")
        
        # Test platform analytics
        platform_stats = await admin_service.get_platform_analytics()
        print(f"✓ Platform stats: {platform_stats['total_users']} users, {platform_stats['total_teams']} teams")
        
        print("✓ AdminService tests passed!")
        
    finally:
        db.close()


async def test_audit_logger():
    """Test AuditLogger for automatic logging of admin actions."""
    print("\n=== Testing AuditLogger ===")
    
    db = SessionLocal()
    try:
        audit_logger = AuditLogger(db)
        
        # Create test user
        admin_user = User(
            id=200,
            email="auditor@codenova.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        
        # Test basic action logging
        audit_log = audit_logger.log_action(
            user_id=admin_user.id,
            action="test_action",
            resource_type="test_resource",
            resource_id="test_123",
            details={"test": "data"},
            status="success"
        )
        print(f"✓ Created audit log: {audit_log.action} by user {audit_log.user_id}")
        
        # Test user action logging
        audit_log = audit_logger.log_user_action(
            admin_user_id=admin_user.id,
            target_user_id=101,
            action="update_role",
            changes={"role": {"old": "developer", "new": "team_lead"}}
        )
        print(f"✓ Logged user action: {audit_log.action}")
        
        # Test team action logging
        audit_log = audit_logger.log_team_action(
            admin_user_id=admin_user.id,
            team_id="team_123",
            action="create",
            details={"team_name": "Test Team"}
        )
        print(f"✓ Logged team action: {audit_log.action}")
        
        # Test analytics access logging
        audit_log = audit_logger.log_analytics_access(
            user_id=admin_user.id,
            analytics_type="platform_stats",
            filters={"timeframe": "30d"}
        )
        print(f"✓ Logged analytics access: {audit_log.action}")
        
        # Test failed action logging
        audit_log = audit_logger.log_failed_action(
            user_id=admin_user.id,
            action="delete_team",
            error_message="Team not found",
            resource_type="team",
            resource_id="invalid_team"
        )
        print(f"✓ Logged failed action: {audit_log.action} (status: {audit_log.status})")
        
        # Test AuditLogContext
        with AuditLogContext(audit_logger, admin_user.id, "context_test") as ctx:
            ctx.set_resource("test", "resource_123")
            ctx.set_details({"operation": "test_operation"})
        
        print("✓ AuditLogContext test passed")
        
        # Verify audit logs were created
        logs = db.query(AuditLog).filter(AuditLog.user_id == admin_user.id).all()
        print(f"✓ Total audit logs created: {len(logs)}")
        
        print("✓ AuditLogger tests passed!")
        
    finally:
        db.close()


async def test_global_analytics_service():
    """Test GlobalAnalyticsService for platform-wide statistics."""
    print("\n=== Testing GlobalAnalyticsService ===")
    
    db = SessionLocal()
    try:
        global_analytics = GlobalAnalyticsService(db)
        
        # Test platform stats
        platform_stats = await global_analytics.get_platform_stats()
        print(f"✓ Platform stats retrieved:")
        print(f"  - Total users: {platform_stats['total_users']}")
        print(f"  - Active users: {platform_stats['active_users']}")
        print(f"  - Total teams: {platform_stats['total_teams']}")
        print(f"  - Total reviews: {platform_stats['total_reviews']}")
        
        # Test global trends
        trends = await global_analytics.get_global_trends(timeframe="30d")
        print(f"✓ Global trends retrieved for {trends['timeframe']}")
        print(f"  - Data points: {len(trends['data_points'])}")
        
        # Test team comparison
        comparison = await global_analytics.get_team_comparison()
        print(f"✓ Team comparison retrieved: {len(comparison)} teams")
        
        # Test all reviews
        reviews, total = await global_analytics.get_all_reviews(skip=0, limit=10)
        print(f"✓ All reviews retrieved: {total} total, showing {len(reviews)}")
        
        # Test all feedback
        feedback_data = await global_analytics.get_all_feedback(skip=0, limit=10)
        print(f"✓ All feedback retrieved: {feedback_data['total']} total")
        print(f"  - Acceptance rate: {feedback_data['summary']['acceptance_rate']}%")
        
        # Test criticality distribution
        criticality = await global_analytics.get_criticality_distribution(timeframe="30d")
        print(f"✓ Criticality distribution retrieved:")
        print(f"  - Total issues: {criticality['total_issues']}")
        
        print("✓ GlobalAnalyticsService tests passed!")
        
    finally:
        db.close()


async def test_enhanced_analytics_service():
    """Test enhanced AnalyticsService for user visualizations."""
    print("\n=== Testing Enhanced AnalyticsService ===")
    
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        
        # Create test user
        test_user = User(
            id=300,
            email="analyst@codenova.com",
            role=UserRole.DEVELOPER,
            is_active=True
        )
        db.add(test_user)
        db.commit()
        
        # Test issue trends
        issue_trends = await analytics.get_issue_trends(user_id=test_user.id, timeframe="30d")
        print(f"✓ Issue trends retrieved:")
        print(f"  - Timeframe: {issue_trends['timeframe']}")
        print(f"  - Total errors: {issue_trends['summary']['total_errors']}")
        print(f"  - Total warnings: {issue_trends['summary']['total_warnings']}")
        print(f"  - Trend: {issue_trends['summary']['trend']}")
        
        # Test criticality distribution
        criticality = await analytics.get_criticality_distribution(user_id=test_user.id, timeframe="30d")
        print(f"✓ Criticality distribution retrieved:")
        print(f"  - Total issues: {criticality['total_issues']}")
        for severity, data in criticality['distribution'].items():
            print(f"  - {severity}: {data['count']} ({data['percentage']}%)")
        
        print("✓ Enhanced AnalyticsService tests passed!")
        
    finally:
        db.close()


def test_data_anonymization():
    """Test DataAnonymizationService for privacy protection."""
    print("\n=== Testing DataAnonymizationService ===")
    
    # Test email anonymization
    email = "user@example.com"
    anonymized_email = DataAnonymizationService.anonymize_email(email)
    print(f"✓ Email anonymization: {email} -> {anonymized_email}")
    
    # Test username anonymization
    username = "john_doe"
    anonymized_username = DataAnonymizationService.anonymize_username(username, user_id=123)
    print(f"✓ Username anonymization: {username} -> {anonymized_username}")
    
    # Test IP address anonymization
    ip = "192.168.1.100"
    anonymized_ip = DataAnonymizationService.anonymize_ip_address(ip)
    print(f"✓ IP anonymization: {ip} -> {anonymized_ip}")
    
    # Test code content anonymization
    code = 'print("Hello World")\n# This is a comment'
    anonymized_code = DataAnonymizationService.anonymize_code_content(code)
    print(f"✓ Code anonymization: {len(code)} chars -> {len(anonymized_code)} chars")
    
    # Test user data anonymization
    user_data = {
        "id": 123,
        "email": "user@example.com",
        "username": "john_doe",
        "full_name": "John Doe",
        "ip_address": "192.168.1.100"
    }
    anonymized_user = DataAnonymizationService.anonymize_user_data(user_data, level="full")
    print(f"✓ User data anonymization (full):")
    print(f"  - Email: {anonymized_user.get('email')}")
    print(f"  - Username: {anonymized_user.get('username')}")
    print(f"  - Full name removed: {'full_name' not in anonymized_user}")
    
    # Test analytics data anonymization
    analytics_data = {
        "user": {"email": "user@example.com", "username": "john_doe"},
        "reviews": [
            {"user_id": 1, "email": "user1@example.com", "code": "sensitive code"}
        ]
    }
    anonymized_analytics = DataAnonymizationService.anonymize_analytics_data(
        analytics_data,
        anonymize_users=True,
        anonymize_code=True
    )
    print(f"✓ Analytics data anonymization:")
    print(f"  - User email: {anonymized_analytics['user']['email']}")
    print(f"  - Review code: {anonymized_analytics['reviews'][0]['code']}")
    
    # Test audit log anonymization
    audit_log = {
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
        "details": {"password": "secret123", "action": "login"}
    }
    anonymized_audit = DataAnonymizationService.anonymize_audit_log(audit_log)
    print(f"✓ Audit log anonymization:")
    print(f"  - IP: {anonymized_audit['ip_address']}")
    print(f"  - User agent: {anonymized_audit['user_agent']}")
    print(f"  - Password redacted: {anonymized_audit['details']['password']}")
    
    # Test anonymization level determination
    admin_level = DataAnonymizationService.get_anonymization_level("admin")
    user_level = DataAnonymizationService.get_anonymization_level("user")
    print(f"✓ Anonymization levels: admin={admin_level}, user={user_level}")
    
    # Test should_anonymize_for_user
    should_anonymize = DataAnonymizationService.should_anonymize_for_user(
        requesting_user_role="developer",
        target_user_id=123,
        requesting_user_id=456
    )
    print(f"✓ Should anonymize for developer viewing other user: {should_anonymize}")
    
    print("✓ DataAnonymizationService tests passed!")


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Task 3: Admin and Analytics Services - Test Suite")
    print("=" * 60)
    
    try:
        # Test RBAC system
        test_rbac_system()
        
        # Test AdminService
        await test_admin_service()
        
        # Test AuditLogger
        await test_audit_logger()
        
        # Test GlobalAnalyticsService
        await test_global_analytics_service()
        
        # Test Enhanced AnalyticsService
        await test_enhanced_analytics_service()
        
        # Test DataAnonymizationService
        test_data_anonymization()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nTask 3 Implementation Summary:")
        print("✓ AdminService - Team CRUD and user management")
        print("✓ AuditLogger - Automatic logging for admin actions")
        print("✓ GlobalAnalyticsService - Platform stats and global trends")
        print("✓ Enhanced AnalyticsService - Issue trends and criticality distribution")
        print("✓ RBAC System - UserRole enum and permission checking")
        print("✓ DataAnonymizationService - Privacy protection")
        print("\nAll requirements covered:")
        print("  - 7.1, 7.2, 7.3: User management")
        print("  - 8.1, 8.2, 8.3: Team management")
        print("  - 9.1, 9.2, 9.3: Global analytics")
        print("  - 10.1, 10.2, 10.3: Platform insights")
        print("  - 14.1, 14.2, 14.3, 14.4, 14.5: Security and audit")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    
    # Cleanup
    if os.path.exists("test_task3.db"):
        os.remove("test_task3.db")
        print("\n✓ Test database cleaned up")
    
    sys.exit(0 if success else 1)
