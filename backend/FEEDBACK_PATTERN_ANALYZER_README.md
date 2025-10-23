# Feedback Pattern Analyzer Service

## Overview

The Feedback Pattern Analyzer service analyzes user feedback patterns to enable personalized AI learning. It aggregates feedback data by category and severity, calculates acceptance rates, and identifies user preferences for different types of code suggestions.

## Requirements Covered

- **8.1**: Store user feedback with context about issue type and category
- **8.2**: Identify patterns in accepted vs rejected suggestions
- **8.9**: Weight recent feedback more heavily and cache patterns

## Architecture

### Database Schema

The service uses the `user_feedback_patterns` table to cache aggregated feedback statistics:

```sql
CREATE TABLE user_feedback_patterns (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    acceptance_rate FLOAT NOT NULL DEFAULT 0.0,
    total_feedback_count INTEGER NOT NULL DEFAULT 0,
    accepted_count INTEGER NOT NULL DEFAULT 0,
    rejected_count INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, category, severity)
);
```

### Key Components

1. **UserFeedbackPattern Model** (`app/models/feedback_patterns.py`)
   - SQLAlchemy model for the patterns table
   - Helper methods for pattern classification
   - Properties for acceptance/rejection thresholds

2. **FeedbackPatternAnalyzer Service** (`app/services/feedback_pattern_analyzer.py`)
   - Core analysis logic
   - Pattern aggregation and calculation
   - Caching and retrieval methods

## Usage

### Basic Usage

```python
from app.services.feedback_pattern_analyzer import FeedbackPatternAnalyzer
from app.core.database import SessionLocal

db = SessionLocal()
analyzer = FeedbackPatternAnalyzer(db)

# Analyze user patterns
result = analyzer.analyze_user_patterns(user_id=123)

# Access results
print(f"Accepted patterns: {result['accepted_patterns']}")
print(f"Rejected patterns: {result['rejected_patterns']}")
print(f"User preferences: {result['preferences']}")
```

### Updating Cached Patterns

```python
# Update cached patterns for a user
updated_count = analyzer.update_cached_patterns(user_id=123)
print(f"Updated {updated_count} pattern records")
```

### Retrieving Cached Patterns

```python
# Fast lookup from cache
cached = analyzer.get_cached_patterns(user_id=123)
print(f"Total patterns: {cached['statistics']['total_patterns']}")
```

### Getting Top Categories

```python
# Get top accepted categories
accepted = analyzer.get_top_accepted_categories(user_id=123, limit=5)
print(f"User prefers: {', '.join(accepted)}")

# Get top rejected categories
rejected = analyzer.get_top_rejected_categories(user_id=123, limit=5)
print(f"User dislikes: {', '.join(rejected)}")
```

## API Methods

### `analyze_user_patterns(user_id, recency_days=90, min_feedback_count=3)`

Analyzes user's feedback patterns to build personalized context.

**Parameters:**
- `user_id` (int): The ID of the user to analyze
- `recency_days` (int): Number of days to look back for feedback (default: 90)
- `min_feedback_count` (int): Minimum feedback count to consider a pattern (default: 3)

**Returns:**
```python
{
    'accepted_patterns': [
        {
            'category': 'security',
            'severity': 'critical',
            'count': 15,
            'acceptance_rate': 0.93,
            'accepted_count': 14,
            'rejected_count': 1,
            'examples': [...]
        }
    ],
    'rejected_patterns': [...],
    'neutral_patterns': [...],
    'preferences': {
        'prefers_categories': ['security', 'bug'],
        'dislikes_categories': ['style', 'naming'],
        'severity_preferences': {...},
        'prefers_detailed_explanations': True,
        'total_patterns_analyzed': 25
    },
    'statistics': {
        'total_feedback': 150,
        'total_accepted': 120,
        'total_rejected': 30,
        'overall_acceptance_rate': 0.80,
        'unique_patterns': 25,
        'recency_days': 90
    }
}
```

### `update_cached_patterns(user_id)`

Updates the cached feedback patterns in the database.

**Parameters:**
- `user_id` (int): The ID of the user to update patterns for

**Returns:**
- `int`: Number of pattern records updated/created

### `get_cached_patterns(user_id)`

Retrieves cached feedback patterns from the database (fast lookup).

**Parameters:**
- `user_id` (int): The ID of the user

**Returns:**
- Dictionary with accepted and rejected patterns

### `get_top_accepted_categories(user_id, limit=5)`

Gets the top categories that the user most frequently accepts.

**Parameters:**
- `user_id` (int): The ID of the user
- `limit` (int): Maximum number of categories to return

**Returns:**
- `List[str]`: List of category names

### `get_top_rejected_categories(user_id, limit=5)`

Gets the top categories that the user most frequently rejects.

**Parameters:**
- `user_id` (int): The ID of the user
- `limit` (int): Maximum number of categories to return

**Returns:**
- `List[str]`: List of category names

## Pattern Classification

Patterns are classified based on acceptance rate:

- **Accepted Pattern**: acceptance_rate >= 0.7 (70%)
- **Rejected Pattern**: acceptance_rate <= 0.3 (30%)
- **Neutral Pattern**: 0.3 < acceptance_rate < 0.7

## Performance Considerations

### Indexes

The table includes several indexes for optimal query performance:

- `idx_user_feedback_patterns_user`: Fast user lookups
- `idx_user_feedback_patterns_category`: Category filtering
- `idx_user_feedback_patterns_severity`: Severity filtering
- `idx_user_feedback_patterns_user_category`: Combined user+category queries
- `idx_user_feedback_patterns_acceptance`: Acceptance rate filtering
- `idx_user_feedback_patterns_updated`: Last updated queries

### Caching Strategy

1. **Real-time Analysis**: `analyze_user_patterns()` performs real-time aggregation
2. **Cached Patterns**: `update_cached_patterns()` stores results for fast retrieval
3. **Fast Lookup**: `get_cached_patterns()` reads from cache without aggregation

### Recommended Usage Pattern

```python
# Background job (daily or after significant feedback)
analyzer.update_cached_patterns(user_id)

# Real-time requests (fast)
patterns = analyzer.get_cached_patterns(user_id)
```

## Integration with Personalized AI

The analyzer output is designed to be used with the Personalized Prompt Builder:

```python
# Get patterns
patterns = analyzer.get_cached_patterns(user_id)

# Build personalized prompt
prompt = f"""
You are analyzing code for a user who:
- Prefers suggestions about: {', '.join(patterns['preferences']['prefers_categories'])}
- Dislikes suggestions about: {', '.join(patterns['preferences']['dislikes_categories'])}

Accepted patterns:
{format_patterns(patterns['accepted_patterns'])}

Rejected patterns:
{format_patterns(patterns['rejected_patterns'])}
"""
```

## Testing

### Run Migration

```bash
python backend/migrations/add_user_feedback_patterns_table.py
```

### Run Simple Tests

```bash
python backend/test_feedback_pattern_analyzer_simple.py
```

### Run Full Tests

```bash
python backend/test_feedback_pattern_analyzer.py
```

## Future Enhancements

1. **Time-based Weighting**: Weight recent feedback more heavily in calculations
2. **Confidence Scores**: Add confidence scores based on feedback volume
3. **Pattern Evolution**: Track how patterns change over time
4. **Cross-user Patterns**: Identify common patterns across similar users
5. **Automatic Updates**: Trigger pattern updates after N new feedback items

## Troubleshooting

### No Patterns Found

If `analyze_user_patterns()` returns empty results:
- Check that the user has provided feedback
- Verify feedback records have associated issues with categories
- Ensure feedback is within the recency window (default: 90 days)
- Check that patterns meet the minimum feedback count (default: 3)

### Slow Queries

If pattern analysis is slow:
- Verify all indexes are created
- Consider reducing `recency_days` parameter
- Use cached patterns instead of real-time analysis
- Check database query performance with EXPLAIN

### Stale Cache

If cached patterns are outdated:
- Run `update_cached_patterns()` for the user
- Consider implementing automatic cache refresh
- Check `last_updated` timestamp in the database
