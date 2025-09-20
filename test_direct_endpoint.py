#!/usr/bin/env python3
"""
Test the direct history endpoint specifically
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_direct_endpoint():
    print("Testing direct history endpoint...")
    
    # First, let's test without authentication to see what error we get
    print("1. Testing without authentication:")
    try:
        response = requests.get(f"{BASE_URL}/analysis/direct/history")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50)
    
    # Now let's try to login and test with authentication
    print("2. Testing with authentication:")
    
    # Login first
    login_data = {
        "username": "demo@example.com",
        "password": "DemoPassword123"
    }
    
    try:
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            print(f"✅ Login successful, token: {token[:20]}...")
            
            # Now test the endpoint with authentication
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{BASE_URL}/analysis/direct/history", headers=headers)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50)
    
    # Let's also test the root analysis endpoint to see if it works
    print("3. Testing base analysis endpoint:")
    try:
        response = requests.get(f"{BASE_URL}/analysis/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_direct_endpoint()