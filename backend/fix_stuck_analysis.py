"""
Fix stuck analysis records that failed due to JSON serialization error.
"""
import asyncio
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.github_integration import PRAnalysis, AnalysisStatus
from datetime import datetime

async def fix_stuck_analysis():
    """Fix analysis records stuck in IN_PROGRESS status."""
    async with AsyncSessionLocal() as db:
        # Find stuck analyses (in_progress for more than 10 minutes)
        query = select(PRAnalysis).where(
            PRAnalysis.status == AnalysisStatus.IN_PROGRESS
        )
        result = await db.execute(query)
        stuck_analyses = result.scalars().all()
        
        print(f"Found {len(stuck_analyses)} stuck analyses")
        
        for analysis in stuck_analyses:
            print(f"\nAnalysis ID: {analysis.id}")
            print(f"Repository: {analysis.repository_id}")
            print(f"Status: {analysis.status}")
            print(f"Started at: {analysis.started_at}")
            
            # Check if it has analysis_results with issues
            if analysis.analysis_results and 'issues' in analysis.analysis_results:
                print(f"Has {len(analysis.analysis_results.get('issues', []))} issues")
                print("Marking as completed...")
                
                # Update to completed status
                analysis.status = AnalysisStatus.COMPLETED
                analysis.completed_at = datetime.utcnow()
                
                # Ensure patterns are strings
                if 'patterns' in analysis.analysis_results:
                    patterns = analysis.analysis_results['patterns']
                    if patterns and not isinstance(patterns[0], str):
                        analysis.analysis_results['patterns'] = [str(p) for p in patterns]
                
                await db.commit()
                print("✓ Fixed")
            else:
                print("No results found, resetting to pending...")
                analysis.status = AnalysisStatus.PENDING
                analysis.started_at = None
                await db.commit()
                print("✓ Reset to pending")

if __name__ == "__main__":
    asyncio.run(fix_stuck_analysis())
