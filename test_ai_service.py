#!/usr/bin/env python3
"""
Test script to debug the AI service issue
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_ai_service():
    """Test the AI service directly"""
    try:
        from app.services.ai_service import aiservice
        
        print("Testing AI Service...")
        print(f"AI Service initialized: {aiservice}")
        
        test_code = """
function add(a, b) {
    return a + b;
}

function divide(a, b) {
    return a / b;  // No check for division by zero
}
"""
        
        print("Calling get_review_for_code...")
        suggestions = aiservice.get_review_for_code(test_code)
        
        print(f"✅ AI Service returned {len(suggestions)} suggestions:")
        for i, suggestion in enumerate(suggestions):
            print(f"  {i+1}. Line {suggestion.get('line_number', 'N/A')}: {suggestion.get('comment', 'No comment')}")
            if 'severity' in suggestion:
                print(f"     Severity: {suggestion['severity']}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connection"""
    try:
        from app.core.database import SessionLocal
        from app.models.analysis import DirectAnalysis
        
        print("\nTesting Database Connection...")
        
        db = SessionLocal()
        try:
            # Try to query the DirectAnalysis table
            count = db.query(DirectAnalysis).count()
            print(f"✅ Database connection successful. DirectAnalysis table has {count} records.")
            return True
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test configuration"""
    try:
        from app.core.config import settings
        
        print("\nTesting Configuration...")
        print(f"Database URL: {settings.DATABASE_URL}")
        
        # Check if GEMINI_API_KEY is set (don't print the actual key)
        if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
            print("✅ GEMINI_API_KEY is configured")
        else:
            print("⚠️  GEMINI_API_KEY is not configured - will use mock responses")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Debugging Enhanced API Issues ===\n")
    
    config_ok = test_config()
    db_ok = test_database_connection()
    ai_ok = test_ai_service()
    
    print(f"\n=== Test Results ===")
    print(f"Configuration: {'✅' if config_ok else '❌'}")
    print(f"Database: {'✅' if db_ok else '❌'}")
    print(f"AI Service: {'✅' if ai_ok else '❌'}")
    
    if all([config_ok, db_ok, ai_ok]):
        print("\n🎉 All tests passed! The API should work now.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")