# Repository Analysis Troubleshooting Guide

## Issue: Analysis Stuck in "Pending" Status

### Problem

When you click "Analyze Repository", the analysis shows as "pending" and never completes because background workers are not running.

### Why This Happens

The `analyze_repository_files` task needs to be processed by background workers (Redis/Celery queue). Without workers running, the task stays in the queue indefinitely.

## Solution Options

### Option 1: Install Dependencies and Start Workers (Recommended)

1. **Install missing dependency:**

   ```bash
   cd backend
   pip install aio-pika
   ```

2. **Start background workers:**

   ```bash
   cd backend
   python start_hybrid_queue.py
   ```

3. **Verify workers are running:**

   - You should see: "Worker started successfully"
   - Leave this terminal running

4. **Click "Analyze Repository" again**
   - The analysis should start processing
   - Status will change: pending → in_progress → completed

---

### Option 2: Run Analysis Directly (Quick Test)

If you can't start workers, you can manually run the analysis task:

1. **Open a Python shell in backend:**

   ```bash
   cd backend
   python
   ```

2. **Run this code:**

   ```python
   import asyncio
   from app.tasks.file_analysis_tasks import analyze_repository_files

   # Replace with your actual repository ID from the database
   repository_id = "21c966e2-ab3a-4a14-ad38-b12ad96284ad"

   # Run the analysis
   result = asyncio.run(analyze_repository_files(
       repository_id=repository_id,
       file_patterns=["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"]
   ))

   print("Analysis completed!")
   print(result)
   ```

3. **Check the UI:**
   - Click refresh button
   - Analysis should now show as "completed" with results

---

### Option 3: Check What's in Database

**Using psql (if you have PostgreSQL client):**

```sql
-- Connect to your database
psql -U your_username -d codenova

-- Check recent analyses
SELECT
    id,
    status,
    pr_title,
    created_at,
    issues_found,
    error_message
FROM pr_analyses
WHERE pr_number = 0
ORDER BY created_at DESC
LIMIT 5;

-- Check full analysis results
SELECT
    id,
    status,
    analysis_results
FROM pr_analyses
WHERE pr_number = 0
ORDER BY created_at DESC
LIMIT 1;
```

**Using DBeaver or pgAdmin:**

1. Open your database GUI
2. Run the above queries
3. Look at the `analysis_results` JSON field

---

## Understanding the Status

### Status Values:

- **pending** = Queued but not started (workers not running)
- **in_progress** = Currently being processed
- **completed** = Finished successfully
- **failed** = Error occurred

### If Status is "pending":

✅ The analysis was created successfully
✅ Database record exists
❌ Workers are not running
❌ Task is not being processed

**Solution:** Start workers with Option 1

### If Status is "failed":

Check `error_message` field in database for details.

---

## Quick Check: Is Everything Working?

Run this checklist:

1. **Backend server running?**

   ```bash
   # Should see: "Application startup complete"
   # Port 8000 should be open
   ```

2. **Can you see the analysis in UI?**

   - Yes, shows "Full Repository Analysis"
   - Status badge shows "pending"
   - Date shows properly (after server restart)

3. **Background workers running?**

   ```bash
   # In separate terminal:
   cd backend
   python start_hybrid_queue.py

   # Should see: "Worker started" and stay running
   ```

4. **Click "Analyze Repository" again**
   - Should process within 1-2 minutes (depending on repo size)
   - Status changes to "in_progress" then "completed"

---

## Expected Timeline (with Workers Running)

| Time    | Status      | What's Happening                                |
| ------- | ----------- | ----------------------------------------------- |
| 0s      | pending     | Analysis queued                                 |
| 1-5s    | in_progress | Discovering files from GitHub                   |
| 5s-2min | in_progress | Analyzing files with AI (depends on file count) |
| 2-5min  | completed   | Results stored, issues counted                  |

---

## Common Errors

### "User object has no attribute 'username'"

**Fixed!** We updated the code to use `email` instead.

### "'aio_pika' module not found"

**Solution:** `pip install aio-pika`

### "Analysis stays pending forever"

**Solution:** Start background workers

### "Invalid Date" in UI

**Fixed!** Added `created_at` to the response schema.

---

## For Now (Without Workers)

**What you CAN see:**

- ✅ Analysis is created
- ✅ Shows in "Code Analyses" list
- ✅ Has title "Full Repository Analysis"
- ✅ Shows "pending" status
- ✅ Has creation date

**What you CANNOT see yet:**

- ❌ Progress updates
- ❌ Files analyzed count
- ❌ Issues found
- ❌ Completed status

**To see actual results:** Start the workers as described in Option 1.

---

## Next Steps

1. **Restart backend server** (to pick up schema fix)

   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Refresh the UI page**

   - The "Invalid Date" should now be fixed

3. **Install aio-pika and start workers**

   ```bash
   pip install aio-pika
   python start_hybrid_queue.py
   ```

4. **Click "Analyze Repository" again**
   - Now it should actually process!

---

## Need Help?

If workers won't start:

1. Check if Redis is running (workers need Redis)
2. Check the error message when starting workers
3. Try Option 2 (run analysis directly) for testing

If analysis fails:

1. Check backend logs for errors
2. Check database `error_message` field
3. Verify GitHub token has access to repository
