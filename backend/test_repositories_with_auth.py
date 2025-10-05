#!/usr/bin/env python3
"""
Test script to verify the repositories API endpoint with authentication
"""

import asyncio
import sys
import os
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

def test_repositories_with_auth():
    """Test the repositories API endpoint with authentication"""
    try:
        client = TestClient(app)
        
        print("Testing authentication and repositories endpoint...")
        
        # First, let's try to login to get a token
        login_data = {
            "email": "test@example.com",  # Admin user from our previous context
            "password": "Test@123"
        }
        
        print("Attempting login...")
        login_response = client.post("/api/v1/auth/login-json", json=login_data)
        
        print(f"Login Status Code: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("access_token")
            
            if token:
                print("Login successful, testing repositories endpoint...")
                
                # Now test repositories endpoint with authentication
                headers = {"Authorization": f"Bearer {token}"}
                repo_response = client.get("/api/v1/github/repositories", headers=headers)
                
                print(f"Repositories Status Code: {repo_response.status_code}")
                print(f"Repositories Response: {repo_response.text}")
                
                if repo_response.status_code == 200:
                    data = repo_response.json()
                    print(f"Success! Found {data.get('total', 0)} repositories")
                    if data.get('repositories'):
                        for repo in data['repositories']:
                            print(f"  - {repo.get('repo_name')} ({repo.get('repo_url')})")
                else:
                    print(f"Repository endpoint failed with status {repo_response.status_code}")
            else:
                print("No access token in login response")
        else:
            print(f"Login failed with status {login_response.status_code}")
            print(f"Login response: {login_response.text}")
            
    except Exception as e:
        print(f"Error testing API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_repositories_with_auth()