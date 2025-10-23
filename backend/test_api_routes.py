"""
Test script to verify all API routes for dashboard and settings improvements are properly registered.

This script checks that all required endpoints exist and are accessible.
"""

import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_route_exists(method: str, path: str, description: str):
    """Test if a route exists by checking the OpenAPI schema."""
    try:
        # Get OpenAPI schema
        response = client.get("/openapi.json")
        if response.status_code != 200:
            print(f"❌ Failed to get OpenAPI schema")
            return False
        
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})
        
        # Check if path exists
        if path in paths:
            methods = paths[path]
            if method.lower() in methods:
                print(f"✅ {method.upper()} {path} - {description}")
                return True
            else:
                print(f"❌ {method.upper()} {path} - Method not found (available: {list(methods.keys())})")
                return False
        else:
            print(f"❌ {method.upper()} {path} - Path not found")
            return False
    except Exception as e:
        print(f"❌ {method.upper()} {path} - Error: {str(e)}")
        return False


def main():
    """Test all required API routes."""
    print("=" * 80)
    print("Testing API Routes for Dashboard and Settings Improvements")
    print("=" * 80)
    print()
    
    all_tests_passed = True
    
    # Analytics Endpoints
    print("📊 Analytics Endpoints (/api/v1/analytics)")
    print("-" * 80)
    tests = [
        ("GET", "/api/v1/analytics/user-stats", "Get user statistics"),
        ("GET", "/api/v1/analytics/usage-trends", "Get usage trends"),
        ("GET", "/api/v1/analytics/feedback-distribution", "Get feedback distribution"),
        ("GET", "/api/v1/analytics/acceptance-rates", "Get acceptance rates"),
        ("GET", "/api/v1/analytics/rejection-patterns", "Get rejection patterns"),
        ("GET", "/api/v1/analytics/usage-statistics", "Get usage statistics"),
        ("GET", "/api/v1/analytics/learning-progress", "Get learning progress"),
        ("GET", "/api/v1/analytics/dashboard", "Get analytics dashboard"),
        ("POST", "/api/v1/analytics/export", "Export analytics data"),
        ("GET", "/api/v1/analytics/health", "Analytics health check"),
    ]
    for method, path, desc in tests:
        if not test_route_exists(method, path, desc):
            all_tests_passed = False
    print()
    
    # Feedback Statistics Endpoints
    print("💬 Feedback Statistics Endpoints (/api/v1/feedback)")
    print("-" * 80)
    tests = [
        ("GET", "/api/v1/feedback/statistics", "Get feedback statistics with timeframe"),
        ("POST", "/api/v1/feedback/feedback", "Submit feedback"),
        ("GET", "/api/v1/feedback/stats", "Get feedback stats"),
        ("GET", "/api/v1/feedback/history", "Get user feedback history"),
        ("POST", "/api/v1/feedback/bulk", "Submit bulk feedback"),
        ("GET", "/api/v1/feedback/trends", "Get feedback trends"),
    ]
    for method, path, desc in tests:
        if not test_route_exists(method, path, desc):
            all_tests_passed = False
    print()
    
    # User Profile Endpoints
    print("👤 User Profile Endpoints (/api/v1/users)")
    print("-" * 80)
    tests = [
        ("GET", "/api/v1/users/profile", "Get current user profile"),
        ("PUT", "/api/v1/users/profile", "Update current user profile"),
        ("POST", "/api/v1/users/profile-picture", "Upload profile picture"),
    ]
    for method, path, desc in tests:
        if not test_route_exists(method, path, desc):
            all_tests_passed = False
    print()
    
    # User Preferences Endpoints
    print("⚙️  User Preferences Endpoints (/api/v1/users)")
    print("-" * 80)
    tests = [
        ("GET", "/api/v1/users/preferences", "Get user preferences"),
        ("PUT", "/api/v1/users/preferences", "Update user preferences"),
        ("GET", "/api/v1/users/notifications", "Get notification preferences"),
        ("PUT", "/api/v1/users/notifications", "Update notification preferences"),
    ]
    for method, path, desc in tests:
        if not test_route_exists(method, path, desc):
            all_tests_passed = False
    print()
    
    # API Key Management Endpoints
    print("🔑 API Key Management Endpoints (/api/v1/users)")
    print("-" * 80)
    tests = [
        ("GET", "/api/v1/users/api-key", "Get API key status"),
        ("PUT", "/api/v1/users/api-key", "Save API key"),
        ("DELETE", "/api/v1/users/api-key", "Delete API key"),
    ]
    for method, path, desc in tests:
        if not test_route_exists(method, path, desc):
            all_tests_passed = False
    print()
    
    # Personalized AI Analysis Endpoints
    print("🤖 Personalized AI Analysis Endpoints (/api/v1/ai)")
    print("-" * 80)
    tests = [
        ("POST", "/api/v1/ai/analyze-with-learning", "Analyze code with learning"),
        ("GET", "/api/v1/ai/personalization-status", "Get personalization status"),
    ]
    for method, path, desc in tests:
        if not test_route_exists(method, path, desc):
            all_tests_passed = False
    print()
    
    # Summary
    print("=" * 80)
    if all_tests_passed:
        print("✅ All API routes are properly registered!")
        print("=" * 80)
        return 0
    else:
        print("❌ Some API routes are missing or not properly registered.")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
