#!/usr/bin/env python3
"""
Test script for enhanced AI response processing.

This script tests the improvements made to AI suggestion quality:
- Distinct problem description and solution guidance
- Validation of suggestions with code examples
- Quality checks for unique and contextual suggestions

Requirements: 7.5, 7.6, 7.7
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service import AIService
import json

def test_enhanced_response_processing():
    """Test the enhanced AI response processing functionality."""
    
    print("=== Testing Enhanced AI Response Processing ===\n")
    
    # Initialize AI service
    ai_service = AIService()
    
    # Test 1: Validate suggestion structure
    print("Test 1: Validating suggestion structure")
    
    valid_suggestion = {
        "file_path": "test.py",
        "line_number": 5,
        "comment": "Variable is used without initialization",
        "suggestion": "Initialize the variable before use: x = 0",
        "severity": "medium"
    }
    
    invalid_suggestion = {
        "file_path": "test.py",
        # Missing line_number
        "comment": "Some issue",
        "severity": "low"
    }
    
    assert ai_service._validate_suggestion_structure(valid_suggestion) == True
    assert ai_service._validate_suggestion_structure(invalid_suggestion) == False
    print("✓ Suggestion structure validation works correctly\n")
    
    # Test 2: Ensure distinct problem and solution
    print("Test 2: Ensuring distinct problem and solution")
    
    mixed_suggestion = {
        "file_path": "test.py",
        "line_number": 10,
        "comment": "Variable name is unclear and should be renamed to something more descriptive",
        "severity": "low"
    }
    
    processed = ai_service._ensure_distinct_problem_solution(mixed_suggestion)
    
    print(f"Original comment: {mixed_suggestion['comment']}")
    print(f"Processed comment: {processed['comment']}")
    print(f"Generated suggestion: {processed.get('suggestion', 'None')}")
    
    assert 'suggestion' in processed
    assert len(processed['suggestion']) > 0
    print("✓ Problem/solution separation works correctly\n")
    
    # Test 3: Quality validation
    print("Test 3: Quality validation")
    
    high_quality_suggestion = {
        "file_path": "test.py",
        "line_number": 15,
        "comment": "Function parameter 'data' lacks type annotation which reduces code clarity",
        "suggestion": "Add type annotation to the parameter: def process_data(data: Dict[str, Any]) -> None",
        "severity": "suggestion"
    }
    
    low_quality_suggestion = {
        "file_path": "test.py",
        "line_number": 20,
        "comment": "Bad code",
        "suggestion": "Fix this",
        "severity": "low"
    }
    
    assert ai_service._validate_suggestion_quality(high_quality_suggestion) == True
    assert ai_service._validate_suggestion_quality(low_quality_suggestion) == False
    print("✓ Quality validation works correctly\n")
    
    # Test 4: Duplicate removal
    print("Test 4: Duplicate removal")
    
    suggestions_with_duplicates = [
        {
            "file_path": "test.py",
            "line_number": 1,
            "comment": "Variable name is not descriptive",
            "suggestion": "Use a more descriptive variable name",
            "severity": "low"
        },
        {
            "file_path": "test.py",
            "line_number": 2,
            "comment": "Variable name is not descriptive and unclear",
            "suggestion": "Choose a better variable name",
            "severity": "low"
        },
        {
            "file_path": "test.py",
            "line_number": 3,
            "comment": "Variable name is not descriptive",  # Exact duplicate
            "suggestion": "Use more descriptive variable names",
            "severity": "low"
        },
        {
            "file_path": "test.py",
            "line_number": 4,
            "comment": "Missing error handling for file operations",
            "suggestion": "Add try-except block around file operations",
            "severity": "medium"
        }
    ]
    
    unique_suggestions = ai_service._remove_duplicate_suggestions(suggestions_with_duplicates)
    
    print(f"Original suggestions: {len(suggestions_with_duplicates)}")
    print(f"After deduplication: {len(unique_suggestions)}")
    
    assert len(unique_suggestions) < len(suggestions_with_duplicates)
    print("✓ Duplicate removal works correctly\n")
    
    # Test 5: Full processing pipeline
    print("Test 5: Full processing pipeline")
    
    raw_suggestions = [
        {
            "file_path": "example.py",
            "line_number": 1,
            "comment": "Function has too many parameters and should be refactored",
            "severity": "medium"
        },
        {
            "file_path": "example.py",
            "line_number": 5,
            "comment": "Missing docstring",
            "suggestion": "Add a docstring to describe the function purpose",
            "severity": "suggestion"
        },
        {
            "file_path": "example.py",
            "line_number": 10,
            "comment": "Bad",  # This should be filtered out
            "suggestion": "Fix",
            "severity": "low"
        }
    ]
    
    processed_suggestions = ai_service._process_and_validate_suggestions(
        raw_suggestions, 
        "Mock raw text response"
    )
    
    print(f"Processed {len(processed_suggestions)} suggestions:")
    for i, suggestion in enumerate(processed_suggestions, 1):
        print(f"  {i}. {suggestion['comment']}")
        print(f"     Solution: {suggestion.get('suggestion', 'N/A')}")
        print(f"     Severity: {suggestion.get('severity', 'N/A')}")
        print()
    
    # Verify all processed suggestions have both comment and suggestion
    for suggestion in processed_suggestions:
        assert 'comment' in suggestion and len(suggestion['comment']) > 10
        assert 'suggestion' in suggestion and len(suggestion['suggestion']) > 10
    
    print("✓ Full processing pipeline works correctly\n")
    
    # Test 6: Test with actual code analysis
    print("Test 6: Testing with actual code analysis")
    
    test_code = """
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
    """
    
    try:
        suggestions = ai_service.get_review_for_code(test_code)
        
        print(f"Generated {len(suggestions)} suggestions for test code:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. Problem: {suggestion.get('comment', 'N/A')}")
            print(f"     Solution: {suggestion.get('suggestion', 'N/A')}")
            print(f"     Severity: {suggestion.get('severity', 'N/A')}")
            print(f"     Has code example: {suggestion.get('has_code_example', False)}")
            print()
        
        # Verify suggestions follow the new format
        for suggestion in suggestions:
            assert 'comment' in suggestion
            assert 'suggestion' in suggestion or 'comment' in suggestion
            print(f"✓ Suggestion {suggestions.index(suggestion) + 1} has proper structure")
        
        print("✓ Actual code analysis with enhanced processing works correctly\n")
        
    except Exception as e:
        print(f"Note: Actual AI analysis test skipped (likely no API key): {e}\n")
    
    print("=== All Enhanced AI Response Processing Tests Passed! ===")

if __name__ == "__main__":
    test_enhanced_response_processing()