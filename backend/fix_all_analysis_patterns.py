"""
Fix all analysis records to ensure patterns are strings, not Pattern objects.
"""
import asyncio
import json
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.github_integration import PRAnalysis
from datetime import datetime

async def fix_all_patterns():
    """Fix patterns in all analysis records."""
    async with AsyncSessionLocal() as db:
        # Get ALL analyses
        query = select(PRAnalysis)
        result = await db.execute(query)
        all_analyses = result.scalars().all()
        
        print(f"Found {len(all_analyses)} total analyses\n")
        
        fixed_count = 0
        for analysis in all_analyses:
            needs_fix = False
            
            if analysis.analysis_results:
                # Check and fix 'patterns' field
                if "patterns" in analysis.analysis_results:
                    patterns = analysis.analysis_results["patterns"]
                    if patterns and isinstance(patterns, list):
                        # Try to convert - if it fails, they're already strings
                        try:
                            new_patterns = [str(p) for p in patterns]
                            if new_patterns != patterns:
                                analysis.analysis_results["patterns"] = new_patterns
                                needs_fix = True
                        except:
                            pass
                
                # Check and fix 'file_patterns' field
                if "file_patterns" in analysis.analysis_results:
                    patterns = analysis.analysis_results["file_patterns"]
                    if patterns and isinstance(patterns, list):
                        try:
                            new_patterns = [str(p) for p in patterns]
                            if new_patterns != patterns:
                                analysis.analysis_results["file_patterns"] = new_patterns
                                needs_fix = True
                        except:
                            pass
            
            if needs_fix:
                try:
                    await db.commit()
                    fixed_count += 1
                    print(f"✓ Fixed analysis {analysis.id}")
                except Exception as e:
                    print(f"✗ Failed to fix analysis {analysis.id}: {e}")
                    await db.rollback()
        
        print(f"\nFixed {fixed_count} analyses")

if __name__ == "__main__":
    asyncio.run(fix_all_patterns())
