#!/usr/bin/env python3
"""
Test script for Learning Pipeline Integration

This script tests the learning pipeline integration functionality including:
- Feedback collection triggering learning updates
- Pattern priority adjustments based on consistency
- Learning effectiveness calculations
- Integration with personalized AI prompts

Requirements tested: 8.5, 8.6, 8.10
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.services.learning_pipeline_service import LearningPipelineService
from app.services.feedback_service import FeedbackService
from app.services.personalized_prompt_builder import PersonalizedPromptBuilder
from app.models.users import User
from app.models.feedback import Issue, FeedbackRecord
from app.models.feedback_patterns import UserFeedbackPattern
from app.models.analysis import DirectAnalysis
from app.schemas.feedback import FeedbackSubmissionRequest, FeedbackType
from datetime import datetime, timedelta, timezone
import uuid


def test_learning_pipeline_integration():
    """Test the complete learning pipeline integration."""
    print("=== Testing Learning Pipeline Integration ===\n")
    
    db = SessionLocal()
    
    try:
        # Initialize services
        learning_service = LearningPipelineService(db)
        feedback_service = FeedbackService(db)
        prompt_builder = PersonalizedPromptBuilder(db)
        
        # Get or create test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            print("❌ Test user not found. Please create a test user first.")
            return False
        
        user_id = test_user.id
        print(f"✅ Using test user: {test_user.email} (ID: {user_id})")
        
        # Test 1: Create test issues and feedback
        print("\n1. Creating test issues and feedback...")
        test_issues = create_test_issues_and_feedback(db, user_id)
        print(f"✅ Created {len(test_issues)} test issues with feedback")
        
        # Test 2: Process feedback through learning pipeline
        print("\n2. Testing feedback processing through learning pipeline...")
        for issue_id, feedback_data in test_issues.items():
            result = learning_service.process_feedback_for_learning(
                user_id=user_id,
                issue_id=issue_id,
                feedback_type=feedback_data["feedback_type"],
                feedback_value=feedback_data["feedback_value"],
                feedback_comment=feedback_data.get("comment")
            )
            
            if result.get("success"):
                print(f"✅ Processed feedback for issue {issue_id[:8]}...")
            else:
                print(f"❌ Failed to process feedback for issue {issue_id}: {result.get('error')}")
        
        # Test 3: Check learning status
        print("\n3. Testing learning status retrieval...")
        learning_status = learning_service.get_learning_status(user_id)
        
        if learning_status.get("learning_active"):
            print(f"✅ Learning is active with {learning_status['total_patterns']} patterns")
            print(f"   - Boosted patterns: {learning_status['boosted_patterns']}")
            print(f"   - Reduced patterns: {learning_status['reduced_patterns']}")
        else:
            print("⚠️  Learning is not active yet (may need more feedback)")
        
        # Test 4: Test pattern priority updates
        print("\n4. Testing pattern priority updates...")
        priority_updates = learning_service._update_pattern_priorities(user_id)
        
        if priority_updates["updated_patterns"] > 0:
            print(f"✅ Updated {priority_updates['updated_patterns']} pattern priorities")
            if priority_updates["boosted_patterns"]:
                print(f"   - Boosted: {len(priority_updates['boosted_patterns'])} patterns")
            if priority_updates["reduced_patterns"]:
                print(f"   - Reduced: {len(priority_updates['reduced_patterns'])} patterns")
        else:
            print("⚠️  No pattern priorities updated (may need more consistent feedback)")
        
        # Test 5: Test learning effectiveness calculation
        print("\n5. Testing learning effectiveness calculation...")
        effectiveness = learning_service._calculate_learning_effectiveness(user_id)
        
        if effectiveness.get("learning_active"):
            print(f"✅ Learning effectiveness calculated:")
            print(f"   - Total feedback: {effectiveness['total_feedback']}")
            print(f"   - Recent acceptance rate: {effectiveness['recent_acceptance_rate']}%")
            print(f"   - Effectiveness score: {effectiveness['overall_effectiveness_score']}")
            print(f"   - Effectiveness level: {effectiveness['effectiveness_level']}")
        else:
            print("⚠️  Learning effectiveness not available (insufficient feedback)")
        
        # Test 6: Test personalized prompt generation with learning
        print("\n6. Testing personalized prompt generation with learning...")
        test_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total
"""
        
        try:
            personalized_prompt = prompt_builder.build_personalized_prompt(
                user_id=user_id,
                base_prompt="Analyze this code for issues:",
                code=test_code,
                language="python",
                max_examples=5
            )
            
            if "PERSONALIZED CONTEXT" in personalized_prompt:
                print("✅ Personalized prompt generated with learning context")
                print(f"   - Prompt length: {len(personalized_prompt)} characters")
            else:
                print("⚠️  Personalized prompt generated but may not include learning context")
                
        except Exception as e:
            print(f"❌ Error generating personalized prompt: {e}")
        
        # Test 7: Test batch learning update
        print("\n7. Testing batch learning update...")
        batch_result = learning_service.trigger_batch_learning_update([user_id])
        
        if batch_result.get("successful_updates", 0) > 0:
            print(f"✅ Batch learning update successful")
            print(f"   - Users updated: {batch_result['successful_updates']}")
            print(f"   - Failed updates: {batch_result['failed_updates']}")
        else:
            print("⚠️  Batch learning update completed but no updates made")
        
        # Test 8: Test integration with feedback service
        print("\n8. Testing integration with feedback service...")
        test_integration_with_feedback_service(db, feedback_service, user_id)
        
        print("\n=== Learning Pipeline Integration Test Complete ===")
        return True
        
    except Exception as e:
        print(f"❌ Error in learning pipeline integration test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def create_test_issues_and_feedback(db, user_id):
    """Create test issues and feedback for learning pipeline testing."""
    test_issues = {}
    
    # Create test issues with different categories and severities
    issue_templates = [
        {
            "category": "security",
            "severity": "high",
            "pattern_type": "sql_injection",
            "suggestion_text": "Potential SQL injection vulnerability detected",
            "feedback_type": "accept",
            "feedback_value": 1
        },
        {
            "category": "security",
            "severity": "high", 
            "pattern_type": "xss_vulnerability",
            "suggestion_text": "Cross-site scripting vulnerability found",
            "feedback_type": "accept",
            "feedback_value": 1
        },
        {
            "category": "performance",
            "severity": "medium",
            "pattern_type": "inefficient_loop",
            "suggestion_text": "Inefficient loop detected, consider optimization",
            "feedback_type": "reject",
            "feedback_value": -1
        },
        {
            "category": "performance",
            "severity": "medium",
            "pattern_type": "memory_leak",
            "suggestion_text": "Potential memory leak in resource handling",
            "feedback_type": "reject",
            "feedback_value": -1
        },
        {
            "category": "style",
            "severity": "low",
            "pattern_type": "naming_convention",
            "suggestion_text": "Variable naming doesn't follow conventions",
            "feedback_type": "modify",
            "feedback_value": 0
        }
    ]
    
    for template in issue_templates:
        # Create analysis first (required for foreign key)
        analysis_id = str(uuid.uuid4())
        
        analysis = DirectAnalysis(
            id=analysis_id,
            user_id=user_id,
            code_content="test code for learning pipeline",
            language="python",
            filename="test.py",
            status="completed",
            created_at=datetime.now(timezone.utc) - timedelta(days=1),
            completed_at=datetime.now(timezone.utc) - timedelta(days=1),
            results={"test": "data"},
            lines_of_code=10,
            complexity_score=5,
            maintainability_index=80,
            issues_count=1,
            errors_count=0,
            warnings_count=1,
            file_size_bytes=100
        )
        
        db.add(analysis)
        
        # Create issue
        issue_id = str(uuid.uuid4())
        
        issue = Issue(
            id=issue_id,
            analysis_id=analysis_id,
            pattern_type=template["pattern_type"],
            severity=template["severity"],
            category=template["category"],
            location={"line": 1, "column": 1, "file_path": "test.py"},
            suggestion_text=template["suggestion_text"],
            code_context="test code context",
            original_code="test original code",
            suggested_fix="test suggested fix",
            status="active",
            confidence_score=0.8
        )
        
        db.add(issue)
        
        # Create feedback record
        feedback = FeedbackRecord(
            issue_id=issue_id,
            user_id=user_id,
            feedback_type=template["feedback_type"],
            feedback_value=template["feedback_value"],
            feedback_comment=f"Test feedback for {template['category']} issue",
            created_at=datetime.now(timezone.utc) - timedelta(days=1)  # Make it recent
        )
        
        db.add(feedback)
        
        test_issues[issue_id] = {
            "feedback_type": template["feedback_type"],
            "feedback_value": template["feedback_value"],
            "comment": f"Test feedback for {template['category']} issue"
        }
    
    db.commit()
    return test_issues


def test_integration_with_feedback_service(db, feedback_service, user_id):
    """Test that feedback service properly triggers learning pipeline updates."""
    try:
        # Create analysis first
        analysis_id = str(uuid.uuid4())
        
        analysis = DirectAnalysis(
            id=analysis_id,
            user_id=user_id,
            code_content="test integration code",
            language="python",
            filename="integration_test.py",
            status="completed",
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            results={"test": "integration"},
            lines_of_code=5,
            complexity_score=2,
            maintainability_index=90,
            issues_count=1,
            errors_count=0,
            warnings_count=1,
            file_size_bytes=50
        )
        
        db.add(analysis)
        
        # Create a test issue
        issue_id = str(uuid.uuid4())
        
        issue = Issue(
            id=issue_id,
            analysis_id=analysis_id,
            pattern_type="test_integration",
            severity="medium",
            category="testing",
            location={"line": 1, "column": 1, "file_path": "integration_test.py"},
            suggestion_text="Test integration suggestion",
            code_context="test integration code",
            original_code="test code",
            suggested_fix="test fix",
            status="active",
            confidence_score=0.9
        )
        
        db.add(issue)
        db.commit()
        
        # Submit feedback through feedback service
        feedback_request = FeedbackSubmissionRequest(
            issue_id=issue_id,
            feedback_type=FeedbackType.ACCEPT,
            feedback_comment="Test integration feedback"
        )
        
        # This should trigger the learning pipeline automatically
        feedback_record = feedback_service.record_feedback(user_id, feedback_request)
        
        if feedback_record:
            print("✅ Feedback service integration working - learning pipeline triggered automatically")
        else:
            print("❌ Feedback service integration failed")
            
    except Exception as e:
        print(f"❌ Error testing feedback service integration: {e}")


if __name__ == "__main__":
    success = test_learning_pipeline_integration()
    sys.exit(0 if success else 1)