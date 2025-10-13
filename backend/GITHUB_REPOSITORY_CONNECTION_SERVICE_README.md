# GitHub Repository Connection Service Implementation

## Overview

This document describes the implementation of the GitHub Repository Connection Service, which handles repository connections, webhook setup, and integration management for the GitHub integration feature.

## Requirements Covered

- **3.3**: Repository webhook setup and management
- **3.5**: Repository integration management and code analysis triggers

## Files Created/Modified

### 1. Service Implementation

- **File**: `backend/app/services/github_repository_connection_service.py`
- **Purpose**: Core service for managing GitHub repository connections
- **Key Features**:
  - Repository connection and webhook setup
  - Repository integration management
  - Pull request analysis triggering
  - Webhook status monitoring
  - Repository settings management

### 2. API Endpoints Enhancement

- **File**: `backend/app/api/v1/endpoints/github.py`
- **Purpose**: Enhanced GitHub API endpoints with repository connection functionality
- **New Endpoints**:
  - `DELETE /repositories/{repository_id}` - Disconnect repository
  - `PUT /repositories/{repository_id}/settings` - Update repository settings
  - `GET /repositories/{repository_id}/webhook-status` - Get webhook status
  - `POST /repositories/{repository_id}/trigger-analysis` - Trigger PR analysis

### 3. Test Files

- **File**: `backend/test_github_repository_connection_service.py`
- **Purpose**: Comprehensive unit tests for the service
- **File**: `backend/test_github_repository_connection_integration.py`
- **Purpose**: Integration tests to verify service compatibility

## Service Features

### Repository Connection Management

#### Connect Repository

```python
async def connect_repository(
    user_id: int,
    repo_url: str,
    webhook_events: Optional[List[str]] = None,
    repository_settings: Optional[Dict[str, Any]] = None
) -> GitHubRepository
```

**Features**:

- Validates GitHub OAuth integration
- Extracts and validates repository URL
- Verifies repository access permissions
- Sets up GitHub webhook with proper configuration
- Creates repository integration record
- Queues initial repository scan

#### Disconnect Repository

```python
async def disconnect_repository(
    user_id: int,
    repository_id: str,
    remove_webhook: bool = True
) -> bool
```

**Features**:

- Removes webhook from GitHub (optional)
- Marks repository integration as inactive
- Maintains data integrity

#### Update Repository Settings

```python
async def update_repository_settings(
    user_id: int,
    repository_id: str,
    settings: Dict[str, Any]
) -> GitHubRepository
```

**Features**:

- Validates settings with bounds checking
- Updates repository configuration
- Maintains backward compatibility

### Pull Request Analysis

#### Trigger Analysis

```python
async def trigger_pull_request_analysis(
    repository_id: str,
    pr_number: int,
    force_reanalysis: bool = False,
    user_id: Optional[int] = None
) -> str
```

**Features**:

- Checks for existing recent analysis
- Retrieves PR information from GitHub
- Creates or updates PR analysis record
- Queues background analysis job
- Returns job ID for tracking

### Webhook Management

#### Get Webhook Status

```python
async def get_repository_webhooks_status(
    user_id: int,
    repository_id: str
) -> Dict[str, Any]
```

**Features**:

- Checks webhook status on GitHub
- Retrieves delivery history
- Provides comprehensive status information

### Repository Listing

#### List User Repositories

```python
async def list_user_repositories(
    user_id: int,
    include_inactive: bool = False,
    page: int = 1,
    per_page: int = 20
) -> Dict[str, Any]
```

**Features**:

- Paginated repository listing
- Optional inactive repository inclusion
- Formatted response with metadata

## Configuration

### Default Webhook Events

- `pull_request`
- `push`
- `issues`
- `issue_comment`
- `pull_request_review`
- `pull_request_review_comment`

### Default Repository Settings

```python
{
    "auto_analysis": True,
    "create_issues": True,
    "comment_on_prs": True,
    "analysis_on_push": False,
    "min_severity_for_issues": "error",
    "max_issues_per_pr": 10,
    "enable_inline_comments": True,
    "analysis_timeout_minutes": 30
}
```

## API Endpoints

### Repository Management

#### Connect Repository

```
POST /api/v1/github/repositories
```

**Body**:

```json
{
  "repo_url": "https://github.com/owner/repo",
  "webhook_events": ["pull_request", "push"],
  "auto_analysis": true,
  "create_issues": true,
  "comment_on_prs": true
}
```

#### List Repositories

```
GET /api/v1/github/repositories?page=1&per_page=20&include_inactive=false
```

#### Disconnect Repository

```
DELETE /api/v1/github/repositories/{repository_id}?remove_webhook=true
```

#### Update Repository Settings

```
PUT /api/v1/github/repositories/{repository_id}/settings
```

**Body**:

```json
{
  "auto_analysis": false,
  "max_issues_per_pr": 5,
  "analysis_timeout_minutes": 45
}
```

#### Get Webhook Status

```
GET /api/v1/github/repositories/{repository_id}/webhook-status
```

#### Trigger PR Analysis

```
POST /api/v1/github/repositories/{repository_id}/trigger-analysis?pr_number=123&force_reanalysis=false
```

## Error Handling

### GitHubIntegrationError

Custom exception class for GitHub-related errors:

- OAuth integration not found
- Invalid repository URL
- Insufficient permissions
- GitHub API errors
- Webhook setup failures

### Validation

- Repository URL format validation
- Settings bounds checking
- Permission verification
- Webhook configuration validation

## Security Features

### Access Control

- User-based repository access verification
- OAuth token validation
- Webhook signature verification
- Permission checking before operations

### Data Protection

- Encrypted access token storage (in production)
- Secure webhook secret management
- Input validation and sanitization

## Integration Points

### Dependencies

- `GitHubOAuthService`: For OAuth integration management
- `BackgroundJobService`: For queuing analysis jobs
- `GitHubRepository` model: For repository data storage
- `PRAnalysis` model: For analysis tracking

### Background Jobs

- `github_pr_analysis`: Pull request analysis job
- `github_repository_scan`: Initial repository scan job

## Testing

### Unit Tests

- Repository connection scenarios
- Settings validation
- URL parsing
- Error handling
- Helper method functionality

### Integration Tests

- Service import and initialization
- API endpoint integration
- Method availability verification
- Configuration validation

## Usage Examples

### Basic Repository Connection

```python
service = GitHubRepositoryConnectionService(db_session)

# Connect repository
repo = await service.connect_repository(
    user_id=1,
    repo_url="https://github.com/owner/repo"
)

# Trigger PR analysis
job_id = await service.trigger_pull_request_analysis(
    repository_id=repo.id,
    pr_number=123
)

# Check webhook status
status = await service.get_repository_webhooks_status(
    user_id=1,
    repository_id=repo.id
)
```

### Repository Management

```python
# List user repositories
repos = await service.list_user_repositories(
    user_id=1,
    page=1,
    per_page=10
)

# Update settings
updated_repo = await service.update_repository_settings(
    user_id=1,
    repository_id=repo.id,
    settings={"auto_analysis": False}
)

# Disconnect repository
success = await service.disconnect_repository(
    user_id=1,
    repository_id=repo.id,
    remove_webhook=True
)
```

## Implementation Status

✅ **Completed**:

- Core service implementation
- API endpoint integration
- Repository connection workflow
- Webhook setup and management
- Pull request analysis triggering
- Settings management
- Error handling
- Unit and integration tests
- Documentation

## Next Steps

1. **Environment Setup**: Resolve Python environment issues for testing
2. **Database Migration**: Ensure all required tables exist
3. **Configuration**: Set up GitHub App credentials and webhook secrets
4. **Frontend Integration**: Update UI to use new repository management endpoints
5. **Monitoring**: Add logging and metrics for repository operations
6. **Performance**: Optimize database queries and background job processing

## Notes

- The service is designed to work with existing GitHub OAuth integration
- All operations are user-scoped for security
- Background job processing enables scalable analysis
- Webhook management provides real-time integration
- Settings validation ensures data integrity
- Comprehensive error handling provides good user experience
