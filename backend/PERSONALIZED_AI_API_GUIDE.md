# Personalized AI Analysis API Guide

## Overview

The Personalized AI Analysis API provides code review capabilities that learn from user feedback to deliver increasingly relevant and accurate suggestions over time.

## Base URL

```
/api/v1/ai
```

## Authentication

All endpoints require JWT authentication via Bearer token:

```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Analyze Code with Learning

Performs AI-powered code analysis with personalization based on user's feedback history.

**Endpoint**: `POST /api/v1/ai/analyze-with-learning`

**Request Body**:
```json
{
  "code": "def example():\n    pass",
  "language": "python",
  "filename": "example.py"  // optional
}
```

**Request Validation**:
- `code`: Required, 1-100,000 characters, max 2000 lines
- `language`: Required, must be supported language (python, javascript, typescript, etc.)
- `filename`: Optional, max 255 characters

**Response** (200 OK):
```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "issues": [
    {
      "id": "issue-abc123",
      "line": 5,
      "column": 1,
      "severity": "warning",
      "message": "Variable 'x' is assigned but never used",
      "rule": "gemini-ai-personalized",
      "category": "ai-review-personalized",
      "suggestion": "Remove the unused variable or use it in your code. Example: del x",
      "personalized": true,
      "ast_context": {
        "function_name": "example",
        "scope": "local"
      }
    }
  ],
  "metrics": {
    "lines_of_code": 150,
    "total_lines": 200,
    "complexity": 12,
    "maintainability_index": 75,
    "duplicate_lines": 0,
    "test_coverage": null
  },
  "summary": "Analyzed 150 lines of python code with personalized AI learning (based on 45 feedback items, 12 recent). Found 3 issues (1 error, 2 warnings). Complexity score: 12. Maintainability: 75%.",
  "created_at": "2025-10-15T01:00:00.000Z",
  "completed_at": "2025-10-15T01:00:02.500Z",
  "language": "python",
  "filename": "example.py",
  "personalization_info": {
    "enabled": true,
    "total_feedback": 45,
    "recent_feedback": 12,
    "accepted_count": 30,
    "rejected_count": 15,
    "top_accepted_categories": ["security", "performance", "best-practices"],
    "top_rejected_categories": ["style", "naming"],
    "message": "Personalization available with 45 feedback items"
  },
  "processing_time_ms": 2500
}
```

**Error Responses**:

- `413 Payload Too Large`: Code exceeds 100KB limit
```json
{
  "detail": "Code content too large: 150.5KB. Maximum allowed: 100KB"
}
```

- `422 Unprocessable Entity`: Validation error
```json
{
  "detail": "Validation error: Code content cannot be empty or only whitespace"
}
```

- `500 Internal Server Error`: Analysis failed
```json
{
  "detail": "Personalized code analysis failed: <error message>"
}
```

**Personalization Behavior**:

When `personalization_info.enabled` is `true`:
- AI prioritizes issue categories user typically accepts
- AI minimizes categories user typically rejects
- Suggestions match style of previously accepted feedback
- Recent feedback (last 30 days) weighted 2x more heavily

When `personalization_info.enabled` is `false`:
- User has no feedback history yet
- Standard AI analysis is performed
- Suggestions follow default patterns

### 2. Get Personalization Status

Retrieves personalization information for the current user without performing analysis.

**Endpoint**: `GET /api/v1/ai/personalization-status`

**Response** (200 OK):
```json
{
  "user_id": 123,
  "personalization": {
    "has_personalization": true,
    "total_feedback": 45,
    "recent_feedback": 12,
    "accepted_count": 30,
    "rejected_count": 15,
    "top_accepted_categories": ["security", "performance", "best-practices"],
    "top_rejected_categories": ["style", "naming"],
    "has_recent_feedback": true,
    "message": "Personalization available with 45 feedback items"
  }
}
```

**When No Personalization Available**:
```json
{
  "user_id": 123,
  "personalization": {
    "has_personalization": false,
    "total_feedback": 0,
    "recent_feedback": 0,
    "message": "No feedback history available for personalization"
  }
}
```

**Use Cases**:
- Check if personalization is available before analysis
- Display personalization badge in UI
- Show user their feedback statistics
- Encourage users to provide feedback

## Supported Languages

The following programming languages are supported:

- `python`
- `javascript`
- `typescript`
- `java`
- `cpp` (C++)
- `c`
- `csharp` (C#)
- `go`
- `rust`
- `php`
- `ruby`
- `swift`
- `kotlin`
- `scala`
- `html`
- `css`
- `sql`
- `json`
- `yaml`
- `xml`
- `markdown`
- `shell`
- `bash`

## Issue Severity Levels

Issues are categorized by severity:

- `error`: Critical issues that must be fixed
- `warning`: Important issues that should be addressed
- `info`: Informational suggestions for improvement
- `suggestion`: Optional enhancements

## Personalization Algorithm

### Feedback Collection
1. User provides feedback on AI suggestions (accept/reject/modify)
2. Feedback stored with issue category, severity, and context
3. Feedback patterns analyzed and cached

### Recency Weighting
- Feedback from last 30 days: **2x weight**
- Older feedback: **1x weight**
- Ensures current preferences take precedence

### Context Building
1. Fetch user's feedback history
2. Separate into accepted vs rejected examples
3. Group by category and severity
4. Select top 10 examples per category
5. Build personalized prompt context

### AI Prompt Enhancement
The personalized prompt includes:
- User's acceptance/rejection patterns
- Top accepted categories (prioritize these)
- Top rejected categories (minimize these)
- Specific examples of liked suggestions
- Specific examples of disliked suggestions
- Preference summary and statistics

### Suggestion Generation
AI generates suggestions that:
- Focus on categories user values
- Avoid or justify categories user dislikes
- Match style of accepted suggestions
- Provide unique, contextual advice
- Include specific implementation guidance

## Integration Examples

### JavaScript/React

```javascript
import axios from 'axios';

// Analyze code with personalization
async function analyzeCode(code, language) {
  try {
    const response = await axios.post(
      '/api/v1/ai/analyze-with-learning',
      {
        code,
        language,
        filename: 'example.py'
      },
      {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      }
    );
    
    const { data } = response;
    
    // Check if personalization was applied
    if (data.personalization_info.enabled) {
      console.log('✨ Personalized analysis applied!');
      console.log(`Based on ${data.personalization_info.total_feedback} feedback items`);
    }
    
    // Display issues
    data.issues.forEach(issue => {
      console.log(`[${issue.severity}] Line ${issue.line}: ${issue.message}`);
      console.log(`Fix: ${issue.suggestion}`);
      if (issue.personalized) {
        console.log('💡 Personalized suggestion');
      }
    });
    
    return data;
    
  } catch (error) {
    if (error.response?.status === 413) {
      console.error('Code is too large (max 100KB)');
    } else if (error.response?.status === 422) {
      console.error('Validation error:', error.response.data.detail);
    } else {
      console.error('Analysis failed:', error.message);
    }
    throw error;
  }
}

// Check personalization status
async function checkPersonalization() {
  const response = await axios.get(
    '/api/v1/ai/personalization-status',
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    }
  );
  
  const { personalization } = response.data;
  
  if (personalization.has_personalization) {
    return {
      available: true,
      feedbackCount: personalization.total_feedback,
      recentCount: personalization.recent_feedback,
      topCategories: personalization.top_accepted_categories
    };
  }
  
  return { available: false };
}
```

### Python

```python
import requests

def analyze_code_with_learning(code: str, language: str, token: str):
    """Analyze code with personalized AI learning."""
    
    response = requests.post(
        'http://localhost:8000/api/v1/ai/analyze-with-learning',
        json={
            'code': code,
            'language': language,
            'filename': 'example.py'
        },
        headers={
            'Authorization': f'Bearer {token}'
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # Check personalization
        if data['personalization_info']['enabled']:
            print(f"✨ Personalized analysis applied!")
            print(f"Based on {data['personalization_info']['total_feedback']} feedback items")
        
        # Display issues
        for issue in data['issues']:
            print(f"[{issue['severity']}] Line {issue['line']}: {issue['message']}")
            print(f"Fix: {issue['suggestion']}")
            if issue.get('personalized'):
                print("💡 Personalized suggestion")
        
        return data
    
    elif response.status_code == 413:
        print("Error: Code is too large (max 100KB)")
    elif response.status_code == 422:
        print(f"Validation error: {response.json()['detail']}")
    else:
        print(f"Analysis failed: {response.text}")
    
    return None

def check_personalization_status(token: str):
    """Check if personalization is available for user."""
    
    response = requests.get(
        'http://localhost:8000/api/v1/ai/personalization-status',
        headers={
            'Authorization': f'Bearer {token}'
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        personalization = data['personalization']
        
        if personalization['has_personalization']:
            print(f"Personalization available!")
            print(f"Total feedback: {personalization['total_feedback']}")
            print(f"Recent feedback: {personalization['recent_feedback']}")
            print(f"Top accepted: {', '.join(personalization['top_accepted_categories'])}")
            return True
        else:
            print("No personalization available yet. Provide feedback to enable!")
            return False
    
    return False
```

## Best Practices

### For Frontend Developers

1. **Check Personalization Status First**
   - Call `/personalization-status` before analysis
   - Show badge if personalization available
   - Encourage users to provide feedback

2. **Display Personalization Info**
   - Show when personalized analysis is used
   - Display user's preference statistics
   - Highlight personalized suggestions

3. **Handle Errors Gracefully**
   - Show user-friendly error messages
   - Provide retry options for network errors
   - Validate code size before sending

4. **Optimize Performance**
   - Debounce analysis requests
   - Show loading indicators
   - Cache results when appropriate

### For Backend Developers

1. **Monitor Performance**
   - Track analysis processing times
   - Monitor personalization query performance
   - Cache personalization contexts (5-min TTL)

2. **Handle Edge Cases**
   - Users with no feedback history
   - Very large feedback histories
   - API key failures

3. **Maintain Data Quality**
   - Validate feedback data
   - Clean up old feedback periodically
   - Monitor feedback patterns

## Rate Limiting

- **Standard Users**: 100 requests per hour
- **Premium Users**: 1000 requests per hour
- **Enterprise**: Unlimited

Rate limit headers included in response:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1634567890
```

## Changelog

### Version 1.0.0 (2025-10-15)
- Initial release
- Personalized analysis endpoint
- Personalization status endpoint
- Support for 24 programming languages
- Recency-weighted feedback learning
- AST-enhanced analysis

## Support

For issues or questions:
- GitHub Issues: [repository]/issues
- Email: support@codenova.com
- Documentation: https://docs.codenova.com/ai-api
