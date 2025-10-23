# CodeNova User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [File Upload Guide](#file-upload-guide)
3. [Code Analysis](#code-analysis)
4. [Feedback System](#feedback-system)
5. [Data Visualizations](#data-visualizations)
6. [Analysis History](#analysis-history)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Creating an Account

1. Navigate to the CodeNova platform
2. Click "Sign Up" in the top right corner
3. Enter your email address and create a password
4. Verify your email address
5. Log in with your credentials

### Dashboard Overview

After logging in, you'll see your dashboard with:

- **Quick Actions**: Upload files or analyze code
- **Recent Analyses**: Your latest code reviews
- **Issue Trends**: Graph showing your code quality over time
- **Criticality Distribution**: Breakdown of issue severity levels

---

## File Upload Guide

### Uploading Single Files

1. Click the **"Upload Files"** button on your dashboard
2. Click the upload area or drag and drop a file
3. Select a source code file from your computer
4. The file will be automatically queued for analysis
5. You'll see a progress indicator while the analysis runs

### Uploading Multiple Files

You can upload multiple files at once for batch analysis:

1. Click the **"Upload Files"** button
2. Select multiple files using Ctrl+Click (Windows/Linux) or Cmd+Click (Mac)
3. Or drag and drop multiple files into the upload zone
4. All files will be queued and analyzed in the background
5. Track progress for each file individually

### Supported File Types

CodeNova supports the following programming languages:

- **Python**: `.py`
- **JavaScript**: `.js`, `.jsx`
- **TypeScript**: `.ts`, `.tsx`
- **Java**: `.java`
- **C/C++**: `.c`, `.cpp`, `.h`, `.hpp`
- **C#**: `.cs`
- **Go**: `.go`
- **Rust**: `.rs`
- **PHP**: `.php`
- **Ruby**: `.rb`
- **Swift**: `.swift`
- **Kotlin**: `.kt`
- **Scala**: `.scala`

### File Size Limits

- **Maximum file size**: 5 MB per file
- **Maximum batch size**: 20 files per upload
- **Total batch size**: 50 MB

### Upload Status

After uploading, files go through these stages:

1. **Queued**: File is waiting to be processed
2. **Processing**: AI is analyzing your code
3. **Completed**: Analysis is ready to view
4. **Failed**: An error occurred (see error message)

---

## Code Analysis

### Using the Monaco Editor

If you prefer to write or paste code directly:

1. Click **"Analyze Code"** on your dashboard
2. Write or paste your code in the editor
3. Click **"Analyze"**
4. **Important**: You'll be prompted to provide a filename
5. Enter a descriptive filename (e.g., `auth_handler.py`)
6. The system will auto-detect the language from the extension
7. Click **"Submit"** to start the analysis

### Why Provide a Filename?

Filenames help you:
- Organize and find your analyses later
- Track which code was analyzed
- Compare different versions of the same file
- Get language-specific analysis

### Real-Time Status Updates

While your code is being analyzed:

- You'll see a **"Processing"** indicator
- Progress percentage updates in real-time
- You can navigate away and come back later
- You'll be notified when analysis is complete

### Understanding Analysis Results

Each analysis provides:

1. **Issue Count**: Total number of issues found
2. **Issue Types**: Categorized by type (errors, warnings, security, style)
3. **Severity Levels**: Severe, High, Medium, Low
4. **Line Numbers**: Exact location of each issue
5. **Suggestions**: AI-generated recommendations
6. **Code Snippets**: Context around each issue

---

## Feedback System

### Why Provide Feedback?

Your feedback helps the AI learn and improve:
- Accepts good suggestions
- Rejects irrelevant suggestions
- Teaches the AI your coding preferences
- Improves future analysis accuracy

### Providing Feedback on Suggestions

For each suggestion in your analysis results:

#### Accept a Suggestion

1. Click the **"Accept"** button next to the suggestion
2. Optionally add a comment explaining why
3. The suggestion is marked as accepted
4. The AI learns this was helpful

#### Reject a Suggestion

1. Click the **"Reject"** button
2. Optionally explain why it wasn't helpful
3. The suggestion is marked as rejected
4. The AI learns to avoid similar suggestions

#### Modify a Suggestion

1. Click the **"Modify"** button
2. Edit the suggestion text
3. Provide your improved version
4. Click **"Submit"**
5. The AI learns from your modification

### Feedback Best Practices

- **Be specific**: Explain why you accepted/rejected
- **Be consistent**: Similar issues should get similar feedback
- **Be timely**: Provide feedback soon after analysis
- **Be honest**: Don't accept suggestions you won't use

### Viewing Your Feedback History

1. Navigate to **"Feedback History"** in the menu
2. See all feedback you've provided
3. Filter by type (accept, reject, modify)
4. Track your feedback patterns

---

## Data Visualizations

### Issue Trends Graph

The Issue Trends graph shows how your code quality changes over time.

#### Understanding the Graph

- **X-Axis**: Time (days, weeks, or months)
- **Y-Axis**: Number of issues
- **Lines**: Different colors for each issue type
  - 🔴 Red: Errors
  - 🟡 Yellow: Warnings
  - 🔵 Blue: Security Issues

#### Using the Graph

1. **Hover** over data points to see exact numbers
2. **Click** legend items to show/hide issue types
3. **Select timeframe**: 7 days, 30 days, or 90 days
4. **Track trends**: See if issues are increasing or decreasing

#### What to Look For

- **Downward trends**: Your code quality is improving ✅
- **Upward trends**: More issues being detected ⚠️
- **Spikes**: Sudden increase (new feature or refactoring?)
- **Flat lines**: Consistent code quality

### Criticality Distribution Chart

This chart shows the severity breakdown of your issues.

#### Understanding the Chart

- **Severe** (Red): Critical issues requiring immediate attention
- **High** (Orange): Important issues to fix soon
- **Medium** (Yellow): Issues to address when possible
- **Low** (Green): Minor improvements and style suggestions

#### Using the Chart

1. **View percentages**: See what portion of issues are critical
2. **Click segments**: Drill down into specific severity levels
3. **Compare over time**: Select different timeframes
4. **Prioritize work**: Focus on severe and high issues first

#### Ideal Distribution

A healthy codebase typically has:
- **Severe**: < 5%
- **High**: < 15%
- **Medium**: 30-40%
- **Low**: 40-50%

### Customizing Visualizations

- **Timeframe selector**: Choose 7d, 30d, or 90d
- **Export data**: Download charts as images
- **Filter by file**: See trends for specific files
- **Compare periods**: View side-by-side comparisons

---

## Analysis History

### Viewing Your History

1. Click **"Analysis History"** in the navigation menu
2. See all your past analyses with filenames
3. Each entry shows:
   - Filename
   - Date and time
   - Status (completed, processing, failed)
   - Number of issues found
   - Language

### Filtering and Sorting

**Filter by:**
- Filename (search box)
- Status (dropdown)
- Date range (date picker)
- Language (dropdown)

**Sort by:**
- Date (newest/oldest first)
- Filename (A-Z or Z-A)
- Issue count (most/least issues)

### Viewing Analysis Details

1. Click on any analysis in your history
2. See the full code that was analyzed
3. View all issues and suggestions
4. Provide feedback on suggestions

---

## Best Practices

### For Best Analysis Results

1. **Use descriptive filenames**: `user_authentication.py` not `file1.py`
2. **Upload complete files**: Partial code may give incomplete results
3. **One file at a time for learning**: Start small, then batch upload
4. **Review results promptly**: Provide feedback while code is fresh
5. **Act on suggestions**: Implement accepted suggestions in your code

### For Effective Feedback

1. **Review all suggestions**: Don't skip any
2. **Be thoughtful**: Consider each suggestion carefully
3. **Explain rejections**: Help the AI understand why
4. **Modify when close**: If a suggestion is almost right, modify it
5. **Track patterns**: Notice what types of suggestions you accept/reject

### For Code Quality Improvement

1. **Check trends regularly**: Review your graphs weekly
2. **Set goals**: Aim to reduce severe/high issues
3. **Focus on security**: Always address security issues first
4. **Learn from patterns**: Notice recurring issues
5. **Iterate**: Re-analyze after making fixes

### For Efficient Workflow

1. **Use batch upload**: For multiple related files
2. **Leverage Monaco editor**: For quick code snippets
3. **Bookmark analyses**: Save important results
4. **Use filters**: Find specific analyses quickly
5. **Enable notifications**: Get alerts when analysis completes

---

## Troubleshooting

### Upload Issues

**Problem**: File won't upload

**Solutions**:
- Check file size (must be < 5 MB)
- Verify file type is supported
- Check internet connection
- Try a different browser
- Clear browser cache

**Problem**: Upload stuck at "Processing"

**Solutions**:
- Wait 2-3 minutes (large files take time)
- Refresh the page
- Check batch status page
- Contact support if > 10 minutes

### Analysis Issues

**Problem**: No issues found (but you expected some)

**Possible reasons**:
- Code is actually clean! ✅
- Language detection failed
- File is too simple
- AI model needs more context

**Problem**: Too many false positives

**Solutions**:
- Provide feedback (reject false positives)
- Check if language was detected correctly
- Ensure code is complete (not a snippet)
- The AI will learn from your feedback

### Feedback Issues

**Problem**: Can't submit feedback

**Solutions**:
- Check internet connection
- Refresh the page
- Log out and log back in
- Try a different browser

**Problem**: Feedback not saving

**Solutions**:
- Ensure you clicked "Submit"
- Check for error messages
- Verify you're still logged in
- Contact support if persists

### Visualization Issues

**Problem**: Graphs not loading

**Solutions**:
- Refresh the page
- Check if you have enough analysis history
- Try a different timeframe
- Clear browser cache
- Disable browser extensions

**Problem**: Data looks incorrect

**Solutions**:
- Verify the timeframe selected
- Check filters are set correctly
- Ensure analyses completed successfully
- Contact support with specific details

### General Issues

**Problem**: Page won't load

**Solutions**:
- Check internet connection
- Try a different browser
- Clear cache and cookies
- Disable VPN if using one
- Check system status page

**Problem**: Session expired

**Solutions**:
- Log in again
- Enable "Remember me" option
- Check if cookies are enabled
- Contact support if happens frequently

---

## Getting Help

### Support Resources

- **Documentation**: [docs.codenova.com](https://docs.codenova.com)
- **FAQ**: [codenova.com/faq](https://codenova.com/faq)
- **Video Tutorials**: [codenova.com/tutorials](https://codenova.com/tutorials)
- **Community Forum**: [forum.codenova.com](https://forum.codenova.com)

### Contact Support

- **Email**: support@codenova.com
- **Live Chat**: Available 9 AM - 5 PM EST
- **Response Time**: Within 24 hours

### Reporting Bugs

When reporting issues, include:
1. What you were trying to do
2. What happened instead
3. Error messages (if any)
4. Browser and version
5. Screenshots (if helpful)

---

## Tips and Tricks

### Power User Features

1. **Keyboard Shortcuts**:
   - `Ctrl+U`: Upload files
   - `Ctrl+A`: Analyze code
   - `Ctrl+H`: View history
   - `Ctrl+F`: Search analyses

2. **Bulk Actions**:
   - Select multiple analyses
   - Export all at once
   - Delete old analyses

3. **Custom Filters**:
   - Save frequently used filters
   - Quick access to specific file types
   - Team-specific views

### Productivity Tips

1. **Morning Review**: Check overnight analyses
2. **Weekly Trends**: Review graphs every Monday
3. **Feedback Friday**: Catch up on pending feedback
4. **Batch Upload**: Upload all files for a feature together
5. **Set Reminders**: For re-analyzing after fixes

---

## What's Next?

Now that you know the basics:

1. ✅ Upload your first file
2. ✅ Analyze some code
3. ✅ Provide feedback on suggestions
4. ✅ Check your visualizations
5. ✅ Track your improvement over time

Happy coding! 🚀
