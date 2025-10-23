# Quick Fix for Dashboard Issues

## The Problem
Dashboard shows empty charts because:
1. API requests were failing - the frontend was getting HTML instead of JSON
2. Wrong authentication token key was being used

## The Solution
1. Added proxy configuration to Vite to forward API requests to the backend server
2. Fixed the Dashboard to use the correct token key (`access_token` instead of `token`)

## What You Need to Do NOW

### 1. Restart the Vite Dev Server (REQUIRED!)
```bash
# Press Ctrl+C to stop the current server
# Then restart:
cd frontend
npm run dev
```

### 2. Make Sure Backend is Running
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Refresh the Dashboard
- Go to http://localhost:5173/dashboard
- Open browser console (F12)
- You should see debug logs showing successful API calls

## What Changed

1. ✅ Added proxy in `vite.config.mjs` to forward `/api` requests to `http://localhost:8000`
2. ✅ Fixed authentication - changed from `localStorage.getItem('token')` to `localStorage.getItem('access_token')`
3. ✅ Removed mock percentage changes from stat cards ("+12%", etc.)
4. ✅ Added "No data available" messages for empty charts
5. ✅ Added debug logging to help troubleshoot

## Expected Result

After restarting the Vite server:
- API requests should work (no more HTML errors)
- If you have data: charts will display
- If you have no data: you'll see "No data available" messages instead of empty charts
- Recent Activity will show actual activities or "No recent activity"

## Still Not Working?

See `DASHBOARD_FIX_GUIDE.md` for detailed troubleshooting steps.
