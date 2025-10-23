# API Routes Summary - Dashboard and Settings Improvements

This document summarizes all API routes created for the dashboard and settings improvements feature.

## Analytics Endpoints (`/api/v1/analytics`)

### User Statistics
- **GET** `/api/v1/analytics/user-stats`
  - Get user statistics including total reviews, analyses, success rate, and recent activity
  - Authentication: Required
  - Requirements: 1.1, 1.3, 1.4, 1.5, 1.6

### Usage Trends
- **GET** `/api/v1/analytics/usage-trends?timeframe={7d|30d|90d|1y}`
  - Get usage trends over time for the current user
  - Query Parameters:
    - `timeframe`: Time period (7d, 30d, 90d, 1y)
  - Authentication: Required
  - Requirements: 1.3, 1.4, 1.5

### Feedback Distribution
- **GET** `/api/v1/analytics/feedback-distribution?timeframe={7d|30d|90d|1y}`
  - Get feedback distribution by type for the current user
  - Query Parameters:
    - `timeframe`: Time period (7d, 30d, 90d, 1y)
  - Authentication: Required
  - Requirements: 1.4, 1.5, 1.6

### Additional Analytics Endpoints
- **GET** `/api/v1/analytics/acceptance-rates`
- **GET** `/api/v1/analytics/rejection-patterns`
- **GET** `/api/v1/analytics/usage-statistics`
- **GET** `/api/v1/analytics/learning-progress`
- **GET** `/api/v1/analytics/dashboard`
- **POST** `/api/v1/analytics/export`
- **WebSocket** `/api/v1/analytics/ws/real-time`
- **GET** `/api/v1/analytics/health`

## Feedback Statistics Endpoints (`/api/v1/feedback`)

### Feedback Statistics
- **GET** `/api/v1/feedback/statistics?timeframe={week|month|quarter|year}`
  - Get comprehensive feedback statistics with timeframe parameter
  - Provides:
    - Aggregation queries for feedback by type (accept/reject/modify)
    - Feedback trends over time periods
    - Model performance metrics based on feedback data
  - Query Parameters:
    - `timeframe`: Time period (week, month, quarter, year)
  - Authentication: Required
  - Requirements: 2.2, 2.3, 2.4, 2.5

### Additional Feedback Endpoints
- **POST** `/api/v1/feedback/feedback` - Submit feedback
- **GET** `/api/v1/feedback/stats` - Get feedback stats
- **GET** `/api/v1/feedback/history` - Get user feedback history
- **POST** `/api/v1/feedback/bulk` - Submit bulk feedback
- **GET** `/api/v1/feedback/{issue_id}` - Get feedback for issue
- **POST** `/api/v1/feedback/{feedback_id}/validate` - Validate feedback (admin)
- **GET** `/api/v1/feedback/trends` - Get feedback trends

## User Profile Endpoints (`/api/v1/users`)

### Current User Profile
- **GET** `/api/v1/users/profile`
  - Get current user's profile information
  - Authentication: Required
  - Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.5

- **PUT** `/api/v1/users/profile`
  - Update current user's profile information
  - Request Body: UserProfileUpdate
    - firstName, lastName, email, jobTitle, bio, programmingLanguages
  - Authentication: Required
  - Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.8, 6.5

### Profile Picture
- **POST** `/api/v1/users/profile-picture`
  - Upload profile picture for current user
  - Request: multipart/form-data with image file
  - Validation: Image type, max 5MB
  - Authentication: Required
  - Requirements: 5.7, 9.1

### User Preferences
- **GET** `/api/v1/users/preferences`
  - Get current user's preferences
  - Authentication: Required
  - Requirements: 4.2, 4.3, 6.4

- **PUT** `/api/v1/users/preferences`
  - Update current user's preferences
  - Request Body: UserPreferences
    - theme, language, defaultProgrammingLanguage, aiModel, etc.
  - Authentication: Required
  - Requirements: 4.2, 4.3, 6.4

### Notification Preferences
- **GET** `/api/v1/users/notifications`
  - Get current user's notification preferences
  - Authentication: Required
  - Requirements: 4.4, 6.4

- **PUT** `/api/v1/users/notifications`
  - Update current user's notification preferences
  - Request Body: NotificationPreferences
    - emailNotifications, pushNotifications, frequency
  - Authentication: Required
  - Requirements: 4.4, 6.4

### User-Specific Endpoints (with user_id)
- **GET** `/api/v1/users/{user_id}/profile`
- **PUT** `/api/v1/users/{user_id}/profile`
- **GET** `/api/v1/users/{user_id}/preferences`
- **PUT** `/api/v1/users/{user_id}/preferences`
- **PUT** `/api/v1/users/{user_id}/notifications`
- **PUT** `/api/v1/users/{user_id}/password`
- **POST** `/api/v1/users/{user_id}/profile-picture`
- **DELETE** `/api/v1/users/{user_id}/profile-picture`
- **GET** `/api/v1/users/{user_id}/theme`
- **PUT** `/api/v1/users/{user_id}/theme`
- **GET** `/api/v1/users/{user_id}/settings`
- **PUT** `/api/v1/users/{user_id}/settings`

## API Key Management Endpoints (`/api/v1/users`)

### API Key Status
- **GET** `/api/v1/users/api-key`
  - Check if user has a Gemini API key configured
  - Returns: `{ hasKey: boolean, keyPreview: string }`
  - Authentication: Required
  - Requirements: 4.8, 6.6

### Save API Key
- **PUT** `/api/v1/users/api-key`
  - Save encrypted Gemini API key for the current user
  - Request Body: `{ apiKey: string }`
  - Validation: Minimum 10 characters
  - Authentication: Required
  - Requirements: 4.8, 4.9, 6.7, 6.8

### Delete API Key
- **DELETE** `/api/v1/users/api-key`
  - Delete user's Gemini API key
  - Authentication: Required
  - Requirements: 4.8, 6.8

## Personalized AI Analysis Endpoints (`/api/v1/ai`)

### Analyze with Learning
- **POST** `/api/v1/ai/analyze-with-learning`
  - Analyze code with personalized AI learning from user feedback history
  - Request Body: PersonalizedAnalysisRequest
    - code: string (max 100KB)
    - language: string
    - filename: string (optional)
  - Response: PersonalizedAnalysisResponse
    - analysis_id, status, issues, metrics, summary
    - personalization_info with feedback statistics
  - Authentication: Required
  - Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 8.3, 8.4, 8.5, 8.6

### Personalization Status
- **GET** `/api/v1/ai/personalization-status`
  - Get personalization status for the current user
  - Returns feedback statistics and personalization availability
  - Authentication: Required
  - Requirements: 8.10

## Authentication and Authorization

All endpoints require authentication via JWT Bearer token in the Authorization header:
```
Authorization: Bearer <token>
```

### Access Control
- **User endpoints**: Users can only access their own data (except admins)
- **Admin endpoints**: Some analytics and feedback endpoints support admin access to other users' data via `user_id` query parameter
- **API key endpoints**: Users can only manage their own API keys

## Error Responses

All endpoints follow standard HTTP status codes:
- `200 OK` - Successful GET request
- `201 Created` - Successful POST request
- `400 Bad Request` - Invalid input or validation error
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `413 Payload Too Large` - Request body too large
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

Error response format:
```json
{
  "detail": "Error message description"
}
```

## Requirements Coverage

This implementation covers the following requirements:

### Requirement 6.1: User Statistics API
✅ `/api/v1/analytics/user-stats` - Returns accurate counts of reviews, analyses, and feedback

### Requirement 6.2: Dashboard Data API
✅ `/api/v1/analytics/usage-trends` - Returns real-time metrics calculated from database
✅ `/api/v1/analytics/feedback-distribution` - Returns feedback distribution data

### Requirement 6.3: Feedback Statistics API
✅ `/api/v1/feedback/statistics` - Returns aggregated feedback data by type and time period

### Requirement 6.4: User Preferences API
✅ `/api/v1/users/preferences` (GET/PUT) - Validates and persists user preferences
✅ `/api/v1/users/notifications` (GET/PUT) - Validates and persists notification preferences

### Requirement 6.5: User Profile API
✅ `/api/v1/users/profile` (GET/PUT) - Validates and persists profile changes
✅ `/api/v1/users/profile-picture` (POST) - Handles profile picture uploads

### Requirement 6.6: API Key Retrieval
✅ `/api/v1/users/api-key` (GET) - Returns API key status securely

### Requirement 6.7: API Key Storage
✅ `/api/v1/users/api-key` (PUT) - Validates and stores encrypted API key

### Requirement 6.8: API Key Usage
✅ AI service integration uses user-provided API key when available

## Testing

To test these endpoints, use the following curl commands:

### Test Analytics Endpoints
```bash
# Get user stats
curl -X GET "http://localhost:8000/api/v1/analytics/user-stats" \
  -H "Authorization: Bearer <token>"

# Get usage trends
curl -X GET "http://localhost:8000/api/v1/analytics/usage-trends?timeframe=30d" \
  -H "Authorization: Bearer <token>"

# Get feedback distribution
curl -X GET "http://localhost:8000/api/v1/analytics/feedback-distribution?timeframe=30d" \
  -H "Authorization: Bearer <token>"
```

### Test Feedback Statistics
```bash
# Get feedback statistics
curl -X GET "http://localhost:8000/api/v1/feedback/statistics?timeframe=week" \
  -H "Authorization: Bearer <token>"
```

### Test User Profile
```bash
# Get profile
curl -X GET "http://localhost:8000/api/v1/users/profile" \
  -H "Authorization: Bearer <token>"

# Update profile
curl -X PUT "http://localhost:8000/api/v1/users/profile" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "jobTitle": "Software Engineer"
  }'
```

### Test Preferences
```bash
# Get preferences
curl -X GET "http://localhost:8000/api/v1/users/preferences" \
  -H "Authorization: Bearer <token>"

# Update preferences
curl -X PUT "http://localhost:8000/api/v1/users/preferences" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "dark",
    "language": "en",
    "defaultProgrammingLanguage": "javascript"
  }'
```

### Test API Key Management
```bash
# Check API key status
curl -X GET "http://localhost:8000/api/v1/users/api-key" \
  -H "Authorization: Bearer <token>"

# Save API key
curl -X PUT "http://localhost:8000/api/v1/users/api-key" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "apiKey": "your-gemini-api-key-here"
  }'

# Delete API key
curl -X DELETE "http://localhost:8000/api/v1/users/api-key" \
  -H "Authorization: Bearer <token>"
```

### Test Personalized AI Analysis
```bash
# Analyze code with learning
curl -X POST "http://localhost:8000/api/v1/ai/analyze-with-learning" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "function test() { console.log(\"hello\"); }",
    "language": "javascript",
    "filename": "test.js"
  }'

# Get personalization status
curl -X GET "http://localhost:8000/api/v1/ai/personalization-status" \
  -H "Authorization: Bearer <token>"
```

## Notes

1. All routes are properly authenticated using JWT tokens via the `get_current_user` dependency
2. Authorization checks ensure users can only access their own data (except admins)
3. Input validation is performed on all request bodies
4. Error handling provides clear error messages
5. All endpoints are documented with requirements coverage
6. Routes are organized by feature area for maintainability
