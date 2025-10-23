# PersonalizedPromptBuilder Service

## Overview

The `PersonalizedPromptBuilder` service enables personalized AI code analysis by learning from user feedback history. It builds customized prompts that align with individual user preferences, improving suggestion relevance and acceptance rates.

## Requirements Coverage

This implementation covers the following requirements:

- **8.3**: When the user triggers a new code review, the AI prompt includes a summary of the user's historical feedback patterns
- **8.4**: When the AI generates suggestions, it considers the user's past acceptance/rejection patterns for similar issue types
- **8.5**: When the user consistently rejects certain types of suggestions, the AI reduces emphasis on those patterns
- **8.6**: When the user consistently accepts certain types of suggestions, the AI prioritizes similar patterns
- **8.7**: When building the AI context, the system includes the user's relevant feedback examples (no limit, configurable)
- **8.10**: When generating the personalized prompt, it includes specific examples of what the user likes and dislikes

## Features

### 1. Feedback History Retrieval
- Fetches all user feedback with associated issue details
- Separates accepted vs rejected suggestions
- No limit on examples (configurable via `max_examples` parameter)
- Includes feedback comments and context

### 2. Recency Weighting
- Recent feedback (last 30 days by default) weighted 2x more heavily
- Configurable recency window via `recency_weight_days` parameter
- Ensures current preferences take priority over older patterns

### 3. Personalized Context Building
- Identifies top accepted and rejected categories
- Formats examples with clear structure
- Builds preference summary with statistics
- Highlights recent feedback with `[RECENT]` markers

### 4. Prompt Generation
- Combines base prompt with personalized context
- Includes user-specific instructions for the AI
- Provides concrete examples of accepted/rejected suggestions
- Maintains code quality standards while respecting preferences

### 5. Personalization Summary
- Quick check for personalization availability
- Returns statistics without building full prompt
- Useful for UI indicators and decision-making

## API Reference

### Class: `PersonalizedPromptBuilder`

#### `__init__(db: Session)`
Initialize the builder with a database session.

```python
from app.services.personalized_prompt_builder import PersonalizedPromptBuilder

builder = PersonalizedPromptBuilder(db)
```

#### `build_personalized_prompt(user_id, base_prompt, code, language, max_examples=None, recency_weight_days=30)`
Build a complete personalized prompt for AI analysis.

**Parameters:**
- `user_id` (int): User ID
- `base_prompt` (str): Base system prompt
- `code` (str): Code to analyze
- `language` (str): Programming language
- `max_examples` (int, optional): Maximum examples per category (None = no limit)
- `recency_weight_days` (int): Days for recency weighting (default: 30)

**Returns:** Complete personalized prompt string

**Example:**
```python
prompt = builder.build_personalized_prompt(
    user_id=1,
    base_prompt="You are a code review assistant...",
    code="def test(): pass",
    language="python",
    max_examples=10  # Limit to 10 examples per category
)
```

#### `fetch_feedback_history(user_id, max_examples=None, recency_weight_days=30)`
Fetch user's feedback history with recency weighting.

**Parameters:**
- `user_id` (int): User ID
- `max_examples` (int, optional): Maximum examples per category
- `recency_weight_days` (int): Days for recency weighting

**Returns:** Dictionary with:
- `accepted_examples`: List of accepted suggestions
- `rejected_examples`: List of rejected suggestions
- `recent_feedback_count`: Count of recent feedback
- `total_feedback_count`: Total feedback count
- `has_feedback`: Boolean indicating if feedback exists

**Example:**
```python
history = builder.fetch_feedback_history(
    user_id=1,
    max_examples=10,
    recency_weight_days=30
)

if history['has_feedback']:
    print(f"Total: {history['total_feedback_count']}")
    print(f"Recent: {history['recent_feedback_count']}")
```

#### `build_personalized_context(feedback_history)`
Build personalized context from feedback history.

**Parameters:**
- `feedback_history` (dict): Dictionary from `fetch_feedback_history()`

**Returns:** Dictionary with:
- `accepted_categories`: Categories user frequently accepts
- `rejected_categories`: Categories user frequently rejects
- `accepted_examples_text`: Formatted accepted examples
- `rejected_examples_text`: Formatted rejected examples
- `preference_summary`: Summary of user preferences
- `has_recent_feedback`: Boolean for recent feedback

**Example:**
```python
history = builder.fetch_feedback_history(user_id=1)
context = builder.build_personalized_context(history)

print(f"Accepts: {context['accepted_categories']}")
print(f"Rejects: {context['rejected_categories']}")
```

#### `get_personalization_summary(user_id)`
Get a summary of personalization data available for a user.

**Parameters:**
- `user_id` (int): User ID

**Returns:** Dictionary with:
- `has_personalization`: Boolean
- `total_feedback`: Total feedback count
- `recent_feedback`: Recent feedback count
- `accepted_count`: Number of accepted examples
- `rejected_count`: Number of rejected examples
- `top_accepted_categories`: Top 3 accepted categories
- `top_rejected_categories`: Top 3 rejected categories
- `has_recent_feedback`: Boolean
- `message`: Status message

**Example:**
```python
summary = builder.get_personalization_summary(user_id=1)

if summary['has_personalization']:
    print(f"✓ Personalization available")
    print(f"  Top accepts: {summary['top_accepted_categories']}")
    print(f"  Top rejects: {summary['top_rejected_categories']}")
else:
    print(f"✗ {summary['message']}")
```

## Integration with AI Service

### Basic Integration

```python
from app.services.personalized_prompt_builder import PersonalizedPromptBuilder

def analyze_code_with_personalization(
    code: str,
    language: str,
    user_id: int,
    db: Session
):
    # Initialize builder
    prompt_builder = PersonalizedPromptBuilder(db)
    
    # Base system prompt
    base_prompt = """You are a code review assistant. Analyze code and provide:
    1. Clear problem descriptions
    2. Specific solutions
    3. Code examples"""
    
    # Build personalized prompt
    personalized_prompt = prompt_builder.build_personalized_prompt(
        user_id=user_id,
        base_prompt=base_prompt,
        code=code,
        language=language,
        max_examples=10  # Limit for token efficiency
    )
    
    # Call AI service with personalized prompt
    response = ai_service.analyze(personalized_prompt)
    
    return response
```

### Advanced Integration with Fallback

```python
def analyze_code_with_optional_personalization(
    code: str,
    language: str,
    user_id: int,
    db: Session
):
    prompt_builder = PersonalizedPromptBuilder(db)
    
    # Check if personalization is available
    summary = prompt_builder.get_personalization_summary(user_id)
    
    base_prompt = "You are a code review assistant..."
    
    if summary['has_personalization']:
        # Use personalized prompt
        prompt = prompt_builder.build_personalized_prompt(
            user_id=user_id,
            base_prompt=base_prompt,
            code=code,
            language=language,
            max_examples=10
        )
        
        response = ai_service.analyze(prompt)
        response['personalized'] = True
        response['personalization_info'] = {
            'total_feedback': summary['total_feedback'],
            'recent_feedback': summary['recent_feedback'],
            'top_accepted': summary['top_accepted_categories'],
            'top_rejected': summary['top_rejected_categories']
        }
    else:
        # Use base prompt without personalization
        prompt = f"{base_prompt}\n\nCode:\n{code}"
        response = ai_service.analyze(prompt)
        response['personalized'] = False
    
    return response
```

## Prompt Structure

The generated personalized prompt includes:

1. **Base Prompt**: Original system instructions
2. **Personalized Context Section**:
   - User name and preference summary
   - Categories user accepts
   - Categories user rejects
   - Examples of accepted suggestions (with [RECENT] markers)
   - Examples of rejected suggestions
3. **Personalization Instructions**:
   - Prioritize accepted categories
   - Minimize rejected categories
   - Match style of accepted examples
   - Weight recent feedback more heavily
4. **Code to Analyze**: The actual code with language specification

### Example Output Structure

```
You are a code review assistant...

## PERSONALIZED CONTEXT FOR USER NAME

This user has provided 15 pieces of feedback with 8 in the last 30 days (weighted more heavily). Overall acceptance rate: 73%.

### Categories This User ACCEPTS:
security, performance, error_handling

### Categories This User REJECTS:
style, naming

### Examples of Suggestions This User ACCEPTED:
1. Category: security, Severity: critical, Pattern: sql_injection [RECENT]
   Suggestion: Use parameterized queries...
   Feedback: accept
   Comment: Good catch, this is important

[... more examples ...]

### Examples of Suggestions This User REJECTED:
1. Category: style, Severity: low, Pattern: whitespace
   Suggestion: Add whitespace around operators...
   Feedback: reject
   Comment: I prefer compact code

[... more examples ...]

## PERSONALIZATION INSTRUCTIONS

Based on the above feedback history:
1. PRIORITIZE suggestions in categories the user accepts: security, performance, error_handling
2. MINIMIZE or carefully justify suggestions in categories the user rejects: style, naming
3. Match the style and detail level demonstrated in accepted examples
4. Pay special attention to RECENT feedback (marked [RECENT]) as it reflects current preferences
5. Provide suggestions similar in structure and tone to those the user has accepted before

## CODE TO ANALYZE

Language: python

```python
[code here]
```

Now analyze the above code with the personalized context in mind...
```

## Recency Weighting

The service implements recency weighting to prioritize current user preferences:

- **Recent feedback** (last 30 days by default): Weight = 2.0
- **Older feedback**: Weight = 1.0

This ensures that:
- Recent preferences take priority in category ranking
- Recent examples appear first in the prompt
- User's evolving preferences are respected
- The AI adapts to changing coding standards

## Configuration Options

### No Limit on Examples (Default)

```python
# Include all feedback examples
prompt = builder.build_personalized_prompt(
    user_id=user_id,
    base_prompt=base_prompt,
    code=code,
    language=language
    # max_examples=None (default)
)
```

### Limited Examples (Token Optimization)

```python
# Limit to 10 examples per category
prompt = builder.build_personalized_prompt(
    user_id=user_id,
    base_prompt=base_prompt,
    code=code,
    language=language,
    max_examples=10
)
```

### Custom Recency Window

```python
# Consider last 60 days as "recent"
prompt = builder.build_personalized_prompt(
    user_id=user_id,
    base_prompt=base_prompt,
    code=code,
    language=language,
    recency_weight_days=60
)
```

## Error Handling

The service handles edge cases gracefully:

1. **User not found**: Returns base prompt without personalization
2. **No feedback history**: Returns base prompt without personalization
3. **Database errors**: Logs error and falls back to base prompt
4. **Invalid parameters**: Validates and uses defaults

## Performance Considerations

- **Caching**: Consider caching personalization summaries (5-minute TTL)
- **Database queries**: Optimized with proper indexes on feedback_records
- **Token usage**: Use `max_examples` to limit prompt size for API efficiency
- **Async processing**: Can be made async for better performance

## Testing

Run the test suite:

```bash
python backend/test_personalized_prompt_builder.py
```

Run usage examples:

```bash
python backend/example_personalized_prompt_usage.py
```

## Dependencies

- SQLAlchemy (database ORM)
- FeedbackPatternAnalyzer (for pattern analysis)
- Database models: User, FeedbackRecord, Issue, UserFeedbackPattern

## Future Enhancements

Potential improvements:

1. **Caching layer**: Cache personalized contexts with TTL
2. **A/B testing**: Compare personalized vs non-personalized results
3. **Feedback quality scoring**: Weight high-quality feedback more heavily
4. **Multi-language support**: Localize prompt text
5. **Category weighting**: Allow users to explicitly prioritize categories
6. **Team preferences**: Incorporate team-level preferences
7. **Async support**: Make all methods async for better performance

## Related Services

- `FeedbackPatternAnalyzer`: Analyzes and caches feedback patterns
- `AIService`: Consumes personalized prompts for code analysis
- `FeedbackService`: Collects user feedback on suggestions

## License

Part of the CodeNova project.
