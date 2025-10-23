"""
Check the issues table specifically for feedback functionality.
"""
import asyncio
from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal
from app.models.github_integration import Issue, PRAnalysis

async def check_issues_table():
    """Check issues table and feedback functionality."""
    
    print("=" * 80)
    print("ISSUES TABLE VERIFICATION")
    print("=" * 80)
    print()
    
    async with AsyncSessionLocal() as session:
        # Get total count
        result = await session.execute(select(Issue))
        all_issues = result.scalars().all()
        
        print(f"Total issues in database: {len(all_issues)}")
        print()
        
        if not all_issues:
            print("⚠️  No issues found in database!")
            print("This might be why feedback is failing.")
            return
        
        # Check recent issues
        print("Recent issues (last 10):")
        print("-" * 80)
        
        for issue in all_issues[-10:]:
            print(f"\nIssue ID: {issue.id}")
            print(f"  PR Analysis ID: {issue.pr_analysis_id}")
            print(f"  File: {issue.file_path}")
            print(f"  Line: {issue.line_number}")
            print(f"  Severity: {issue.severity}")
            print(f"  Status: {issue.status}")
            print(f"  Feedback: {issue.feedback or '(none)'}")
            print(f"  Issue Hash: {issue.issue_hash or '(none)'}")
            print(f"  Message: {issue.message[:100]}...")
        
        # Check for issues with feedback
        result = await session.execute(
            select(Issue).where(Issue.feedback.isnot(None))
        )
        issues_with_feedback = result.scalars().all()
        
        print(f"\n\nIssues with feedback: {len(issues_with_feedback)}")
        
        # Check for issues without pr_analysis
        result = await session.execute(text("""
            SELECT i.id, i.pr_analysis_id, i.file_path
            FROM issues i
            LEFT JOIN pr_analyses pa ON i.pr_analysis_id = pa.id
            WHERE pa.id IS NULL
        """))
        orphaned = result.fetchall()
        
        if orphaned:
            print(f"\n⚠️  Found {len(orphaned)} orphaned issues (pr_analysis doesn't exist):")
            for issue_id, pr_id, file_path in orphaned[:5]:
                print(f"  - Issue {issue_id}: pr_analysis_id={pr_id}, file={file_path}")
        else:
            print("\n✓ All issues have valid pr_analysis_id")
        
        # Check for issues without issue_hash
        result = await session.execute(
            select(Issue).where(Issue.issue_hash.is_(None))
        )
        no_hash = result.scalars().all()
        
        if no_hash:
            print(f"\n⚠️  Found {len(no_hash)} issues without issue_hash")
            print("  This might cause problems with issue tracking")
        else:
            print("\n✓ All issues have issue_hash")
        
        # Check pr_analyses with issues
        print(f"\n\n{'=' * 80}")
        print("PR ANALYSES WITH ISSUES")
        print(f"{'=' * 80}\n")
        
        result = await session.execute(
            select(PRAnalysis).where(PRAnalysis.issues_found > 0)
        )
        analyses_with_issues = result.scalars().all()
        
        print(f"PR Analyses with issues: {len(analyses_with_issues)}")
        
        for analysis in analyses_with_issues[-5:]:
            print(f"\nAnalysis ID: {analysis.id}")
            print(f"  Repository: {analysis.repository_id}")
            print(f"  PR Number: {analysis.pr_number}")
            print(f"  Status: {analysis.status}")
            print(f"  Issues Found: {analysis.issues_found}")
            
            # Count actual issues
            result = await session.execute(
                select(Issue).where(Issue.pr_analysis_id == analysis.id)
            )
            actual_issues = result.scalars().all()
            print(f"  Actual Issues in DB: {len(actual_issues)}")
            
            if analysis.issues_found != len(actual_issues):
                print(f"  ⚠️  MISMATCH: issues_found={analysis.issues_found} but actual={len(actual_issues)}")
        
        # Test issue lookup by ID
        print(f"\n\n{'=' * 80}")
        print("TESTING ISSUE LOOKUP")
        print(f"{'=' * 80}\n")
        
        if all_issues:
            test_issue = all_issues[0]
            print(f"Testing lookup for issue ID: {test_issue.id}")
            
            # Try to fetch it
            result = await session.execute(
                select(Issue).where(Issue.id == test_issue.id)
            )
            found = result.scalar_one_or_none()
            
            if found:
                print(f"✓ Successfully found issue by ID")
                print(f"  File: {found.file_path}")
                print(f"  Message: {found.message[:100]}...")
            else:
                print(f"❌ Could not find issue by ID!")
        
        print(f"\n{'=' * 80}")
        print("VERIFICATION COMPLETE")
        print(f"{'=' * 80}\n")


if __name__ == "__main__":
    asyncio.run(check_issues_table())
