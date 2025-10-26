#!/usr/bin/env python3
"""
Test script to verify user management displays accurate data.

This script tests:
- User count matches database
- Team assignments display correctly  
- Role badges display correctly
- Search and filter functionality with real data

Requirements: 5.1, 5.2, 5.3, 5.4
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.users import User, UserRole
from app.models.team import Team
from app.services.admin_service import AdminService
from app.api.v1.endpoints.admin import get_all_users
from app.core.config import settings

class UserManagementAccuracyTest:
    """Test class for verifying user management data accuracy."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.admin_service = AdminService(self.db)
        self.test_results = []
        
    def log_result(self, test_name: str, passed: bool, message: str):
        """Log test result."""
        status = "PASS" if passed else "FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "message": message
        })
        print(f"[{status}] {test_name}: {message}")
    
    async def test_user_count_accuracy(self):
        """Test that user count matches database."""
        print("\n=== Testing User Count Accuracy ===")
        
        try:
            # Get direct database count
            db_user_count = self.db.query(User).count()
            
            # Get count through admin service
            all_users = await self.admin_service.get_all_users()
            service_user_count = len(all_users)
            
            # Test accuracy
            if db_user_count == service_user_count:
                self.log_result(
                    "User Count Accuracy",
                    True,
                    f"Database count ({db_user_count}) matches service count ({service_user_count})"
                )
            else:
                self.log_result(
                    "User Count Accuracy",
                    False,
                    f"Database count ({db_user_count}) != service count ({service_user_count})"
                )
            
            # Test with different limits
            limited_users = await self.admin_service.get_all_users(limit=5)
            expected_limit = min(5, db_user_count)
            
            if len(limited_users) == expected_limit:
                self.log_result(
                    "User Count with Limit",
                    True,
                    f"Limited query returned correct count: {len(limited_users)}"
                )
            else:
                self.log_result(
                    "User Count with Limit",
                    False,
                    f"Limited query returned {len(limited_users)}, expected {expected_limit}"
                )
                
        except Exception as e:
            self.log_result("User Count Accuracy", False, f"Error: {str(e)}")
    
    async def test_team_assignments_accuracy(self):
        """Test that team assignments display correctly."""
        print("\n=== Testing Team Assignment Accuracy ===")
        
        try:
            # Get all users with team assignments
            users = await self.admin_service.get_all_users()
            
            team_assignment_errors = []
            users_with_teams = 0
            users_without_teams = 0
            
            for user in users:
                if user.team_id:
                    users_with_teams += 1
                    # Verify team exists
                    team = await self.admin_service.get_team_by_id(user.team_id)
                    if not team:
                        team_assignment_errors.append(
                            f"User {user.id} ({user.email}) assigned to non-existent team {user.team_id}"
                        )
                else:
                    users_without_teams += 1
            
            if not team_assignment_errors:
                self.log_result(
                    "Team Assignment Integrity",
                    True,
                    f"All team assignments valid. {users_with_teams} users with teams, {users_without_teams} without teams"
                )
            else:
                self.log_result(
                    "Team Assignment Integrity",
                    False,
                    f"Found {len(team_assignment_errors)} invalid team assignments: {team_assignment_errors}"
                )
            
            # Test team filtering
            teams = await self.admin_service.get_all_teams()
            for team in teams:
                team_users = await self.admin_service.get_all_users(team_id=team.id)
                db_team_users = self.db.query(User).filter(User.team_id == team.id).all()
                
                if len(team_users) == len(db_team_users):
                    self.log_result(
                        f"Team Filter - {team.name}",
                        True,
                        f"Team filter returned correct count: {len(team_users)}"
                    )
                else:
                    self.log_result(
                        f"Team Filter - {team.name}",
                        False,
                        f"Team filter returned {len(team_users)}, database has {len(db_team_users)}"
                    )
                    
        except Exception as e:
            self.log_result("Team Assignment Accuracy", False, f"Error: {str(e)}")
    
    async def test_role_display_accuracy(self):
        """Test that role badges display correctly."""
        print("\n=== Testing Role Display Accuracy ===")
        
        try:
            users = await self.admin_service.get_all_users()
            
            role_counts = {role.value: 0 for role in UserRole}
            role_errors = []
            
            for user in users:
                if user.role:
                    if user.role.value in role_counts:
                        role_counts[user.role.value] += 1
                    else:
                        role_errors.append(f"User {user.id} has invalid role: {user.role}")
                else:
                    role_errors.append(f"User {user.id} has no role assigned")
            
            # Verify against database
            db_role_counts = {}
            for role in UserRole:
                count = self.db.query(User).filter(User.role == role).count()
                db_role_counts[role.value] = count
            
            role_accuracy = True
            for role_value in role_counts:
                if role_counts[role_value] != db_role_counts[role_value]:
                    role_accuracy = False
                    self.log_result(
                        f"Role Count - {role_value}",
                        False,
                        f"Service count {role_counts[role_value]} != DB count {db_role_counts[role_value]}"
                    )
                else:
                    self.log_result(
                        f"Role Count - {role_value}",
                        True,
                        f"Correct count: {role_counts[role_value]}"
                    )
            
            if not role_errors:
                self.log_result(
                    "Role Assignment Validity",
                    True,
                    "All users have valid roles assigned"
                )
            else:
                self.log_result(
                    "Role Assignment Validity",
                    False,
                    f"Found {len(role_errors)} role errors: {role_errors}"
                )
                
        except Exception as e:
            self.log_result("Role Display Accuracy", False, f"Error: {str(e)}")
    
    async def test_search_functionality(self):
        """Test search and filter functionality with real data."""
        print("\n=== Testing Search and Filter Functionality ===")
        
        try:
            # Test search by email
            all_users = await self.admin_service.get_all_users()
            
            if all_users:
                # Test search with first user's email
                test_user = all_users[0]
                search_term = test_user.email.split('@')[0]  # Use part of email
                
                search_results = await self.admin_service.get_all_users(search=search_term)
                
                # Verify search results contain the test user
                found_test_user = any(user.id == test_user.id for user in search_results)
                
                if found_test_user:
                    self.log_result(
                        "Email Search",
                        True,
                        f"Search for '{search_term}' correctly found user {test_user.email}"
                    )
                else:
                    self.log_result(
                        "Email Search",
                        False,
                        f"Search for '{search_term}' did not find user {test_user.email}"
                    )
                
                # Test search by name if available
                if test_user.full_name:
                    name_search = test_user.full_name.split()[0]  # Use first name
                    name_results = await self.admin_service.get_all_users(search=name_search)
                    
                    found_by_name = any(user.id == test_user.id for user in name_results)
                    
                    if found_by_name:
                        self.log_result(
                            "Name Search",
                            True,
                            f"Search for '{name_search}' correctly found user {test_user.full_name}"
                        )
                    else:
                        self.log_result(
                            "Name Search",
                            False,
                            f"Search for '{name_search}' did not find user {test_user.full_name}"
                        )
                
                # Test case-insensitive search
                case_search = test_user.email.upper()
                case_results = await self.admin_service.get_all_users(search=case_search)
                
                found_case_insensitive = any(user.id == test_user.id for user in case_results)
                
                if found_case_insensitive:
                    self.log_result(
                        "Case-Insensitive Search",
                        True,
                        f"Case-insensitive search for '{case_search}' worked correctly"
                    )
                else:
                    self.log_result(
                        "Case-Insensitive Search",
                        False,
                        f"Case-insensitive search for '{case_search}' failed"
                    )
            else:
                self.log_result(
                    "Search Functionality",
                    False,
                    "No users available to test search functionality"
                )
                
        except Exception as e:
            self.log_result("Search Functionality", False, f"Error: {str(e)}")
    
    async def test_role_filtering(self):
        """Test role-based filtering."""
        print("\n=== Testing Role Filtering ===")
        
        try:
            for role in UserRole:
                # Get users with specific role through service
                role_users = await self.admin_service.get_all_users(role=role)
                
                # Get users with specific role directly from database
                db_role_users = self.db.query(User).filter(User.role == role).all()
                
                if len(role_users) == len(db_role_users):
                    self.log_result(
                        f"Role Filter - {role.value}",
                        True,
                        f"Filter returned correct count: {len(role_users)}"
                    )
                else:
                    self.log_result(
                        f"Role Filter - {role.value}",
                        False,
                        f"Filter returned {len(role_users)}, database has {len(db_role_users)}"
                    )
                    
        except Exception as e:
            self.log_result("Role Filtering", False, f"Error: {str(e)}")
    
    async def test_active_status_filtering(self):
        """Test active status filtering."""
        print("\n=== Testing Active Status Filtering ===")
        
        try:
            # Test active users filter
            active_users = await self.admin_service.get_all_users(is_active=True)
            db_active_users = self.db.query(User).filter(User.is_active == True).all()
            
            if len(active_users) == len(db_active_users):
                self.log_result(
                    "Active Users Filter",
                    True,
                    f"Active filter returned correct count: {len(active_users)}"
                )
            else:
                self.log_result(
                    "Active Users Filter",
                    False,
                    f"Active filter returned {len(active_users)}, database has {len(db_active_users)}"
                )
            
            # Test inactive users filter
            inactive_users = await self.admin_service.get_all_users(is_active=False)
            db_inactive_users = self.db.query(User).filter(User.is_active == False).all()
            
            if len(inactive_users) == len(db_inactive_users):
                self.log_result(
                    "Inactive Users Filter",
                    True,
                    f"Inactive filter returned correct count: {len(inactive_users)}"
                )
            else:
                self.log_result(
                    "Inactive Users Filter",
                    False,
                    f"Inactive filter returned {len(inactive_users)}, database has {len(db_inactive_users)}"
                )
                
        except Exception as e:
            self.log_result("Active Status Filtering", False, f"Error: {str(e)}")
    
    async def test_pagination_accuracy(self):
        """Test pagination functionality."""
        print("\n=== Testing Pagination Accuracy ===")
        
        try:
            total_users = self.db.query(User).count()
            
            if total_users == 0:
                self.log_result(
                    "Pagination Test",
                    True,
                    "No users to test pagination with"
                )
                return
            
            # Test first page
            page_size = 5
            first_page = await self.admin_service.get_all_users(skip=0, limit=page_size)
            expected_first_page_size = min(page_size, total_users)
            
            if len(first_page) == expected_first_page_size:
                self.log_result(
                    "First Page Pagination",
                    True,
                    f"First page returned correct count: {len(first_page)}"
                )
            else:
                self.log_result(
                    "First Page Pagination",
                    False,
                    f"First page returned {len(first_page)}, expected {expected_first_page_size}"
                )
            
            # Test second page if there are enough users
            if total_users > page_size:
                second_page = await self.admin_service.get_all_users(skip=page_size, limit=page_size)
                expected_second_page_size = min(page_size, total_users - page_size)
                
                if len(second_page) == expected_second_page_size:
                    self.log_result(
                        "Second Page Pagination",
                        True,
                        f"Second page returned correct count: {len(second_page)}"
                    )
                else:
                    self.log_result(
                        "Second Page Pagination",
                        False,
                        f"Second page returned {len(second_page)}, expected {expected_second_page_size}"
                    )
                
                # Verify no overlap between pages
                first_page_ids = {user.id for user in first_page}
                second_page_ids = {user.id for user in second_page}
                overlap = first_page_ids.intersection(second_page_ids)
                
                if not overlap:
                    self.log_result(
                        "Page Overlap Check",
                        True,
                        "No overlap between pagination pages"
                    )
                else:
                    self.log_result(
                        "Page Overlap Check",
                        False,
                        f"Found {len(overlap)} overlapping users between pages"
                    )
                    
        except Exception as e:
            self.log_result("Pagination Accuracy", False, f"Error: {str(e)}")
    
    async def test_user_data_completeness(self):
        """Test that user data is complete and accurate."""
        print("\n=== Testing User Data Completeness ===")
        
        try:
            users = await self.admin_service.get_all_users()
            
            incomplete_users = []
            users_with_missing_data = []
            
            for user in users:
                issues = []
                
                # Check required fields
                if not user.email:
                    issues.append("missing email")
                
                if not user.role:
                    issues.append("missing role")
                
                if user.is_active is None:
                    issues.append("missing is_active status")
                
                if not user.created_at:
                    issues.append("missing created_at")
                
                # Check optional but important fields
                if not user.full_name and not user.first_name:
                    users_with_missing_data.append(f"User {user.id} has no name information")
                
                if issues:
                    incomplete_users.append(f"User {user.id}: {', '.join(issues)}")
            
            if not incomplete_users:
                self.log_result(
                    "User Data Completeness",
                    True,
                    f"All {len(users)} users have complete required data"
                )
            else:
                self.log_result(
                    "User Data Completeness",
                    False,
                    f"Found {len(incomplete_users)} users with incomplete data: {incomplete_users}"
                )
            
            if users_with_missing_data:
                self.log_result(
                    "User Name Information",
                    False,
                    f"Found {len(users_with_missing_data)} users with missing name data"
                )
            else:
                self.log_result(
                    "User Name Information",
                    True,
                    "All users have name information"
                )
                
        except Exception as e:
            self.log_result("User Data Completeness", False, f"Error: {str(e)}")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("USER MANAGEMENT ACCURACY TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\nREQUIREMENTS VERIFICATION:")
        print("5.1 - Display all actual users from database: ", end="")
        user_count_passed = any(r["test"] == "User Count Accuracy" and r["status"] == "PASS" for r in self.test_results)
        print("✓ PASS" if user_count_passed else "✗ FAIL")
        
        print("5.2 - Display accurate user information: ", end="")
        data_completeness_passed = any(r["test"] == "User Data Completeness" and r["status"] == "PASS" for r in self.test_results)
        print("✓ PASS" if data_completeness_passed else "✗ FAIL")
        
        print("5.3 - Display accurate role and team information: ", end="")
        role_passed = any("Role Count" in r["test"] and r["status"] == "PASS" for r in self.test_results)
        team_passed = any("Team Assignment" in r["test"] and r["status"] == "PASS" for r in self.test_results)
        print("✓ PASS" if role_passed and team_passed else "✗ FAIL")
        
        print("5.4 - Search and filter functionality works: ", end="")
        search_passed = any("Search" in r["test"] and r["status"] == "PASS" for r in self.test_results)
        filter_passed = any("Filter" in r["test"] and r["status"] == "PASS" for r in self.test_results)
        print("✓ PASS" if search_passed and filter_passed else "✗ FAIL")
        
        return failed_tests == 0
    
    async def run_all_tests(self):
        """Run all user management accuracy tests."""
        print("Starting User Management Accuracy Tests...")
        print(f"Database: {settings.DATABASE_URL}")
        print(f"Test started at: {datetime.now()}")
        
        try:
            await self.test_user_count_accuracy()
            await self.test_team_assignments_accuracy()
            await self.test_role_display_accuracy()
            await self.test_search_functionality()
            await self.test_role_filtering()
            await self.test_active_status_filtering()
            await self.test_pagination_accuracy()
            await self.test_user_data_completeness()
            
        except Exception as e:
            print(f"Critical error during testing: {e}")
            self.log_result("Critical Error", False, str(e))
        
        finally:
            self.db.close()
        
        return self.print_summary()

async def main():
    """Main function to run the tests."""
    tester = UserManagementAccuracyTest()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! User management displays accurate data.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please review the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())