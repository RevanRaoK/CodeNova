#!/usr/bin/env python3
"""
Test script to verify user role editing API endpoints are working correctly.
This script tests the three main endpoints required for task 5:
1. PUT /api/v1/admin/users/{user_id}/role
2. PUT /api/v1/admin/users/{user_id}/team/{team_id} 
3. PUT /api/v1/admin/users/{user_id}/status
"""

import requests
import json
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

BASE_URL = "http://localhost:8000/api/v1"

def get_admin_token():
    """Get admin authentication token"""
    try:
        # Try to login as admin using form data with proper content type
        login_data = {
            "username": "revankokkirala@gmail.com",
            "password": "Test@123"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data, headers=headers)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Failed to login as admin: {response.status_code} - {response.text}")
            # Try the JSON endpoint instead
            login_json_data = {
                "email": "revankokkirala@gmail.com",
                "password": "Test@123"
            }
            response = requests.post(f"{BASE_URL}/auth/login-json", json=login_json_data)
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                print(f"Failed with JSON endpoint: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"Error getting admin token: {e}")
        return None

def test_user_role_update(token, user_id):
    """Test updating user role"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n=== Testing User Role Update (User ID: {user_id}) ===")
    
    # Test updating role to team_lead
    role_data = {"role": "team_lead"}
    response = requests.put(
        f"{BASE_URL}/admin/users/{user_id}/role", 
        json=role_data, 
        headers=headers
    )
    
    print(f"Update role to team_lead: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_user_status_update(token, user_id):
    """Test updating user status"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n=== Testing User Status Update (User ID: {user_id}) ===")
    
    # Test updating status to inactive
    status_data = {"is_active": False}
    response = requests.put(
        f"{BASE_URL}/admin/users/{user_id}/status", 
        json=status_data, 
        headers=headers
    )
    
    print(f"Update status to inactive: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_user_team_assignment(token, user_id, team_id):
    """Test assigning user to team"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n=== Testing User Team Assignment (User ID: {user_id}, Team ID: {team_id}) ===")
    
    # Test assigning to team
    response = requests.put(
        f"{BASE_URL}/admin/users/{user_id}/team/{team_id}", 
        headers=headers
    )
    
    print(f"Assign to team: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_user_team_removal(token, user_id):
    """Test removing user from team"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n=== Testing User Team Removal (User ID: {user_id}) ===")
    
    # Test removing from team using the PUT endpoint with null team_id
    team_data = {"team_id": None}
    response = requests.put(
        f"{BASE_URL}/admin/users/{user_id}/team", 
        json=team_data, 
        headers=headers
    )
    
    print(f"Remove from team: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def get_test_user_and_team(token):
    """Get a test user and team for testing"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get users
    response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    if response.status_code != 200:
        print(f"Failed to get users: {response.status_code} - {response.text}")
        return None, None
    
    users = response.json()
    test_user = None
    
    # Find a non-admin user for testing
    for user in users:
        if user.get('role') != 'admin':
            test_user = user
            break
    
    if not test_user:
        print("No non-admin user found for testing")
        return None, None
    
    # Get teams
    response = requests.get(f"{BASE_URL}/admin/teams", headers=headers)
    if response.status_code != 200:
        print(f"Failed to get teams: {response.status_code} - {response.text}")
        return test_user['id'], None
    
    teams = response.json()
    test_team = teams[0] if teams else None
    
    return test_user['id'], test_team['id'] if test_team else None

def main():
    print("Testing User Role Editing API Endpoints")
    print("=" * 50)
    
    # Get admin token
    token = get_admin_token()
    if not token:
        print("Failed to get admin token. Make sure the backend is running and admin user exists.")
        return
    
    print("✓ Successfully authenticated as admin")
    
    # Get test user and team
    user_id, team_id = get_test_user_and_team(token)
    if not user_id:
        print("No test user available")
        return
    
    print(f"✓ Found test user ID: {user_id}")
    if team_id:
        print(f"✓ Found test team ID: {team_id}")
    else:
        print("⚠ No teams available for team assignment test")
    
    # Run tests
    results = []
    
    # Test 1: User role update
    results.append(test_user_role_update(token, user_id))
    
    # Test 2: User status update  
    results.append(test_user_status_update(token, user_id))
    
    # Test 3: User team assignment (if team available)
    if team_id:
        results.append(test_user_team_assignment(token, user_id, team_id))
        results.append(test_user_team_removal(token, user_id))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All API endpoints are working correctly!")
    else:
        print("❌ Some API endpoints have issues")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)