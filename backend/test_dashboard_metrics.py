#!/usr/bin/env python3

import requests
import json

# Test the dashboard metrics endpoint
url = "http://localhost:8000/api/v1/admin/analytics/dashboard-metrics"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZW1haWwiOiJyYWNoYXByYW5hdmFuYWRoQGdtYWlsLmNvbSIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc2MTY3NjU3NywiaWF0IjoxNzYxNjc0Nzc3LCJ0eXBlIjoiYWNjZXNzIn0.eIoz9tNhmjM0oBjTPIxWBwfT8cZjBtQY1sTj5-5DQwM"

headers = {"Authorization": f"Bearer {token}"}

try:
    print("Testing dashboard metrics endpoint...")
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS!")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "="*50)

# Also test platform stats
url2 = "http://localhost:8000/api/v1/admin/analytics/platform"
try:
    print("Testing platform stats endpoint...")
    response = requests.get(url2, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS!")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Exception: {e}")