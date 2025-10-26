#!/usr/bin/env python3

import requests
import json

# Test the dashboard metrics endpoint
url = "http://localhost:8000/api/v1/admin/analytics/dashboard-metrics"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZW1haWwiOiJyZXZhbmtva2tpcmFsYUBnbWFpbC5jb20iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NjE0OTMxMTksImlhdCI6MTc2MTQ5MTMxOSwidHlwZSI6ImFjY2VzcyJ9.Cxl9kTC4LURgDdgMfHy9HK6pBmqMSxYnvg22BXsr_z4"

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