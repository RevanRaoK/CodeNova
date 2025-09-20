#!/usr/bin/env python3
"""
Test if the analysis endpoints can be imported without errors
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    print("Testing endpoint imports...")
    
    try:
        from app.api.v1.endpoints import analysis
        print("✅ Analysis endpoints imported successfully")
        
        # Check if the router has the expected endpoints
        routes = [route.path for route in analysis.router.routes]
        print(f"Available routes: {routes}")
        
        expected_routes = ['/analyze-code', '/direct/history', '/direct/stats']
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"✅ Found route: {route}")
            else:
                print(f"❌ Missing route: {route}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_imports()