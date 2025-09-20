#!/usr/bin/env python3
"""
Test script to isolate the analyze-code endpoint issue
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_single_endpoint():
    print("Testing single analyze-code endpoint...")
    
    # First login to get token
    login_data = {
        "username": "test@example.com",
        "password": "TestPassword123"
    }
    
    login_response = requests.post(
        f"{BASE_URL}/auth/login", 
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    access_token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test the analyze-code endpoint with minimal data
    simple_code_data = {
        "code": "console.log('hello world');",
        "language": "javascript"
    }
    
    print("Sending request to /analysis/analyze-code...")
    print(f"Request data: {json.dumps(simple_code_data, indent=2)}")
    
    try:
        analysis_response = requests.post(
            f"{BASE_URL}/analysis/analyze-code",
            json=simple_code_data,
            headers=headers,
            timeout=30  # Add timeout
        )
        
        print(f"Response status: {analysis_response.status_code}")
        print(f"Response headers: {dict(analysis_response.headers)}")
        
        if analysis_response.status_code == 200:
            print("✅ Success!")
            result = analysis_response.json()
            print(f"Analysis ID: {result.get('analysis_id')}")
            print(f"Status: {result.get('status')}")
            print(f"Issues count: {len(result.get('issues', []))}")
        else:
            print("❌ Failed!")
            print(f"Response text: {analysis_response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - server might be hanging")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the server running?")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_single_endpoint()