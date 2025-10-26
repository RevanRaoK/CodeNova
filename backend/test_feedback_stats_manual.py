#!/usr/bin/env python3
"""
Manual test script for feedback statistics functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.admin_service import AdminService
from app.core.database import SessionLocal
from app.models.users import User, UserRole
from app.models.team import Team
from app.models.feedback import FeedbackRecord, Issue
from app.models.analysis import DirectAnalysis
import uuid
from datetime import datetime


def test_feedback_statistics():
    """Test the feedback statistics functionality manually."""
    
    db = SessionLocal()
    
    try:
        # Create admin service
        admin_service = AdminService(db)
        
        # Test with empty database
        print("Testing with empty database...")
        stats = admin_service.get_feedback_statistics()
        print(f"Empty stats: {stats}")
        
        # Create test data
        print("\nCreating test data...")
        
        # Create admin user
        admin_user = User(
            email="admin@test.com",
            hashed_password="hashed_password",
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"Created admin user: {admin_user.id}")
        
        # Create team
        team = Team(
            id=str(uuid.uuid4()),
            name="Test Team",
            admin_id=admin_user.id
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        print(f"Created team: {team.id}")
        
        # Create regular user
        user = User(
            email="user@test.com",
            hashed_password="hashed_password",
            full_name="Test User",
            role=UserRole.USER,
            team_id=team.id,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created user: {user.id}")
        
        # Create analysis
        analysis = DirectAnalysis(
            id=str(uuid.uuid4()),
            user_id=user.id,
            code_content="def test(): pass",
            language="python",
            status="completed",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        print(f"Created analysis: {analysis.id}")
        
        # Create issue
        issue = Issue(
            id="a" * 64,  # 64-character hash
            analysis_id=analysis.id,
            pattern_type="unused_variable",
            severity="medium",
            location={"line": 10, "column": 5},
            suggestion_text="Remove unused variable",
            code_context="def test(): unused_var = 1",
            status="active"
        )
        db.add(issue)
        db.commit()
        db.refresh(issue)
        print(f"Created issue: {issue.id}")
        
        # Create feedback records
        feedback_types = ["accept", "reject", "modify", "accept", "accept"]
        for i, feedback_type in enumerate(feedback_types):
            feedback_value = 1 if feedback_type == "accept" else (-1 if feedback_type == "reject" else 0)
            
            feedback = FeedbackRecord(
                issue_id=issue.id,
                user_id=user.id,
                feedback_type=feedback_type,
                feedback_value=feedback_value,
                feedback_comment=f"Test feedback {i}",
                created_at=datetime.utcnow()
            )
            db.add(feedback)
        
        db.commit()
        print(f"Created {len(feedback_types)} feedback records")
        
        # Test statistics calculation
        print("\nTesting statistics calculation...")
        stats = admin_service.get_feedback_statistics()
        print(f"All users stats: {stats}")
        
        # Test with team filtering
        print(f"\nTesting with team filtering (team_id: {team.id})...")
        team_stats = admin_service.get_feedback_statistics(team_id=team.id)
        print(f"Team stats: {team_stats}")
        
        # Test with nonexistent team
        print("\nTesting with nonexistent team...")
        empty_stats = admin_service.get_feedback_statistics(team_id="nonexistent-team")
        print(f"Nonexistent team stats: {empty_stats}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    test_feedback_statistics()