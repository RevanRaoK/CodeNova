#!/usr/bin/env python3
"""
Test script to verify team management displays accurate data.

This script tests:
- Team count matches database
- Member counts are accurate
- Team deletion functionality
- Empty state when no teams exist

Requirements: 6.1, 6.2, 6.3, 6.4
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.users import User, UserRole
from app.models.team import Team
from app.services.admin_service import AdminService
from app.schemas.team import TeamCreate


class TeamManagementAccuracyTest:
    """Test class for verifying team management accuracy."""
    
    def __init__(self):
        self.db = next(get_db())
        self.admin_service = AdminService(self.db)
        self.test_results = []
        self.created_teams = []
        self.created_users = []
    
    def log_result(self, test_name: str, passed: bool, message: str, details: Dict[str, Any] = None):
        """Log test result."""
        result = {
            "test": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        print(f"   {message}")
        if details:
            print(f"   Details: {json.dumps(details, indent=2)}")
        print()
    
    async def setup_test_data(self):
        """Create test data for team management tests."""
        print("Setting up test data...")
        
        # Create test admin user
        admin_user = User(
            email="test_admin@example.com",
            full_name="Test Admin",
            first_name="Test",
            last_name="Admin",
            role=UserRole.ADMIN,
            is_active=True,
            hashed_password="dummy_hash"
        )
        self.db.add(admin_user)
        self.db.commit()
        self.db.refresh(admin_user)
        self.created_users.append(admin_user.id)
        
        # Create test team lead user
        team_lead_user = User(
            email="test_teamlead@example.com",
            full_name="Test Team Lead",
            first_name="Test",
            last_name="Lead",
            role=UserRole.TEAM_LEAD,
            is_active=True,
            hashed_password="dummy_hash"
        )
        self.db.add(team_lead_user)
        self.db.commit()
        self.db.refresh(team_lead_user)
        self.created_users.append(team_lead_user.id)
        
        # Create regular users
        for i in range(3):
            user = User(
                email=f"test_user_{i}@example.com",
                full_name=f"Test User {i}",
                first_name="Test",
                last_name=f"User{i}",
                role=UserRole.USER,
                is_active=True,
                hashed_password="dummy_hash"
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            self.created_users.append(user.id)
        
        # Create test teams
        team1_data = TeamCreate(
            name="Test Team Alpha",
            admin_id=team_lead_user.id,
            settings={"description": "First test team"}
        )
        team1 = await self.admin_service.create_team(team1_data, admin_user.id)
        self.created_teams.append(team1.id)
        
        team2_data = TeamCreate(
            name="Test Team Beta",
            admin_id=admin_user.id,
            settings={"description": "Second test team"}
        )
        team2 = await self.admin_service.create_team(team2_data, admin_user.id)
        self.created_teams.append(team2.id)
        
        # Assign users to teams
        users = self.db.query(User).filter(User.role == UserRole.USER).all()
        if len(users) >= 2:
            # Assign first user to team1
            users[0].team_id = team1.id
            # Assign second user to team1 (so team1 has 2 members)
            users[1].team_id = team1.id
            # Leave third user unassigned
            self.db.commit()
        
        print(f"Created {len(self.created_teams)} test teams and {len(self.created_users)} test users")
        return admin_user.id
    
    async def test_team_count_accuracy(self):
        """Test that team count matches database."""
        # Get teams from service
        teams_from_service = await self.admin_service.get_all_teams()
        
        # Get teams directly from database
        teams_from_db = self.db.query(Team).all()
        
        service_count = len(teams_from_service)
        db_count = len(teams_from_db)
        
        passed = service_count == db_count
        
        self.log_result(
            "Team Count Accuracy",
            passed,
            f"Service returned {service_count} teams, database has {db_count} teams",
            {
                "service_count": service_count,
                "database_count": db_count,
                "teams_from_service": [{"id": t.id, "name": t.name} for t in teams_from_service],
                "teams_from_db": [{"id": t.id, "name": t.name} for t in teams_from_db]
            }
        )
        
        return passed
    
    async def test_member_count_accuracy(self):
        """Test that member counts are accurate."""
        teams = await self.admin_service.get_all_teams()
        all_passed = True
        
        for team in teams:
            # Get member count from database
            actual_member_count = self.db.query(User).filter(User.team_id == team.id).count()
            
            # Get member count from team object
            reported_member_count = getattr(team, 'member_count', 0)
            
            passed = actual_member_count == reported_member_count
            all_passed = all_passed and passed
            
            self.log_result(
                f"Member Count Accuracy - Team {team.name}",
                passed,
                f"Team reports {reported_member_count} members, database has {actual_member_count}",
                {
                    "team_id": team.id,
                    "team_name": team.name,
                    "reported_count": reported_member_count,
                    "actual_count": actual_member_count
                }
            )
        
        return all_passed
    
    async def test_team_data_completeness(self):
        """Test that teams have all required data fields."""
        teams = await self.admin_service.get_all_teams()
        all_passed = True
        
        required_fields = ['id', 'name', 'admin_id', 'created_at']
        
        for team in teams:
            missing_fields = []
            for field in required_fields:
                if not hasattr(team, field) or getattr(team, field) is None:
                    missing_fields.append(field)
            
            # Check if admin relationship is loaded
            admin_loaded = hasattr(team, 'admin') and team.admin is not None
            
            # Check if member_count is present
            member_count_present = hasattr(team, 'member_count')
            
            passed = len(missing_fields) == 0 and admin_loaded and member_count_present
            all_passed = all_passed and passed
            
            self.log_result(
                f"Team Data Completeness - {team.name}",
                passed,
                f"Team has all required fields and relationships",
                {
                    "team_id": team.id,
                    "missing_fields": missing_fields,
                    "admin_loaded": admin_loaded,
                    "member_count_present": member_count_present,
                    "admin_name": team.admin.full_name if admin_loaded else None
                }
            )
        
        return all_passed
    
    async def test_team_deletion_functionality(self):
        """Test team deletion functionality."""
        # Create a temporary team for deletion test
        admin_user_id = self.created_users[0]  # Use first created user as admin
        
        temp_team_data = TeamCreate(
            name="Temporary Team for Deletion",
            admin_id=admin_user_id,
            settings={"temporary": True}
        )
        temp_team = await self.admin_service.create_team(temp_team_data, admin_user_id)
        temp_team_id = temp_team.id
        
        # Assign a user to this team
        if len(self.created_users) > 1:
            user_to_assign = self.db.query(User).filter(User.id == self.created_users[1]).first()
            if user_to_assign:
                user_to_assign.team_id = temp_team_id
                self.db.commit()
        
        # Verify team exists before deletion
        team_before = await self.admin_service.get_team_by_id(temp_team_id)
        team_exists_before = team_before is not None
        
        # Get member count before deletion
        members_before = self.db.query(User).filter(User.team_id == temp_team_id).count()
        
        # Delete the team
        deletion_success = await self.admin_service.delete_team(temp_team_id, admin_user_id)
        
        # Verify team no longer exists
        team_after = await self.admin_service.get_team_by_id(temp_team_id)
        team_exists_after = team_after is not None
        
        # Verify users are unassigned
        members_after = self.db.query(User).filter(User.team_id == temp_team_id).count()
        
        passed = (team_exists_before and deletion_success and 
                 not team_exists_after and members_after == 0)
        
        self.log_result(
            "Team Deletion Functionality",
            passed,
            f"Team deletion {'succeeded' if passed else 'failed'}",
            {
                "team_id": temp_team_id,
                "team_existed_before": team_exists_before,
                "deletion_returned_success": deletion_success,
                "team_exists_after": team_exists_after,
                "members_before_deletion": members_before,
                "members_after_deletion": members_after
            }
        )
        
        return passed
    
    async def test_empty_state_handling(self):
        """Test empty state when no teams exist."""
        # Store current teams
        original_teams = await self.admin_service.get_all_teams()
        
        # Temporarily delete all teams
        for team in original_teams:
            await self.admin_service.delete_team(team.id, self.created_users[0])
        
        # Test empty state
        empty_teams = await self.admin_service.get_all_teams()
        empty_count = len(empty_teams)
        
        # Restore teams (create new ones since we deleted the originals)
        admin_user_id = self.created_users[0]
        restored_teams = []
        
        for i, original_team in enumerate(original_teams):
            team_data = TeamCreate(
                name=f"Restored {original_team.name}",
                admin_id=original_team.admin_id,
                settings=original_team.settings or {}
            )
            restored_team = await self.admin_service.create_team(team_data, admin_user_id)
            restored_teams.append(restored_team)
            self.created_teams.append(restored_team.id)
        
        passed = empty_count == 0
        
        self.log_result(
            "Empty State Handling",
            passed,
            f"Empty state returns {empty_count} teams (expected 0)",
            {
                "empty_teams_count": empty_count,
                "original_teams_count": len(original_teams),
                "restored_teams_count": len(restored_teams)
            }
        )
        
        return passed
    
    async def test_team_admin_relationship(self):
        """Test that team admin relationships are properly loaded."""
        teams = await self.admin_service.get_all_teams()
        all_passed = True
        
        for team in teams:
            # Check if admin relationship is loaded
            admin_loaded = hasattr(team, 'admin') and team.admin is not None
            
            if admin_loaded:
                # Verify admin exists in database
                admin_in_db = self.db.query(User).filter(User.id == team.admin_id).first()
                admin_exists = admin_in_db is not None
                
                # Verify admin data matches
                admin_data_matches = (admin_exists and 
                                    team.admin.id == admin_in_db.id and
                                    team.admin.full_name == admin_in_db.full_name)
            else:
                admin_exists = False
                admin_data_matches = False
            
            passed = admin_loaded and admin_exists and admin_data_matches
            all_passed = all_passed and passed
            
            self.log_result(
                f"Team Admin Relationship - {team.name}",
                passed,
                f"Admin relationship {'properly loaded' if passed else 'has issues'}",
                {
                    "team_id": team.id,
                    "admin_id": team.admin_id,
                    "admin_loaded": admin_loaded,
                    "admin_exists_in_db": admin_exists,
                    "admin_data_matches": admin_data_matches,
                    "admin_name": team.admin.full_name if admin_loaded else None
                }
            )
        
        return all_passed
    
    async def cleanup_test_data(self):
        """Clean up test data."""
        print("Cleaning up test data...")
        
        # Delete created teams
        for team_id in self.created_teams:
            try:
                team = self.db.query(Team).filter(Team.id == team_id).first()
                if team:
                    # Unassign users first
                    self.db.query(User).filter(User.team_id == team_id).update({"team_id": None})
                    # Delete team
                    self.db.delete(team)
                    self.db.commit()
            except Exception as e:
                print(f"Error deleting team {team_id}: {e}")
        
        # Delete created users
        for user_id in self.created_users:
            try:
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
                    self.db.delete(user)
                    self.db.commit()
            except Exception as e:
                print(f"Error deleting user {user_id}: {e}")
        
        print(f"Cleaned up {len(self.created_teams)} teams and {len(self.created_users)} users")
    
    async def run_all_tests(self):
        """Run all team management accuracy tests."""
        print("🧪 Starting Team Management Accuracy Tests")
        print("=" * 50)
        
        try:
            # Setup test data
            await self.setup_test_data()
            
            # Run tests
            test_methods = [
                self.test_team_count_accuracy,
                self.test_member_count_accuracy,
                self.test_team_data_completeness,
                self.test_team_admin_relationship,
                self.test_team_deletion_functionality,
                self.test_empty_state_handling
            ]
            
            passed_tests = 0
            total_tests = len(test_methods)
            
            for test_method in test_methods:
                try:
                    result = await test_method()
                    if result:
                        passed_tests += 1
                except Exception as e:
                    self.log_result(
                        test_method.__name__,
                        False,
                        f"Test failed with exception: {str(e)}",
                        {"exception": str(e)}
                    )
            
            # Print summary
            print("=" * 50)
            print(f"📊 Test Summary: {passed_tests}/{total_tests} tests passed")
            
            if passed_tests == total_tests:
                print("🎉 All team management accuracy tests PASSED!")
                return True
            else:
                print(f"⚠️  {total_tests - passed_tests} test(s) FAILED")
                return False
                
        except Exception as e:
            print(f"❌ Test suite failed with error: {e}")
            return False
        finally:
            # Always cleanup
            await self.cleanup_test_data()
    
    def save_results(self, filename: str = "team_management_test_results.json"):
        """Save test results to file."""
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results if r["passed"]),
                "results": self.test_results
            }, f, indent=2)
        print(f"📄 Test results saved to {filename}")


async def main():
    """Main function to run team management accuracy tests."""
    tester = TeamManagementAccuracyTest()
    
    try:
        success = await tester.run_all_tests()
        tester.save_results()
        
        if success:
            print("\n✅ Team management displays accurate data!")
            sys.exit(0)
        else:
            print("\n❌ Team management has accuracy issues!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())