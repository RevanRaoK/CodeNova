# Admin Dashboard Components

This directory contains all admin dashboard components for the CodeNova platform.

## Components Overview

### Main Dashboard
- **AdminDashboard.jsx** - Main admin dashboard with tabbed interface and navigation

### User Management
- **UserManagementPanel.jsx** - User management with searchable table, filters, role/status/team assignment
  - Features: Search, filter by team, sort, pagination
  - Permission-based: Prevents self-role modification
  - Requirements: 7.1, 7.2, 7.3, 7.4, 7.5

### Team Management
- **TeamManagementPanel.jsx** - Team CRUD operations with member management
  - Features: Create, edit, delete teams with confirmation dialogs
  - Member management capabilities
  - Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6

### Analytics & Insights
- **AdminAnalyticsDashboard.jsx** - Global analytics dashboard with platform stats
  - Features: Platform-wide metrics, global charts, multiple views
  - Includes: GlobalReviewsTable, GlobalFeedbackTable, TeamComparisonChart
  - Requirements: 9.1, 9.2, 9.3, 9.4, 10.1, 10.2, 10.3, 10.4

- **TeamAnalyticsPanel.jsx** - Team-specific analytics and performance metrics
  - Features: Usage trends, member performance, feedback distribution
  - Requirements: Team performance tracking

- **PlatformStatsPanel.jsx** - Platform statistics and system health
  - Features: Usage statistics, performance metrics, system health indicators

### Data Tables
- **GlobalReviewsTable.jsx** - All code reviews across the platform
  - Features: Filtering, pagination, sorting, search
  - Requirements: 10.1, 10.2, 10.3, 10.4

- **GlobalFeedbackTable.jsx** - All feedback across the platform
  - Features: Feedback type filtering, summary statistics
  - Requirements: 10.1, 10.2, 10.3, 10.4

### Visualizations
- **TeamComparisonChart.jsx** - Team performance comparison
  - Features: Bar chart, radar chart, table view
  - Metrics: Reviews, acceptance rates, code quality
  - Requirements: 9.1, 9.2, 9.3, 9.4

### Audit & Logging
- **AuditLogPanel.jsx** - System audit logs with filtering
  - Features: Action filtering, date range, user filtering
  - Requirements: 14.4

## Permission-Based Rendering

All components implement permission-based rendering:
- Admin-only features are restricted
- Self-modification prevention (users can't change their own role/status)
- Team leads can only view their own team data
- Confirmation dialogs for high-risk actions

## Usage

```jsx
import AdminDashboard from './components/AdminDashboard';

// In your app
<AdminDashboard activeSection="users" />
```

## API Integration

Components integrate with:
- `adminService.js` - Admin-specific operations
- `analyticsService.js` - Analytics data
- Backend endpoints under `/admin/*`

## Requirements Coverage

Task 7 Requirements:
- ✅ 7.1, 7.2, 7.3, 7.4, 7.5 - User Management
- ✅ 8.1, 8.2, 8.3, 8.4, 8.5, 8.6 - Team Management
- ✅ 9.1, 9.2, 9.3, 9.4 - Global Analytics
- ✅ 10.1, 10.2, 10.3, 10.4 - Global Reviews & Feedback
- ✅ 11.1, 11.2, 11.3, 11.4 - Visualizations
- ✅ 12.5 - Confirmation Dialogs
- ✅ 14.4 - Audit Logging
