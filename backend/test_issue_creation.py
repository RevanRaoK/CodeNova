"""
Test issue creation and retrieval to debug "Issue not found" errors.
"""
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.github_integration import Issue, PRAnalysis
from app.services.issue_id_service import issue_id_service
from sqlalchemy import select

async def test_issue_creation():
    """Test the issue creation and retrieval process."""
    
    print("=" * 80)
    print("TESTING ISSUE CREATION AND RETRIEVAL")
    print("=" * 80)
    print()
    
    async with AsyncSessionLocal() as session:
        # Get a recent pr_analysis
        result = await session.execute(
            select(PRAnalysis).order_by(PRAnalysis.created_at.desc()).limit(1)
        )
        pr_analysis = result.scalar_one_or_none()
        
        if not pr_analysis:
            print("❌ No PR analyses found in database")
            print("Please run a repository analysis first")
            return
        
        print(f"Using PR Analysis: {pr_analysis.id}")
        print(f"  Repository: {pr_analysis.repository_id}")
        print(f"  Status: {pr_analysis.status}")
        print(f"  Issues Found: {pr_analysis.issues_found}")
        print()
        
        # Check if analysis_results has issues
        if not pr_analysis.analysis_results:
            print("❌ No analysis_results in PR analysis")
            return
        
        issues_in_results = pr_analysis.analysis_results.get('issues', [])
        print(f"Issues in analysis_results JSON: {len(issues_in_results)}")
        
        # Check actual issues in database
        result = await session.execute(
            select(Issue).where(Issue.pr_analysis_id == pr_analysis.id)
        )
        issues_in_db = result.scalars().all()
        print(f"Issues in database: {len(issues_in_db)}")
        print()
        
        if len(issues_in_results) != len(issues_in_db):
            print("⚠️  MISMATCH: Issues in JSON != Issues in database")
            print("This means issues are not being created properly!")
            print()
        
        # Test creating an issue
        print("Testing issue creation...")
        test_issue_data = {
            "file_path": "test.py",
            "line_number": 10,
            "severity": "high",
            "message": "Test issue for debugging",
            "rule_id": "test-rule",
            "suggestion": "Fix this test issue"
        }
        
        try:
            issue_id = await issue_id_service.create_or_update_issue(
                session=session,
                pr_analysis_id=str(pr_analysis.id),
                **test_issue_data
            )
            await session.commit()
            
            print(f"✓ Created test issue with ID: {issue_id}")
            print()
            
            # Try to retrieve it
            print("Testing issue retrieval...")
            result = await session.execute(
                select(Issue).where(Issue.id == issue_id)
            )
            retrieved_issue = result.scalar_one_or_none()
            
            if retrieved_issue:
                print(f"✓ Successfully retrieved issue")
                print(f"  ID: {retrieved_issue.id}")
                print(f"  File: {retrieved_issue.file_path}")
                print(f"  Message: {retrieved_issue.message}")
                print(f"  Status: {retrieved_issue.status}")
                print()
                
                # Test updating feedback
                print("Testing feedback update...")
                await issue_id_service.update_issue_feedback(
                    session=session,
                    issue_id=issue_id,
                    feedback="This is test feedback",
                    status="acknowledged"
                )
                await session.commit()
                
                # Retrieve again
                await session.refresh(retrieved_issue)
                print(f"✓ Updated feedback")
                print(f"  Feedback: {retrieved_issue.feedback}")
                print(f"  Status: {retrieved_issue.status}")
                print()
                
                # Clean up test issue
                await session.delete(retrieved_issue)
                await session.commit()
                print("✓ Cleaned up test issue")
                
            else:
                print(f"❌ Could not retrieve issue with ID: {issue_id}")
                print("This is the problem!")
                
        except Exception as e:
            print(f"❌ Error during test: {e}")
            import traceback
            traceback.print_exc()
        
        # Show sample of existing issues
        print(f"\n{'=' * 80}")
        print("SAMPLE OF EXISTING ISSUES")
        print(f"{'=' * 80}\n")
        
        if issues_in_db:
            for issue in issues_in_db[:3]:
                print(f"Issue ID: {issue.id}")
                print(f"  File: {issue.file_path}")
                print(f"  Line: {issue.line_number}")
                print(f"  Severity: {issue.severity}")
                print(f"  Status: {issue.status}")
                print(f"  Feedback: {issue.feedback or '(none)'}")
                print(f"  Hash: {issue.issue_hash or '(none)'}")
                print()
        else:
            print("No existing issues found")
        
        print(f"{'=' * 80}")
        print("TEST COMPLETE")
        print(f"{'=' * 80}\n")


if __name__ == "__main__":
    asyncio.run(test_issue_creation())
