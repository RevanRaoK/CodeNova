#!/usr/bin/env python3

import requests
import json

# Test the actual endpoint that the frontend is calling
url = "http://localhost:8000/api/v1/analysis/direct/history"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZW1haWwiOiJyZXZhbmtva2tpcmFsYUBnbWFpbC5jb20iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NjE0OTMxMTksImlhdCI6MTc2MTQ5MTMxOSwidHlwZSI6ImFjY2VzcyJ9.Cxl9kTC4LURgDdgMfHy9HK6pBmqMSxYnvg22BXsr_z4"
}

try:
    print("Testing analysis history endpoint...")
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total analyses: {data.get('total_count', 0)}")
        print(f"Analyses returned: {len(data.get('analyses', []))}")
        
        print("\nFirst 3 analyses:")
        for i, analysis in enumerate(data.get('analyses', [])[:3]):
            print(f"{i+1}. ID: {analysis.get('analysis_id')}")
            print(f"   Type: {analysis.get('type')}")
            print(f"   Filename: {analysis.get('filename')}")
            print(f"   Status: {analysis.get('status')}")
            print(f"   Issues: {analysis.get('issues_count', 0)}")
            print(f"   Created: {analysis.get('created_at')}")
            print("---")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")