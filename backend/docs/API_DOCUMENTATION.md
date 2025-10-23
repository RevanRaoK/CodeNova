# CodeNova API Documentation

## Overview

This document provides comprehensive API documentation for the CodeNova Intelligent Code Review Bot platform. All endpoints require authentication unless otherwise specified.

## Base URL

```
Development: http://localhost:8000/api/v1
Production: https://api.code-nova.tech/api/v1
```

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Obtain Token

**POST** `/auth/login`

```json
Request:
{
  "username": "user@example.com",
  "password": "your_password"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "role": "user"
  }
}
```

---

## File Upload Endpoints

### Upload Multiple Files

**POST** `/files/upload-batch`

Upload one or more source code files for analysis.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Multiple files with key `files`

```bash
curl -X POST http://localhost:8000/api/v1/files/upload-batch \
  -H "Authorization: Bearer <token>" \
  -F "files=@src/main.py" \
  -F "files=@src/utils.py"
```

**Response:**
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "files": [
    {
      "file_id": "660e8400-e29b-41d4-a716-446655440001",
      "filename": "main.py",
      "status": "queued",
      "size_bytes": 2048
    },
    {
      "file_id": "660e8400-e29b-41d4-a716-446655440002",
      "filename": "utils.py",
      "status": "queued",
      "size_bytes": 1536
    }
  ],
  "total_files": 2,
  "queued_count": 2
}
```

**Status Codes:**
- `200 OK` - Files uploaded successfully
- `400 Bad Request` - Invalid file type or size exceeded
- `401 Unauthorized` - Missing or invalid token
- `413 Payload Too Large` - File size exceeds limit

### Get Batch Status

**GET** `/files/batch/{batch_id}/status`

Get the current status of a file batch upload.

**Response:**
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "total_files": 2,
  "completed_files": 1,
  "failed_files": 0,
  "files": [
    {
      "file_id": "660e8400-e29b-41d4-a716-446655440001",
      "filename": "main.py",
      "status": "completed",
      "analysis_id": "770e8400-e29b-41d4-a716-446655440003"
    },
    {
      "file_id": "660e8400-e29b-41d4-a716-446655440002",
      "filename": "utils.py",
      "status": "processing",
      "analysis_id": null
    }
  ]
}
```

### List User Files

**GET** `/files/list`

Get a list of all files uploaded by the current user.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 50)
- `status` (optional): Filter by status (queued, processing, completed, failed)

**Response:**
```json
{
  "files": [
    {
      "file_id": "660e8400-e29b-41d4-a716-446655440001",
      "filename": "main.py",
      "original_filename": "main.py",
      "file_size": 2048,
      "language": "python",
      "status": "completed",
      "created_at": "2025-10-22T10:30:00Z",
      "analysis_id": "770e8400-e29b-41d4-a716-446655440003"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 50
}
```

---

## Analysis Endpoints

### Analyze Code (Monaco Editor)

**POST** `/analysis/analyze-code`

Submit code from the Monaco editor for analysis.

**Request:**
```json
{
  "code": "def hello():\n    print('Hello, World!')",
  "language": "python",
  "filename": "hello.py"
}
```

**Response:**
```json
{
  "analysis_id": "880e8400-e29b-41d4-a716-446655440004",
  "status": "processing",
  "filename": "hello.py",
  "created_at": "2025-10-22T10:35:00Z"
}
```

### Get Analysis History

**GET** `/analysis/direct/history`

Get the user's analysis history with filenames.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)
- `status` (optional): Filter by status
- `filename` (optional): Filter by filename

**Response:**
```json
{
  "analyses": [
    {
      "analysis_id": "880e8400-e29b-41d4-a716-446655440004",
      "filename": "hello.py",
      "language": "python",
      "status": "completed",
      "issues_count": 3,
      "created_at": "2025-10-22T10:35:00Z",
      "completed_at": "2025-10-22T10:35:15Z"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 20
}
```

### Get Analysis Details

**GET** `/analysis/direct/{analysis_id}`

Get detailed results for a specific analysis.

**Response:**
```json
{
  "analysis_id": "880e8400-e29b-41d4-a716-446655440004",
  "filename": "hello.py",
  "language": "python",
  "status": "completed",
  "code": "def hello():\n    print('Hello, World!')",
  "created_at": "2025-10-22T10:35:00Z",
  "completed_at": "2025-10-22T10:35:15Z",
  "issues": [
    {
      "issue_id": "990e8400-e29b-41d4-a716-446655440005",
      "type": "style",
      "severity": "low",
      "message": "Missing docstring",
      "line_number": 1,
      "suggestion": "Add a docstring to describe the function",
      "code_snippet": "def hello():",
      "feedback_status": null
    }
  ]
}
```

### Get Analysis Issues

**GET** `/analysis/direct/{analysis_id}/issues`

Get all issues/suggestions for an analysis.

**Response:**
```json
{
  "analysis_id": "880e8400-e29b-41d4-a716-446655440004",
  "issues": [
    {
      "issue_id": "990e8400-e29b-41d4-a716-446655440005",
      "type": "style",
      "severity": "low",
      "message": "Missing docstring",
      "line_number": 1,
      "suggestion": "Add a docstring to describe the function",
      "code_snippet": "def hello():",
      "feedback_status": null
    }
  ],
  "total_issues": 1
}
```

### Get Analysis Status (Real-time)

**GET** `/analysis/direct/{analysis_id}/status`

Get the current status of an analysis (for polling).

**Response:**
```json
{
  "analysis_id": "880e8400-e29b-41d4-a716-446655440004",
  "status": "processing",
  "progress": 45,
  "updated_at": "2025-10-22T10:35:10Z"
}
```

### WebSocket: Analysis Status

**WS** `/ws/analysis/{analysis_id}`

Real-time status updates for an analysis.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/analysis/880e8400-e29b-41d4-a716-446655440004');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Status:', data.status, 'Progress:', data.progress);
};
```

**Messages:**
```json
{
  "analysis_id": "880e8400-e29b-41d4-a716-446655440004",
  "status": "processing",
  "progress": 75,
  "updated_at": "2025-10-22T10:35:12Z"
}
```

---

## Feedback Endpoints

### Submit Feedback

**POST** `/feedback/submit`

Submit feedback for an individual suggestion.

**Request:**
```json
{
  "issue_id": "990e8400-e29b-41d4-a716-446655440005",
  "feedback_type": "accept",
  "comment": "Good suggestion",
  "modified_suggestion": null
}
```

**Feedback Types:**
- `accept` - User accepts the suggestion
- `reject` - User rejects the suggestion
- `modify` - User modifies the suggestion

**Response:**
```json
{
  "feedback_id": "aa0e8400-e29b-41d4-a716-446655440006",
  "issue_id": "990e8400-e29b-41d4-a716-446655440005",
  "feedback_type": "accept",
  "created_at": "2025-10-22T10:40:00Z"
}
```

### Get User Feedback History

**GET** `/feedback/history`

Get the user's feedback history.

**Query Parameters:**
- `page` (optional): Page number
- `page_size` (optional): Items per page
- `feedback_type` (optional): Filter by type

**Response:**
```json
{
  "feedback": [
    {
      "feedback_id": "aa0e8400-e29b-41d4-a716-446655440006",
      "issue_id": "990e8400-e29b-41d4-a716-446655440005",
      "feedback_type": "accept",
      "comment": "Good suggestion",
      "created_at": "2025-10-22T10:40:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

---

## Analytics Endpoints

### Get Issue Trends

**GET** `/analytics/issue-trends`

Get time-series data for issue trends.

**Query Parameters:**
- `timeframe`: Time period (7d, 30d, 90d)
- `user_id` (optional): Specific user (admin only)

**Response:**
```json
{
  "timeframe": "30d",
  "data_points": [
    {
      "date": "2025-10-01",
      "errors": 5,
      "security_issues": 2,
      "warnings": 8,
      "total": 15
    },
    {
      "date": "2025-10-02",
      "errors": 3,
      "security_issues": 1,
      "warnings": 6,
      "total": 10
    }
  ],
  "summary": {
    "total_errors": 150,
    "total_security": 45,
    "total_warnings": 230,
    "trend": "improving"
  }
}
```

### Get Criticality Distribution

**GET** `/analytics/criticality-distribution`

Get issue severity distribution.

**Query Parameters:**
- `timeframe`: Time period (7d, 30d, 90d)
- `user_id` (optional): Specific user (admin only)

**Response:**
```json
{
  "timeframe": "30d",
  "distribution": {
    "severe": {
      "count": 12,
      "percentage": 5.2
    },
    "high": {
      "count": 45,
      "percentage": 19.5
    },
    "medium": {
      "count": 98,
      "percentage": 42.4
    },
    "low": {
      "count": 76,
      "percentage": 32.9
    }
  },
  "total_issues": 231
}
```

---

## Admin Endpoints

### Team Management

#### Create Team

**POST** `/admin/teams`

Create a new team (Admin only).

**Request:**
```json
{
  "name": "Backend Team",
  "description": "Backend development team"
}
```

**Response:**
```json
{
  "team_id": "bb0e8400-e29b-41d4-a716-446655440007",
  "name": "Backend Team",
  "description": "Backend development team",
  "created_at": "2025-10-22T11:00:00Z",
  "admin_id": 1
}
```

#### List Teams

**GET** `/admin/teams`

Get all teams.

**Response:**
```json
{
  "teams": [
    {
      "team_id": "bb0e8400-e29b-41d4-a716-446655440007",
      "name": "Backend Team",
      "description": "Backend development team",
      "member_count": 5,
      "created_at": "2025-10-22T11:00:00Z"
    }
  ],
  "total": 3
}
```

#### Get Team Details

**GET** `/admin/teams/{team_id}`

Get detailed information about a team.

**Response:**
```json
{
  "team_id": "bb0e8400-e29b-41d4-a716-446655440007",
  "name": "Backend Team",
  "description": "Backend development team",
  "created_at": "2025-10-22T11:00:00Z",
  "admin_id": 1,
  "members": [
    {
      "user_id": 2,
      "username": "john@example.com",
      "role": "user",
      "joined_at": "2025-10-22T11:05:00Z"
    }
  ]
}
```

#### Update Team

**PUT** `/admin/teams/{team_id}`

Update team information.

**Request:**
```json
{
  "name": "Backend Development Team",
  "description": "Updated description"
}
```

#### Delete Team

**DELETE** `/admin/teams/{team_id}`

Delete a team (requires confirmation).

**Response:**
```json
{
  "message": "Team deleted successfully",
  "team_id": "bb0e8400-e29b-41d4-a716-446655440007"
}
```

#### Get Team Members

**GET** `/admin/teams/{team_id}/members`

Get all members of a team.

**Response:**
```json
{
  "team_id": "bb0e8400-e29b-41d4-a716-446655440007",
  "members": [
    {
      "user_id": 2,
      "username": "john@example.com",
      "email": "john@example.com",
      "role": "user",
      "is_active": true,
      "joined_at": "2025-10-22T11:05:00Z"
    }
  ],
  "total_members": 5
}
```

### User Management

#### List Users

**GET** `/admin/users`

Get all users with filtering and pagination.

**Query Parameters:**
- `page` (optional): Page number
- `page_size` (optional): Items per page
- `team_id` (optional): Filter by team
- `role` (optional): Filter by role
- `is_active` (optional): Filter by status
- `search` (optional): Search by username/email

**Response:**
```json
{
  "users": [
    {
      "user_id": 2,
      "username": "john@example.com",
      "email": "john@example.com",
      "role": "user",
      "is_active": true,
      "team_id": "bb0e8400-e29b-41d4-a716-446655440007",
      "team_name": "Backend Team",
      "created_at": "2025-10-15T09:00:00Z",
      "last_login": "2025-10-22T08:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50
}
```

#### Get User Details

**GET** `/admin/users/{user_id}`

Get detailed information about a user.

**Response:**
```json
{
  "user_id": 2,
  "username": "john@example.com",
  "email": "john@example.com",
  "role": "user",
  "is_active": true,
  "team_id": "bb0e8400-e29b-41d4-a716-446655440007",
  "team_name": "Backend Team",
  "created_at": "2025-10-15T09:00:00Z",
  "last_login": "2025-10-22T08:30:00Z",
  "statistics": {
    "total_analyses": 45,
    "total_feedback": 32,
    "acceptance_rate": 68.5
  }
}
```

#### Update User Role

**PUT** `/admin/users/{user_id}/role`

Update a user's role.

**Request:**
```json
{
  "role": "team_lead"
}
```

**Roles:**
- `user` - Regular user
- `team_lead` - Team leader
- `admin` - Administrator

**Response:**
```json
{
  "user_id": 2,
  "username": "john@example.com",
  "role": "team_lead",
  "updated_at": "2025-10-22T11:30:00Z"
}
```

#### Update User Status

**PUT** `/admin/users/{user_id}/status`

Activate or deactivate a user.

**Request:**
```json
{
  "is_active": false
}
```

#### Assign User to Team

**PUT** `/admin/users/{user_id}/team/{team_id}`

Assign a user to a team.

**Response:**
```json
{
  "user_id": 2,
  "team_id": "bb0e8400-e29b-41d4-a716-446655440007",
  "team_name": "Backend Team",
  "assigned_at": "2025-10-22T11:35:00Z"
}
```

#### Remove User from Team

**DELETE** `/admin/users/{user_id}/team`

Remove a user from their current team.

### Global Analytics

#### Get Platform Statistics

**GET** `/admin/analytics/platform`

Get platform-wide statistics.

**Response:**
```json
{
  "total_users": 150,
  "total_teams": 12,
  "total_reviews": 5420,
  "active_users_30d": 98,
  "total_issues_found": 12450,
  "avg_issues_per_review": 2.3,
  "feedback_participation_rate": 67.5,
  "top_languages": [
    {"language": "python", "count": 2340},
    {"language": "javascript", "count": 1890}
  ]
}
```

#### Get Global Trends

**GET** `/admin/analytics/global-trends`

Get platform-wide issue trends.

**Query Parameters:**
- `timeframe`: Time period (7d, 30d, 90d)
- `team_id` (optional): Filter by team

**Response:**
```json
{
  "timeframe": "30d",
  "data_points": [
    {
      "date": "2025-10-01",
      "reviews": 45,
      "errors": 89,
      "warnings": 156,
      "security_issues": 23,
      "total_issues": 268
    }
  ],
  "summary": {
    "total_reviews": 1350,
    "total_issues": 8040,
    "avg_issues_per_review": 5.96
  }
}
```

#### Get Team Comparison

**GET** `/admin/analytics/team-comparison`

Compare performance metrics across teams.

**Response:**
```json
{
  "teams": [
    {
      "team_id": "bb0e8400-e29b-41d4-a716-446655440007",
      "team_name": "Backend Team",
      "total_reviews": 450,
      "avg_issues_per_review": 2.1,
      "feedback_acceptance_rate": 72.5,
      "active_members": 5
    }
  ]
}
```

#### Get All Reviews

**GET** `/admin/analytics/all-reviews`

Get all code reviews across the platform.

**Query Parameters:**
- `page`, `page_size`: Pagination
- `team_id` (optional): Filter by team
- `date_from`, `date_to` (optional): Date range

**Response:**
```json
{
  "reviews": [
    {
      "analysis_id": "880e8400-e29b-41d4-a716-446655440004",
      "user_id": 2,
      "username": "john@example.com",
      "team_name": "Backend Team",
      "filename": "auth.py",
      "created_at": "2025-10-15T10:30:00Z",
      "issues_count": 5,
      "feedback_count": 3
    }
  ],
  "total": 5420,
  "page": 1,
  "page_size": 50
}
```

#### Get All Feedback

**GET** `/admin/analytics/all-feedback`

Get all feedback across the platform.

**Query Parameters:**
- `page`, `page_size`: Pagination
- `feedback_type` (optional): Filter by type
- `team_id` (optional): Filter by team

**Response:**
```json
{
  "feedback": [
    {
      "feedback_id": "aa0e8400-e29b-41d4-a716-446655440006",
      "user_id": 2,
      "username": "john@example.com",
      "issue_id": "990e8400-e29b-41d4-a716-446655440005",
      "feedback_type": "accept",
      "created_at": "2025-10-15T11:00:00Z"
    }
  ],
  "summary": {
    "total_feedback": 3250,
    "acceptance_rate": 68.5,
    "rejection_rate": 22.3,
    "modification_rate": 9.2
  },
  "total": 3250,
  "page": 1,
  "page_size": 50
}
```

### Audit Logs

#### Get Audit Logs

**GET** `/admin/audit-logs`

Get audit logs with filtering.

**Query Parameters:**
- `page`, `page_size`: Pagination
- `user_id` (optional): Filter by user
- `action` (optional): Filter by action type
- `resource_type` (optional): Filter by resource
- `date_from`, `date_to` (optional): Date range

**Response:**
```json
{
  "logs": [
    {
      "log_id": 1,
      "timestamp": "2025-10-22T11:30:00Z",
      "user_id": 1,
      "username": "admin@example.com",
      "action": "update_user_role",
      "resource_type": "user",
      "resource_id": "2",
      "details": {
        "old_role": "user",
        "new_role": "team_lead"
      },
      "ip_address": "192.168.1.100"
    }
  ],
  "total": 1250,
  "page": 1,
  "page_size": 50
}
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "error": "validation_error",
  "message": "File size exceeds maximum allowed size of 5MB",
  "details": {
    "file_size": 10485760,
    "max_size": 5242880
  },
  "timestamp": "2025-10-22T12:00:00Z",
  "request_id": "cc0e8400-e29b-41d4-a716-446655440008"
}
```

### Common Error Codes

- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `409` - Conflict (duplicate resource)
- `413` - Payload Too Large (file size exceeded)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## Rate Limiting

API requests are rate-limited per user:

- **Regular Users**: 100 requests per minute
- **Team Leads**: 200 requests per minute
- **Admins**: 500 requests per minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1698062400
```

---

## Pagination

All list endpoints support pagination:

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Response Format:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

---

## Filtering and Sorting

Many endpoints support filtering and sorting:

**Query Parameters:**
- `sort_by`: Field to sort by
- `sort_order`: `asc` or `desc`
- Various filter parameters specific to each endpoint

Example:
```
GET /api/v1/analysis/direct/history?sort_by=created_at&sort_order=desc&status=completed
```

---

## WebSocket Connections

WebSocket connections require authentication via query parameter:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/analysis/123?token=<jwt_token>');
```

---

## Best Practices

1. **Always handle errors gracefully** - Check status codes and error messages
2. **Use pagination** - Don't fetch all records at once
3. **Implement retry logic** - For transient failures (500, 503)
4. **Cache responses** - When appropriate to reduce API calls
5. **Use WebSockets** - For real-time updates instead of polling
6. **Validate input** - Before sending to API
7. **Store tokens securely** - Never expose JWT tokens in client-side code
8. **Monitor rate limits** - Check rate limit headers

---

## Support

For API support, contact: kokkiralarevan2005@gmail.com
