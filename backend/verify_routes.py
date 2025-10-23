"""
Verify that all required API routes are properly registered in the router.

This script directly inspects the FastAPI router to check route registration.
"""

import sys
from app.main import app

def check_routes():
    """Check all routes registered in the FastAPI app."""
    print("=" * 80)
    print("Verifying API Routes for Dashboard and Settings Improvements")
    print("=" * 80)
    print()
    
    # Get all routes from the app
    routes = {}
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            path = route.path
            methods = route.methods
            if path not in routes:
                routes[path] = []
            routes[path].extend(methods)
    
    # Define required routes
    required_routes = {
        # Analytics Endpoints
        "/api/v1/analytics/user-stats": ["GET"],
        "/api/v1/analytics/usage-trends": ["GET"],
        "/api/v1/analytics/feedback-distribution": ["GET"],
        "/api/v1/analytics/acceptance-rates": ["GET"],
        "/api/v1/analytics/rejection-patterns": ["GET"],
        "/api/v1/analytics/usage-statistics": ["GET"],
        "/api/v1/analytics/learning-progress": ["GET"],
        "/api/v1/analytics/dashboard": ["GET"],
        "/api/v1/analytics/export": ["POST"],
        "/api/v1/analytics/health": ["GET"],
        
        # Feedback Statistics Endpoints (note: some have /feedback/ prefix due to route structure)
        "/api/v1/feedback/statistics": ["GET"],
        "/api/v1/feedback/feedback": ["POST"],
        "/api/v1/feedback/feedback/stats": ["GET"],
        "/api/v1/feedback/feedback/history": ["GET"],
        "/api/v1/feedback/feedback/bulk": ["POST"],
        "/api/v1/feedback/feedback/trends": ["GET"],
        
        # User Profile Endpoints
        "/api/v1/users/profile": ["GET", "PUT"],
        "/api/v1/users/profile-picture": ["POST"],
        
        # User Preferences Endpoints
        "/api/v1/users/preferences": ["GET", "PUT"],
        "/api/v1/users/notifications": ["GET", "PUT"],
        
        # API Key Management Endpoints
        "/api/v1/users/api-key": ["GET", "PUT", "DELETE"],
        
        # Personalized AI Analysis Endpoints
        "/api/v1/ai/analyze-with-learning": ["POST"],
        "/api/v1/ai/personalization-status": ["GET"],
    }
    
    all_passed = True
    
    # Check each required route
    print("Checking Required Routes:")
    print("-" * 80)
    
    for path, required_methods in sorted(required_routes.items()):
        if path in routes:
            registered_methods = [m for m in routes[path] if m != "HEAD" and m != "OPTIONS"]
            missing_methods = [m for m in required_methods if m not in registered_methods]
            
            if missing_methods:
                print(f"⚠️  {path}")
                print(f"   Missing methods: {', '.join(missing_methods)}")
                print(f"   Registered: {', '.join(registered_methods)}")
                all_passed = False
            else:
                methods_str = ', '.join(required_methods)
                print(f"✅ {path} [{methods_str}]")
        else:
            print(f"❌ {path} - NOT REGISTERED")
            all_passed = False
    
    print()
    print("=" * 80)
    
    # Show all registered routes for debugging
    print("\nAll Registered Routes:")
    print("-" * 80)
    for path in sorted(routes.keys()):
        if path.startswith("/api/v1/"):
            methods = [m for m in routes[path] if m != "HEAD" and m != "OPTIONS"]
            print(f"{path} [{', '.join(methods)}]")
    
    print()
    print("=" * 80)
    
    if all_passed:
        print("✅ All required API routes are properly registered!")
        return 0
    else:
        print("❌ Some required API routes are missing or incomplete.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(check_routes())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
