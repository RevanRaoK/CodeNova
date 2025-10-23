# Design Document

## Overview

This design document outlines the architecture and implementation approach for transforming the admin dashboard from displaying dummy/placeholder data to showing accurate, real-time information from the database. The solution focuses on eliminating hardcoded values, implementing missing functionality (particularly user role editing), removing unnecessary UI components, and enhancing the analytics section with flexible team filtering and integrated feedback dashboard capabilities.

## Architecture

### System Components

The admin dashboard follows a three-tier architecture:

1. **Frontend Layer** (React Components)
   - AdminDashboard.jsx - Main container with tab navigation
   - AdminAnalyticsDashboard.jsx - Overview and analytics display
   - UserManagementPanel.jsx - User listing and role management
   - TeamManagementPanel.jsx - Team management interface
   - AuditLogPanel.jsx - Audit log display
   - Supporting components (modals, tables, charts)

2. **API Layer** (FastAPI Endpoints)
   - `/api/v1/admin/*` - Admin-specific endpoints
   - `/api/v1/analytics/*` - Analytics and reporting endpoints
   - Authentication and authorization middleware

3. **Service Layer** (Python Services)
   - AdminService - User and team management operations
   - GlobalAnalyticsService - Platform-wide analytics
   - AuditLogger - Audit trail management

4. **Data Layer** (PostgreSQL Database)
   - Users table
   - Teams table
   - DirectAnalysis table (reviews)
   - FeedbackRecord table
   - Issue table
   - AuditLog table

### Data Flow

```
User Action → Frontend Component → API Endpoint → Service Layer → Database
                                                        ↓
                                                   Audit Logger
                                                        ↓
                                                   AuditLog Table
```

## Components and Interfaces

### 1. Dashboard Overview Component Redesign

**Current State:**
- Displays hardcoded metrics (1234 users)
- Includes system health status bar
- Shows placeholder data

**New Design:**
- Remove system health status bar entirely
- Display real-time metrics from database queries
- Show accurate counts with proper empty states

**Component Structure:**
```jsx
AdminAnalyticsDashboard
├── Header (with date range selector)
├── Metrics Cards (4 cards)
│   ├── Total Users (from database)
│   ├── Total Reviews (from database)
│   ├── Acceptance Rate (calculated)
│   └── Active Teams (from database)
├── Recent Activities Feed (real data)
└── View Tabs (overview, reviews, feedback, teams)
```

**API Integration:**
- `GET /api/v1/admin/analytics/platform` - Platform-wide statistics
- `GET /api/v1/admin/analytics/dashboard-metrics` - Dashboard-specific metrics

### 2. User Management with Role Editing

**Current State:**
- Edit button exists but non-functional
- Role displayed as static badge
- No modal or inline editing capability

**New Design:**
- Implement role editing modal
- Add inline role dropdown with immediate save
- Display success/error feedback
- Log role changes to audit trail

**Component Structure:**
```jsx
UserManagementPanel
├── User Table
│   ├── User Row
│   │   ├── User Info
│   │   ├── Role Dropdown (editable)
│   │   ├── Team Assignment
│   │   └── Actions Column
│   │       └── Edit Button → UserEditModal
│   └── ...
└── UserEditModal
    ├── Role Selection
    ├── Team Assignment
    ├── Status Toggle
    └── Save/Cancel Actions
```

**Modal Design:**
- Title: "Edit User: [User Name]"
- Fields:
  - Role dropdown (user, team_lead, admin)
  - Team dropdown (with "No Team" option)
  - Active status toggle
- Actions: Save, Cancel
- Validation: Prevent self-role modification

**API Integration:**
- `PUT /api/v1/admin/users/{user_id}/role` - Update user role
- `PUT /api/v1/admin/users/{user_id}/team/{team_id}` - Assign team
- `PUT /api/v1/admin/users/{user_id}/status` - Update status

### 3. Analytics with Flexible Team Selection

**Current State:**
- Requires team selection
- No "All Users" option
- Limited filtering capabilities

**New Design:**
- Default to "All Users" view
- Add team filter dropdown with "All Users" as first option
- Maintain date range filters (Last 30 Days, Last 90 Days)
- Update all charts and metrics based on selection

**Filter Component:**
```jsx
AnalyticsFilters
├── Team Selector
│   ├── Option: "All Users" (default)
│   ├── Option: Team 1
│   ├── Option: Team 2
│   └── ...
└── Date Range Selector
    ├── Option: "Last 30 Days"
    └── Option: "Last 90 Days"
```

**API Integration:**
- `GET /api/v1/admin/analytics/platform?team_id={id}&date_range={range}` - Filtered analytics
- `GET /api/v1/analytics/global-trends?team_id={id}&timeframe={range}` - Trend data

### 4. Integrated Feedback Dashboard

**Current State:**
- Feedback dashboard exists only in user-facing pages
- Admin analytics lacks feedback insights

**New Design:**
- Integrate full feedback dashboard into admin analytics
- Add feedback-specific tab in analytics view
- Display feedback patterns, statistics, and trends
- Filter by team or show all users

**Component Structure:**
```jsx
AdminAnalyticsDashboard
└── Feedback View Tab
    ├── Feedback Statistics Cards
    │   ├── Total Feedback
    │   ├── Acceptance Rate
    │   ├── Rejection Rate
    │   └── Modification Rate
    ├── Feedback Patterns Chart
    ├── Feedback Trends Over Time
    └── GlobalFeedbackTable
```

**API Integration:**
- `GET /api/v1/analytics/feedback-stats?team_id={id}` - Feedback statistics
- `GET /api/v1/analytics/feedback-patterns?team_id={id}` - Pattern analysis
- `GET /api/v1/admin/feedback/all?team_id={id}` - All feedback records

### 5. Audit Logs Enhancement

**Current State:**
- Displays audit logs
- Includes "platform" filter option

**New Design:**
- Remove "platform" option from filters
- Simplify filter options to:
  - Action Type (user actions, team actions, settings)
  - User ID
  - Date Range
- Ensure all admin actions are logged

**Filter Options:**
```
Action Types:
- All Actions
- User Role Updated
- Team Created
- Team Updated
- Team Deleted
- User Added to Team
- User Removed from Team
- Settings Updated
```

**API Integration:**
- `GET /api/v1/admin/audit-logs?action={type}&user_id={id}&date_from={date}&date_to={date}` - Filtered logs

## Data Models

### Dashboard Metrics Response

```typescript
interface DashboardMetrics {
  total_users: number;
  active_users: number;
  total_teams: number;
  total_reviews: number;
  reviews_today: number;
  total_feedback: number;
  acceptance_rate: number;
  recent_activities: Activity[];
}

interface Activity {
  id: string;
  type: 'user_created' | 'review_completed' | 'team_created' | 'role_updated';
  user_id: number;
  user_name: string;
  description: string;
  timestamp: string;
}
```

### User Edit Request

```typescript
interface UserEditRequest {
  role?: 'user' | 'team_lead' | 'admin';
  team_id?: string | null;
  is_active?: boolean;
}

interface UserEditResponse {
  id: number;
  email: string;
  full_name: string;
  role: string;
  team_id: string | null;
  is_active: boolean;
  updated_at: string;
}
```

### Analytics Filter State

```typescript
interface AnalyticsFilters {
  team_id: string | null; // null means "All Users"
  date_range: '30d' | '90d';
}

interface PlatformAnalytics {
  total_users: number;
  active_users: number;
  total_teams: number;
  total_reviews: number;
  total_issues_found: number;
  avg_issues_per_review: number;
  feedback_participation_rate: number;
  role_distribution: Record<string, number>;
  recent_activity: {
    new_users_30d: number;
    new_analyses_30d: number;
    active_users_30d: number;
  };
}
```

### Audit Log Entry

```typescript
interface AuditLogEntry {
  id: string;
  user_id: number;
  user: {
    full_name: string;
    email: string;
  };
  action: string;
  resource_type: 'user' | 'team' | 'settings';
  resource_id: string;
  changes: Record<string, any>;
  details: string;
  ip_address: string;
  timestamp: string;
}
```

## Error Handling

### Frontend Error Handling

1. **API Call Failures**
   - Display toast notification with error message
   - Log error to console for debugging
   - Maintain previous state (don't clear data)
   - Provide retry mechanism where appropriate

2. **Empty States**
   - Show meaningful empty state messages
   - Display "0" for zero counts (not hide the metric)
   - Provide guidance on next steps (e.g., "No users yet. Create your first user.")

3. **Permission Errors**
   - Redirect to access denied page
   - Display clear error message
   - Provide "Go Back" button

### Backend Error Handling

1. **Database Query Failures**
   - Return empty arrays/objects with zero counts
   - Log error with full stack trace
   - Return 500 status with generic error message
   - Never return dummy data as fallback

2. **Authorization Failures**
   - Return 403 Forbidden with clear message
   - Log unauthorized access attempts
   - Create audit log entry

3. **Validation Errors**
   - Return 400 Bad Request with field-specific errors
   - Validate all input parameters
   - Prevent SQL injection and XSS

## Testing Strategy

### Unit Tests

1. **Frontend Component Tests**
   - Test metric display with real data
   - Test empty state rendering
   - Test role editing modal functionality
   - Test filter state management
   - Test error handling and toast notifications

2. **Backend Service Tests**
   - Test AdminService methods with real database
   - Test GlobalAnalyticsService calculations
   - Test audit logging for all admin actions
   - Test permission checks
   - Test data aggregation accuracy

### Integration Tests

1. **API Endpoint Tests**
   - Test complete request/response cycle
   - Test authentication and authorization
   - Test data filtering and pagination
   - Test error responses

2. **End-to-End Tests**
   - Test complete user role editing workflow
   - Test analytics filtering and data updates
   - Test audit log creation and retrieval
   - Test team selection and data filtering

### Data Validation Tests

1. **Accuracy Tests**
   - Verify user counts match database
   - Verify review counts match database
   - Verify team counts match database
   - Verify calculated metrics (acceptance rate, avg issues)

2. **Real-time Update Tests**
   - Create new user, verify count updates
   - Complete review, verify metrics update
   - Change user role, verify audit log created
   - Delete team, verify counts update

## Implementation Phases

### Phase 1: Remove Dummy Data and System Health Bar
- Remove system health status bar from AdminAnalyticsDashboard
- Update all API calls to fetch real data
- Remove hardcoded values from components
- Implement proper empty states

### Phase 2: Implement User Role Editing
- Create UserEditModal component
- Implement role change API integration
- Add inline role dropdown
- Implement audit logging for role changes
- Add success/error feedback

### Phase 3: Enhance Analytics with Team Filtering
- Add "All Users" option to team filter
- Set "All Users" as default selection
- Update analytics API to support team_id=null
- Update all charts and metrics to respect filter
- Maintain date range filtering

### Phase 4: Integrate Feedback Dashboard
- Create feedback statistics components
- Add feedback tab to analytics view
- Integrate GlobalFeedbackTable component
- Implement team filtering for feedback data
- Add feedback pattern visualization

### Phase 5: Clean Up Audit Logs
- Remove "platform" option from filters
- Simplify action type options
- Ensure all admin actions create audit entries
- Test audit log creation for all operations

### Phase 6: Testing and Validation
- Write unit tests for all components
- Write integration tests for API endpoints
- Perform data accuracy validation
- Test with real production-like data
- Performance testing with large datasets

## Security Considerations

1. **Authentication**
   - All admin endpoints require authentication
   - JWT token validation on every request
   - Token expiration handling

2. **Authorization**
   - Role-based access control (RBAC)
   - Admin-only endpoints protected
   - Team lead restrictions enforced
   - Prevent self-role modification

3. **Audit Trail**
   - Log all admin actions
   - Include user ID, timestamp, IP address
   - Store before/after values for changes
   - Immutable audit log entries

4. **Data Protection**
   - Sanitize all user inputs
   - Prevent SQL injection
   - Prevent XSS attacks
   - Rate limiting on API endpoints

5. **Privacy**
   - Don't expose sensitive user data
   - Mask email addresses where appropriate
   - Limit data access based on role

## Performance Considerations

1. **Database Queries**
   - Use indexed columns for filtering
   - Implement pagination for large datasets
   - Cache frequently accessed data (with TTL)
   - Use database aggregation functions

2. **Frontend Optimization**
   - Lazy load components
   - Debounce search inputs
   - Virtualize long lists
   - Memoize expensive calculations

3. **API Response Times**
   - Target < 200ms for simple queries
   - Target < 1s for complex analytics
   - Implement request timeouts
   - Show loading states

4. **Caching Strategy**
   - Cache platform statistics (5 minute TTL)
   - Cache team lists (10 minute TTL)
   - Invalidate cache on data changes
   - Use Redis for distributed caching

## Monitoring and Observability

1. **Metrics to Track**
   - API response times
   - Error rates by endpoint
   - User action frequency
   - Database query performance

2. **Logging**
   - Log all admin actions
   - Log API errors with context
   - Log slow queries (> 1s)
   - Log authentication failures

3. **Alerts**
   - Alert on high error rates
   - Alert on slow response times
   - Alert on authentication failures
   - Alert on database connection issues

## Accessibility

1. **Keyboard Navigation**
   - All interactive elements keyboard accessible
   - Proper tab order
   - Focus indicators visible

2. **Screen Readers**
   - Semantic HTML elements
   - ARIA labels where needed
   - Descriptive button text
   - Table headers properly marked

3. **Visual Design**
   - Sufficient color contrast
   - Don't rely solely on color
   - Readable font sizes
   - Clear error messages

## Migration Strategy

1. **Backward Compatibility**
   - Maintain existing API contracts
   - Add new endpoints without breaking old ones
   - Deprecate old endpoints gradually

2. **Data Migration**
   - No database schema changes required
   - Verify data integrity before deployment
   - Test with production data snapshot

3. **Rollout Plan**
   - Deploy backend changes first
   - Deploy frontend changes after backend stable
   - Monitor error rates closely
   - Have rollback plan ready

4. **User Communication**
   - Notify admins of upcoming changes
   - Provide documentation for new features
   - Offer training if needed
   - Collect feedback after deployment
