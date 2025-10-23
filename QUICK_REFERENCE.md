# Quick Reference Card - Keep This Handy

## Start Commands

### Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```

## URLs

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Test Code (Copy-Paste Ready)

```javascript
function test() {
  var password = "admin123";
  console.log(password);
  eval(userInput);
}
```

## Expected Results

- **Analysis Time:** 30-60 seconds
- **Issues Found:** 3-5 issues
- **Severity:** Critical, High, Medium
- **Feedback:** Success message on click

## Troubleshooting

| Problem | Solution |
|---------|----------|
| 404 Error | Restart backend |
| 401 Error | Login again |
| No results | Wait longer (60s) |
| Network Error | Check backend running |
| Console errors | Clear cache (Ctrl+Shift+R) |

## Success Indicators

✅ Backend: "Application startup complete"
✅ Frontend: "Local: http://localhost:5173/"
✅ Login: Dashboard loads
✅ Analysis: Issues appear
✅ Feedback: Success message
✅ History: Shows past analyses

## Demo Flow

1. Login
2. Go to Code Review
3. Paste test code
4. Click "Analyze Code"
5. Wait for results
6. Click thumbs up on issue
7. Click "View History"
8. Show Dashboard

**Total Time:** 3 minutes

## Key Features to Mention

1. AI-powered (Google Gemini)
2. Security detection
3. Multiple languages
4. Feedback system
5. Analytics dashboard

## If Demo Fails

Show:
1. Screenshots
2. Backend logs
3. Code walkthrough
4. README documentation

## Files to Submit

- [ ] All code files
- [ ] README.md
- [ ] Screenshots folder
- [ ] .env.example files
- [ ] requirements.txt
- [ ] package.json

## Last Minute Checks

- [ ] Backend starts
- [ ] Frontend starts
- [ ] Can login
- [ ] Analysis works
- [ ] Feedback works
- [ ] Screenshots taken

## Emergency Fixes

### Backend won't start
```bash
pip install -r requirements.txt
```

### Frontend won't start
```bash
npm install
```

### Database error
```bash
python create_tables.py
```

### Cache issues
Press: `Ctrl+Shift+R`

## Contact Info for README

```
Name: [Your Name]
Email: [Your Email]
College: [Your College]
Course: [Your Course]
Date: October 15, 2025
```

## Submission Checklist

- [ ] Code tested
- [ ] Screenshots taken
- [ ] README written
- [ ] .env files documented
- [ ] All features working
- [ ] No console errors
- [ ] Database populated
- [ ] API documented

## Confidence Reminders

✅ Backend works (logs prove it)
✅ Frontend works (just tested)
✅ Features complete
✅ Code clean
✅ Documentation ready

**You're ready to submit!**

---

Print this page and keep it with you tomorrow!
