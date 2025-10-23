## Database Verification and Fix Scripts

These scripts help you verify and fix database schema issues, especially related to the issues table and feedback functionality.

## Quick Start

Run the master health check script:

```bash
cd backend
python database_health_check.py
```

This will:
1. Verify the entire database schema
2. Automatically fix common issues
3. Check the issues table specifically
4. Provide a summary of the database health

## Individual Scripts

### 1. `verify_database_schema.py`
**Purpose**: Comprehensive schema verification

**What it checks**:
- All tables exist
- All required columns exist
- Column types and nullable constraints
- Indexes and foreign keys
- Orphaned records
- Duplicate issue_hash values
- Record counts

**Usage**:
```bash
python verify_database_schema.py
```

**Output**: Detailed report of schema status with ✓ or ❌ for each check

### 2. `check_issues_table.py`
**Purpose**: Specific checks for the issues table and feedback functionality

**What it checks**:
- Total issues count
- Recent issues details
- Issues with feedback
- Orphaned issues (pr_analysis doesn't exist)
- Issues without issue_hash
- PR analyses with issues
- Issue lookup by ID

**Usage**:
```bash
python check_issues_table.py
```

**Output**: Detailed report of issues table status

### 3. `fix_database_issues.py`
**Purpose**: Automatically fix common database issues

**What it fixes**:
- Adds missing columns (issue_hash, feedback, status)
- Updates NULL status values to 'open'
- Generates missing issue_hash values
- Deletes orphaned issues
- Creates missing indexes

**Usage**:
```bash
python fix_database_issues.py
```

**Output**: List of fixes applied

### 4. `database_health_check.py`
**Purpose**: Master script that runs all checks and fixes

**Usage**:
```bash
python database_health_check.py
```

**Output**: Complete health check report with automatic fixes

## Common Issues and Solutions

### Issue: "Issue with ID [###] not found"

**Cause**: The issue exists in the analysis results JSON but not in the issues table

**Solution**:
1. Run `python database_health_check.py`
2. Check if issues are being created properly
3. Verify the issue_id_service is working

### Issue: Missing columns in issues table

**Symptoms**:
- Errors about missing columns
- Feedback not saving
- Status not updating

**Solution**:
```bash
python fix_database_issues.py
```

This will add any missing columns automatically.

### Issue: Orphaned issues

**Symptoms**:
- Issues that reference non-existent pr_analyses
- Foreign key constraint errors

**Solution**:
```bash
python fix_database_issues.py
```

This will delete orphaned issues.

### Issue: Missing issue_hash

**Symptoms**:
- Duplicate issues being created
- Issue tracking not working properly

**Solution**:
```bash
python fix_database_issues.py
```

This will generate issue_hash for all issues.

## Database Schema Reference

### issues table

Required columns:
- `id` (VARCHAR, PRIMARY KEY)
- `pr_analysis_id` (VARCHAR, FOREIGN KEY)
- `file_path` (VARCHAR)
- `line_number` (INTEGER)
- `severity` (VARCHAR)
- `message` (TEXT)
- `rule_id` (VARCHAR, nullable)
- `suggestion` (TEXT, nullable)
- `status` (VARCHAR, default 'open')
- `feedback` (TEXT, nullable)
- `issue_hash` (VARCHAR(64), nullable)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

Required indexes:
- `idx_issues_pr_analysis` on `pr_analysis_id`
- `idx_issues_status` on `status`
- `idx_issues_hash` on `issue_hash`

### pr_analyses table

Required columns:
- `id` (VARCHAR, PRIMARY KEY)
- `repository_id` (VARCHAR, FOREIGN KEY)
- `pr_number` (INTEGER)
- `status` (VARCHAR)
- `issues_found` (INTEGER, nullable)
- `analysis_results` (JSON, nullable)
- ... (see verify_database_schema.py for complete list)

## Troubleshooting

### Script fails with "module not found"

Make sure you're in the backend directory:
```bash
cd backend
python database_health_check.py
```

### Script fails with database connection error

Check your database is running and `.env` file has correct credentials:
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check .env file
cat .env | grep DATABASE
```

### Script shows schema issues but fix doesn't work

Some issues might require manual intervention:
1. Check the error messages carefully
2. Run the individual scripts to see more details
3. Manually run SQL commands if needed

## After Running Fixes

1. **Restart backend server**:
   ```bash
   # Kill existing process
   pkill -f "uvicorn app.main:app"
   
   # Start new process
   uvicorn app.main:app --reload
   ```

2. **Trigger new analysis**:
   - Go to UI
   - Select a repository
   - Click "Analyze Repository"

3. **Test feedback**:
   - Go to analysis results
   - Try providing feedback on an issue
   - Should work without "Issue not found" error

## Need Help?

If these scripts don't fix your issue:
1. Check the detailed output from `verify_database_schema.py`
2. Look at the actual error messages in backend logs
3. Check if the issue_id_service is creating issues properly
4. Verify the API endpoint for feedback is working
