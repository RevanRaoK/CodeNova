# Dashboard Fix Guide

## Problem
The dashboard is showing empty charts and "No recent activity" because the API requests are failing with the error:
```
SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON
```

This error means the frontend is receiving HTML (likely a 404 page) instead of JSON from the API.

## Root Causes
1. The Vite dev server was not configured to proxy API requests to the backend server. When the frontend tries to fetch from `/api/v1/analytics/user-stats`, it was looking for that route on the Vite server (port 5173) instead of the backend server (port 8000).
2. The Dashboard was using the wrong localStorage key for the auth token (`token` instead of `access_token`).

## Solution Applied

### 1. Added Proxy Configuration to Vite
Updated `frontend/vite.config.mjs` to proxy all `/api` requests to the backend:

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      secure: false,
    },
  },
  // ... other config
}
```

### 2. Fixed Authentication Token
Changed Dashboard to use the correct localStorage key:
- Changed from: `localStorage.getItem('token')`
- Changed to: `localStorage.getItem('access_token')`

### 3. Added Better Error Logging
Updated `Dashboard.jsx` to log:
- The URL being fetched
- Whether a token was found
- The response status
- The actual error response text

This will help debug any remaining issues.

### 4. Removed Mock Percentages
Removed the mock percentage changes ("+12%", "+8%", etc.) from the stat cards as requested.

### 5. Added Empty State Messages
Added helpful messages when charts have no data:
- "No usage data available for this timeframe"
- "No feedback data available for this timeframe"
- "No performance data available for this timeframe"

## Steps to Fix

### Step 1: Restart the Vite Dev Server
The proxy configuration requires a server restart:

```bash
# Stop the current dev server (Ctrl+C)
# Then restart it:
cd frontend
npm run dev
```

### Step 2: Ensure Backend is Running
Make sure the backend server is running on port 8000:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Verify Backend Endpoints
Test that the backend endpoints are working:

```bash
# Get your auth token from localStorage in browser console:
# localStorage.getItem('token')

# Then test the endpoints:
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/analytics/user-stats
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/analytics/usage-trends?timeframe=30d
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/analytics/feedback-distribution?timeframe=30d
```

### Step 4: Check Browser Console
After restarting the dev server:
1. Open the dashboard in your browser
2. Open DevTools (F12)
3. Go to the Console tab
4. Look for the new debug logs:
   - "Fetching user stats from: /api/v1/analytics/user-stats"
   - "User stats response status: 200"
   - "User stats data: {...}"

### Step 5: Check Network Tab
1. Open DevTools → Network tab
2. Refresh the dashboard
3. Look for requests to `/api/v1/analytics/...`
4. Check that they return status 200 (not 404)
5. Click on each request to see the response data

## Expected Behavior After Fix

### If Backend Has Data:
- Stat cards show actual numbers (not zeros)
- Usage Trends chart displays data
- Feedback Distribution pie chart appears
- Performance Metrics chart shows lines
- Recent Activity shows actual activities

### If Backend Has No Data:
- Stat cards show zeros
- Charts show "No data available" messages
- Recent Activity shows "No recent activity"

## Troubleshooting

### Issue: Still getting HTML responses
**Solution**: Make sure you restarted the Vite dev server after updating the config.

### Issue: 401 Unauthorized errors
**Solution**: 
1. Check that you're logged in
2. Verify the token in localStorage: `localStorage.getItem('token')`
3. Try logging out and logging back in

### Issue: 404 Not Found errors
**Solution**: 
1. Verify the backend server is running
2. Check that the analytics router is properly included in `backend/app/api/v1/router.py`
3. Test the endpoints directly with curl

### Issue: Backend returns empty data
**Solution**: 
1. Check that you have data in the database
2. Run some analyses to generate data
3. Create some feedback records
4. The analytics endpoints need actual data to display

### Issue: Charts still empty even with data
**Solution**:
1. Check the browser console for the "Dashboard Data:" log
2. Verify the data structure matches what the component expects
3. Check that the data transformation logic is correct

## Testing the Fix

1. **Restart Vite dev server** (most important!)
2. **Ensure backend is running** on port 8000
3. **Login to the application**
4. **Navigate to the dashboard**
5. **Open browser console** and check for:
   - No errors
   - Debug logs showing successful API calls
   - "Dashboard Data:" log showing actual data
6. **Check the Network tab** for successful API calls
7. **Verify charts display** (or show "No data" messages if database is empty)

## Next Steps

If the dashboard still shows no data after following these steps:
1. Check the backend logs for errors
2. Verify the database has data
3. Test the analytics service methods directly
4. Check that the user has permission to access the data

## Files Modified

- `frontend/vite.config.mjs` - Added proxy configuration
- `frontend/components/Dashboard.jsx` - Added logging and removed mock percentages
