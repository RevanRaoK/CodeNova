# Issues Table Fix - Summary

## The Problem
Your `issues` table has **BOTH old and new schemas merged together**:

```
OLD SCHEMA (from Windows/PR analysis):
- pr_analysis_id (NOT NULL) → pr_analyses table
- file_path, line_number, message, rule_id, suggestion

NEW SCHEMA (from current models):  
- analysis_id (nullable) → direct_analyses table
- pattern_type, category, location, suggestion_text, code_context
```

**Why it's broken:**
- Your code tries to insert with `analysis_id` 
- But database requires `pr_analysis_id` (NOT NULL)
- Result: IntegrityError when creating issues

## The Root Cause
When you moved from Windows to Linux, the database migration added new columns but didn't remove old ones. SQLAlchemy doesn't automatically drop columns - it only adds missing ones.

## The Solution

### Step 1: Check What Data Exists
```bash
python check_existing_data.py
```

This shows you:
- How many issues exist
- Which schema they use (old vs new)
- Whether it's safe to delete

### Step 2: Run the Fix
```bash
python fix_issues_table_clean.py
```

This will:
1. ✓ Drop old columns (pr_analysis_id, file_path, etc.)
2. ✓ Keep new columns (analysis_id, pattern_type, etc.)
3. ✓ Make analysis_id NOT NULL
4. ✓ Add proper foreign key to direct_analyses
5. ✓ Clear existing data (since schema is incompatible)

**WARNING:** This deletes all existing issues! But based on your error, they weren't being saved anyway.

### Step 3: Verify
```bash
python verify_database_schema.py
```

Should show clean schema with no errors.

### Step 4: Test
1. Upload a file for analysis
2. Issues should be created successfully
3. Feedback submission should work

## Quick Start (If You Just Want It Fixed)

```bash
# Check what exists (optional)
python check_existing_data.py

# Fix it
python fix_issues_table_clean.py

# Verify
python verify_database_schema.py

# Test your API
# Upload a file and check if issues are created
```

## Why This Happened

On Windows, you probably:
1. Created the database fresh with the old schema
2. Everything worked

On Linux, you:
1. Had an existing database with old schema
2. Updated the models to new schema
3. SQLAlchemy added new columns but kept old ones
4. Now you have both, causing conflicts

## Alternative: Start Fresh

If you don't care about any data:

```bash
# Drop and recreate database
python -c "
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def reset():
    async with AsyncSessionLocal() as session:
        await session.execute(text('DROP TABLE IF EXISTS issues CASCADE'))
        await session.execute(text('DROP TABLE IF EXISTS feedback_records CASCADE'))
        await session.commit()
        print('Tables dropped. Restart your app to recreate them.')

asyncio.run(reset())
"
```

Then restart your FastAPI app - SQLAlchemy will create clean tables.

## Files Created

1. **TROUBLESHOOTING_PLAN.md** - Detailed analysis and options
2. **check_existing_data.py** - See what data exists
3. **check_actual_schema.py** - See actual database schema
4. **fix_issues_table_clean.py** - The actual fix script
5. **FIX_SUMMARY.md** - This file

## Need Help?

If the fix script fails, share the error and I'll help debug it.
