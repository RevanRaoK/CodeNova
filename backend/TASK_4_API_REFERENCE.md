# Task 4 API Endpoints - Quick Reference

## File Upload Endpoints

### Upload Files Batch
```http
POST /api/v1/file-upload/upload-batch
Authorization: Bearer <token>
Content-Type: multipart/form-data

files: [file1, file2, ...]
```

**Response:**
```json
{
  "batch_id": "uuid",
  "total_files": 5,
  "queued_count": 5,
  "status": "processing",
  "created_at": "2025-10-21T10:30:00Z",
  "files": [
    {
      "file_id": "uuid",
      "filename": "example.py",
      "status": "queued",
      "size_bytes": 1024,
      "language": "python"
    }
  ]
}
```

### Get Batch Status
```http
GET /api/v1/file-upload/batch/{batch_id}/status
Authorization: Bearer <token>
```

### List User Files
```http
GET /api/v1/file-upload/files?page=1&page_size=20&status=completed
Authorization: Bearer <token>
```

## Enhanced Analysis Endpoints

### Get Analysis History
```http
GET /api/v1/analysis-enhanced/history?page=1&page_size=20&filename=example.py
Authorization: Bearer <token>
```

### Get Analysis Status
```http
GET /api/v1/analysis-enhanced/{analysis_id}/status
Authorization: Bearer <token>
```

### WebSocket Status Updates
```
WS /api/v1/analysis-enhanced/ws/{analysis_id}
```

## Admin Team Management

### Create Team
```http
POST /api/v1/admin/teams
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Backend Team",
  "description": "Backend development team"
}
```

### List Teams
```http
GET /api/v1/admin/teams?skip=0&limit=100
Authorization: Bearer <admin_token>
```

### Get Team Details
```http
GET /api/v1/admin/teams/{team_id}
Authorization: Bearer <admin_token>
```

### Update Team
```http
PUT /api/v1/admin/teams/{team_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Updated Team Name",
  "description": "Updated description"
}
```

### Delete Team
```http
DELETE /api/v1/admin/teams/{team_id}
Authorization: Bearer <admin_token>
```

### Get Team Members
```http
GET /api/v1/admin/teams/{team_id}/members
Authorization: Bearer <admin_token>
```

### Add Team Member
```http
POST /api/v1/admin/teams/{team_id}/members/{user_id}
Authorization: Bearer <admin_token>
```

### Remove Team Member
```http
DELETE /api/v1/admin/teams/{team_id}/members/{user_id}
Authorization: Bearer <admin_token>
```

## Admin User Management

### List Users
```http
GET /api/v1/admin/users?team_id=uuid&role=USER&is_active=true&search=john&skip=0&limit=100
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `team_id` - Filter by team
- `role` - Filter by role (USER, ADMIN, TEAM_LEAD, etc.)
- `is_active` - Filter by active status
- `search` - Search by username or email
- `skip` - Pagination offset
- `limit` - Items per page

### Get User Details
```http
GET /api/v1/admin/users/{user_id}
Authorization: Bearer <admin_token>
```

**Response includes:**
- User information
- Activity statistics
- Total analyses
- Total feedback
- Average issues per analysis

### Update User Role
```http
PUT /api/v1/admin/users/{user_id}/role
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "role": "TEAM_LEAD"
}
```

### Update User Status
```http
PUT /api/v1/admin/users/{user_id}/status
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "is_active": false
}
```

### Assign User to Team
```http
PUT /api/v1/admin/users/{user_id}/team?team_id=uuid
Authorization: Bearer <admin_token>
```

## Admin Analytics

### Get Platform Statistics
```http
GET /api/v1/admin/analytics/platform
Authorization: Bearer <admin_token>
```

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
  "timestamp": "2025-10-21T10:30:00Z"
}
```

### Get Global Trends
```http
GET /api/v1/admin/analytics/global-trends?timeframe=30d&team_id=uuid
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `timeframe` - 7d, 30d, or 90d
- `team_id` - Optional team filter

### Get Team Comparison
```http
GET /api/v1/admin/analytics/team-comparison
Authorization: Bearer <admin_token>
```

### Get All Reviews
```http
GET /api/v1/admin/analytics/all-reviews?page=1&page_size=50&team_id=uuid&date_from=2025-01-01&date_to=2025-12-31
Authorization: Bearer <admin_token>
```

### Get All Feedback
```http
GET /api/v1/admin/analytics/all-feedback?page=1&page_size=50&feedback_type=accept&team_id=uuid
Authorization: Bearer <admin_token>
```

## User Analytics

### Get Issue Trends
```http
GET /api/v1/user-analytics/issue-trends?timeframe=30d
Authorization: Bearer <token>
```

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
```http
GET /api/v1/user-analytics/criticality-distribution?timeframe=30d
Authorization: Bearer <token>
```

**Response:**
```json
{
  "timeframe": "30d",
  "distribution": [
    {
      "severity": "severe",
      "count": 12,
      "percentage": 5.2
    },
    {
      "severity": "high",
      "count": 45,
      "percentage": 19.5
    }
  ],
  "total_issues": 231
}
```

## Audit Logs

### Get Audit Logs
```http
GET /api/v1/admin/audit-logs?page=1&page_size=50&action=update_user_role&resource_type=user&user_id=123&date_from=2025-01-01&date_to=2025-12-31
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `page` - Page number
- `page_size` - Items per page
- `action` - Filter by action type
- `resource_type` - Filter by resource type
- `user_id` - Filter by user
- `date_from` - Start date
- `date_to` - End date

### Get Available Actions
```http
GET /api/v1/admin/audit-logs/actions
Authorization: Bearer <admin_token>
```

### Get Available Resource Types
```http
GET /api/v1/admin/audit-logs/resource-types
Authorization: Bearer <admin_token>
```

## Authentication

All endpoints require authentication via Bearer token:
```http
Authorization: Bearer <your_jwt_token>
```

Admin endpoints additionally require admin role.

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

- Auth endpoints: 100 requests per hour (dev), 10 requests per hour (prod)
- Other endpoints: No rate limiting currently

## WebSocket Protocol

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/analysis-enhanced/ws/{analysis_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Status:', data.status, 'Progress:', data.progress);
};
```

### Message Format
```json
{
  "analysis_id": "uuid",
  "status": "processing",
  "progress": 45,
  "filename": "example.py",
  "updated_at": "2025-10-21T10:30:00Z"
}
```

## Testing with cURL

### Upload Files
```bash
curl -X POST "http://localhost:8000/api/v1/file-upload/upload-batch" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@file1.py" \
  -F "files=@file2.js"
```

### Get Platform Stats
```bash
curl -X GET "http://localhost:8000/api/v1/admin/analytics/platform" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Create Team
```bash
curl -X POST "http://localhost:8000/api/v1/admin/teams" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Backend Team", "description": "Backend development"}'
```

## Interactive API Documentation

Access the interactive Swagger UI at:
```
http://localhost:8000/docs
```

Access the ReDoc documentation at:
```
http://localhost:8000/redoc
```
