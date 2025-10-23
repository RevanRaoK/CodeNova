#!/usr/bin/env python3
"""
Quick test script to verify admin endpoints are working correctly.
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = "admin@example.com"  # Change this to your admin user
TEST_USER_PASSWORD = "admin123"  # Change this to your admin password

def login():
    """Login and get access token."""
    print("Logging in...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Login successful")
        return data.get("access_token")
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(response.text)
        return None

def test_platform_stats(token):
    """Test platform statistics endpoint."""
    print("\nTesting platform stats...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/admin/analytics/platform",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Platform stats retrieved successfully")
        print(f"  Total users: {data.get('total_users', 0)}")
        print(f"  Total teams: {data.get('total_teams', 0)}")
        print(f"  Total reviews: {data.get('total_reviews', 0)}")
        return True
    else:
        print(f"✗ Platform stats failed: {response.status_code}")
        print(response.text)
        return False

def test_get_users(token):
    """Test get all users endpoint."""
    print("\nTesting get all users...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/admin/users",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        user_count = len(data) if isinstance(data, list) else data.get('total', 0)
        print(f"✓ Users retrieved successfully")
        print(f"  User count: {user_count}")
        return True
    else:
        print(f"✗ Get users failed: {response.status_code}")
        print(response.text)
        return False

def test_get_teams(token):
    """Test get all teams endpoint."""
    print("\nTesting get all teams...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/admin/teams",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        team_count = len(data) if isinstance(data, list) else data.get('total', 0)
        print(f"✓ Teams retrieved successfully")
        print(f"  Team count: {team_count}")
        return True
    else:
        print(f"✗ Get teams failed: {response.status_code}")
        print(response.text)
        return False

def test_create_team(token):
    """Test create team endpoint."""
    print("\nTesting create team...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    team_data = {
        "name": "Test Team",
        "settings": {}
    }
    
    response = requests.post(
        f"{BASE_URL}/admin/teams",
        headers=headers,
        json=team_data
    )
    
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✓ Team created successfully")
        print(f"  Team ID: {data.get('id')}")
        print(f"  Team name: {data.get('name')}")
        return data.get('id')
    else:
        print(f"✗ Create team failed: {response.status_code}")
        print(response.text)
        return None

def test_global_trends(token):
    """Test global trends endpoint."""
    print("\nTesting global trends...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/admin/analytics/global-trends?timeframe=30d",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Global trends retrieved successfully")
        print(f"  Timeframe: {data.get('timeframe')}")
        print(f"  Data points: {len(data.get('data_points', []))}")
        return True
    else:
        print(f"✗ Global trends failed: {response.status_code}")
        print(response.text)
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Admin Endpoints Test Suite")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        print("\n✗ Cannot proceed without authentication")
        sys.exit(1)
    
    # Run tests
    results = []
    results.append(("Platform Stats", test_platform_stats(token)))
    results.append(("Get Users", test_get_users(token)))
    results.append(("Get Teams", test_get_teams(token)))
    results.append(("Create Team", test_create_team(token) is not None))
    results.append(("Global Trends", test_global_trends(token)))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
