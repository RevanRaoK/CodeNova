"""
Unit tests for feedback statistics service methods.

This script tests the service layer methods for feedback statistics.
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.feedback_service import FeedbackService
from app.models.feedback import FeedbackRecord, Issue
from app.models.users import User
from app.models.analysis import DirectAnalysis
from app.core.database import Base


def test_empty_statistics():
    """Test that empty statistics are returned when no data exists."""
    print("\n" + "="*60)
    print("Test: Empty Statistics Response")
    print("="*60)
    
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Create a test user
        user = User(
            email="test@example.com",
            hashed_password="dummy",
            first_name="Test",
            last_name="User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Test with no feedback data
        service = FeedbackService(db)
        result = service.get_feedback_statistics_with_timeframe(
            user_id=user.id,
            timeframe="week"
        )
        
        print("\nResult:")
        print(f"  Total Feedback: {result['totalFeedback']}")
        print(f"  Acceptance Rate: {result['acceptanceRate']}")
        print(f"  Feedback By Type: {result['feedbackByType']}")
        print(f"  Feedback Trends: {result['feedbackTrends']}")
        print(f"  Model Performance: {result['modelPerformance']}")
        print(f"  Timeframe: {result['timeframe']}")
        
        # Assertions
        assert result['totalFeedback'] == 0, "Expected 0 total feedback"
        assert result['acceptanceRate'] == 0.0, "Expected 0.0 acceptance rate"
        assert len(result['feedbackByType']) == 3, "Expected 3 feedback types"
        assert result['timeframe'] == "week", "Expected timeframe to be 'week'"
        
        print("\n✅ Test passed: Empty statistics returned correctly")
        
    finally:
        db.close()


def test_statistics_with_data():
    """Test statistics calculation with sample data."""
    print("\n" + "="*60)
    print("Test: Statistics with Sample Data")
    print("="*60)
    
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Create a test user
        user = User(
            email="test@example.com",
            hashed_password="dummy",
            first_name="Test",
            last_name="User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create a test analysis
        analysis = DirectAnalysis(
            id="test-analysis-123",
            user_id=user.id,
            code_content="print('hello')",
            language="python",
            status="completed"
        )
        db.add(analysis)
        db.commit()
        
        # Create test issues and feedback
        now = datetime.utcnow()
        
        for i in range(10):
            # Create issue
            issue = Issue(
                id=f"issue-{i:03d}" + "0" * 57,  # 64 char hash
                analysis_id=analysis.id,
                pattern_type="code_quality",
                severity="medium",
                location={"line": i + 1},
                suggestion_text=f"Suggestion {i}",
                code_context=f"Code context {i}",
                confidence_score=0.85
            )
            db.add(issue)
            db.commit()
            db.refresh(issue)
            
            # Create feedback (70% accept, 20% reject, 10% modify)
            if i < 7:
                feedback_type = "accept"
                feedback_value = 1
            elif i < 9:
                feedback_type = "reject"
                feedback_value = -1
            else:
                feedback_type = "modify"
                feedback_value = 0
            
            feedback = FeedbackRecord(
                issue_id=issue.id,
                user_id=user.id,
                feedback_type=feedback_type,
                feedback_value=feedback_value,
                created_at=now - timedelta(days=i)
            )
            db.add(feedback)
        
        db.commit()
        
        # Test statistics
        service = FeedbackService(db)
        result = service.get_feedback_statistics_with_timeframe(
            user_id=user.id,
            timeframe="month"
        )
        
        print("\nResult:")
        print(f"  Total Feedback: {result['totalFeedback']}")
        print(f"  Acceptance Rate: {result['acceptanceRate']}%")
        print(f"  Feedback By Type:")
        for item in result['feedbackByType']:
            print(f"    - {item['type']}: {item['count']}")
        print(f"  Feedback Trends: {len(result['feedbackTrends'])} data points")
        print(f"  Model Performance: {len(result['modelPerformance'])} metrics")
        
        # Assertions
        assert result['totalFeedback'] == 10, f"Expected 10 total feedback, got {result['totalFeedback']}"
        assert result['acceptanceRate'] == 70.0, f"Expected 70.0% acceptance rate, got {result['acceptanceRate']}"
        
        # Check feedback by type
        feedback_dict = {item['type']: item['count'] for item in result['feedbackByType']}
        assert feedback_dict['accept'] == 7, f"Expected 7 accepts, got {feedback_dict['accept']}"
        assert feedback_dict['reject'] == 2, f"Expected 2 rejects, got {feedback_dict['reject']}"
        assert feedback_dict['modify'] == 1, f"Expected 1 modify, got {feedback_dict['modify']}"
        
        # Check model performance metrics
        assert len(result['modelPerformance']) > 0, "Expected model performance metrics"
        metric_names = {m['metric'] for m in result['modelPerformance']}
        assert 'Acceptance Rate' in metric_names, "Expected 'Acceptance Rate' metric"
        assert 'Rejection Rate' in metric_names, "Expected 'Rejection Rate' metric"
        
        print("\n✅ Test passed: Statistics calculated correctly")
        
    finally:
        db.close()


def test_different_timeframes():
    """Test statistics with different timeframe parameters."""
    print("\n" + "="*60)
    print("Test: Different Timeframes")
    print("="*60)
    
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Create a test user
        user = User(
            email="test@example.com",
            hashed_password="dummy",
            first_name="Test",
            last_name="User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        service = FeedbackService(db)
        
        # Test each timeframe
        timeframes = ["week", "month", "quarter", "year"]
        
        for timeframe in timeframes:
            result = service.get_feedback_statistics_with_timeframe(
                user_id=user.id,
                timeframe=timeframe
            )
            
            print(f"\n  Timeframe: {timeframe}")
            print(f"    - Returned timeframe: {result['timeframe']}")
            
            assert result['timeframe'] == timeframe, f"Expected timeframe '{timeframe}', got '{result['timeframe']}'"
            assert 'totalFeedback' in result, "Missing totalFeedback"
            assert 'acceptanceRate' in result, "Missing acceptanceRate"
            assert 'feedbackByType' in result, "Missing feedbackByType"
            assert 'feedbackTrends' in result, "Missing feedbackTrends"
            assert 'modelPerformance' in result, "Missing modelPerformance"
        
        print("\n✅ Test passed: All timeframes work correctly")
        
    finally:
        db.close()


def main():
    """Run all unit tests."""
    print("="*60)
    print("Feedback Statistics Service Unit Tests")
    print("="*60)
    
    try:
        test_empty_statistics()
        test_statistics_with_data()
        test_different_timeframes()
        
        print("\n" + "="*60)
        print("✅ All unit tests passed!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
