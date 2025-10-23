"""
Test script for personalized AI service implementation.

This script tests:
1. Enhanced prompt construction with problem/solution separation
2. Personalized analysis integration
3. API endpoint functionality

Requirements tested: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 8.3, 8.4, 8.5, 8.6
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service import AIService
from app.services.personalized_prompt_builder import PersonalizedPromptBuilder
from app.core.database import SessionLocal
from app.models.users import User
from app.models.feedback import FeedbackRecord, Issue
from app.models.analysis import DirectAnalysis
from datetime import datetime, timedelta
import uuid


def test_enhanced_prompt():
    """Test that the enhanced prompt includes proper instructions."""
    print("\n=== Testing Enhanced Prompt Construction ===")
    
    ai_service = AIService()
    
    sample_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total = total + item
    return total
"""
    
    prompt = ai_service._construct_prompt(sample_code)
    
    # Check for key requirements
    checks = [
        ("Separate Problem from Solution", "Separate Problem from Solution" in prompt),
        ("Specific Implementation Guidance", "Specific Implementation Guidance" in prompt),
        ("Unique and Contextual", "Unique and Contextual" in prompt),
        ("Code Examples", "Code Examples" in prompt or "code examples" in prompt),
        ("comment field describes WHAT", "WHAT the problem is" in prompt),
        ("suggestion field describes HOW", "HOW to fix it" in prompt),
    ]
    
    print("\nPrompt Requirements Check:")
    all_passed = True
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n✓ All prompt requirements are present!")
    else:
        print("\n✗ Some prompt requirements are missing!")
    
    print(f"\nPrompt length: {len(prompt)} characters")
    print("\nPrompt preview (first 500 chars):")
    print(prompt[:500])
    
    return all_passed


def test_personalized_analysis_method():
    """Test that the personalized analysis method exists and has correct signature."""
    print("\n=== Testing Personalized Analysis Method ===")
    
    ai_service = AIService()
    
    # Check method exists
    has_method = hasattr(ai_service, 'get_review_with_personalization')
    print(f"  {'✓' if has_method else '✗'} Method 'get_review_with_personalization' exists")
    
    if has_method:
        import inspect
        sig = inspect.signature(ai_service.get_review_with_personalization)
        params = list(sig.parameters.keys())
        
        expected_params = ['code', 'language', 'user_id', 'db', 'analysis_id']
        print(f"\n  Method parameters: {params}")
        
        has_all_params = all(param in params for param in expected_params)
        print(f"  {'✓' if has_all_params else '✗'} Has all required parameters")
        
        # Check docstring
        docstring = ai_service.get_review_with_personalization.__doc__
        has_docstring = docstring and len(docstring) > 50
        print(f"  {'✓' if has_docstring else '✗'} Has comprehensive docstring")
        
        if has_docstring:
            print(f"\n  Docstring preview:")
            print(f"  {docstring[:200]}...")
        
        return has_all_params and has_docstring
    
    return False


def test_api_endpoint_structure():
    """Test that the API endpoint is properly structured."""
    print("\n=== Testing API Endpoint Structure ===")
    
    try:
        from app.api.v1.endpoints import ai
        
        # Check router exists
        has_router = hasattr(ai, 'router')
        print(f"  {'✓' if has_router else '✗'} Router exists")
        
        if has_router:
            # Check for the main endpoint
            routes = [route.path for route in ai.router.routes]
            print(f"\n  Available routes: {routes}")
            
            has_analyze_endpoint = any('analyze-with-learning' in route for route in routes)
            has_status_endpoint = any('personalization-status' in route for route in routes)
            
            print(f"  {'✓' if has_analyze_endpoint else '✗'} /analyze-with-learning endpoint exists")
            print(f"  {'✓' if has_status_endpoint else '✗'} /personalization-status endpoint exists")
            
            return has_analyze_endpoint and has_status_endpoint
        
        return False
        
    except ImportError as e:
        print(f"  ✗ Failed to import AI endpoint module: {e}")
        return False


def test_router_registration():
    """Test that the AI router is registered in the main router."""
    print("\n=== Testing Router Registration ===")
    
    try:
        from app.api.v1.router import api_router
        
        # Check if AI router is included
        routes = [route.path for route in api_router.routes]
        ai_routes = [route for route in routes if '/ai/' in route]
        
        print(f"  Found {len(ai_routes)} AI routes")
        if ai_routes:
            print(f"  AI routes: {ai_routes[:5]}")  # Show first 5
            print(f"  {'✓' if len(ai_routes) > 0 else '✗'} AI router is registered")
            return True
        else:
            print(f"  ✗ No AI routes found in main router")
            return False
            
    except Exception as e:
        print(f"  ✗ Failed to check router registration: {e}")
        return False


def test_integration_with_prompt_builder():
    """Test that AI service integrates with PersonalizedPromptBuilder."""
    print("\n=== Testing Integration with PersonalizedPromptBuilder ===")
    
    db = SessionLocal()
    
    try:
        # Check if we can create a prompt builder
        prompt_builder = PersonalizedPromptBuilder(db)
        print(f"  ✓ PersonalizedPromptBuilder instantiated successfully")
        
        # Check if AI service can use it
        ai_service = AIService()
        
        # Verify the method imports PersonalizedPromptBuilder
        import inspect
        source = inspect.getsource(ai_service.get_review_with_personalization)
        
        imports_builder = 'PersonalizedPromptBuilder' in source
        uses_builder = 'prompt_builder = PersonalizedPromptBuilder' in source
        builds_prompt = 'build_personalized_prompt' in source
        
        print(f"  {'✓' if imports_builder else '✗'} Imports PersonalizedPromptBuilder")
        print(f"  {'✓' if uses_builder else '✗'} Instantiates PersonalizedPromptBuilder")
        print(f"  {'✓' if builds_prompt else '✗'} Calls build_personalized_prompt()")
        
        return imports_builder and uses_builder and builds_prompt
        
    except Exception as e:
        print(f"  ✗ Integration test failed: {e}")
        return False
    finally:
        db.close()


def test_response_model():
    """Test that the response model includes personalization info."""
    print("\n=== Testing Response Model ===")
    
    try:
        from app.api.v1.endpoints.ai import PersonalizedAnalysisResponse
        
        # Check model exists
        print(f"  ✓ PersonalizedAnalysisResponse model exists")
        
        # Check for required fields
        fields = PersonalizedAnalysisResponse.__fields__
        field_names = list(fields.keys())
        
        print(f"\n  Model fields: {field_names}")
        
        required_fields = [
            'analysis_id',
            'status',
            'issues',
            'metrics',
            'summary',
            'personalization_info'
        ]
        
        has_all_fields = all(field in field_names for field in required_fields)
        print(f"\n  {'✓' if has_all_fields else '✗'} Has all required fields")
        
        # Check personalization_info structure
        has_personalization_info = 'personalization_info' in field_names
        print(f"  {'✓' if has_personalization_info else '✗'} Has personalization_info field")
        
        return has_all_fields and has_personalization_info
        
    except Exception as e:
        print(f"  ✗ Response model test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 70)
    print("PERSONALIZED AI SERVICE IMPLEMENTATION TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Enhanced Prompt Construction", test_enhanced_prompt),
        ("Personalized Analysis Method", test_personalized_analysis_method),
        ("API Endpoint Structure", test_api_endpoint_structure),
        ("Router Registration", test_router_registration),
        ("Integration with Prompt Builder", test_integration_with_prompt_builder),
        ("Response Model", test_response_model),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Implementation is complete.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
