"""
Test script for feedback statistics API endpoint.

This script tests the new /api/v1/feedback/statistics endpoint
to ensure it properly aggregates feedback data and calculates metrics.

Requirements tested: 2.2, 2.3, 2.4, 2.5
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test credentials (update with actual test user)
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"


def login() -> str:
    """Login and get access token."""
    response = requests.post(
        f"{API_BASE}/auth/login",
        data={
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✓ Login successful")
        return token
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(response.text)
        return None


def test_feedback_statistics(token: str):
    """Test the feedback statistics endpoint."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "="*60)
    print("Testing Feedback Statistics Endpoint")
    print("="*60)
    
    # Test different timeframes
    timeframes = ["week", "month", "quarter", "year", "all"]
    
    for timeframe in timeframes:
        print(f"\n--- Testing timeframe: {timeframe} ---")
        
        response = requests.get(
            f"{API_BASE}/feedback/statistics",
            headers=headers,
            params={"timeframe": timeframe}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Request successful for timeframe '{timeframe}'")
            print(f"  Total feedback: {data.get('total_feedback', 0)}")
            print(f"  Acceptance rate: {data.get('acceptance_rate', 0)}%")
            print(f"  Rejection rate: {data.get('rejection_rate', 0)}%")
            print(f"  Modification rate: {data.get('modification_rate', 0)}%")
            
            # Check feedback by type
            feedback_by_type = data.get('feedback_by_type', {})
            if feedback_by_type:
                counts = feedback_by_type.get('counts', {})
                print(f"  Feedback counts: Accept={counts.get('accept', 0)}, "
                      f"Reject={counts.get('reject', 0)}, "
                      f"Modify={counts.get('modify', 0)}, "
                      f"Ignore={counts.get('ignore', 0)}")
            
            # Check feedback trends
            trends = data.get('feedback_trends', [])
            print(f"  Trend data points: {len(trends)}")
            if trends:
                latest_trend = trends[-1]
                print(f"  Latest trend ({latest_trend['date']}): "
                      f"Accept={latest_trend['accept']}, "
                      f"Reject={latest_trend['reject']}")
            
            # Check model performance metrics
            model_performance = data.get('model_performance', [])
            print(f"  Model performance metrics: {len(model_performance)}")
            for metric in model_performance:
                print(f"    - {metric['metric']}: {metric['value']}{metric['unit']}")
            
            # Check pattern statistics
            pattern_stats = data.get('pattern_feedback_stats', {})
            print(f"  Pattern types analyzed: {len(pattern_stats)}")
            
        else:
            print(f"✗ Request failed for timeframe '{timeframe}': {response.status_code}")
            print(f"  Error: {response.text}")


def test_invalid_timeframe(token: str):
    """Test with invalid timeframe parameter."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "="*60)
    print("Testing Invalid Timeframe")
    print("="*60)
    
    response = requests.get(
        f"{API_BASE}/feedback/statistics",
        headers=headers,
        params={"timeframe": "invalid"}
    )
    
    if response.status_code == 400:
        print("✓ Correctly rejected invalid timeframe")
        print(f"  Error message: {response.json().get('detail', 'N/A')}")
    else:
        print(f"✗ Expected 400 status code, got {response.status_code}")


def test_unauthorized_access():
    """Test accessing endpoint without authentication."""
    print("\n" + "="*60)
    print("Testing Unauthorized Access")
    print("="*60)
    
    response = requests.get(f"{API_BASE}/feedback/statistics")
    
    if response.status_code == 401:
        print("✓ Correctly rejected unauthorized request")
    else:
        print(f"✗ Expected 401 status code, got {response.status_code}")


def test_response_structure(token: str):
    """Test that response has all required fields."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "="*60)
    print("Testing Response Structure")
    print("="*60)
    
    response = requests.get(
        f"{API_BASE}/feedback/statistics",
        headers=headers,
        params={"timeframe": "month"}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        required_fields = [
            "timeframe",
            "total_feedback",
            "feedback_by_type",
            "acceptance_rate",
            "rejection_rate",
            "modification_rate",
            "feedback_trends",
            "model_performance",
            "pattern_feedback_stats",
            "feedback_by_date",
            "generated_at"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if not missing_fields:
            print("✓ All required fields present in response")
            
            # Validate nested structures
            feedback_by_type = data.get('feedback_by_type', {})
            if 'counts' in feedback_by_type and 'rates' in feedback_by_type:
                print("✓ feedback_by_type has correct structure")
            else:
                print("✗ feedback_by_type missing 'counts' or 'rates'")
            
            # Validate trends structure
            trends = data.get('feedback_trends', [])
            if trends and isinstance(trends, list):
                trend_fields = ['date', 'accept', 'reject', 'modify', 'total', 'acceptance_rate']
                if all(field in trends[0] for field in trend_fields):
                    print("✓ feedback_trends has correct structure")
                else:
                    print("✗ feedback_trends missing required fields")
            
            # Validate model performance structure
            performance = data.get('model_performance', [])
            if performance and isinstance(performance, list):
                perf_fields = ['metric', 'value', 'unit', 'description']
                if all(field in performance[0] for field in perf_fields):
                    print("✓ model_performance has correct structure")
                else:
                    print("✗ model_performance missing required fields")
        else:
            print(f"✗ Missing required fields: {', '.join(missing_fields)}")
    else:
        print(f"✗ Request failed: {response.status_code}")


def main():
    """Run all tests."""
    print("="*60)
    print("Feedback Statistics API Endpoint Tests")
    print("="*60)
    
    # Login
    token = login()
    if not token:
        print("\n✗ Cannot proceed without authentication token")
        return
    
    # Run tests
    test_feedback_statistics(token)
    test_invalid_timeframe(token)
    test_unauthorized_access()
    test_response_structure(token)
    
    print("\n" + "="*60)
    print("Test Suite Complete")
    print("="*60)


if __name__ == "__main__":
    main()
