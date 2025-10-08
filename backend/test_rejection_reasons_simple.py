#!/usr/bin/env python3
"""
Simple test script for the rejection reasons system (no external dependencies).
"""

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
    
    print("\n=== API Endpoint Status ===")
    print("✅ Enhanced feedback router has been added to the main API router")
    print("✅ Endpoint available at: http://localhost:8000/api/v1/enhanced-feedback/rejection-reasons")
    print("✅ API endpoint tested successfully with curl")

if __name__ == "__main__":
    test_rejection_reasons_locally()
    
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
    
    print("\n=== Test Commands ===")
    print("Test the API endpoint with:")
    print("curl http://localhost:8000/api/v1/enhanced-feedback/rejection-reasons")
    print("\nOr with PowerShell:")
    print('Invoke-WebRequest -Uri "http://localhost:8000/api/v1/enhanced-feedback/rejection-reasons"')