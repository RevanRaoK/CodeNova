#!/usr/bin/env python3

import requests
import json

# Test the specific analysis that's failing
analysis_id = "1a706e94-fa8b-4e3c-aa4f-ef32930bd990"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZW1haWwiOiJyZXZhbmtva2tpcmFsYUBnbWFpbC5jb20iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NjE0OTMxMTksImlhdCI6MTc2MTQ5MTMxOSwidHlwZSI6ImFjY2VzcyJ9.Cxl9kTC4LURgDdgMfHy9HK6pBmqMSxYnvg22BXsr_z4"

headers = {"Authorization": f"Bearer {token}"}

# Test different endpoints
endpoints = [
    f"http://localhost:8000/api/v1/analysis/direct/{analysis_id}",
    f"http://localhost:8000/api/v1/analysis/batch/{analysis_id}",
    f"http://localhost:8000/api/v1/files/analysis/result/{analysis_id}"
]

for endpoint in endpoints:
    print(f"\nTesting: {endpoint}")
    try:
        response = requests.get(endpoint, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS!")
            print(f"Analysis ID: {data.get('analysis_id', 'N/A')}")
            print(f"Type: {data.get('type', 'N/A')}")
            print(f"Status: {data.get('status', 'N/A')}")
            print(f"Issues: {len(data.get('issues', []))}")
            break
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

print("\n" + "="*50)
print("CONCLUSION: Need to fix the frontend to use correct endpoint based on analysis type")