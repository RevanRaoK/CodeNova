#!/usr/bin/env python3
"""
Test script to verify the repositories API endpoint
"""

import asyncio
import sys
import os
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

def test_repositories_endpoint():
    """Test the repositories API endpoint"""
    try:
        client = TestClient(app)
        
        print("Testing /api/v1/github/repositories endpoint...")
        
        # First, let's try without authentication to see what happens
        response = client.get("/api/v1/github/repositories")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("Authentication required - this is expected")
        elif response.status_code == 200:
            print("Success! Repository data returned")
            data = response.json()
            print(f"Repository count: {data.get('total', 0)}")
        else:
            print(f"Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"Error testing API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_repositories_endpoint()