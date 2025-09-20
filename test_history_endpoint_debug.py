#!/usr/bin/env python3
"""
Debug the history endpoint with detailed logging
"""

import requests
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

BASE_URL = "http://localhost:8000/api/v1"

def test_history_endpoint_debug():
    print("Debugging history endpoint...")
    
    # Login with the user we know has data
    login_data = {
        "username": "demo@example.com",
        "password": "DemoPassword123"
    }
    
    print("1. Logging in...")
    try:
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
        
        token_data = login_response.json()
        token = token_data.get("access_token")
        user_info = token_data.get("user", {})
        
        print(f"✅ Login successful")
        print(f"User ID: {user_info.get('id')}")
        print(f"User Email: {user_info.get('email')}")
        print(f"Token: {token[:20]}...")
        
        # Now test the history endpoint
        print("\n2. Testing history endpoint...")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/analysis/direct/history", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('total_count', 0)} analyses")
            for analysis in data.get('analyses', []):
                print(f"  - {analysis.get('analysis_id')}: {analysis.get('language')} ({analysis.get('status')})")
        else:
            print(f"❌ Failed with status {response.status_code}")
            
            # Let's also test the stats endpoint
            print("\n3. Testing stats endpoint...")
            stats_response = requests.get(f"{BASE_URL}/analysis/direct/stats", headers=headers)
            print(f"Stats Status Code: {stats_response.status_code}")
            print(f"Stats Response: {stats_response.text}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_user_id_mismatch():
    """Test if there's a user ID mismatch issue"""
    print("\n" + "="*50)
    print("Testing for user ID mismatch...")
    
    try:
        from app.core.database import SessionLocal
        from app.models.users import User
        from app.services.auth_service import AuthService
        
        db = SessionLocal()
        
        try:
            # Find the user by email
            user = db.query(User).filter(User.email == "demo@example.com").first()
            if user:
                print(f"Database User ID: {user.id}")
                print(f"Database User Email: {user.email}")
                
                # Test the auth service
                authenticated_user = AuthService.authenticate_user(db, "demo@example.com", "DemoPassword123")
                if authenticated_user:
                    print(f"Auth Service User ID: {authenticated_user.id}")
                    print(f"Auth Service User Email: {authenticated_user.email}")
                    
                    if user.id == authenticated_user.id:
                        print("✅ User IDs match")
                    else:
                        print("❌ User ID mismatch!")
                else:
                    print("❌ Auth service authentication failed")
            else:
                print("❌ User not found in database")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error testing user ID: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_history_endpoint_debug()
    test_user_id_mismatch()