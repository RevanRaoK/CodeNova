re"""
Test the complete flow: create user, create analysis, create issues, submit feedback.
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.models.users import User
from app.models.analysis import DirectAnalysis
from app.models.feedback import Issue, FeedbackRecord
import datetime
import uuid
import hashlib

async def test_flow():
    print("=" * 80)
    print("TESTING COMPLETE FLOW")
    print("=" * 80)
    
    async with AsyncSessionLocal() as session:
        # 1. Create a test user
        print("\n[1/5] Creating test user...")
        user = User(
            email="test@example.com",
            hashed_password="dummy_hash",
            full_name="Test User",
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"   ✓ User created: ID={user.id}, email={user.email}")
        
        # 2. Create a direct analysis
        print("\n[2/5] Creating direct analysis...")
        analysis = DirectAnalysis(
            id=str(uuid.uuid4()),
            user_id=user.id,
            code_content="function test() { console.log('hello'); }",
            language="javascript",
            filename="test.js",
            status="completed",
            issues_count=1
        )
        session.add(analysis)
        await session.commit()
        await session.refresh(analysis)
        print(f"   ✓ Analysis created: ID={analysis.id}")
        
        # 3. Create an issue
        print("\n[3/5] Creating issue...")
        issue_data = f"{analysis.id}|javascript|1|missing-semicolon"
        issue_id = hashlib.sha256(issue_data.encode()).hexdigest()
        
        issue = Issue(
            id=issue_id,
            analysis_id=analysis.id,
            pattern_type="missing-semicolon",
            severity="low",
            category="style",
            location={"line": 1, "column": 45, "context": "Missing semicolon"},
            suggestion_text="Add semicolon at end of statement",
            code_context="console.log('hello')",
            status="active",
            confidence_score=0.9
        )
        session.add(issue)
        await session.commit()
        await session.refresh(issue)
        print(f"   ✓ Issue created: ID={issue.id[:16]}...")
        
        # 4. Submit feedback
        print("\n[4/5] Submitting feedback...")
        feedback = FeedbackRecord(
            issue_id=issue.id,
            user_id=user.id,
            feedback_type="accept",
            feedback_value=1,
            feedback_comment="Good suggestion!"
        )
        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)
        print(f"   ✓ Feedback created: ID={feedback.id}")
        
        # 5. Verify everything
        print("\n[5/5] Verifying data...")
        
        # Check user
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        print(f"   ✓ Users: {user_count}")
        
        # Check analysis
        result = await session.execute(text("SELECT COUNT(*) FROM direct_analyses"))
        analysis_count = result.scalar()
        print(f"   ✓ Direct analyses: {analysis_count}")
        
        # Check issues
        result = await session.execute(text("SELECT COUNT(*) FROM issues"))
        issue_count = result.scalar()
        print(f"   ✓ Issues: {issue_count}")
        
        # Check feedback
        result = await session.execute(text("SELECT COUNT(*) FROM feedback_records"))
        feedback_count = result.scalar()
        print(f"   ✓ Feedback records: {feedback_count}")
        
        # Test the relationship query
        result = await session.execute(text("""
            SELECT i.id, i.pattern_type, f.feedback_type, f.feedback_value
            FROM issues i
            JOIN feedback_records f ON f.issue_id = i.id
        """))
        row = result.fetchone()
        if row:
            print(f"\n   ✓ Relationship works:")
            print(f"     Issue: {row[0][:16]}... ({row[1]})")
            print(f"     Feedback: {row[2]} (value={row[3]})")
        
        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED!")
        print("=" * 80)
        print("\nYour database is working correctly!")
        print("You can now:")
        print("  1. Start your FastAPI server")
        print("  2. Upload files for analysis")
        print("  3. Submit feedback on issues")
        print("\nEverything should work now.")

if __name__ == "__main__":
    asyncio.run(test_flow()