#!/usr/bin/env python3
"""
Script to create test feedback data for development and testing.
Run this to populate the database with sample feedback records.
"""

import sys
import os
import hashlib
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from app.models.users import User
from app.models.analysis import DirectAnalysis
from app.models.feedback import Issue, FeedbackRecord
from app.services.feedback_service import FeedbackService
from app.schemas.feedback import FeedbackSubmissionRequest, FeedbackType, ExperienceLevel, ReviewContext


def create_test_user(db: Session) -> User:
    """Create or get a test user for feedback."""
    # Try to find existing test user
    test_user = db.query(User).filter(User.email == "test@example.com").first()
    
    if not test_user:
        print("Creating test user...")
        test_user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password="$2b$12$test_hashed_password",  # This is just for testing
            role="user",
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"Created test user with ID: {test_user.id}")
    else:
        print(f"Using existing test user with ID: {test_user.id}")
    
    return test_user


def create_test_analysis(db: Session, user: User) -> DirectAnalysis:
    """Create a test analysis record."""
    analysis = DirectAnalysis(
        user_id=user.id,
        code_content="""
def process_data(data):
    temp = []  # Unused variable
    result = []
    for item in data:
        if item is not None:
            result.append(item.upper())
    return result
        """,
        language="python",
        filename="test_code.py",
        status="completed",
        lines_of_code=8,
        complexity_score=3,
        maintainability_index=75,
        issues_count=3,
        errors_count=0,
        warnings_count=2,
        file_size_bytes=256
    )
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    print(f"✓ Created test analysis with ID: {analysis.id}")
    return analysis


def generate_issue_id(content: str) -> str:
    """Generate a deterministic issue ID based on content."""
    return hashlib.sha256(content.encode()).hexdigest()


def create_test_issues(db: Session, analysis: DirectAnalysis):
    """Create test issues for the analysis."""
    
    test_issues = [
        {
            "pattern_type": "unused_variable",
            "severity": "low",
            "suggestion_text": "Remove unused variable 'temp' on line 2",
            "code_context": "temp = []  # Unused variable",
            "location": {"line": 2, "column": 5, "start_line": 2, "end_line": 2},
            "original_code": "temp = []",
            "suggested_fix": "# Remove this line"
        },
        {
            "pattern_type": "null_check",
            "severity": "medium", 
            "suggestion_text": "Add null check before accessing item properties",
            "code_context": "if item is not None:",
            "location": {"line": 5, "column": 12, "start_line": 5, "end_line": 5},
            "original_code": "if item is not None:",
            "suggested_fix": "if item is not None and hasattr(item, 'upper'):"
        },
        {
            "pattern_type": "performance",
            "severity": "medium",
            "suggestion_text": "Use list comprehension for better performance",
            "code_context": "for item in data:\n    if item is not None:\n        result.append(item.upper())",
            "location": {"line": 4, "column": 5, "start_line": 4, "end_line": 6},
            "original_code": "for item in data:\n    if item is not None:\n        result.append(item.upper())",
            "suggested_fix": "result = [item.upper() for item in data if item is not None]"
        },
        {
            "pattern_type": "naming_convention",
            "severity": "low",
            "suggestion_text": "Consider more descriptive variable names",
            "code_context": "def process_data(data):",
            "location": {"line": 1, "column": 17, "start_line": 1, "end_line": 1},
            "original_code": "def process_data(data):",
            "suggested_fix": "def process_data(input_data):"
        },
        {
            "pattern_type": "error_handling",
            "severity": "high",
            "suggestion_text": "Add error handling for potential AttributeError",
            "code_context": "result.append(item.upper())",
            "location": {"line": 6, "column": 13, "start_line": 6, "end_line": 6},
            "original_code": "result.append(item.upper())",
            "suggested_fix": "try:\n    result.append(item.upper())\nexcept AttributeError:\n    result.append(str(item).upper())"
        },
        {
            "pattern_type": "code_style",
            "severity": "low",
            "suggestion_text": "Add docstring to function",
            "code_context": "def process_data(data):",
            "location": {"line": 1, "column": 1, "start_line": 1, "end_line": 1},
            "original_code": "def process_data(data):",
            "suggested_fix": "def process_data(data):\n    \"\"\"Process data by converting to uppercase.\"\"\""
        },
        {
            "pattern_type": "type_hints",
            "severity": "medium",
            "suggestion_text": "Add type hints for better code documentation",
            "code_context": "def process_data(data):",
            "location": {"line": 1, "column": 1, "start_line": 1, "end_line": 1},
            "original_code": "def process_data(data):",
            "suggested_fix": "def process_data(data: List[Any]) -> List[str]:"
        },
        {
            "pattern_type": "optimization",
            "severity": "medium",
            "suggestion_text": "Consider using filter() for better readability",
            "code_context": "for item in data:\n    if item is not None:",
            "location": {"line": 4, "column": 5, "start_line": 4, "end_line": 5},
            "original_code": "for item in data:\n    if item is not None:",
            "suggested_fix": "for item in filter(None, data):"
        },
        {
            "pattern_type": "best_practices",
            "severity": "low",
            "suggestion_text": "Initialize result list with expected capacity if known",
            "code_context": "result = []",
            "location": {"line": 3, "column": 5, "start_line": 3, "end_line": 3},
            "original_code": "result = []",
            "suggested_fix": "result = [] if not data else [None] * len(data)"
        }
    ]
    
    created_issues = []
    print(f"Creating {len(test_issues)} test issues...")
    
    for i, issue_data in enumerate(test_issues):
        # Generate deterministic issue ID
        content_for_id = f"{analysis.id}_{issue_data['pattern_type']}_{issue_data['location']['line']}"
        issue_id = generate_issue_id(content_for_id)
        
        issue = Issue(
            id=issue_id,
            analysis_id=analysis.id,
            pattern_type=issue_data["pattern_type"],
            severity=issue_data["severity"],
            location=issue_data["location"],
            suggestion_text=issue_data["suggestion_text"],
            code_context=issue_data["code_context"],
            original_code=issue_data["original_code"],
            suggested_fix=issue_data["suggested_fix"],
            confidence_score=0.8 + (i % 3) * 0.1  # Vary confidence scores
        )
        
        db.add(issue)
        created_issues.append(issue)
        print(f"✓ Created issue {i+1}: {issue_data['pattern_type']} (ID: {issue_id[:8]}...)")
    
    db.commit()
    print(f"Successfully created {len(created_issues)} issues!")
    return created_issues


def create_test_feedback_data(db: Session, user: User, issues: list):
    """Create sample feedback data for the issues."""
    
    # Sample feedback data with different types and contexts
    feedback_templates = [
        {
            "feedback_type": "accept",
            "feedback_comment": "Great suggestion! This helped improve code readability.",
            "user_experience_level": "intermediate",
            "code_review_context": "team"
        },
        {
            "feedback_type": "reject", 
            "feedback_comment": "This suggestion doesn't apply to our use case.",
            "user_experience_level": "expert",
            "code_review_context": "production"
        },
        {
            "feedback_type": "modify",
            "feedback_comment": "Good idea, but I have a better implementation.",
            "modified_suggestion": "Use a more specific approach for this context",
            "user_experience_level": "expert",
            "code_review_context": "personal"
        },
        {
            "feedback_type": "accept",
            "feedback_comment": "Excellent catch! This fixed a potential bug.",
            "user_experience_level": "intermediate", 
            "code_review_context": "team"
        },
        {
            "feedback_type": "reject",
            "feedback_comment": "Already implemented this differently in our codebase.",
            "user_experience_level": "beginner",
            "code_review_context": "personal"
        },
        {
            "feedback_type": "accept",
            "feedback_comment": "Perfect! This improves performance significantly.",
            "user_experience_level": "expert",
            "code_review_context": "production"
        },
        {
            "feedback_type": "modify",
            "feedback_comment": "Good suggestion, but needs adjustment for our architecture.",
            "modified_suggestion": "Use a different approach that fits our existing patterns",
            "user_experience_level": "expert",
            "code_review_context": "team"
        },
        {
            "feedback_type": "accept",
            "feedback_comment": "Simple but effective improvement.",
            "user_experience_level": "intermediate",
            "code_review_context": "personal"
        },
        {
            "feedback_type": "reject",
            "feedback_comment": "This conflicts with our existing error handling strategy.",
            "user_experience_level": "expert",
            "code_review_context": "production"
        }
    ]
    
    print(f"Creating feedback for {len(issues)} issues...")
    
    created_count = 0
    for i, issue in enumerate(issues):
        if i >= len(feedback_templates):
            break
            
        template = feedback_templates[i]
        
        try:
            # Map feedback type to value
            feedback_value_map = {
                "accept": 1,
                "reject": -1, 
                "modify": 0,
                "ignore": 0
            }
            
            feedback_record = FeedbackRecord(
                issue_id=issue.id,
                user_id=user.id,
                feedback_type=template["feedback_type"],
                feedback_value=feedback_value_map[template["feedback_type"]],
                feedback_comment=template["feedback_comment"],
                modified_suggestion=template.get("modified_suggestion"),
                user_experience_level=template["user_experience_level"],
                code_review_context=template["code_review_context"],
                context_data={
                    "file_path": "test_code.py",
                    "line_number": issue.location.get("line", 1),
                    "suggestion_text": issue.suggestion_text
                },
                is_validated=i % 3 == 0  # Validate every 3rd feedback
            )
            
            # Adjust the created_at timestamp to spread them over time
            days_ago = len(issues) - i
            feedback_record.created_at = datetime.utcnow() - timedelta(days=days_ago)
            
            db.add(feedback_record)
            created_count += 1
            print(f"✓ Created feedback {i+1}: {template['feedback_type']} for issue {issue.id[:8]}...")
            
        except Exception as e:
            print(f"✗ Failed to create feedback {i+1}: {e}")
            continue
    
    db.commit()
    print(f"\nSuccessfully created {created_count} feedback records!")
    return created_count


def main():
    """Main function to create test data."""
    print("Creating test feedback data...")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Create or get test user
        test_user = create_test_user(db)
        
        # Create test analysis
        analysis = create_test_analysis(db, test_user)
        
        # Create test issues
        issues = create_test_issues(db, analysis)
        
        # Create test feedback data
        created_count = create_test_feedback_data(db, test_user, issues)
        
        print(f"\n🎉 Test data creation complete!")
        print(f"Created:")
        print(f"  - 1 analysis record")
        print(f"  - {len(issues)} issue records")
        print(f"  - {created_count} feedback records")
        print(f"For user: {test_user.email}")
        print(f"\nYou can now log in as '{test_user.email}' to see the feedback history.")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())