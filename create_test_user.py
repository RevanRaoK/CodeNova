#!/usr/bin/env python3
"""
Create a test user for login
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def create_test_user():
    print("Creating test user...")
    
    # User data
    user_data = {
        "email": "demo@example.com",
        "full_name": "Demo User",
        "password": "DemoPassword123"
    }
    
    print(f"Creating user: {user_data['email']}")
    
    try:
        # Try to register
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ User created successfully!")
            data = response.json()
            print(f"User: {data.get('user', {}).get('email')}")
            print(f"Token: {data.get('access_token', '')[:20]}...")
            print("\nYou can now login with:")
            print(f"Email: {user_data['email']}")
            print(f"Password: {user_data['password']}")
        elif response.status_code == 400 and "already registered" in response.text:
            print("ℹ️  User already exists, testing login...")
            
            # Try to login
            login_data = {
                "username": user_data['email'],
                "password": user_data['password']
            }
            
            login_response = requests.post(
                f"{BASE_URL}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if login_response.status_code == 200:
                print("✅ Login successful with existing user!")
                print(f"Email: {user_data['email']}")
                print(f"Password: {user_data['password']}")
            else:
                print("❌ Login failed with existing user")
                print(f"Response: {login_response.text}")
        else:
            print("❌ User creation failed!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_test_user()