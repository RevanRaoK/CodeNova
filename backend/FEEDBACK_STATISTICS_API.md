# Feedback Statistics API Endpoint

## Overview

This document describes the `/api/v1/feedback/statistics` endpoint that provides comprehensive feedback statistics with timeframe-based aggregation, trend analysis, and model performance metrics.

**Requirements Covered:** 2.2, 2.3, 2.4, 2.5

## Endpoint Details

### GET /api/v1/feedback/statistics

Retrieves comprehensive feedback statistics including:
- Aggregation queries for feedback by type (accept/reject/modify)
- Feedback trends over time periods
- Model performance metrics based on feedback data
- Pattern-specific statistics

#### Authentication

Required: Yes (Bearer token)

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `timeframe` | string | No | "week" | Time period for analysis. Valid values: `week`, `month`, `quarter`, `year`, `all` |
| `user_id` | integer | No | current user | Filter by specific user ID (admin only) |

#### Response Schema

```json
{
  "timeframe": "string",
  "total_feedback": "integer",
  "feedback_by_type": {
    "counts": {
      "accept": "integer",
      "reject": "integer",
      "modify": "integer",
      "ignore": "integer"
    },
    "rates": {
      "acceptance_rate": "float",
      "rejection_rate": "float",
      "modification_rate": "float",
      "ignore_rate": "float"
    }
  },
  "acceptance_rate": "float",
  "rejection_rate": "float",
  "modification_rate": "float",
  "feedback_trends": [
    {
      "date": "string (YYYY-MM-DD)",
      "accept": "integer",
      "reject": "integer",
      "modify": "integer",
      "ignore": "integer",
      "total": "integer",
      "acceptance_rate": "float"
    }
  ],
  "model_performance": [
    {
      "metric": "string",
      "value": "float",
      "unit": "string",
      "description": "string"
    }
  ],
  "pattern_feedback_stats": {
    "pattern_type": {
      "acceptance_rate": "float",
      "rejection_rate": "float",
      "modification_rate": "float",
      "total_feedback": "integer"
    }
  },
  "feedback_by_date": {
    "YYYY-MM-DD": "integer"
  },
  "generated_at": "string (ISO 8601)"
}
```

#### Example Request

```bash
curl -X GET "http://localhost:8000/api/v1/feedback/statistics?timeframe=month" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Example Response

```json
{
  "timeframe": "month",
  "total_feedback": 1250,
  "feedback_by_type": {
    "counts": {
      "accept": 906,
      "reject": 228,
      "modify": 116,
      "ignore": 0
    },
    "rates": {
      "acceptance_rate": 72.48,
      "rejection_rate": 18.24,
      "modification_rate": 9.28,
      "ignore_rate": 0.0
    }
  },
  "acceptance_rate": 72.48,
  "rejection_rate": 18.24,
  "modification_rate": 9.28,
  "feedback_trends": [
    {
      "date": "2024-01-15",
      "accept": 45,
      "reject": 12,
      "modify": 5,
      "ignore": 0,
      "total": 62,
      "acceptance_rate": 72.58
    },
    {
      "date": "2024-01-16",
      "accept": 38,
      "reject": 8,
      "modify": 4,
      "ignore": 0,
      "total": 50,
      "acceptance_rate": 76.0
    }
  ],
  "model_performance": [
    {
      "metric": "Acceptance Rate",
      "value": 72.48,
      "unit": "%",
      "description": "Percentage of suggestions accepted by users"
    },
    {
      "metric": "Suggestion Quality Score",
      "value": 77.12,
      "unit": "%",
      "description": "Weighted quality metric (accept=100%, modify=50%, reject=0%)"
    },
    {
      "metric": "User Engagement Rate",
      "value": 100.0,
      "unit": "%",
      "description": "Percentage of suggestions that received active feedback"
    },
    {
      "metric": "Average Confidence Score",
      "value": 85.3,
      "unit": "%",
      "description": "Average AI confidence for accepted suggestions"
    },
    {
      "metric": "Model Accuracy",
      "value": 82.5,
      "unit": "%",
      "description": "Current active model accuracy score"
    }
  ],
  "pattern_feedback_stats": {
    "unused_variable": {
      "acceptance_rate": 85.2,
      "rejection_rate": 10.5,
      "modification_rate": 4.3,
      "total_feedback": 320
    },
    "code_complexity": {
      "acceptance_rate": 68.5,
      "rejection_rate": 22.1,
      "modification_rate": 9.4,
      "total_feedback": 215
    }
  },
  "feedback_by_date": {
    "2024-01-15": 62,
    "2024-01-16": 50,
    "2024-01-17": 48
  },
  "generated_at": "2024-01-18T10:30:00.123456"
}
```

## Features

### 1. Aggregation by Feedback Type

The endpoint aggregates feedback into four categories:
- **Accept**: User accepted the AI suggestion
- **Reject**: User rejected the AI suggestion
- **Modify**: User modified the AI suggestion before accepting
- **Ignore**: User ignored the suggestion

Both raw counts and percentage rates are provided.

### 2. Feedback Trends Over Time

Daily breakdown of feedback showing:
- Count of each feedback type per day
- Total feedback per day
- Daily acceptance rate

This allows tracking of model performance improvements over time.

### 3. Model Performance Metrics

Five key performance indicators:

1. **Acceptance Rate**: Percentage of suggestions accepted by users
2. **Suggestion Quality Score**: Weighted metric where accept=100%, modify=50%, reject=0%
3. **User Engagement Rate**: Percentage of suggestions that received active feedback (not ignored)
4. **Average Confidence Score**: Average AI confidence for accepted suggestions
5. **Model Accuracy**: Current active model's accuracy score from the model_versions table

### 4. Pattern-Specific Statistics

Breakdown of feedback rates by issue pattern type (e.g., unused_variable, code_complexity), showing:
- Acceptance rate for each pattern
- Rejection rate for each pattern
- Modification rate for each pattern
- Total feedback count for each pattern

This helps identify which types of suggestions are most/least effective.

## Timeframe Options

| Timeframe | Days | Description |
|-----------|------|-------------|
| `week` | 7 | Last 7 days |
| `month` | 30 | Last 30 days |
| `quarter` | 90 | Last 90 days |
| `year` | 365 | Last 365 days |
| `all` | unlimited | All historical data |

## Error Responses

### 400 Bad Request

Invalid timeframe parameter:

```json
{
  "detail": "Invalid timeframe. Must be one of: week, month, quarter, year, all"
}
```

### 401 Unauthorized

Missing or invalid authentication token:

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

Attempting to access another user's data without admin privileges:

```json
{
  "detail": "Admin access required to view other users' data"
}
```

### 500 Internal Server Error

Server-side error during processing:

```json
{
  "detail": "Failed to retrieve feedback statistics: [error details]"
}
```

## Implementation Details

### Service Layer

The `FeedbackService` class provides the `get_feedback_statistics_with_timeframe()` method that:

1. Validates the timeframe parameter
2. Builds database queries with appropriate date filters
3. Aggregates feedback by type
4. Calculates trends over time
5. Computes model performance metrics
6. Groups statistics by pattern type

### Database Queries

The implementation uses efficient aggregation queries:
- Single query to fetch all relevant feedback records
- In-memory aggregation using Python collections
- Joins with Issue table for pattern information
- Joins with ModelVersion table for model metrics

### Performance Considerations

- Results are calculated on-demand (no caching in initial implementation)
- Consider adding Redis caching for frequently requested timeframes
- Database indexes on `created_at` and `feedback_type` columns improve query performance

## Usage Examples

### Frontend Integration

```typescript
// Fetch monthly feedback statistics
async function getFeedbackStatistics(timeframe: string = 'month') {
  const response = await fetch(
    `/api/v1/feedback/statistics?timeframe=${timeframe}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch feedback statistics');
  }
  
  return await response.json();
}

// Display on dashboard
const stats = await getFeedbackStatistics('month');
console.log(`Acceptance Rate: ${stats.acceptance_rate}%`);
console.log(`Total Feedback: ${stats.total_feedback}`);
```

### Python Client

```python
import requests

def get_feedback_statistics(token: str, timeframe: str = 'month'):
    """Fetch feedback statistics from API."""
    response = requests.get(
        'http://localhost:8000/api/v1/feedback/statistics',
        headers={'Authorization': f'Bearer {token}'},
        params={'timeframe': timeframe}
    )
    response.raise_for_status()
    return response.json()

# Usage
stats = get_feedback_statistics(access_token, 'quarter')
print(f"Acceptance Rate: {stats['acceptance_rate']}%")
```

## Testing

A comprehensive test script is provided in `test_feedback_statistics.py`:

```bash
# Run the test script
python backend/test_feedback_statistics.py
```

The test script validates:
- Authentication requirements
- All timeframe options
- Invalid parameter handling
- Response structure and required fields
- Nested object structures

## Future Enhancements

1. **Caching**: Add Redis caching for improved performance
2. **Filtering**: Add more filter options (pattern_type, severity, date range)
3. **Export**: Add CSV/JSON export functionality
4. **Real-time Updates**: WebSocket support for live statistics
5. **Comparison**: Compare statistics across different time periods
6. **User Segments**: Analyze statistics by user experience level

## Related Endpoints

- `GET /api/v1/feedback/stats` - Legacy statistics endpoint (to be deprecated)
- `GET /api/v1/feedback/trends` - Detailed trend analysis
- `GET /api/v1/analytics/dashboard` - Comprehensive analytics dashboard
- `GET /api/v1/analytics/acceptance-rates` - Detailed acceptance rate analysis

## Changelog

### Version 1.0.0 (2024-01-18)
- Initial implementation
- Support for 5 timeframe options
- Aggregation by feedback type
- Trend calculation over time
- Model performance metrics
- Pattern-specific statistics
