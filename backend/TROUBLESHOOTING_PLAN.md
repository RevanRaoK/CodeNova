# Database Schema Issue - Troubleshooting Plan

## Problem Summary
The `issues` table has BOTH old and new column schemas merged together:
- **Old schema** (from Windows/PR analysis): `pr_analysis_id` (NOT NULL) + old columns
- **New schema** (from models): `analysis_id` (nullable) + new columns
- **Result**: Columns were ADDED instead of REPLACED, causing conflicts

## Current State
```
issues table has:
- pr_analysis_id (NOT NULL) ← OLD, points to pr_analyses
- analysis_id (nullable)    ← NEW, points to direct_analyses
- file_path, line_number, message, rule_id, suggestion ← OLD columns
- pattern_type, category, location, suggestion_text, code_context ← NEW columns
```

## Root Cause
When the SQLAlchemy model was updated, it added new columns but didn't remove old ones.
The code is trying to insert with `analysis_id` but the database requires `pr_analysis_id`.

## Solution Options

### Option 1: Clean Migration (RECOMMENDED)
Drop the old columns and keep only the new schema that matches the model.

**Pros:**
- Clean schema matching the model
- No confusion about which columns to use
- Works with current codebase

**Cons:**
- Loses any existing PR analysis data
- Need to ensure no code references old columns

### Option 2: Keep Both Schemas
Make both columns nullable and update code to handle both.

**Pros:**
- Preserves existing data
- Can support both PR and direct analysis

**Cons:**
- Complex code logic
- Confusing schema
- Maintenance nightmare

### Option 3: Separate Tables
Create separate tables for PR issues and direct analysis issues.

**Pros:**
- Clear separation of concerns
- No data loss

**Cons:**
- More complex queries
- Code needs major refactoring

## Recommended Action Plan

### Phase 1: Backup and Assess
- [x] Check current schema
- [ ] Count records in issues table
- [ ] Check if any PR analysis data exists
- [ ] Backup database

### Phase 2: Clean Migration
- [ ] Drop old columns from issues table
- [ ] Make analysis_id NOT NULL
- [ ] Update foreign key to point to direct_analyses
- [ ] Verify schema matches model

### Phase 3: Verification
- [ ] Run schema verification script
- [ ] Test issue creation
- [ ] Test feedback submission
- [ ] Verify API endpoints work

## Implementation Scripts

### Script 1: Check Data
```python
# Count existing data
SELECT COUNT(*) FROM issues WHERE pr_analysis_id IS NOT NULL;
SELECT COUNT(*) FROM issues WHERE analysis_id IS NOT NULL;
```

### Script 2: Clean Migration
```sql
-- Drop old columns
ALTER TABLE issues DROP COLUMN IF EXISTS pr_analysis_id;
ALTER TABLE issues DROP COLUMN IF EXISTS file_path;
ALTER TABLE issues DROP COLUMN IF EXISTS line_number;
ALTER TABLE issues DROP COLUMN IF EXISTS message;
ALTER TABLE issues DROP COLUMN IF EXISTS rule_id;
ALTER TABLE issues DROP COLUMN IF EXISTS suggestion;
ALTER TABLE issues DROP COLUMN IF EXISTS feedback;
ALTER TABLE issues DROP COLUMN IF EXISTS issue_hash;

-- Make analysis_id NOT NULL
ALTER TABLE issues ALTER COLUMN analysis_id SET NOT NULL;

-- Add foreign key constraint
ALTER TABLE issues ADD CONSTRAINT issues_analysis_id_fkey 
    FOREIGN KEY (analysis_id) REFERENCES direct_analyses(id);
```

### Script 3: Verify
```python
# Run verify_database_schema.py
# Should show clean schema matching the model
```

## Decision Required
Which option do you want to proceed with?
1. Clean migration (drop old columns) - RECOMMENDED
2. Keep both schemas (complex)
3. Separate tables (major refactor)
