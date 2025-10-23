"""
Simple test script for FeedbackPatternAnalyzer service.

This script tests the feedback pattern analysis functionality with minimal dependencies.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Set minimal environment to avoid complex imports
os.environ.setdefault('DATABASE_URL', os.getenv('DATABASE_URL', ''))
os.environ.setdefault('SECRET_KEY', 'test_secret_key_for_testing_only')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Create engine and session
engine = create_engine(os.getenv('DATABASE_URL'))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def test_table_exists():
    """Test that the user_feedback_patterns table exists."""
    print("\n=== Testing Table Existence ===")
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'user_feedback_patterns'
            );
        """))
        exists = result.scalar()
        
        if exists:
            print("✓ user_feedback_patterns table exists")
            
            # Get column info
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'user_feedback_patterns'
                ORDER BY ordinal_position;
            """))
            
            print("\n📋 Table Columns:")
            for row in result:
                print(f"  - {row[0]}: {row[1]}")
            
            return True
        else:
            print("✗ user_feedback_patterns table does not exist")
            return False


def test_analyzer_import():
    """Test that the FeedbackPatternAnalyzer can be imported."""
    print("\n=== Testing Analyzer Import ===")
    
    try:
        from app.services.feedback_pattern_analyzer import FeedbackPatternAnalyzer
        print("✓ FeedbackPatternAnalyzer imported successfully")
        
        # Check methods exist
        methods = ['analyze_user_patterns', 'update_cached_patterns', 
                   'get_cached_patterns', 'get_top_accepted_categories',
                   'get_top_rejected_categories']
        
        print("\n📦 Available Methods:")
        for method in methods:
            if hasattr(FeedbackPatternAnalyzer, method):
                print(f"  ✓ {method}")
            else:
                print(f"  ✗ {method} (missing)")
        
        return True
    except Exception as e:
        print(f"✗ Failed to import FeedbackPatternAnalyzer: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_import():
    """Test that the UserFeedbackPattern model can be imported."""
    print("\n=== Testing Model Import ===")
    
    try:
        from app.models.feedback_patterns import UserFeedbackPattern
        print("✓ UserFeedbackPattern model imported successfully")
        
        # Check attributes
        attributes = ['id', 'user_id', 'category', 'severity', 
                     'acceptance_rate', 'total_feedback_count',
                     'accepted_count', 'rejected_count', 'last_updated']
        
        print("\n📦 Model Attributes:")
        for attr in attributes:
            if hasattr(UserFeedbackPattern, attr):
                print(f"  ✓ {attr}")
            else:
                print(f"  ✗ {attr} (missing)")
        
        return True
    except Exception as e:
        print(f"✗ Failed to import UserFeedbackPattern: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_basic_query():
    """Test basic database query on the patterns table."""
    print("\n=== Testing Basic Query ===")
    
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT COUNT(*) FROM user_feedback_patterns"))
        count = result.scalar()
        print(f"✓ Query successful: {count} patterns in database")
        return True
    except Exception as e:
        print(f"✗ Query failed: {e}")
        return False
    finally:
        db.close()


def test_analyzer_instantiation():
    """Test that the analyzer can be instantiated."""
    print("\n=== Testing Analyzer Instantiation ===")
    
    db = SessionLocal()
    try:
        from app.services.feedback_pattern_analyzer import FeedbackPatternAnalyzer
        
        analyzer = FeedbackPatternAnalyzer(db)
        print("✓ FeedbackPatternAnalyzer instantiated successfully")
        
        # Test empty pattern result
        result = analyzer._empty_pattern_result()
        print(f"✓ Empty pattern result generated: {len(result)} keys")
        
        return True
    except Exception as e:
        print(f"✗ Failed to instantiate analyzer: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Run all simple tests."""
    print("=" * 60)
    print("Testing FeedbackPatternAnalyzer Service (Simple)")
    print("=" * 60)
    
    tests = [
        ("Table Exists", test_table_exists),
        ("Model Import", test_model_import),
        ("Analyzer Import", test_analyzer_import),
        ("Basic Query", test_basic_query),
        ("Analyzer Instantiation", test_analyzer_instantiation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
