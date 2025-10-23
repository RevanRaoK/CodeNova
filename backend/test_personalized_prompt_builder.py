"""
Test script for PersonalizedPromptBuilder service.

This script tests the personalized prompt builder functionality including:
- Fetching feedback history with recency weighting
- Building personalized context
- Generating personalized prompts
"""

import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.users import User
from app.models.feedback import FeedbackRecord, Issue
from app.models.analysis import DirectAnalysis
from app.services.personalized_prompt_builder import PersonalizedPromptBuilder
import uuid


def create_test_data(db: Session):
    """Create test data for personalized prompt builder testing."""
    print("Creating test data...")
    
    # Create or get test user
    test_user = db.query(User).filter(User.email == "test_personalization@example.com").first()
    if not test_user:
        test_user = User(
            email="test_personalization@example.com",
            full_name="Test Personalization User",
            first_name="Test",
            last_name="User",
            hashed_password="test_hash",
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
    
    print(f"Test user ID: {test_user.id}")
    
    # Create test analysis
    test_analysis = DirectAnalysis(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        code_content="def test(): pass",
        language="python",
        status="completed"
    )
    db.add(test_analysis)
    db.commit()
    
    # Create test issues with feedback
    test_issues = [
        {
            'pattern_type': 'security_vulnerability',
            'category': 'security',
            'severity': 'critical',
            'suggestion_text': 'Use parameterized queries to prevent SQL injection',
            'feedback_type': 'accept',
            'feedback_value': 1,
            'is_recent': True
        },
        {
            'pattern_type': 'performance_issue',
            'category': 'performance',
            'severity': 'high',
            'suggestion_text': 'Use list comprehension instead of loop for better performance',
            'feedback_type': 'accept',
            'feedback_value': 1,
            'is_recent': True
        },
        {
            'pattern_type': 'style_issue',
            'category': 'style',
            'severity': 'low',
            'suggestion_text': 'Add whitespace around operators',
            'feedback_type': 'reject',
            'feedback_value': -1,
            'is_recent': False
        },
        {
            'pattern_type': 'naming_convention',
            'category': 'naming',
            'severity': 'warning',
            'suggestion_text': 'Use snake_case for variable names',
            'feedback_type': 'reject',
            'feedback_value': -1,
            'is_recent': False
        },
        {
            'pattern_type': 'error_handling',
            'category': 'error_handling',
            'severity': 'high',
            'suggestion_text': 'Add try-except block to handle potential exceptions',
            'feedback_type': 'accept',
            'feedback_value': 1,
            'is_recent': True
        },
    ]
    
    created_issues = []
    for issue_data in test_issues:
        # Create issue
        issue_id = str(uuid.uuid4())[:64]  # Simulate hash
        issue = Issue(
            id=issue_id,
            analysis_id=test_analysis.id,
            pattern_type=issue_data['pattern_type'],
            category=issue_data['category'],
            severity=issue_data['severity'],
            suggestion_text=issue_data['suggestion_text'],
            code_context="test code context",
            location={'line': 1, 'column': 1}
        )
        db.add(issue)
        db.commit()
        
        # Create feedback
        created_at = datetime.utcnow() if issue_data['is_recent'] else datetime.utcnow() - timedelta(days=60)
        feedback = FeedbackRecord(
            issue_id=issue.id,
            user_id=test_user.id,
            feedback_type=issue_data['feedback_type'],
            feedback_value=issue_data['feedback_value'],
            feedback_comment=f"Test feedback for {issue_data['category']}",
            created_at=created_at
        )
        db.add(feedback)
        db.commit()
        
        created_issues.append(issue)
    
    print(f"Created {len(created_issues)} test issues with feedback")
    return test_user, created_issues


def test_fetch_feedback_history(db: Session, user_id: int):
    """Test fetching feedback history."""
    print("\n=== Testing fetch_feedback_history ===")
    
    builder = PersonalizedPromptBuilder(db)
    history = builder.fetch_feedback_history(user_id)
    
    print(f"Has feedback: {history['has_feedback']}")
    print(f"Total feedback count: {history['total_feedback_count']}")
    print(f"Recent feedback count: {history['recent_feedback_count']}")
    print(f"Accepted examples: {len(history['accepted_examples'])}")
    print(f"Rejected examples: {len(history['rejected_examples'])}")
    
    print("\nAccepted examples:")
    for ex in history['accepted_examples']:
        recent = "[RECENT]" if ex['is_recent'] else ""
        print(f"  - {ex['category']} ({ex['severity']}) {recent}")
    
    print("\nRejected examples:")
    for ex in history['rejected_examples']:
        recent = "[RECENT]" if ex['is_recent'] else ""
        print(f"  - {ex['category']} ({ex['severity']}) {recent}")
    
    return history


def test_build_personalized_context(db: Session, feedback_history: dict):
    """Test building personalized context."""
    print("\n=== Testing build_personalized_context ===")
    
    builder = PersonalizedPromptBuilder(db)
    context = builder.build_personalized_context(feedback_history)
    
    print(f"Accepted categories: {context['accepted_categories']}")
    print(f"Rejected categories: {context['rejected_categories']}")
    print(f"Has recent feedback: {context['has_recent_feedback']}")
    print(f"\nPreference summary:\n{context['preference_summary']}")
    
    return context


def test_build_personalized_prompt(db: Session, user_id: int):
    """Test building complete personalized prompt."""
    print("\n=== Testing build_personalized_prompt ===")
    
    builder = PersonalizedPromptBuilder(db)
    
    base_prompt = """You are a code review assistant. When analyzing code, provide:
1. Issue Description: Clearly describe WHAT the problem is
2. Suggestion: Provide specific, actionable steps on HOW to fix it
3. Code Example: Include concrete code showing the fix"""
    
    test_code = """
def process_user_data(user_input):
    query = "SELECT * FROM users WHERE id = " + user_input
    result = db.execute(query)
    return result
"""
    
    personalized_prompt = builder.build_personalized_prompt(
        user_id=user_id,
        base_prompt=base_prompt,
        code=test_code,
        language="python"
    )
    
    print("Generated personalized prompt:")
    print("=" * 80)
    print(personalized_prompt)
    print("=" * 80)
    
    return personalized_prompt


def test_get_personalization_summary(db: Session, user_id: int):
    """Test getting personalization summary."""
    print("\n=== Testing get_personalization_summary ===")
    
    builder = PersonalizedPromptBuilder(db)
    summary = builder.get_personalization_summary(user_id)
    
    print(f"Has personalization: {summary['has_personalization']}")
    print(f"Total feedback: {summary.get('total_feedback', 0)}")
    print(f"Recent feedback: {summary.get('recent_feedback', 0)}")
    print(f"Accepted count: {summary.get('accepted_count', 0)}")
    print(f"Rejected count: {summary.get('rejected_count', 0)}")
    print(f"Top accepted categories: {summary.get('top_accepted_categories', [])}")
    print(f"Top rejected categories: {summary.get('top_rejected_categories', [])}")
    print(f"Message: {summary['message']}")
    
    return summary


def test_user_without_feedback(db: Session):
    """Test behavior with user who has no feedback."""
    print("\n=== Testing user without feedback ===")
    
    # Create user without feedback
    new_user = db.query(User).filter(User.email == "no_feedback@example.com").first()
    if not new_user:
        new_user = User(
            email="no_feedback@example.com",
            full_name="No Feedback User",
            hashed_password="test_hash",
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    
    builder = PersonalizedPromptBuilder(db)
    
    # Test fetch_feedback_history
    history = builder.fetch_feedback_history(new_user.id)
    print(f"Has feedback: {history['has_feedback']}")
    assert not history['has_feedback'], "Should have no feedback"
    
    # Test get_personalization_summary
    summary = builder.get_personalization_summary(new_user.id)
    print(f"Has personalization: {summary['has_personalization']}")
    assert not summary['has_personalization'], "Should have no personalization"
    
    # Test build_personalized_prompt (should return base prompt)
    base_prompt = "You are a code review assistant."
    prompt = builder.build_personalized_prompt(
        user_id=new_user.id,
        base_prompt=base_prompt,
        code="def test(): pass",
        language="python"
    )
    print(f"Prompt length: {len(prompt)}")
    assert "PERSONALIZED CONTEXT" not in prompt, "Should not have personalized context"
    
    print("✓ User without feedback handled correctly")


def main():
    """Run all tests."""
    print("Starting PersonalizedPromptBuilder tests...\n")
    
    db = SessionLocal()
    
    try:
        # Create test data
        test_user, test_issues = create_test_data(db)
        
        # Test 1: Fetch feedback history
        feedback_history = test_fetch_feedback_history(db, test_user.id)
        
        # Test 2: Build personalized context
        personalized_context = test_build_personalized_context(db, feedback_history)
        
        # Test 3: Build personalized prompt
        personalized_prompt = test_build_personalized_prompt(db, test_user.id)
        
        # Test 4: Get personalization summary
        summary = test_get_personalization_summary(db, test_user.id)
        
        # Test 5: User without feedback
        test_user_without_feedback(db)
        
        print("\n" + "=" * 80)
        print("✓ All tests passed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
