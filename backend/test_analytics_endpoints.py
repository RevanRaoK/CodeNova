"""
Test script for new analytics API endpoints.

This script tests the three new endpoints:
- /api/v1/analytics/user-stats
- /api/v1/analytics/usage-trends
- /api/v1/analytics/feedback-distribution
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_login():
    """Login and get access token."""
    print("Testing login...")
    
    # Try to login with a test user
    login_data = {
        "username": "test@example.com",
        "password": "testpassword"
    }
    
    response = requests.post(f"{API_BASE}/auth/login", data=login_data)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"✓ Login successful")
        return token
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def test_user_stats(token):
    """Test /api/v1/analytics/user-stats endpoint."""
    print("\nTesting /api/v1/analytics/user-stats...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/analytics/user-stats", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ User stats retrieved successfully")
        print(f"  Total Reviews: {data.get('totalReviews', 0)}")
        print(f"  Total Analyses: {data.get('totalAnalyses', 0)}")
        print(f"  Success Rate: {data.get('successRate', 0)}%")
        print(f"  Acceptance Rate: {data.get('acceptanceRate', 0)}%")
        print(f"  Recent Activity Count: {len(data.get('recentActivity', []))}")
        return True
    else:
        print(f"✗ Failed to get user stats: {response.status_code}")
        print(f"  Response: {response.text}")
        return False

def test_usage_trends(token):
    """Test /api/v1/analytics/usage-trends endpoint."""
    print("\nTesting /api/v1/analytics/usage-trends...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test different timeframes
    timeframes = ["7d", "30d", "90d"]
    
    for timeframe in timeframes:
        response = requests.get(
            f"{API_BASE}/analytics/usage-trends",
            headers=headers,
            params={"timeframe": timeframe}
        )
        
        if response.status_code == 200:
            data = response.json()
            trends_count = len(data.get('trends', []))
            print(f"✓ Usage trends ({timeframe}) retrieved: {trends_count} data points")
        else:
            print(f"✗ Failed to get usage trends ({timeframe}): {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    
    return True

def test_feedback_distribution(token):
    """Test /api/v1/analytics/feedback-distribution endpoint."""
    print("\nTesting /api/v1/analytics/feedback-distribution...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test different timeframes
    timeframes = ["7d", "30d"]
    
    for timeframe in timeframes:
        response = requests.get(
            f"{API_BASE}/analytics/feedback-distribution",
            headers=headers,
            params={"timeframe": timeframe}
        )
        
        if response.status_code == 200:
            data = response.json()
            distribution = data.get('distribution', {})
            total = data.get('total', 0)
            print(f"✓ Feedback distribution ({timeframe}) retrieved")
            print(f"  Accept: {distribution.get('accept', 0)}")
            print(f"  Reject: {distribution.get('reject', 0)}")
            print(f"  Modify: {distribution.get('modify', 0)}")
            print(f"  Total: {total}")
        else:
            print(f"✗ Failed to get feedback distribution ({timeframe}): {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Analytics API Endpoints Test")
    print("=" * 60)
    
    # Login first
    token = test_login()
    
    if not token:
        print("\n✗ Cannot proceed without authentication token")
        print("\nNote: Make sure you have a test user created.")
        print("You can create one using backend/create_test_user.py")
        return
    
    # Run tests
    results = []
    results.append(("User Stats", test_user_stats(token)))
    results.append(("Usage Trends", test_usage_trends(token)))
    results.append(("Feedback Distribution", test_feedback_distribution(token)))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
