#!/usr/bin/env python3
"""
Simple test to verify login credentials work
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_login():
    print("Testing login credentials...")
    
    # Test the exact credentials
    login_data = {
        "username": "test@example.com",
        "password": "TestPassword123"
    }
    
    print(f"Attempting login with: {login_data['username']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            data = response.json()
            print(f"User: {data.get('user', {}).get('email')}")
            print(f"Token: {data.get('access_token', '')[:20]}...")
        else:
            print("❌ Login failed!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()