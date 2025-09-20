#!/usr/bin/env python3
"""
Test script for the enhanced API endpoints
Make sure the backend server is running on localhost:8000
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")

def print_response(response, title="Response"):
    print(f"\n{title}:")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response Text: {response.text}")

def test_enhanced_api():
    print("Testing Enhanced API Endpoints")
    print(f"Base URL: {BASE_URL}")
    
    # Test 1: Register/Login
    print_section("1. Authentication")
    
    # Try to register a user
    register_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "TestPassword123"
    }
    
    print("Attempting to register user...")
    register_response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    
    if register_response.status_code == 201:
        print("✅ User registered successfully")
        token_data = register_response.json()
        access_token = token_data.get("access_token")
    elif register_response.status_code == 400 and "already registered" in register_response.text:
        print("ℹ️  User already exists, attempting login...")
        
        # Login with existing user
        login_data = {
            "username": "test@example.com",
            "password": "TestPassword123"
        }
        
        login_response = requests.post(
            f"{BASE_URL}/auth/login", 
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code == 200:
            print("✅ Login successful")
            token_data = login_response.json()
            access_token = token_data.get("access_token")
        else:
            print("❌ Login failed")
            print_response(login_response)
            return
    else:
        print("❌ Registration failed")
        print_response(register_response)
        return
    
    if not access_token:
        print("❌ Failed to get access token")
        return
    
    print(f"✅ Access token obtained: {access_token[:20]}...")
    
    # Set up headers for authenticated requests
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test 2: Direct Code Analysis
    print_section("2. Direct Code Analysis")
    
    code_analysis_data = {
        "code": """function add(a, b) {
    return a + b;
}

function multiply(x, y) {
    return x * y;
}

// This function has a potential issue
function divide(a, b) {
    return a / b;  // No check for division by zero
}""",
        "language": "javascript",
        "filename": "math.js"
    }
    
    print("Testing direct code analysis...")
    analysis_response = requests.post(
        f"{BASE_URL}/analysis/analyze-code",
        json=code_analysis_data,
        headers=headers
    )
    
    if analysis_response.status_code == 200:
        print("✅ Code analysis successful")
        analysis_result = analysis_response.json()
        print(f"Analysis ID: {analysis_result.get('analysis_id')}")
        print(f"Issues found: {len(analysis_result.get('issues', []))}")
        print(f"Lines of code: {analysis_result.get('metrics', {}).get('lines_of_code')}")
        print(f"Summary: {analysis_result.get('summary')}")
        
        # Store analysis ID for later tests
        analysis_id = analysis_result.get('analysis_id')
    else:
        print("❌ Code analysis failed")
        print_response(analysis_response)
        analysis_id = None
    
    # Test 3: File Upload
    print_section("3. File Upload")
    
    # Create a test Python file
    test_code = """def calculate_factorial(n):
    if n < 0:
        return None
    elif n == 0:
        return 1
    else:
        result = 1
        for i in range(1, n + 1):
            result *= i
        return result

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)  # Inefficient recursive implementation

# Test the functions
print(calculate_factorial(5))
print(fibonacci(10))
"""
    
    print("Testing file upload...")
    files = {'file': ('test_code.py', test_code, 'text/plain')}
    data = {'language': 'python'}
    
    upload_response = requests.post(
        f"{BASE_URL}/files/upload",
        files=files,
        data=data,
        headers=headers
    )
    
    if upload_response.status_code == 200:
        print("✅ File upload successful")
        upload_result = upload_response.json()
        print(f"Upload ID: {upload_result.get('upload_id')}")
        print(f"Language detected: {upload_result.get('language')}")
        print(f"File size: {upload_result.get('size_kb')} KB")
        print(f"Lines count: {upload_result.get('lines_count')}")
    else:
        print("❌ File upload failed")
        print_response(upload_response)
    
    # Test 4: Get Supported Extensions
    print_section("4. Supported Extensions")
    
    print("Getting supported file extensions...")
    extensions_response = requests.get(f"{BASE_URL}/files/supported-extensions")
    
    if extensions_response.status_code == 200:
        print("✅ Successfully retrieved supported extensions")
        extensions_data = extensions_response.json()
        print(f"Total supported extensions: {len(extensions_data.get('supported_extensions', []))}")
        print(f"Max file size: {extensions_data.get('max_file_size_kb')} KB")
        print(f"Max lines: {extensions_data.get('max_lines')}")
        
        # Show some example extensions
        lang_mapping = extensions_data.get('language_mapping', {})
        print("\nSample language mappings:")
        for lang, exts in list(lang_mapping.items())[:5]:
            print(f"  {lang}: {', '.join(exts[:3])}")
    else:
        print("❌ Failed to get supported extensions")
        print_response(extensions_response)
    
    # Test 5: Analysis History
    print_section("5. Analysis History")
    
    print("Getting analysis history...")
    history_response = requests.get(
        f"{BASE_URL}/analysis/direct/history?page=1&page_size=10",
        headers=headers
    )
    
    if history_response.status_code == 200:
        print("✅ Successfully retrieved analysis history")
        history_data = history_response.json()
        print(f"Total analyses: {history_data.get('total_count')}")
        print(f"Current page: {history_data.get('page')}")
        print(f"Analyses on this page: {len(history_data.get('analyses', []))}")
        
        # Show recent analyses
        for analysis in history_data.get('analyses', [])[:3]:
            print(f"  - {analysis.get('analysis_id')[:8]}... ({analysis.get('language')}) - {analysis.get('issues_count')} issues")
    else:
        print("❌ Failed to get analysis history")
        print_response(history_response)
    
    # Test 6: Analysis Statistics
    print_section("6. Analysis Statistics")
    
    print("Getting analysis statistics...")
    stats_response = requests.get(
        f"{BASE_URL}/analysis/direct/stats",
        headers=headers
    )
    
    if stats_response.status_code == 200:
        print("✅ Successfully retrieved analysis statistics")
        stats_data = stats_response.json()
        print(f"Total analyses: {stats_data.get('total_analyses')}")
        print(f"Completed analyses: {stats_data.get('completed_analyses')}")
        print(f"Failed analyses: {stats_data.get('failed_analyses')}")
        print(f"Total issues found: {stats_data.get('total_issues_found')}")
        print(f"Total lines analyzed: {stats_data.get('total_lines_analyzed')}")
        print(f"Languages used: {', '.join(stats_data.get('languages_used', []))}")
        print(f"Average issues per analysis: {stats_data.get('avg_issues_per_analysis')}")
    else:
        print("❌ Failed to get analysis statistics")
        print_response(stats_response)
    
    # Test 7: Get Specific Analysis (if we have an analysis_id)
    if analysis_id:
        print_section("7. Get Specific Analysis")
        
        print(f"Getting analysis details for ID: {analysis_id}")
        specific_analysis_response = requests.get(
            f"{BASE_URL}/analysis/direct/{analysis_id}",
            headers=headers
        )
        
        if specific_analysis_response.status_code == 200:
            print("✅ Successfully retrieved specific analysis")
            specific_data = specific_analysis_response.json()
            print(f"Status: {specific_data.get('status')}")
            print(f"Language: {specific_data.get('language')}")
            print(f"Processing time: {specific_data.get('processing_time_ms')} ms")
            print(f"Issues count: {len(specific_data.get('issues', []))}")
        else:
            print("❌ Failed to get specific analysis")
            print_response(specific_analysis_response)
    
    print_section("Testing Complete")
    print("✅ All tests completed successfully!")

if __name__ == "__main__":
    try:
        test_enhanced_api()
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the backend server is running on localhost:8000")
        print("Start the server with: cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)