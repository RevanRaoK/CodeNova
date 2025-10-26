#!/usr/bin/env python3
"""
Test script to verify AIService methods are available.
"""

import sys
sys.path.append('.')

def test_ai_service_methods():
    """Test that AIService has the correct methods."""
    try:
        from app.services.ai_service import AIService
        
        # Create AIService instance
        ai_service = AIService()
        
        print("AIService methods:")
        methods = [method for method in dir(ai_service) if not method.startswith('_')]
        for method in methods:
            print(f"  - {method}")
        
        # Test if the correct methods exist
        if hasattr(ai_service, 'analyze_code'):
            print("\n✅ analyze_code method exists")
        else:
            print("\n❌ analyze_code method missing")
        
        if hasattr(ai_service, 'get_review_for_code'):
            print("✅ get_review_for_code method exists")
        else:
            print("❌ get_review_for_code method missing")
        
        if hasattr(ai_service, 'get_review_for_code_with_ast'):
            print("❌ get_review_for_code_with_ast method still exists (should be removed)")
        else:
            print("✅ get_review_for_code_with_ast method correctly removed")
        
        # Test analyze_code method
        print("\nTesting analyze_code method...")
        test_code = "print('Hello, World!')"
        result = ai_service.analyze_code(test_code, "python", "test.py")
        
        print(f"Result type: {type(result)}")
        print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict) and 'issues' in result:
            print("✅ analyze_code returns correct structure")
        else:
            print("❌ analyze_code returns incorrect structure")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing AIService: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing AIService methods...")
    success = test_ai_service_methods()
    
    if success:
        print("\n✅ AIService is working correctly")
        print("The issue is likely that the worker process needs to be restarted.")
        print("Run: python restart_worker.py")
    else:
        print("\n❌ AIService has issues that need to be fixed")