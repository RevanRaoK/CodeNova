# Feedback Dashboard Debugging Guide

## Issue
Charts are taking only half the space and not displaying data even when data is available.

## Changes Made to Fix

### 1. Added Console Logging
Added extensive console logging to track data flow:
- `FeedbackDashboard.jsx`: Logs raw API response and all data arrays
- `feedbackService.js`: Logs raw API response and processed data
- `FeedbackStatsChart.jsx`: Logs received data and transformed data
- `FeedbackTrendsChart.jsx`: Logs received data and transformed data
- `ModelPerformanceChart.jsx`: Logs received data and transformed data

### 2. Fixed Data Processing
Updated `processFeedbackStatsResponse()` in `feedbackService.js`:
- Correctly extracts `feedback_by_type.counts` from nested structure
- Filters out feedback types with zero counts
- Ensures all arrays are properly formatted

### 3. Added Array Safety Checks
All chart components now:
- Check if data is an array using `Array.isArray()`
- Use safe array variable (`dataArray`) throughout
- Handle empty/undefined data gracefully

## How to Debug

### Step 1: Check Browser Console
Open the browser console and navigate to the Feedback Dashboard. You should see:

```
Feedback Dashboard Data: { totalFeedback: X, acceptanceRate: Y, ... }
Feedback By Type: [{ type: 'Accept', count: X }, ...]
Feedback Trends: [{ date: '...', accept: X, ... }, ...]
Model Performance: [{ metric: '...', value: X, ... }, ...]
```

### Step 2: Verify API Response
Check the raw API response:
```
Raw API Response: { 
  total_feedback: X,
  feedback_by_type: {
    counts: { accept: X, reject: Y, modify: Z },
    rates: { ... }
  },
  ...
}
```

### Step 3: Check Chart Data
Each chart component logs:
```
FeedbackStatsChart received data: [...]
Transformed pieData: [...]
Transformed barData: [...]
```

### Step 4: Common Issues

#### Issue: Empty Arrays
**Symptom**: `feedbackByType: []` or `feedbackTrends: []`
**Cause**: No feedback data in database for the selected timeframe
**Solution**: 
- Try different timeframes (week, month, year)
- Verify feedback exists in database
- Check if user has submitted any feedback

#### Issue: Data Structure Mismatch
**Symptom**: Charts show "No data" but console shows data
**Cause**: Data format doesn't match what charts expect
**Solution**: Check the transformed data in console logs

#### Issue: Charts Taking Half Space
**Symptom**: Charts are narrow or compressed
**Cause**: CSS grid layout issue
**Solution**: 
- Check parent container has proper width
- Verify `lg:grid-cols-2` is working for the charts grid
- Check if there are conflicting CSS classes

## Expected Data Structures

### feedbackByType (for FeedbackStatsChart)
```javascript
[
  { type: 'Accept', count: 75 },
  { type: 'Reject', count: 50 },
  { type: 'Modify', count: 25 }
]
```

### feedbackTrends (for FeedbackTrendsChart)
```javascript
[
  {
    date: '2024-01-01',
    accept: 10,
    reject: 5,
    modify: 2,
    total: 17,
    acceptance_rate: 58.82
  },
  ...
]
```

### modelPerformance (for ModelPerformanceChart)
```javascript
[
  {
    metric: 'Acceptance Rate',
    value: 75.0,
    unit: '%',
    description: 'Percentage of suggestions accepted by users'
  },
  ...
]
```

## Testing Steps

1. **Login to the application** with an account that has feedback data
2. **Navigate to Feedback Dashboard**
3. **Open browser console** (F12)
4. **Check console logs** for data flow
5. **Try different timeframes** (Day, Week, Month, Year)
6. **Verify charts display** with proper data
7. **Check chart responsiveness** by resizing browser window

## Quick Fixes

### If charts are not showing:
1. Check if `stats` object is populated
2. Verify arrays are not empty: `stats.feedbackByType.length > 0`
3. Check console for errors
4. Verify API endpoint is returning data

### If charts are too narrow:
1. Check parent container width
2. Verify grid classes: `grid-cols-1 lg:grid-cols-2`
3. Check for conflicting CSS
4. Ensure ResponsiveContainer has proper width

### If data exists but charts show "No data":
1. Check data transformation in console logs
2. Verify data format matches expected structure
3. Check if filtering is removing all data
4. Verify chart component is receiving data prop

## API Endpoint

```
GET /api/v1/feedback/statistics?timeframe={week|month|quarter|year}
```

Response should include:
- `total_feedback`: number
- `feedback_by_type`: object with `counts` and `rates`
- `feedback_trends`: array of daily data
- `model_performance`: array of metrics
