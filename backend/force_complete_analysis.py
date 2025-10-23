"""
Force complete the stuck analysis by manually fixing the database record.
"""
import asyncio
import json
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.github_integration import PRAnalysis, AnalysisStatus
from datetime import datetime

async def force_complete_analysis():
    """Force complete stuck analyses."""
    async with AsyncSessionLocal() as db:
        # Find the most recent stuck analysis
        query = select(PRAnalysis).where(
            PRAnalysis.status == AnalysisStatus.IN_PROGRESS
        ).order_by(PRAnalysis.created_at.desc())
        
        result = await db.execute(query)
        stuck_analyses = result.scalars().all()
        
        print(f"Found {len(stuck_analyses)} stuck analyses\n")
        
        for analysis in stuck_analyses:
            print(f"Analysis ID: {analysis.id}")
            print(f"Repository: {analysis.repository_id}")
            print(f"Status: {analysis.status}")
            
            # Mark as completed
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.utcnow()
            
            # Create minimal results if none exist
            if not analysis.analysis_results:
                analysis.analysis_results = {
                    "status": "completed",
                    "message": "Analysis completed with errors, manually fixed",
                    "total_files": 0,
                    "files_analyzed": 0,
                    "files_failed": 0
                }
            else:
                # Update status in existing results
                analysis.analysis_results["status"] = "completed"
                analysis.analysis_results["completed_at"] = datetime.utcnow().isoformat()
                
                # Ensure patterns are strings
                if "patterns" in analysis.analysis_results:
                    patterns = analysis.analysis_results["patterns"]
                    if patterns and isinstance(patterns, list):
                        analysis.analysis_results["patterns"] = [str(p) for p in patterns]
                
                # Ensure file_patterns are strings
                if "file_patterns" in analysis.analysis_results:
                    patterns = analysis.analysis_results["file_patterns"]
                    if patterns and isinstance(patterns, list):
                        analysis.analysis_results["file_patterns"] = [str(p) for p in patterns]
            
            await db.commit()
            print("✓ Marked as completed\n")

if __name__ == "__main__":
    asyncio.run(force_complete_analysis())
