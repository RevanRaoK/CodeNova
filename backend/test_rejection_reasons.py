#!/usr/bin/env python3
"""
Test script for the new rejection reasons system.
"""

import requests
import json
from app.schemas.rejection_reasons import get_rejection_reasons_for_api, get_rejection_reasons_by_category

def test_rejection_reasons_locally():
    """Test the rejection reasons system locally."""
    print("=== Testing Rejection Reasons System ===\n")
    
    # Test getting all rejection reasons
    print("1. All Rejection Reasons:")
    all_reasons = get_rejection_reasons_for_api()
    for reason, info in all_reasons.items():
        print(f"   {reason}: {info['description']}")
    
    print(f"\nTotal reasons: {len(all_reasons)}\n")
    
    # Test getting reasons by category
    print("2. Rejection Reasons by Category:")
    categories = get_rejection_reasons_by_category()
    for category, reasons in categories.items():
        print(f"\n   {category}:")
        for reason in reasons:
            print(f"     - {reason['display_name']}: {reason['description']}")
    
    print(f"\nTotal categories: {len(categories)}")

def test_api_endpoint():
    """Test the API endpoint (requires server to be running)."""
    try:
        print("\n=== Testing API Endpoint ===")
        response = requests.get("http://localhost:8000/api/v1/enhanced-feedback/rejection-reasons")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API endpoint working!")
            print(f"Total reasons: {data['total_reasons']}")
            print(f"Categories: {list(data['categories'].keys())}")
        else:
            print(f"❌ API endpoint failed with status: {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("⚠️  Server not running - skipping API test")
    except Exception as e:
        print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    test_rejection_reasons_locally()
    test_api_endpoint()
    
    print("\n=== Example Usage ===")
    print("Valid rejection reasons for API calls:")
    reasons = get_rejection_reasons_for_api()
    example_reasons = list(reasons.keys())[:3]
    print(f"Example: {example_reasons}")
    
    print("\nExample API request body:")
    example_request = {
        "suggestion_id": "example-suggestion-123",
        "action": "reject",
        "rejection_reasons": example_reasons,
        "custom_reason": "Additional context about why this was rejected",
        "suggestion_type": "code_improvement"
    }
    print(json.dumps(example_request, indent=2))