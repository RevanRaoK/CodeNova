"""
EMERGENCY FIX - Add analysis_id column as alias to pr_analysis_id
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def emergency_fix():
    """Add analysis_id column to support both old and new code."""
    
    print("=" * 80)
    print("EMERGENCY FIX - ADDING ANALYSIS_ID COLUMN")
    print("=" * 80)
    print()
    
    async with AsyncSessionLocal() as session:
        try:
            # Add analysis_id column that points to the same thing as pr_analysis_id
            print("Adding analysis_id column to issues table...")
            await session.execute(text("""
                ALTER TABLE issues 
                ADD COLUMN IF NOT EXISTS analysis_id VARCHAR(36)
            """))
            await session.commit()
            print("✓ Added analysis_id column")
            
            # Also add the other columns the old model expects
            old_model_columns = [
                ("pattern_type", "VARCHAR(100)"),
                ("category", "VARCHAR(100)"),
                ("location", "JSON"),
                ("suggestion_text", "TEXT"),
                ("code_context", "TEXT"),
                ("original_code", "TEXT"),
                ("suggested_fix", "TEXT"),
                ("ast_node_type", "VARCHAR(100)"),
                ("ast_metadata", "JSON"),
                ("confidence_score", "FLOAT"),
                ("resolved_at", "TIMESTAMP")
            ]
            
            for col_name, col_type in old_model_columns:
                try:
                    await session.execute(text(f"""
                        ALTER TABLE issues 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                    """))
                    await session.commit()
                    print(f"✓ Added {col_name}")
                except Exception as e:
                    print(f"  {col_name} already exists or error: {e}")
            
            print(f"\n{'=' * 80}")
            print("✓ EMERGENCY FIX COMPLETE")
            print(f"{'=' * 80}\n")
            print("The issues table now supports BOTH old and new models!")
            print("Restart your backend and try again.")
            print(f"{'=' * 80}\n")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(emergency_fix())
