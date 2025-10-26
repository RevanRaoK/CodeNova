#!/usr/bin/env python3
"""
Simple test script to isolate the feedback submission issue.
"""

import sys
import os
sys.path.append('.')

def test_feedback_service():
    """Test the feedback service in isolation."""
    try:
        print("=== Testing Feedback Service ===")
        
        # Test imports
        print("1. Testing imports...")
        from app.services.feedback_service import FeedbackService
        from app.schemas.feedback import FeedbackSubmissionRequest, FeedbackType
        from app.core.database import SessionLocal
        print("   ✓ Imports successful")
        
        # Test schema creation
        print("2. Testing schema creation...")
        feedback_request = FeedbackSubmissionRequest(
            issue_id='test-issue-123',
            feedback_type=FeedbackType.ACCEPT,
            feedback_comment='Test feedback'
        )
        print(f"   ✓ Schema created: {feedback_request.issue_id}")
        
        # Test database connection
        print("3. Testing database connection...")
        db = SessionLocal()
        feedback_service = FeedbackService(db)
        print("   ✓ Database connection successful")
        
        # Test the problematic method
        print("4. Testing record_feedback method...")
        try:
            result = feedback_service.record_feedback(
                user_id=1,  # Assuming user ID 1 exists
                feedback_request=feedback_request
            )
            print(f"   ✓ Feedback recorded: {result.id}")
        except Exception as e:
            print(f"   ✗ Error in record_feedback: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        db.close()
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_feedback_service()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)