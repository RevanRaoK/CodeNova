#!/usr/bin/env python3
"""
Test script to verify the analysis history endpoint works correctly.
"""

import sys
import requests
import json

def test_analysis_history_endpoint():
    """Test the analysis history endpoint."""
    
    # You'll need to replace this with a valid token
    # You can get this from the browser's developer tools or login endpoint
    token = "your-jwt-token-here"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test the endpoint
    url = "http://localhost:8000/api/v1/analysis/direct/history"
    
    print(f"Testing endpoint: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Response data:")
            print(json.dumps(data, indent=2))
        elif response.status_code == 401:
            print("❌ Authentication failed. Please update the token in this script.")
        elif response.status_code == 404:
            print("❌ Endpoint not found. Check if the server is running and endpoint exists.")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the backend server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=== Analysis History Endpoint Test ===")
    print("Note: You need to update the token in this script with a valid JWT token")
    print("You can get a token by:")
    print("1. Login to the frontend")
    print("2. Open browser developer tools")
    print("3. Check localStorage or sessionStorage for the auth token")
    print("4. Update the 'token' variable in this script")
    print()
    
    test_analysis_history_endpoint()