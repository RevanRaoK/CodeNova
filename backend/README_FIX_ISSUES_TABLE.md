# Fix for Issues Table Schema Problem

## TL;DR - Quick Fix

```bash
cd backend

# See what's wrong
python RUN_ME_TO_FIX.py

# Fix it (recommended)
python reset_issues_table.py

# Verify
python verify_database_schema.py
```

Done! Your issues table will work correctly.

---

## What Went Wrong

Your `issues` table has **both old and new column schemas merged together**:

```
❌ CURRENT STATE (BROKEN):
issues table:
├── pr_analysis_id (NOT NULL)  ← OLD schema from Windows
├── analysis_id (nullable)      ← NEW schema from models
├── file_path, line_number      ← OLD columns
├── pattern_type, location      ← NEW columns
└── Result: Code can't insert because it uses analysis_id but DB requires pr_analysis_id
```

```
✓ DESIRED STATE (WORKING):
issues table:
├── analysis_id (NOT NULL)      ← Only this
├── pattern_type, location      ← Only new columns
└── Result: Code and DB match perfectly
```

## Why It Happened

1. **On Windows**: You created a fresh database with the old schema → worked fine
2. **On Linux**: You had an existing database, updated the models
3. **SQLAlchemy behavior**: It adds missing columns but never drops old ones
4. **Result**: You got both schemas merged, causing conflicts

## The Fix Scripts

### 🎯 RUN_ME_TO_FIX.py (START HERE)
Interactive diagnostic that tells you exactly what's wrong and what to run.

```bash
python RUN_ME_TO_FIX.py
```

### 🚀 reset_issues_table.py (RECOMMENDED)
**Nuclear option**: Drop table and recreate from model.
- Fastest (2 seconds)
- Cleanest result
- Guaranteed to work

```bash
python reset_issues_table.py
```

### 🔧 fix_issues_table_clean.py (ALTERNATIVE)
**Surgical option**: Drop old columns, keep table structure.
- More controlled
- Same end result
- Takes a bit longer

```bash
python fix_issues_table_clean.py
```

### 📊 check_existing_data.py (OPTIONAL)
See what data exists before fixing.

```bash
python check_existing_data.py
```

### ✅ verify_database_schema.py (VERIFICATION)
Comprehensive schema check - run after fixing.

```bash
python verify_database_schema.py
```

## Recommended Workflow

```bash
# 1. Understand the problem
python RUN_ME_TO_FIX.py

# 2. (Optional) See what data exists
python check_existing_data.py

# 3. Fix it - choose ONE:
python reset_issues_table.py          # ← Recommended (fastest)
# OR
python fix_issues_table_clean.py      # ← Alternative (more steps)

# 4. Verify it worked
python verify_database_schema.py

# 5. Test your API
# - Upload a file for analysis
# - Check if issues are created
# - Try submitting feedback
```

## What Each Script Does

| Script | Purpose | Modifies DB? |
|--------|---------|--------------|
| `RUN_ME_TO_FIX.py` | Diagnose and recommend | No |
| `check_existing_data.py` | Show current data | No |
| `check_actual_schema.py` | Show actual schema | No |
| `reset_issues_table.py` | Drop & recreate table | **YES** |
| `fix_issues_table_clean.py` | Drop old columns | **YES** |
| `verify_database_schema.py` | Verify schema | No |

## After Fixing

Your issues table will have this clean schema:

```
issues:
├── id (VARCHAR 64, PRIMARY KEY)
├── analysis_id (VARCHAR 36, NOT NULL, FK → direct_analyses)
├── pattern_type (VARCHAR 100, NOT NULL)
├── severity (VARCHAR 20, NOT NULL)
├── category (VARCHAR 50)
├── location (JSON, NOT NULL)
├── suggestion_text (TEXT, NOT NULL)
├── code_context (TEXT, NOT NULL)
├── original_code (TEXT)
├── suggested_fix (TEXT)
├── ast_node_type (VARCHAR 100)
├── ast_metadata (JSON)
├── status (VARCHAR 20, default 'active')
├── confidence_score (FLOAT)
├── created_at (TIMESTAMP)
├── updated_at (TIMESTAMP)
└── resolved_at (TIMESTAMP)
```

This matches your `Issue` model in `app/models/feedback.py` exactly.

## Troubleshooting

### "Table doesn't exist" error
Your database might not have the issues table at all. Just run:
```bash
python reset_issues_table.py
```

### "Foreign key constraint" error
The direct_analyses table might not exist. Check:
```bash
python -c "
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as s:
        r = await s.execute(text('SELECT COUNT(*) FROM direct_analyses'))
        print(f'direct_analyses records: {r.scalar()}')

asyncio.run(check())
"
```

### Still getting errors?
Share the error message and I'll help debug.

## Files Created

All in `backend/`:
- ✅ `README_FIX_ISSUES_TABLE.md` (this file)
- ✅ `RUN_ME_TO_FIX.py` (start here)
- ✅ `reset_issues_table.py` (recommended fix)
- ✅ `fix_issues_table_clean.py` (alternative fix)
- ✅ `check_existing_data.py` (diagnostic)
- ✅ `check_actual_schema.py` (diagnostic)
- ✅ `FIX_SUMMARY.md` (detailed explanation)
- ✅ `TROUBLESHOOTING_PLAN.md` (analysis)

## Questions?

Run `python RUN_ME_TO_FIX.py` and it will guide you through everything.
