# Task 3 Services - Usage Guide

Quick reference for using the admin and analytics services implemented in Task 3.

## Table of Contents
1. [AdminService](#adminservice)
2. [AuditLogger](#auditlogger)
3. [GlobalAnalyticsService](#globalanalyticsservice)
4. [AnalyticsService](#analyticsservice)
5. [DataAnonymizationService](#dataanonymizationservice)
6. [RBAC System](#rbac-system)

---

## AdminService

### Initialization
```python
from app.services import AdminService
from sqlalchemy.orm import Session

admin_service = AdminService(db)
```

### Team Management

#### Create Team
```python
from app.schemas.team import TeamCreate

team_data = TeamCreate(
    name="Engineering Team",
    settings={"max_members": 50, "auto_assign": True}
)
team = await admin_service.create_team(team_data, admin_user_id=1)
```

#### Update Team
```python
from app.schemas.team import TeamUpdate

team_update = TeamUpdate(name="Senior Engineering Team")
updated_team = await admin_service.update_team(
    team_id="team-uuid",
    team_data=team_update,
    admin_user_id=1
)
```

#### Delete Team
```python
success = await admin_service.delete_team(
    team_id="team-uuid",
    admin_user_id=1
)
```

#### Get Teams
```python
# Get all teams
teams = await admin_service.get_all_teams(skip=0, limit=100)

# Get specific team
team = await admin_service.get_team_by_id("team-uuid")

# Get team analytics
analytics = await admin_service.get_team_analytics("team-uuid")
```

### User Management

#### Get Users
```python
# Get all users
users = await admin_service.get_all_users(skip=0, limit=100)

# Get users by team
team_users = await admin_service.get_all_users(team_id="team-uuid")

# Get specific user
user = await admin_service.get_user_by_id(user_id=123)
```

#### Update User Role
```python
from app.models.users import UserRole

updated_user = await admin_service.update_user_role(
    user_id=123,
    role=UserRole.TEAM_LEAD,
    admin_user_id=1
)
```

#### Update User Status
```python
# Deactivate user
updated_user = await admin_service.update_user_status(
    user_id=123,
    is_active=False,
    admin_user_id=1
)
```

#### Assign User to Team
```python
updated_user = await admin_service.assign_user_to_team(
    user_id=123,
    team_id="team-uuid",
    admin_user_id=1
)
```

### Platform Analytics

#### Get Platform Statistics
```python
stats = await admin_service.get_platform_analytics()
# Returns: total_users, active_users, total_teams, total_analyses, etc.
```

#### Get Audit Logs
```python
logs, total = await admin_service.get_audit_logs(
    admin_user_id=1,  # Optional: filter by admin
    action="team_create",  # Optional: filter by action
    resource_type="team",  # Optional: filter by resource
    start_date=datetime(2025, 1, 1),  # Optional
    end_date=datetime(2025, 12, 31),  # Optional
    skip=0,
    limit=50
)
```

---

## AuditLogger

### Initialization
```python
from app.services import AuditLogger

audit_logger = AuditLogger(db)
```

### Basic Action Logging
```python
audit_log = audit_logger.log_action(
    user_id=1,
    action="create_resource",
    resource_type="team",
    resource_id="team-123",
    details={"name": "New Team"},
    changes={"status": {"old": "draft", "new": "active"}},
    request=request,  # FastAPI Request object
    status="success"
)
```

### Specialized Logging Methods

#### Log User Action
```python
audit_log = audit_logger.log_user_action(
    admin_user_id=1,
    target_user_id=123,
    action="update_role",
    changes={"role": {"old": "developer", "new": "team_lead"}},
    request=request
)
```

#### Log Team Action
```python
audit_log = audit_logger.log_team_action(
    admin_user_id=1,
    team_id="team-uuid",
    action="create",
    details={"team_name": "Engineering", "member_count": 0},
    request=request
)
```

#### Log Analytics Access
```python
audit_log = audit_logger.log_analytics_access(
    user_id=1,
    analytics_type="platform_stats",
    filters={"timeframe": "30d", "team_id": "team-uuid"},
    request=request
)
```

#### Log Failed Action
```python
audit_log = audit_logger.log_failed_action(
    user_id=1,
    action="delete_team",
    error_message="Team has active members",
    resource_type="team",
    resource_id="team-uuid",
    request=request
)
```

### Using AuditLogContext

```python
from app.services import AuditLogContext

with AuditLogContext(audit_logger, user_id=1, action="complex_operation") as ctx:
    # Perform operation
    result = perform_complex_operation()
    
    # Set context information
    ctx.set_resource("team", result.team_id)
    ctx.set_details({"operation_type": "bulk_update", "count": 10})
    ctx.set_changes({"status": {"old": "pending", "new": "completed"}})
    
    # If exception occurs, it's automatically logged as failed
```

---

## GlobalAnalyticsService

### Initialization
```python
from app.services import GlobalAnalyticsService

global_analytics = GlobalAnalyticsService(db)
```

### Platform Statistics
```python
stats = await global_analytics.get_platform_stats()
# Returns:
# - total_users, active_users
# - total_teams, total_reviews
# - total_issues_found, total_feedback
# - acceptance_rate, avg_issues_per_review
# - role_distribution
# - recent_activity (30-day metrics)
```

### Global Trends
```python
trends = await global_analytics.get_global_trends(
    timeframe="30d",  # Options: 7d, 30d, 90d, 1y
    team_id="team-uuid"  # Optional: filter by team
)
# Returns:
# - data_points: [{date, reviews, errors, warnings, security_issues}]
# - summary: {total_reviews, total_errors, total_warnings, avg_daily_reviews}
```

### Team Comparison
```python
comparison = await global_analytics.get_team_comparison()
# Returns list of teams with:
# - team_id, team_name, member_count
# - total_reviews, avg_issues_per_review
# - feedback_acceptance_rate
# - active_members_30d
```

### All Reviews
```python
reviews, total = await global_analytics.get_all_reviews(
    team_id="team-uuid",  # Optional
    date_from=datetime(2025, 1, 1),  # Optional
    date_to=datetime(2025, 12, 31),  # Optional
    skip=0,
    limit=50
)
# Returns list of reviews with user, team, filename, issues_count, etc.
```

### All Feedback
```python
feedback_data = await global_analytics.get_all_feedback(
    feedback_type="accept",  # Optional: accept, reject, modify
    team_id="team-uuid",  # Optional
    skip=0,
    limit=50
)
# Returns:
# - feedback: list of feedback records
# - total: total count
# - summary: {acceptance_rate, rejection_rate, modification_rate}
```

### Criticality Distribution
```python
distribution = await global_analytics.get_criticality_distribution(
    timeframe="30d",
    team_id="team-uuid"  # Optional
)
# Returns:
# - distribution: {severe, high, medium, low} with count and percentage
# - total_issues
```

---

## AnalyticsService

### Initialization
```python
from app.services import AnalyticsService

analytics = AnalyticsService(db, redis_client=redis_client)
```

### Issue Trends (User-Specific)
```python
trends = await analytics.get_issue_trends(
    user_id=123,
    timeframe="30d"  # Options: 7d, 30d, 90d, 1y
)
# Returns:
# - data_points: [{date, errors, security_issues, warnings, total}]
# - summary: {total_errors, total_security_issues, total_warnings, trend}
# - trend: "improving", "declining", "stable", or "insufficient_data"
```

### Criticality Distribution (User-Specific)
```python
distribution = await analytics.get_criticality_distribution(
    user_id=123,
    timeframe="30d"
)
# Returns:
# - distribution: {severe, high, medium, low} with count and percentage
# - total_issues
# - severity_breakdown: top 5 patterns per severity level
```

### Cache Management
```python
# Invalidate specific cache pattern
analytics.invalidate_cache("issue_trends:user_id:123:*")

# Invalidate all cache for a user
analytics.invalidate_user_cache(user_id=123)
```

---

## DataAnonymizationService

### Basic Anonymization

#### Email
```python
from app.services import DataAnonymizationService

anonymized = DataAnonymizationService.anonymize_email("user@example.com")
# Returns: "user_[hash]@anonymized.local"
```

#### Username
```python
anonymized = DataAnonymizationService.anonymize_username("john_doe", user_id=123)
# Returns: "user_123"
```

#### IP Address
```python
anonymized = DataAnonymizationService.anonymize_ip_address("192.168.1.100")
# Returns: "192.168.1.0"
```

#### Code Content
```python
anonymized = DataAnonymizationService.anonymize_code_content(
    code='print("Hello")',
    preserve_structure=True
)
# Returns: 'print("[REDACTED]")'
```

### Structured Data Anonymization

#### User Data
```python
user_data = {
    "id": 123,
    "email": "user@example.com",
    "username": "john_doe",
    "full_name": "John Doe",
    "ip_address": "192.168.1.100"
}

# Partial anonymization (email and username only)
anonymized = DataAnonymizationService.anonymize_user_data(
    user_data,
    level="partial"
)

# Full anonymization (all PII removed)
anonymized = DataAnonymizationService.anonymize_user_data(
    user_data,
    level="full"
)
```

#### Analytics Data
```python
analytics_data = {
    "user": {"email": "user@example.com", "username": "john_doe"},
    "reviews": [
        {"user_id": 1, "email": "user1@example.com", "code": "sensitive code"}
    ]
}

anonymized = DataAnonymizationService.anonymize_analytics_data(
    analytics_data,
    anonymize_users=True,
    anonymize_code=True
)
```

#### Audit Log
```python
audit_log = {
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 Chrome/91.0",
    "details": {"password": "secret123", "action": "login"}
}

anonymized = DataAnonymizationService.anonymize_audit_log(audit_log)
```

### Access Control Helpers

#### Check if Anonymization Needed
```python
should_anonymize = DataAnonymizationService.should_anonymize_for_user(
    requesting_user_role="developer",
    target_user_id=123,
    requesting_user_id=456
)
# Returns: True (developer viewing another user's data)
```

#### Get Anonymization Level
```python
level = DataAnonymizationService.get_anonymization_level("admin")
# Returns: "none" (admins see full data)

level = DataAnonymizationService.get_anonymization_level("user")
# Returns: "full" (regular users see fully anonymized data)
```

---

## RBAC System

### Using Role Checkers in Endpoints

#### Require Admin
```python
from app.core.rbac import require_admin
from fastapi import Depends

@router.get("/admin/users")
async def get_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    # Only admins can access
    admin_service = AdminService(db)
    return await admin_service.get_all_users()
```

#### Require Admin or Team Lead
```python
from app.core.rbac import require_admin_or_team_lead

@router.get("/teams/{team_id}/analytics")
async def get_team_analytics(
    team_id: str,
    current_user: User = Depends(require_admin_or_team_lead),
    db: Session = Depends(get_db)
):
    # Admins and team leads can access
    admin_service = AdminService(db)
    return await admin_service.get_team_analytics(team_id)
```

#### Custom Role Checker
```python
from app.core.rbac import RoleChecker
from app.models.users import UserRole

@router.post("/reviews")
async def create_review(
    current_user: User = Depends(RoleChecker([UserRole.DEVELOPER, UserRole.REVIEWER])),
    db: Session = Depends(get_db)
):
    # Only developers and reviewers can create reviews
    pass
```

#### Permission Checker
```python
from app.core.rbac import PermissionChecker, Permissions

@router.get("/analytics/platform")
async def get_platform_analytics(
    current_user: User = Depends(PermissionChecker(Permissions.ANALYTICS_READ)),
    db: Session = Depends(get_db)
):
    # Only users with analytics.read permission can access
    pass
```

### Using Decorators

```python
from app.core.rbac import requires_role
from app.models.users import UserRole

@requires_role(UserRole.ADMIN, UserRole.TEAM_LEAD)
def sensitive_operation(user: User):
    # Only admins and team leads can call this function
    pass
```

---

## Complete Example: Admin Endpoint with Audit Logging

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.services import AdminService, AuditLogger, DataAnonymizationService
from app.core.rbac import require_admin
from app.api.deps import get_db, get_current_user
from app.models.users import User, UserRole
from app.schemas.team import TeamCreate, TeamResponse

router = APIRouter()

@router.post("/admin/teams", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new team (admin only)."""
    try:
        # Initialize services
        admin_service = AdminService(db)
        audit_logger = AuditLogger(db)
        
        # Create team with audit logging context
        with AuditLogContext(
            audit_logger, 
            current_user.id, 
            "create_team",
            request=request
        ) as ctx:
            # Create team
            team = await admin_service.create_team(team_data, current_user.id)
            
            # Set audit context
            ctx.set_resource("team", team.id)
            ctx.set_details({"team_name": team.name})
            
            return team
            
    except Exception as e:
        # Log failed action
        audit_logger.log_failed_action(
            user_id=current_user.id,
            action="create_team",
            error_message=str(e),
            resource_type="team",
            request=request
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/analytics/platform")
async def get_platform_analytics(
    request: Request,
    anonymize: bool = True,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get platform-wide analytics."""
    # Initialize services
    global_analytics = GlobalAnalyticsService(db)
    audit_logger = AuditLogger(db)
    
    # Log analytics access
    audit_logger.log_analytics_access(
        user_id=current_user.id,
        analytics_type="platform_stats",
        request=request
    )
    
    # Get analytics data
    stats = await global_analytics.get_platform_stats()
    
    # Anonymize if requested and user is not admin
    if anonymize and current_user.role != UserRole.ADMIN:
        stats = DataAnonymizationService.anonymize_analytics_data(
            stats,
            anonymize_users=True,
            anonymize_code=True
        )
    
    return stats
```

---

## Best Practices

### 1. Always Use Audit Logging for Admin Actions
```python
# Good
with AuditLogContext(audit_logger, user_id, action) as ctx:
    result = perform_action()
    ctx.set_resource("type", result.id)

# Also Good
audit_logger.log_user_action(admin_id, target_id, action, changes)
```

### 2. Apply Data Anonymization Based on User Role
```python
# Check if anonymization is needed
if DataAnonymizationService.should_anonymize_for_user(
    requesting_user_role=current_user.role.value,
    target_user_id=target_user_id,
    requesting_user_id=current_user.id
):
    data = DataAnonymizationService.anonymize_analytics_data(data)
```

### 3. Use Appropriate RBAC Checks
```python
# Use specific role checkers
current_user: User = Depends(require_admin)

# Or permission checkers for fine-grained control
current_user: User = Depends(PermissionChecker(Permissions.TEAM_WRITE))
```

### 4. Handle Errors Gracefully
```python
try:
    result = await service.operation()
except Exception as e:
    audit_logger.log_failed_action(user_id, action, str(e))
    raise HTTPException(status_code=500, detail="Operation failed")
```

### 5. Use Caching for Analytics
```python
# Analytics service has built-in caching
analytics = AnalyticsService(db, redis_client)
trends = await analytics.get_issue_trends(user_id, timeframe)

# Invalidate cache when data changes
analytics.invalidate_user_cache(user_id)
```

---

## Common Patterns

### Pattern 1: Admin Operation with Full Audit Trail
```python
async def admin_operation(admin_id: int, target_id: int, db: Session):
    admin_service = AdminService(db)
    audit_logger = AuditLogger(db)
    
    with AuditLogContext(audit_logger, admin_id, "operation") as ctx:
        result = await admin_service.perform_operation(target_id, admin_id)
        ctx.set_resource("resource_type", result.id)
        ctx.set_details({"key": "value"})
        return result
```

### Pattern 2: Analytics with Anonymization
```python
async def get_analytics(user_id: int, current_user: User, db: Session):
    analytics = AnalyticsService(db)
    data = await analytics.get_issue_trends(user_id, "30d")
    
    # Anonymize if viewing other user's data
    if DataAnonymizationService.should_anonymize_for_user(
        current_user.role.value, user_id, current_user.id
    ):
        data = DataAnonymizationService.anonymize_analytics_data(data)
    
    return data
```

### Pattern 3: Team Management with Validation
```python
async def manage_team(team_id: str, admin_id: int, db: Session):
    admin_service = AdminService(db)
    
    # Verify team exists
    team = await admin_service.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Perform operation
    result = await admin_service.update_team(team_id, data, admin_id)
    return result
```

---

## Troubleshooting

### Issue: Audit logs not being created
**Solution**: Ensure AuditLog model is imported and database tables are created
```python
from app.models.audit_log import AuditLog
# Run migrations or create tables
```

### Issue: Permission denied errors
**Solution**: Check user role and permissions
```python
# Verify user has correct role
print(f"User role: {current_user.role.value}")

# Check if user has permission
perm_checker = PermissionChecker(Permissions.USER_READ)
has_perm = perm_checker._has_permission(current_user, Permissions.USER_READ)
```

### Issue: Analytics returning empty data
**Solution**: Verify data exists and timeframe is appropriate
```python
# Check if user has analyses
analyses_count = db.query(DirectAnalysis).filter(
    DirectAnalysis.user_id == user_id
).count()
print(f"User has {analyses_count} analyses")
```

### Issue: Cache not working
**Solution**: Ensure Redis client is passed to AnalyticsService
```python
from app.core.cache import get_redis_client

redis_client = get_redis_client()
analytics = AnalyticsService(db, redis_client=redis_client)
```

---

## Additional Resources

- **Implementation Summary**: `backend/TASK_3_IMPLEMENTATION_SUMMARY.md`
- **Test Suite**: `backend/test_task3_services.py`
- **RBAC Documentation**: `backend/app/core/rbac.py`
- **Models Documentation**: `backend/app/models/`

---

**Last Updated**: October 21, 2025
**Task Status**: ✅ Complete
