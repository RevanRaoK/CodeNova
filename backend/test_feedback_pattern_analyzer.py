"""
Test script for FeedbackPatternAnalyzer service.

This script tests the feedback pattern analysis functionality including:
- Analyzing user feedback patterns
- Calculating acceptance rates
- Identifying top accepted/rejected categories
- Caching patterns in the database
"""

import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.feedback_pattern_analyzer import FeedbackPatternAnalyzer
from app.models.feedback import Issue, FeedbackRecord
from app.models.feedback_patterns import UserFeedbackPattern
from app.models.users import User
from app.models.analysis import DirectAnalysis
import uuid


def create_test_data(db: Session):
    """Create test data for pattern analysis."""
    print("\n=== Creating Test Data ===")
    
    # Check if test user exists
    test_user = db.query(User).filter(User.email == "pattern_test@example.com").first()
    
    if not test_user:
        print("Creating test user...")
        test_user = User(
            email="pattern_test@example.com",
            full_name="Pattern Test User",
            hashed_password="test_hash",
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✓ Created test user with ID: {test_user.id}")
    else:
        print(f"✓ Using existing test user with ID: {test_user.id}")
    
    # Create a test analysis
    analysis_id = str(uuid.uuid4())
    analysis = DirectAnalysis(
        id=analysis_id,
        user_id=test_user.id,
        code_content="def test(): pass",
        language="python",
        status="completed"
    )
    db.add(analysis)
    db.commit()
    print(f"✓ Created test analysis: {analysis_id}")
    
    # Create test issues with different categories and severities
    test_issues = [
        # Security issues (mostly accepted)
        {"category": "security", "severity": "critical", "pattern": "sql_injection", "feedback": "accept"},
        {"category": "security", "severity": "high", "pattern": "xss_vulnerability", "feedback": "accept"},
        {"category": "security", "severity": "critical", "pattern": "hardcoded_secret", "feedback": "accept"},
        {"category": "security", "severity": "high", "pattern": "insecure_random", "feedback": "accept"},
        
        # Performance issues (mixed)
        {"category": "performance", "severity": "warning", "pattern": "inefficient_loop", "feedback": "accept"},
        {"category": "performance", "severity": "low", "pattern": "unnecessary_copy", "feedback": "reject"},
        {"category": "performance", "severity": "warning", "pattern": "n_plus_one_query", "feedback": "accept"},
        
        # Style issues (mostly rejected)
        {"category": "style", "severity": "info", "pattern": "line_too_long", "feedback": "reject"},
        {"category": "style", "severity": "info", "pattern": "missing_docstring", "feedback": "reject"},
        {"category": "style", "severity": "low", "pattern": "naming_convention", "feedback": "reject"},
        {"category": "style", "severity": "info", "pattern": "whitespace", "feedback": "reject"},
        
        # Bug issues (accepted)
        {"category": "bug", "severity": "high", "pattern": "null_pointer", "feedback": "accept"},
        {"category": "bug", "severity": "warning", "pattern": "type_mismatch", "feedback": "accept"},
        {"category": "bug", "severity": "high", "pattern": "logic_error", "feedback": "accept"},
    ]
    
    created_issues = []
    for i, issue_data in enumerate(test_issues):
        # Create issue
        issue_id = f"test_issue_{i}_{uuid.uuid4().hex[:8]}"
        issue = Issue(
            id=issue_id,
            analysis_id=analysis_id,
            pattern_type=issue_data["pattern"],
            severity=issue_data["severity"],
            category=issue_data["category"],
            location={"line": i + 1, "column": 0},
            suggestion_text=f"Fix {issue_data['pattern']}",
            code_context="test code",
            status="active"
        )
        db.add(issue)
        created_issues.append(issue)
        
        # Create feedback
        feedback = FeedbackRecord(
            issue_id=issue_id,
            user_id=test_user.id,
            feedback_type=issue_data["feedback"],
            feedback_value=1 if issue_data["feedback"] == "accept" else -1,
            created_at=datetime.utcnow() - timedelta(days=i)  # Spread over time
        )
        db.add(feedback)
    
    db.commit()
    print(f"✓ Created {len(test_issues)} test issues with feedback")
    
    return test_user.id


def test_analyze_user_patterns(db: Session, user_id: int):
    """Test the analyze_user_patterns method."""
    print("\n=== Testing analyze_user_patterns ===")
    
    analyzer = FeedbackPatternAnalyzer(db)
    result = analyzer.analyze_user_patterns(user_id)
    
    print(f"\n📊 Analysis Results:")
    print(f"  Total feedback: {result['statistics']['total_feedback']}")
    print(f"  Overall acceptance rate: {result['statistics']['overall_acceptance_rate']}")
    print(f"  Unique patterns: {result['statistics']['unique_patterns']}")
    
    print(f"\n✅ Accepted Patterns ({len(result['accepted_patterns'])}):")
    for pattern in result['accepted_patterns']:
        print(f"  - {pattern['category']} ({pattern['severity']}): "
              f"{pattern['acceptance_rate']*100:.0f}% acceptance, "
              f"{pattern['count']} feedback items")
    
    print(f"\n❌ Rejected Patterns ({len(result['rejected_patterns'])}):")
    for pattern in result['rejected_patterns']:
        print(f"  - {pattern['category']} ({pattern['severity']}): "
              f"{pattern['acceptance_rate']*100:.0f}% acceptance, "
              f"{pattern['count']} feedback items")
    
    print(f"\n🎯 User Preferences:")
    prefs = result['preferences']
    print(f"  Prefers categories: {', '.join(prefs['prefers_categories']) or 'None'}")
    print(f"  Dislikes categories: {', '.join(prefs['dislikes_categories']) or 'None'}")
    print(f"  Severity preferences:")
    for severity, data in prefs['severity_preferences'].items():
        print(f"    - {severity}: {data['acceptance_rate']*100:.0f}% acceptance ({data['total']} items)")
    
    return result


def test_update_cached_patterns(db: Session, user_id: int):
    """Test the update_cached_patterns method."""
    print("\n=== Testing update_cached_patterns ===")
    
    analyzer = FeedbackPatternAnalyzer(db)
    updated_count = analyzer.update_cached_patterns(user_id)
    
    print(f"✓ Updated {updated_count} cached pattern records")
    
    # Verify cached patterns
    cached_patterns = db.query(UserFeedbackPattern).filter(
        UserFeedbackPattern.user_id == user_id
    ).all()
    
    print(f"\n📦 Cached Patterns in Database ({len(cached_patterns)}):")
    for pattern in cached_patterns:
        print(f"  - {pattern.category} ({pattern.severity}): "
              f"{pattern.acceptance_rate*100:.0f}% acceptance, "
              f"{pattern.total_feedback_count} feedback items")
    
    return cached_patterns


def test_get_cached_patterns(db: Session, user_id: int):
    """Test the get_cached_patterns method."""
    print("\n=== Testing get_cached_patterns ===")
    
    analyzer = FeedbackPatternAnalyzer(db)
    result = analyzer.get_cached_patterns(user_id)
    
    print(f"\n📦 Retrieved Cached Patterns:")
    print(f"  Total patterns: {result['statistics']['total_patterns']}")
    print(f"  Last updated: {result['statistics']['last_updated']}")
    
    print(f"\n✅ Accepted Patterns ({len(result['accepted_patterns'])}):")
    for pattern in result['accepted_patterns']:
        print(f"  - {pattern['category']} ({pattern['severity']}): "
              f"{pattern['acceptance_rate']*100:.0f}% acceptance")
    
    print(f"\n❌ Rejected Patterns ({len(result['rejected_patterns'])}):")
    for pattern in result['rejected_patterns']:
        print(f"  - {pattern['category']} ({pattern['severity']}): "
              f"{pattern['acceptance_rate']*100:.0f}% acceptance")


def test_top_categories(db: Session, user_id: int):
    """Test the get_top_accepted_categories and get_top_rejected_categories methods."""
    print("\n=== Testing Top Categories ===")
    
    analyzer = FeedbackPatternAnalyzer(db)
    
    accepted = analyzer.get_top_accepted_categories(user_id, limit=5)
    print(f"\n✅ Top Accepted Categories: {', '.join(accepted) or 'None'}")
    
    rejected = analyzer.get_top_rejected_categories(user_id, limit=5)
    print(f"❌ Top Rejected Categories: {', '.join(rejected) or 'None'}")


def cleanup_test_data(db: Session):
    """Clean up test data."""
    print("\n=== Cleaning Up Test Data ===")
    
    test_user = db.query(User).filter(User.email == "pattern_test@example.com").first()
    
    if test_user:
        # Delete cached patterns
        db.query(UserFeedbackPattern).filter(
            UserFeedbackPattern.user_id == test_user.id
        ).delete()
        
        # Delete feedback records
        db.query(FeedbackRecord).filter(
            FeedbackRecord.user_id == test_user.id
        ).delete()
        
        # Delete issues and analyses
        analyses = db.query(DirectAnalysis).filter(
            DirectAnalysis.user_id == test_user.id
        ).all()
        
        for analysis in analyses:
            db.query(Issue).filter(Issue.analysis_id == analysis.id).delete()
            db.delete(analysis)
        
        # Delete user
        db.delete(test_user)
        db.commit()
        
        print("✓ Test data cleaned up successfully")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing FeedbackPatternAnalyzer Service")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Create test data
        user_id = create_test_data(db)
        
        # Run tests
        test_analyze_user_patterns(db, user_id)
        test_update_cached_patterns(db, user_id)
        test_get_cached_patterns(db, user_id)
        test_top_categories(db, user_id)
        
        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        
        # Ask if user wants to clean up
        response = input("\nClean up test data? (y/n): ")
        if response.lower() == 'y':
            cleanup_test_data(db)
        else:
            print("Test data preserved for inspection")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
