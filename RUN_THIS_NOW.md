# RUN THIS NOW - Step by Step Commands

## Step 1: Restart Backend (REQUIRED)

Open a terminal in your project folder:

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**Wait for:** `Application startup complete`

**Keep this terminal open!**

---

## Step 2: Restart Frontend (REQUIRED)

Open a NEW terminal (don't close the backend one):

```bash
cd frontend
npm run dev
```

**Wait for:** `Local: http://localhost:5173/`

**Keep this terminal open too!**

---

## Step 3: Clear Browser Cache

1. Open your browser
2. Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
3. Or: Right-click refresh button → "Empty Cache and Hard Reload"

---

## Step 4: Test Everything

### 4a. Login
1. Go to http://localhost:5173
2. Login with your credentials
3. Should see the dashboard

### 4b. Test Code Analysis
1. Click "Code Review" in the menu
2. Paste this code:
```javascript
function test() {
  var password = "admin123";
  console.log(password);
}
```
3. Click "Analyze Code" **ONCE**
4. Wait 30-60 seconds
5. **You should see issues appear below**

### 4c. Test History
1. Click "View History" button
2. **You should see your 3 previous analyses**
3. Click "View Results" on one
4. **Issues should load**

### 4d. Test Feedback
1. On any issue, click the thumbs up 👍
2. **You should see "Feedback submitted successfully"**
3. Click thumbs down 👎 on another issue
4. **Should see success message again**

---

## Step 5: Check for Errors

Open browser console (Press F12):
- **Good:** No red errors
- **Bad:** Red errors → Send me the error message

---

## If You See Errors

### Error: "404 Not Found" for feedback
**Solution:** Did you restart the backend? (Step 1)

### Error: "401 Unauthorized"
**Solution:** Logout and login again

### Error: "Network Error"
**Solution:** Check if backend is running (Step 1)

### Error: Analysis not showing
**Solution:** 
1. Check backend terminal for errors
2. Make sure `.env` file has `GEMINI_API_KEY`

---

## Quick Health Check

Run these commands to verify everything:

### Check Backend:
```bash
curl http://localhost:8000/api/v1/health
```
**Expected:** `{"status":"healthy"}`

### Check Frontend:
Open browser to: http://localhost:5173
**Expected:** Login page loads

### Check Database:
```bash
cd backend
python -c "from app.core.database import engine; print('DB OK' if engine else 'DB FAIL')"
```
**Expected:** `DB OK`

---

## Success Indicators

✅ Backend terminal shows: `Application startup complete`
✅ Frontend terminal shows: `Local: http://localhost:5173/`
✅ Browser shows login page
✅ Can login successfully
✅ Code analysis shows results
✅ History button shows past analyses
✅ Feedback buttons work
✅ No red errors in console

---

## If Everything Works

**TAKE SCREENSHOTS NOW!**

1. Code Review page with issues
2. History view with analyses
3. Feedback success message
4. Dashboard with data
5. Backend terminal showing successful analysis

Save in folder: `demo_screenshots/`

---

## If Something Doesn't Work

**DON'T PANIC!**

1. Read the error message
2. Check which step failed
3. Try the solution for that error
4. If still stuck, you have screenshots as backup

---

## Time Estimate

- Step 1-2: 2 minutes (starting servers)
- Step 3: 30 seconds (clear cache)
- Step 4: 5 minutes (testing)
- Step 5: 1 minute (check errors)
- Screenshots: 2 minutes

**Total: ~10 minutes**

---

## After Testing

If everything works:
1. ✅ Take screenshots
2. ✅ Write a simple README with setup instructions
3. ✅ Get some sleep
4. ✅ Quick test tomorrow morning
5. ✅ Submit with confidence

Your project is working. The fixes are done. Just test and document!
