"""
Quick script to check repository analysis status
"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.github_integration import PRAnalysis

async def check_status():
    async with AsyncSessionLocal() as db:
        # Get most recent repository analysis
        query = select(PRAnalysis).where(
            PRAnalysis.pr_number == 0
        ).order_by(PRAnalysis.created_at.desc()).limit(5)
        
        result = await db.execute(query)
        analyses = result.scalars().all()
        
        print("\n=== Recent Repository Analyses ===\n")
        if not analyses:
            print("No repository analyses found.")
        else:
            for analysis in analyses:
                print(f"ID: {analysis.id}")
                print(f"Repository ID: {analysis.repository_id}")
                print(f"Status: {analysis.status}")
                print(f"Title: {analysis.pr_title}")
                print(f"Author: {analysis.pr_author}")
                print(f"Created: {analysis.created_at}")
                print(f"Started: {analysis.started_at}")
                print(f"Completed: {analysis.completed_at}")
                print(f"Issues Found: {analysis.issues_found}")
                print(f"Analysis Results: {analysis.analysis_results}")
                print(f"Error: {analysis.error_message}")
                print("-" * 80)

if __name__ == "__main__":
    asyncio.run(check_status())
