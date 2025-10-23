#!/usr/bin/env python3
"""Check if analysis issues are being saved correctly."""

import asyncio
from sqlalchemy import select
from app.core.database import get_db_async
from app.models.github_integration import PRAnalysis

async def check_analyses():
    """Check recent analyses."""
    async for db in get_db_async():
        # Get recent analyses
        query = select(PRAnalysis).order_by(PRAnalysis.created_at.desc()).limit(5)
        result = await db.execute(query)
        analyses = result.scalars().all()
        
        print("=" * 60)
        print("Recent PR Analyses")
        print("=" * 60)
        
        for analysis in analyses:
            print(f"\nAnalysis ID: {analysis.id}")
            print(f"Repository ID: {analysis.repository_id}")
            print(f"PR Number: {analysis.pr_number}")
            print(f"Status: {analysis.status}")
            print(f"Issues Found: {analysis.issues_found}")
            print(f"Errors: {analysis.errors_count}")
            print(f"Warnings: {analysis.warnings_count}")
            print(f"Created: {analysis.created_at}")
            print(f"Completed: {analysis.completed_at}")
            
            if analysis.analysis_results:
                results = analysis.analysis_results
                print(f"Results Status: {results.get('status', 'N/A')}")
                print(f"Total Files: {results.get('total_files', 0)}")
                print(f"Files Analyzed: {results.get('files_analyzed', 0)}")
                
                if 'summary' in results:
                    summary = results['summary']
                    print(f"Summary Total Issues: {summary.get('total_issues', 0)}")
                    print(f"Summary Errors: {summary.get('errors', 0)}")
                    print(f"Summary Warnings: {summary.get('warnings', 0)}")
                
                if 'issues' in results:
                    print(f"Issues in JSON: {len(results['issues'])} issues")
                    if results['issues']:
                        print(f"First issue: {results['issues'][0]}")
            
            print("-" * 60)
        
        break

if __name__ == "__main__":
    asyncio.run(check_analyses())
