# Design Document

## Overview

This design document outlines the technical approach for implementing a comprehensive platform enhancement that transforms the existing code analysis tool into a full-featured platform with feedback systems, analytics dashboards, admin controls, file storage, message queuing, user management, GitHub integration, and homepage redesign.

The platform will maintain its current FastAPI backend and React frontend architecture while adding new microservices and integrations to support the enhanced functionality.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        HP[Homepage]
        DA[Dashboard App]
        AD[Admin Dashboard]
    end
    
    subgraph "API Gateway"
        AG[FastAPI Gateway]
    end
    
    subgraph "Core Services"
        AS[Analysis Service]
        FS[Feedback Service]
        US[User Service]
        AN[Analytics Service]
        GS[GitHub Service]
    end
    
    subgraph "Infrastructure"
        PG[(PostgreSQL)]
        RD[(Redis Cache)]
        RQ[RabbitMQ]
        DO[Digital Ocean Spaces]
        GH[GitHub API]
    end
    
    HP --> AG
    DA --> AG
    AD --> AG
    AG --> AS
    AG --> FS
    AG --> US
    AG --> AN
    AG --> GS
    AS --> PG
    AS --> RD
    AS --> RQ
    FS --> PG
    US --> PG
    AN --> PG
    GS --> GH
    AS --> DO
```

### Technology Stack

**Backend:**
- FastAPI (Python) - Main API framework
- SQLAlchemy - ORM for database operations
- PostgreSQL - Primary database
- Redis - Caching and session storage
- RabbitMQ - Message queuing
- Celery - Background task processing
- Digital Ocean Spaces SDK - File storage
- GitHub API - Repository integration

**Frontend:**
- React 19 - UI framework
- Vite - Build tool
- Tailwind CSS - Styling
- React Router - Navigation
- Recharts - Analytics visualization
- Monaco Editor - Code display

## Components and Interfaces

### 1. Feedback System Components

#### Backend Components

**FeedbackService**
```python
class FeedbackService:
    async def create_feedback(self, suggestion_id: str, user_id: str, action: str, reasons: List[str], custom_reason: str = None)
    async def get_feedback_analytics(self, user_id: str = None, date_range: DateRange = None)
    async def update_ai_learning_patterns(self, feedback_data: FeedbackData)
```

**FeedbackRepository**
```python
class FeedbackRepository:
    async def save_feedback(self, feedback: Feedback)
    async def get_feedback_by_suggestion(self, suggestion_id: str)
    async def get_analytics_data(self, filters: AnalyticsFilters)
```

#### Frontend Components

**FeedbackWidget**
```jsx
const FeedbackWidget = ({ suggestion, onFeedbackSubmit }) => {
    // Displays accept/reject buttons
    // Shows rejection reason checkboxes
    // Handles custom reason input
}
```

### 2. Analytics Dashboard Components

#### Backend Components

**AnalyticsService**
```python
class AnalyticsService:
    async def get_acceptance_rates(self, user_id: str = None, timeframe: str = "30d")
    async def get_rejection_patterns(self, user_id: str = None)
    async def get_usage_statistics(self, user_id: str = None)
    async def get_learning_progress(self)
```

#### Frontend Components

**AnalyticsDashboard**
```jsx
const AnalyticsDashboard = () => {
    // Displays acceptance rate charts
    // Shows rejection reason breakdowns
    // Renders usage statistics
    // Shows learning progress indicators
}
```

### 3. Admin Dashboard Components

#### Backend Components

**AdminService**
```python
class AdminService:
    async def get_all_users(self, team_id: str = None)
    async def update_user_role(self, user_id: str, role: UserRole)
    async def get_team_analytics(self, team_id: str)
    async def manage_team_structure(self, team_data: TeamData)
```

#### Frontend Components

**AdminDashboard**
```jsx
const AdminDashboard = () => {
    // User management interface
    // Role assignment controls
    // Team analytics display
    // Team structure management
}
```

### 4. File Storage Integration

#### Backend Components

**FileStorageService**
```python
class FileStorageService:
    async def upload_file(self, file: UploadFile, user_id: str)
    async def get_file_url(self, file_id: str, user_id: str)
    async def delete_file(self, file_id: str, user_id: str)
    async def list_user_files(self, user_id: str)
```

### 5. GitHub Integration Components

#### Backend Components

**GitHubService**
```python
class GitHubService:
    async def setup_webhook(self, repo_url: str, user_id: str)
    async def handle_pr_event(self, webhook_data: dict)
    async def analyze_pr_files(self, pr_data: PRData)
    async def post_pr_comment(self, repo: str, pr_number: int, comment: str)
    async def create_repository_issue(self, repo: str, issue_data: IssueData)
```

#### Frontend Components

**GitHubIntegration**
```jsx
const GitHubIntegration = () => {
    // Repository connection interface
    // Webhook status display
    // PR analysis results
    // Repository issues list
}
```

### 6. Message Queuing System

#### Queue Handlers

**AnalysisQueue**
```python
class AnalysisQueue:
    async def enqueue_file_analysis(self, file_data: FileData)
    async def process_analysis_job(self, job_data: JobData)
    async def handle_github_pr_analysis(self, pr_data: PRData)
```

## Data Models

### Core Models

```python
# Feedback Models
class Feedback(Base):
    id: UUID
    suggestion_id: str
    user_id: UUID
    action: FeedbackAction  # ACCEPT, REJECT
    rejection_reasons: List[str]
    custom_reason: Optional[str]
    timestamp: datetime
    
class FeedbackAnalytics(Base):
    id: UUID
    user_id: Optional[UUID]
    acceptance_rate: float
    common_rejections: dict
    period_start: datetime
    period_end: datetime

# GitHub Integration Models
class GitHubRepository(Base):
    id: UUID
    user_id: UUID
    repo_url: str
    webhook_id: str
    is_active: bool
    created_at: datetime
    
class PRAnalysis(Base):
    id: UUID
    repository_id: UUID
    pr_number: int
    analysis_results: dict
    issues_created: List[str]
    status: AnalysisStatus
    created_at: datetime

# File Storage Models
class StoredFile(Base):
    id: UUID
    user_id: UUID
    filename: str
    file_path: str
    file_size: int
    content_type: str
    spaces_url: str
    created_at: datetime

# User Management Models
class User(Base):
    id: UUID
    email: str
    role: UserRole  # USER, ADMIN, TEAM_LEAD
    team_id: Optional[UUID]
    preferences: dict
    created_at: datetime
    
class Team(Base):
    id: UUID
    name: str
    admin_id: UUID
    members: List[UUID]
    settings: dict
    created_at: datetime
```

### Database Schema Updates

```sql
-- Feedback tables
CREATE TABLE feedback (
    id UUID PRIMARY KEY,
    suggestion_id VARCHAR NOT NULL,
    user_id UUID REFERENCES users(id),
    action VARCHAR NOT NULL,
    rejection_reasons JSONB,
    custom_reason TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- GitHub integration tables
CREATE TABLE github_repositories (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    repo_url VARCHAR NOT NULL,
    webhook_id VARCHAR,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pr_analyses (
    id UUID PRIMARY KEY,
    repository_id UUID REFERENCES github_repositories(id),
    pr_number INTEGER NOT NULL,
    analysis_results JSONB,
    issues_created JSONB,
    status VARCHAR DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- File storage tables
CREATE TABLE stored_files (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    filename VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    file_size BIGINT,
    content_type VARCHAR,
    spaces_url VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enhanced user management
ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user';
ALTER TABLE users ADD COLUMN team_id UUID;
ALTER TABLE users ADD COLUMN preferences JSONB DEFAULT '{}';

CREATE TABLE teams (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    admin_id UUID REFERENCES users(id),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Error Handling

### API Error Responses

```python
class APIError(Exception):
    def __init__(self, status_code: int, message: str, details: dict = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}

# Specific error types
class FeedbackError(APIError):
    pass

class GitHubIntegrationError(APIError):
    pass

class FileStorageError(APIError):
    pass

class AdminPermissionError(APIError):
    pass
```

### Frontend Error Handling

```jsx
// Global error boundary
class ErrorBoundary extends React.Component {
    // Handles React component errors
}

// API error handling
const useApiError = () => {
    const handleError = (error) => {
        // Log error
        // Show user-friendly message
        // Retry logic for transient errors
    };
    return { handleError };
};
```

## Testing Strategy

### Backend Testing

**Unit Tests**
- Service layer tests with mocked dependencies
- Repository tests with test database
- Model validation tests
- Utility function tests

**Integration Tests**
- API endpoint tests
- Database integration tests
- External service integration tests (GitHub API, Digital Ocean Spaces)
- Message queue integration tests

**End-to-End Tests**
- Complete user workflows
- Admin functionality tests
- GitHub webhook processing tests

### Frontend Testing

**Unit Tests**
- Component rendering tests
- Hook functionality tests
- Utility function tests

**Integration Tests**
- API service integration tests
- Router navigation tests
- Context provider tests

**End-to-End Tests**
- User journey tests
- Admin workflow tests
- Cross-browser compatibility tests

### Test Data Management

```python
# Test fixtures for consistent test data
@pytest.fixture
def sample_feedback():
    return Feedback(
        suggestion_id="test-suggestion-1",
        user_id=uuid4(),
        action=FeedbackAction.REJECT,
        rejection_reasons=["incorrect", "not_applicable"],
        custom_reason="Custom test reason"
    )

@pytest.fixture
def mock_github_webhook():
    return {
        "action": "opened",
        "pull_request": {
            "number": 123,
            "head": {"sha": "abc123"},
            "base": {"repo": {"full_name": "user/repo"}}
        }
    }
```

### Performance Testing

- Load testing for file upload/analysis workflows
- Stress testing for concurrent GitHub webhook processing
- Cache performance validation
- Database query optimization validation

## Security Considerations

### Authentication & Authorization

- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- GitHub OAuth integration for repository access
- API rate limiting and request validation

### Data Protection

- Encryption at rest for sensitive data
- Secure file storage with signed URLs
- Input validation and sanitization
- SQL injection prevention through ORM

### GitHub Integration Security

- Webhook signature verification
- Scoped GitHub token permissions
- Secure credential storage
- Repository access validation

## Deployment Strategy

### Infrastructure Requirements

- PostgreSQL database with TimescaleDB extension
- Redis cluster for caching and sessions
- RabbitMQ cluster for message queuing
- Digital Ocean Spaces for file storage
- Load balancer for API gateway

### Environment Configuration

```yaml
# Production environment variables
DATABASE_URL: postgresql://user:pass@host:5432/db
REDIS_URL: redis://host:6379
RABBITMQ_URL: amqp://user:pass@host:5672/
DIGITAL_OCEAN_SPACES_KEY: your-spaces-key
DIGITAL_OCEAN_SPACES_SECRET: your-spaces-secret
GITHUB_CLIENT_ID: your-github-client-id
GITHUB_CLIENT_SECRET: your-github-client-secret
GITHUB_WEBHOOK_SECRET: your-webhook-secret
```

### Monitoring and Logging

- Application performance monitoring (APM)
- Error tracking and alerting
- Database performance monitoring
- Queue depth and processing time monitoring
- GitHub API rate limit monitoring