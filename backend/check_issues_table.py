"""
Check the issues table specifically for feedback functionality.
"""
import asyncio
from sqlalchemy import select, text
"""Detailed checks for the issues table and related feedback records."""

import asyncio
from typing import Dict

from sqlalchemy import func, select, text

from app.core.database import AsyncSessionLocal
from app.models.analysis import DirectAnalysis
from app.models.feedback import FeedbackRecord, Issue


async def check_issues_table() -> None:
    """Inspect stored issues to ensure feedback and relationships look healthy."""

    print("=" * 80)
    print("ISSUES TABLE VERIFICATION")
    print("=" * 80)
    print()

    async with AsyncSessionLocal() as session:
        # Fetch all issues (most recent first for easier reading)
        result = await session.execute(select(Issue).order_by(Issue.created_at.desc()))
        all_issues = result.scalars().all()

        print(f"Total issues in database: {len(all_issues)}")
        print()

        if not all_issues:
            print("⚠️  No issues found in database!")
            print("This might be why feedback is failing.")
            return

        # Pre-compute feedback counts per issue for quick lookups
        feedback_counts: Dict[str, int] = {}
        feedback_result = await session.execute(
            select(FeedbackRecord.issue_id, func.count())
            .group_by(FeedbackRecord.issue_id)
        )
        feedback_counts = dict(feedback_result.all())

        # Show a sample of the newest issues
        print("Recent issues (newest 10):")
        print("-" * 80)

        for issue in all_issues[:10]:
            location = issue.location or {}
            line_info = location.get("line") or location.get("start_line")
            context_preview_lines = (issue.code_context or "").splitlines()
            context_preview = context_preview_lines[0] if context_preview_lines else "(no context)"

            print(f"\nIssue ID: {issue.id}")
            print(f"  Analysis ID: {issue.analysis_id}")
            print(f"  Pattern: {issue.pattern_type}")
            print(f"  Severity: {issue.severity}")
            print(f"  Status: {issue.status or 'unknown'}")
            print(f"  Confidence: {issue.confidence_score if issue.confidence_score is not None else 'n/a'}")
            print(f"  Line/Range: {line_info or '(unspecified)'}")
            print(f"  Feedback records: {feedback_counts.get(issue.id, 0)}")
            print(f"  Suggestion preview: {issue.suggestion_text[:80]}...")
            print(f"  Context preview: {context_preview[:80]}...")

        # Count issues that already have feedback records
        result = await session.execute(
            select(Issue.id)
            .join(FeedbackRecord, FeedbackRecord.issue_id == Issue.id)
            .group_by(Issue.id)
        )
        issues_with_feedback = [row[0] for row in result.all()]

        print(f"\n\nIssues with feedback: {len(issues_with_feedback)}")
        if issues_with_feedback:
            sample_ids = ", ".join(issues_with_feedback[:10])
            print(f"  Sample IDs: {sample_ids}")

        # Ensure each issue still has its originating direct analysis
        result = await session.execute(text(
            """
            SELECT i.id, i.analysis_id
            FROM issues i
            LEFT JOIN direct_analyses da ON i.analysis_id = da.id
            WHERE da.id IS NULL
            """
        ))
        orphaned = result.fetchall()

        if orphaned:
            print(f"\n⚠️  Found {len(orphaned)} orphaned issues (analysis_id missing in direct_analyses):")
            for issue_id, analysis_id in orphaned[:5]:
                print(f"  - Issue {issue_id}: analysis_id={analysis_id}")
        else:
            print("\n✓ All issues reference valid direct analyses")

        # Aggregate direct analyses that currently have issues stored
        print(f"\n\n{'=' * 80}")
        print("DIRECT ANALYSES WITH ISSUES")
        print(f"{'=' * 80}\n")

        result = await session.execute(
            select(
                DirectAnalysis.id,
                DirectAnalysis.user_id,
                DirectAnalysis.language,
                DirectAnalysis.status,
                func.count(Issue.id).label("issue_count"),
            )
            .join(Issue, Issue.analysis_id == DirectAnalysis.id)
            .group_by(DirectAnalysis.id)
            .order_by(func.count(Issue.id).desc())
        )
        analysis_rows = result.all()

        print(f"Direct analyses that generated issues: {len(analysis_rows)}")

        for row in analysis_rows[:5]:
            da_id, user_id, language, status, issue_count = row
            print(f"\nDirectAnalysis ID: {da_id}")
            print(f"  User ID: {user_id}")
            print(f"  Language: {language}")
            print(f"  Status: {status}")
            print(f"  Issues Stored: {issue_count}")

        # Spot-check issue lookup by ID to verify query paths still work
        print(f"\n\n{'=' * 80}")
        print("TESTING ISSUE LOOKUP")
        print(f"{'=' * 80}\n")

        test_issue = all_issues[0]
        print(f"Testing lookup for issue ID: {test_issue.id}")

        lookup = await session.execute(select(Issue).where(Issue.id == test_issue.id))
        found = lookup.scalar_one_or_none()

        if found:
            print("✓ Successfully found issue by ID")
            print(f"  Pattern: {found.pattern_type}")
            print(f"  Suggestion preview: {found.suggestion_text[:100]}...")
        else:
            print("❌ Could not find issue by ID!")

        print(f"\n{'=' * 80}")
        print("VERIFICATION COMPLETE")
        print(f"{'=' * 80}\n")


if __name__ == "__main__":
    asyncio.run(check_issues_table())
