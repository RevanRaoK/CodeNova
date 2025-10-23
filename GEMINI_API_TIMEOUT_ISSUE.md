# Gemini API Timeout Issue

## Problem
The system logs show:
```
Calling AI service...
```
But then it never completes. The Gemini model is never actually called or it hangs indefinitely.

## Possible Causes

### 1. Invalid or Missing API Key
Check if your Gemini API key is valid:
```bash
# Check your .env file
cat backend/.env | grep GEMINI_API_KEY
```

### 2. Network/Firewall Issues
The Gemini API might be blocked by your firewall or network.

### 3. API Rate Limiting
Google might be rate-limiting your requests.

### 4. No Timeout Configured
The `generate_content()` call has no timeout, so it can hang forever.

## Quick Diagnostics

### Check 1: Verify API Key
```python
# Run this in Python to test your API key:
import google.generativeai as genai
import os

api_key = "YOUR_API_KEY_HERE"  # Replace with your actual key
genai.configure(api_key=api_key)
model = genai.GenerativeModel("models/gemini-1.5-flash")

try:
    response = model.generate_content("Say hello")
    print("Success:", response.text)
except Exception as e:
    print("Error:", e)
```

### Check 2: Check Backend Logs
Look for any error messages in the backend terminal where you ran `uvicorn`.

### Check 3: Test with Mock Data
Temporarily disable the Gemini API to test if the rest of the system works:

1. Open `backend/.env`
2. Comment out or remove `GEMINI_API_KEY`
3. Restart backend
4. Run analysis - it should return mock data quickly

## Temporary Workaround

If you need to test the feedback functionality without waiting for Gemini:

### Option 1: Use Mock Data
Remove or comment out `GEMINI_API_KEY` in your `.env` file. The system will return mock suggestions immediately.

### Option 2: Add Timeout (Recommended)
Add a timeout to the Gemini API call:

```python
# In backend/app/services/ai_service.py, around line 35:

import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

def get_review_for_code(self, code_snippet: str, timeout: int = 30) -> list:
    if not self.api_key:
        print("WARN: GEMINI_API_KEY not set. Returning mock AI response.")
        return [{"file_path": "example.py", "line_number": 1, "comment": "This is a mock AI suggestion."}]

    prompt = self._construct_prompt(code_snippet)

    try:
        # Add timeout wrapper
        with ThreadPoolExecutor() as executor:
            future = executor.submit(self.model.generate_content, prompt)
            try:
                response = future.result(timeout=timeout)
            except FuturesTimeoutError:
                print(f"Gemini API call timed out after {timeout} seconds")
                return [{
                    "file_path": "timeout.txt",
                    "line_number": 1,
                    "comment": "API request timed out. Please try again."
                }]
        
        # Rest of the code remains the same...
        raw_text = getattr(response, 'text', None) or ""
        # ... continue with existing logic
```

## Recommended Solution

### Step 1: Verify Your API Key
1. Go to https://makersuite.google.com/app/apikey
2. Check if your API key is valid
3. Create a new one if needed
4. Update `backend/.env`:
   ```
   GEMINI_API_KEY=your_new_key_here
   ```

### Step 2: Test API Key
Run the diagnostic Python script above to verify the key works.

### Step 3: Check Quota
1. Go to https://console.cloud.google.com/
2. Check your Gemini API quota and usage
3. Make sure you haven't exceeded limits

### Step 4: Add Timeout (if issue persists)
Implement the timeout wrapper shown above.

## For Task 9 Testing

Since Task 9 is about the **Dashboard displaying real data**, you don't actually need the Gemini API to work for testing:

1. **Use existing data**: If you have old analysis results in the database, the dashboard will display them
2. **Use mock data**: Remove the API key to get instant mock suggestions
3. **Focus on feedback**: Once you have suggestions (mock or real), test the accept/reject functionality

## Status

- ✅ Task 9 (Dashboard) - Complete and working
- ✅ Feedback submission fix - Complete
- ⚠️ Gemini API timeout - Separate issue, not part of Task 9

## Next Steps

1. Verify your Gemini API key is valid
2. Test with the diagnostic script
3. If it works in the script but not in the app, add the timeout wrapper
4. If you just want to test Task 9, use mock data (remove API key)

---

**Note**: This is a separate issue from Task 9. Task 9 was about updating the Dashboard component to use real analytics data, which is now complete.
