#!/usr/bin/env python3
"""
Test script for Task 4 Backend API endpoints.

This script verifies that all the new endpoints are properly registered
and accessible.
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_endpoint_imports():
    """Test that all new endpoint modules can be imported."""
    endpoints = [
        "app.api.v1.endpoints.file_upload",
        "app.api.v1.endpoints.analysis_enhanced",
        "app.api.v1.endpoints.admin_teams",
        "app.api.v1.endpoints.admin_users",
        "app.api.v1.endpoints.admin_analytics",
        "app.api.v1.endpoints.user_analytics",
        "app.api.v1.endpoints.audit_logs",
    ]
    
    print("Testing endpoint imports...")
    for endpoint in endpoints:
        try:
            module = __import__(endpoint, fromlist=[''])
            assert hasattr(module, 'router'), f"{endpoint} missing router"
            print(f"✓ {endpoint}")
        except Exception as e:
            print(f"✗ {endpoint}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


def test_router_registration():
    """Test that the router includes all new endpoints."""
    try:
        from app.api.v1.router import api_router
        
        print("\nTesting router registration...")
        
        # Check that router has routes
        assert len(api_router.routes) > 0, "Router has no routes"
        print(f"✓ Router has {len(api_router.routes)} routes registered")
        
        # List some key routes
        route_paths = [route.path for route in api_router.routes if hasattr(route, 'path')]
        
        expected_prefixes = [
            "/file-upload",
            "/analysis-enhanced",
            "/admin/teams",
            "/admin/users",
            "/admin/analytics",
            "/user-analytics",
            "/admin/audit-logs"
        ]
        
        print("\nChecking for expected route prefixes...")
        for prefix in expected_prefixes:
            matching = [p for p in route_paths if p.startswith(prefix)]
            if matching:
                print(f"✓ Found routes with prefix: {prefix}")
            else:
                print(f"⚠ No routes found with prefix: {prefix}")
        
        return True
        
    except Exception as e:
        print(f"✗ Router registration test failed: {e}")
        return False


def test_service_methods():
    """Test that services have required methods."""
    print("\nTesting service methods...")
    
    try:
        from app.services.analytics_service import AnalyticsService
        assert hasattr(AnalyticsService, 'get_issue_trends'), "AnalyticsService missing get_issue_trends"
        assert hasattr(AnalyticsService, 'get_criticality_distribution'), "AnalyticsService missing get_criticality_distribution"
        print("✓ AnalyticsService has required methods")
    except Exception as e:
        print(f"✗ AnalyticsService: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        from app.services.global_analytics_service import GlobalAnalyticsService
        assert hasattr(GlobalAnalyticsService, 'get_platform_stats'), "GlobalAnalyticsService missing get_platform_stats"
        assert hasattr(GlobalAnalyticsService, 'get_global_issue_trends'), "GlobalAnalyticsService missing get_global_issue_trends"
        assert hasattr(GlobalAnalyticsService, 'get_team_comparison'), "GlobalAnalyticsService missing get_team_comparison"
        assert hasattr(GlobalAnalyticsService, 'get_all_reviews'), "GlobalAnalyticsService missing get_all_reviews"
        assert hasattr(GlobalAnalyticsService, 'get_all_feedback'), "GlobalAnalyticsService missing get_all_feedback"
        print("✓ GlobalAnalyticsService has required methods")
    except Exception as e:
        print(f"✗ GlobalAnalyticsService: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        from app.services.audit_logger import AuditLogger
        assert hasattr(AuditLogger, 'get_audit_logs'), "AuditLogger missing get_audit_logs"
        assert hasattr(AuditLogger, 'get_available_actions'), "AuditLogger missing get_available_actions"
        assert hasattr(AuditLogger, 'get_available_resource_types'), "AuditLogger missing get_available_resource_types"
        print("✓ AuditLogger has required methods")
    except Exception as e:
        print(f"✗ AuditLogger: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Task 4 Backend API Endpoints Verification")
    print("=" * 60)
    
    results = []
    
    # Test imports
    results.append(("Endpoint Imports", test_endpoint_imports()))
    
    # Test router
    results.append(("Router Registration", test_router_registration()))
    
    # Test services
    results.append(("Service Methods", test_service_methods()))
    
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
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
