# Routing, Navigation, and Integration Guide

## Overview

This document describes the routing, navigation, and integration enhancements implemented for the CodeNova platform as part of Task 10.

## Table of Contents

1. [Application Routing](#application-routing)
2. [Route Guards](#route-guards)
3. [Navigation Menu](#navigation-menu)
4. [File Upload Integration](#file-upload-integration)
5. [Feedback Learning Integration](#feedback-learning-integration)
6. [Loading and Empty States](#loading-and-empty-states)
7. [Usage Examples](#usage-examples)

---

## Application Routing

### Main Routes

The application uses React Router v6 for client-side routing. All routes are defined in `frontend/src/App.tsx`.

#### Public Routes
- `/` - Homepage (smart route that redirects authenticated users to dashboard)
- `/login` - User login page
- `/signup` - User registration page
- `/github/callback` - GitHub OAuth callback handler

#### Protected Routes (Require Authentication)
- `/dashboard` - Main user dashboard with analytics
- `/code-review` - Code review interface with file upload
- `/analysis-history` - View past code analyses
- `/pattern-library` - Legacy route (redirects to analysis-history)
- `/feedback-dashboard` - View and manage feedback
- `/github` - GitHub integration settings
- `/settings` - User settings
- `/profile` - User profile management
- `/integration-demo` - Demo page showing all integrated features

#### Admin Routes (Require Admin/Team Lead Role)
- `/admin` - Admin dashboard overview
- `/admin/users` - User management panel
- `/admin/teams` - Team management panel
- `/admin/analytics` - Team analytics
- `/admin/audit` - Audit log viewer
- `/admin/stats` - Platform statistics

### Route Structure

```typescript
<Routes>
  {/* Public routes */}
  <Route path="/" element={<HomeRoute />} />
  <Route path="/login" element={<Login />} />
  <Route path="/signup" element={<Signup />} />
  
  {/* Admin routes with role-based access */}
  <Route path="/admin/*" element={<AdminRouter />} />
  
  {/* Protected user routes */}
  <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
    <Route path="/dashboard" element={<Dashboard />} />
    {/* ... other protected routes */}
  </Route>
</Routes>
```

---

## Route Guards

### ProtectedRoute Component

Location: `frontend/components/ProtectedRoute.jsx`

The `ProtectedRoute` component provides authentication and authorization checks:

#### Features
- **Authentication Check**: Verifies user is logged in
- **Role-Based Access**: Optional role checking for restricted routes
- **Loading States**: Shows loading spinner during auth verification
- **Redirect Handling**: Preserves intended destination for post-login redirect
- **Access Denied UI**: User-friendly message for unauthorized access

#### Usage

```jsx
// Basic authentication check
<ProtectedRoute>
  <Dashboard />
</ProtectedRoute>

// With role-based access control
<ProtectedRoute allowedRoles={['admin', 'team_lead']}>
  <AdminDashboard />
</ProtectedRoute>

// With custom redirect
<ProtectedRoute redirectTo="/admin/login">
  <AdminPanel />
</ProtectedRoute>
```

#### Props
- `children` (ReactNode): Protected content to render
- `allowedRoles` (string[]): Optional array of roles that can access the route
- `redirectTo` (string): Custom redirect path (default: '/login')

### AdminRouter Component

Location: `frontend/components/AdminRouter.jsx`

Specialized router for admin routes with built-in role checking:

```jsx
<AdminRouter />
// Automatically checks for 'admin' or 'team_lead' role
// Redirects to /admin/login if not authenticated
// Shows access denied if authenticated but not authorized
```

---

## Navigation Menu

### Sidebar Component

Location: `frontend/components/Layout/Sidebar.jsx`

The sidebar navigation has been enhanced with:

#### Features
- **Role-Based Menu Items**: Admin section only visible to admins/team leads
- **Organized Sections**: Grouped by functionality (Main, Analysis, Integrations, Administration, Account)
- **Active State Highlighting**: Visual indication of current page
- **Responsive Design**: Mobile-friendly with backdrop overlay
- **Smooth Transitions**: Animated open/close

#### Menu Structure

```
Main
  - Dashboard
  - Code Review

Analysis
  - Analysis History
  - Feedback

Integrations
  - GitHub

Administration (Admin/Team Lead only)
  - Admin Dashboard

Account
  - Settings
  - Profile
```

#### Implementation

```jsx
// Role-based rendering
const isAdmin = user?.role === 'admin' || user?.role === 'team_lead';

{isAdmin && (
  <div className="mb-4">
    <div className="text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-2 px-4">
      Administration
    </div>
    <NavLink to="/admin">
      <ShieldIcon />
      <span>Admin Dashboard</span>
    </NavLink>
  </div>
)}
```

### AdminLayout Sidebar

Location: `frontend/components/Layout/AdminLayout.jsx`

Separate navigation for admin pages with:
- Platform statistics
- User management
- Team management
- Analytics
- Audit logs
- Back to main app link

---

## File Upload Integration

### FileUploadIntegration Component

Location: `frontend/components/FileUploadIntegration.jsx`

Integrated component that connects file upload → analysis → results workflow.

#### Features
- **Drag and Drop**: Intuitive file upload
- **Automatic Analysis**: Triggers analysis immediately after upload
- **Progress Tracking**: Real-time upload and analysis progress
- **Batch Processing**: Handles multiple files
- **Auto-Navigation**: Optional redirect to results page
- **Status Polling**: Monitors batch analysis completion

#### Usage

```jsx
import FileUploadIntegration from '../components/FileUploadIntegration';

<FileUploadIntegration
  onAnalysisComplete={(results) => {
    console.log('Analysis complete:', results);
  }}
  autoNavigate={true} // Redirect to analysis history when done
/>
```

#### Workflow

1. User uploads files (drag-drop or click)
2. Files are validated and uploaded to server
3. Batch analysis is automatically triggered
4. Component polls for batch status
5. Results are displayed when complete
6. Optional navigation to detailed results

#### Integration Points

- **Upload Service**: `analysisService.uploadMultipleFiles()`
- **Batch Status**: `analysisService.getBatchStatus()`
- **Results**: `analysisService.getBatchAnalysisResults()`
- **Notifications**: Uses `useNotification` hook for user feedback

---

## Feedback Learning Integration

### FeedbackLearningIntegration Component

Location: `frontend/components/FeedbackLearningIntegration.jsx`

Connects user feedback to the AI learning module.

#### Features
- **Three Feedback Types**: Accept, Reject, Modify
- **Modification Input**: Allow users to suggest improvements
- **Learning Impact Display**: Shows how feedback improves the model
- **Optional Comments**: Additional context for feedback
- **Real-time Updates**: Immediate feedback submission

#### Usage

```jsx
import FeedbackLearningIntegration from '../components/FeedbackLearningIntegration';

<FeedbackLearningIntegration
  issueId="issue-123"
  suggestion="Use const instead of let"
  onFeedbackSubmit={(result) => {
    console.log('Feedback submitted:', result);
    console.log('Learning impact:', result.learning_impact);
  }}
/>
```

#### Feedback Flow

1. User views AI suggestion
2. User provides feedback (accept/reject/modify)
3. Feedback is sent to learning module
4. Learning module updates AI model
5. User sees impact metrics (confidence improvement, etc.)

#### Integration Points

- **Feedback Service**: `feedbackService.submitFeedback()`
- **Learning Module**: Backend processes feedback for model improvement
- **Notifications**: Success/error messages via `useNotification`

---

## Loading and Empty States

### LoadingState Component

Location: `frontend/components/LoadingState.jsx`

Reusable loading state component with multiple variants.

#### Variants

1. **Spinner**: Rotating loader icon
2. **Dots**: Bouncing dots animation
3. **Pulse**: Pulsing circle
4. **Skeleton**: Content placeholder

#### Usage

```jsx
import LoadingState from '../components/LoadingState';

// Spinner variant
<LoadingState 
  variant="spinner" 
  size="md" 
  message="Loading data..." 
/>

// Full screen loading
<LoadingState 
  variant="spinner" 
  size="lg" 
  message="Processing..." 
  fullScreen={true}
/>

// Skeleton for content loading
<LoadingState variant="skeleton" />
```

### EmptyState Component

Shows helpful messages when there's no data.

```jsx
import { EmptyState } from '../components/LoadingState';

<EmptyState
  icon={UploadIcon}
  title="No files uploaded yet"
  description="Upload your first code file to get started"
  action={
    <button onClick={handleUpload}>
      Upload Files
    </button>
  }
/>
```

### ErrorState Component

Displays error messages with retry functionality.

```jsx
import { ErrorState } from '../components/LoadingState';

<ErrorState
  title="Failed to load data"
  message="We couldn't load your analysis history"
  onRetry={handleRetry}
/>
```

---

## Usage Examples

### Example 1: Protected Route with Role Check

```jsx
// In App.tsx
<Route
  path="/admin/*"
  element={
    <ProtectedRoute allowedRoles={['admin', 'team_lead']}>
      <AdminLayout>
        <Routes>
          <Route path="/" element={<AdminDashboard />} />
          <Route path="/users" element={<UserManagement />} />
        </Routes>
      </AdminLayout>
    </ProtectedRoute>
  }
/>
```

### Example 2: File Upload with Analysis

```jsx
// In CodeReview page
import FileUploadIntegration from '../components/FileUploadIntegration';

function CodeReview() {
  const handleAnalysisComplete = (results) => {
    // Update UI with results
    setAnalysisResults(results);
    showSuccess('Analysis complete!');
  };

  return (
    <div>
      <h1>Code Review</h1>
      <FileUploadIntegration
        onAnalysisComplete={handleAnalysisComplete}
        autoNavigate={false}
      />
    </div>
  );
}
```

### Example 3: Feedback with Learning

```jsx
// In ReviewResults component
import FeedbackLearningIntegration from '../components/FeedbackLearningIntegration';

function ReviewResults({ issues }) {
  return (
    <div>
      {issues.map(issue => (
        <div key={issue.id}>
          <p>{issue.message}</p>
          <FeedbackLearningIntegration
            issueId={issue.id}
            suggestion={issue.suggestion}
            onFeedbackSubmit={(result) => {
              console.log('Learning impact:', result.learning_impact);
            }}
          />
        </div>
      ))}
    </div>
  );
}
```

### Example 4: Loading States

```jsx
// In Dashboard component
import LoadingState, { EmptyState, ErrorState } from '../components/LoadingState';

function Dashboard() {
  const { data, loading, error } = useDashboardData();

  if (loading) {
    return <LoadingState variant="spinner" message="Loading dashboard..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Failed to load dashboard"
        message={error.message}
        onRetry={refetch}
      />
    );
  }

  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon={ChartIcon}
        title="No data available"
        description="Start analyzing code to see your dashboard"
        action={<Link to="/code-review">Analyze Code</Link>}
      />
    );
  }

  return <DashboardContent data={data} />;
}
```

---

## Testing

### Manual Testing Checklist

- [ ] Navigate to all routes as unauthenticated user
- [ ] Verify redirects to login page
- [ ] Login and verify redirect to intended destination
- [ ] Test all navigation menu items
- [ ] Verify admin menu only shows for admin/team_lead
- [ ] Test file upload integration workflow
- [ ] Submit feedback and verify learning module connection
- [ ] Test all loading state variants
- [ ] Verify empty states display correctly
- [ ] Test error states with retry functionality
- [ ] Verify role-based access control
- [ ] Test mobile responsive navigation

### Integration Testing

```javascript
// Example test for protected route
describe('ProtectedRoute', () => {
  it('redirects to login when not authenticated', () => {
    render(
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    );
    expect(window.location.pathname).toBe('/login');
  });

  it('shows access denied for unauthorized role', () => {
    // Mock user with 'user' role
    render(
      <ProtectedRoute allowedRoles={['admin']}>
        <AdminPanel />
      </ProtectedRoute>
    );
    expect(screen.getByText(/access denied/i)).toBeInTheDocument();
  });
});
```

---

## Best Practices

1. **Always use ProtectedRoute** for authenticated pages
2. **Specify allowedRoles** for admin/restricted routes
3. **Show loading states** during async operations
4. **Use empty states** when no data is available
5. **Provide error states** with retry functionality
6. **Keep navigation organized** with logical grouping
7. **Test role-based access** thoroughly
8. **Use consistent loading patterns** across the app

---

## Troubleshooting

### Issue: Route not protected
**Solution**: Wrap route with `<ProtectedRoute>` component

### Issue: Admin menu not showing
**Solution**: Verify user role is 'admin' or 'team_lead'

### Issue: Redirect loop
**Solution**: Check that login page is not wrapped in ProtectedRoute

### Issue: File upload not triggering analysis
**Solution**: Verify `analysisService.uploadMultipleFiles()` is working

### Issue: Feedback not connecting to learning module
**Solution**: Check `feedbackService.submitFeedback()` API endpoint

---

## Future Enhancements

- [ ] Add breadcrumb navigation
- [ ] Implement route-based code splitting
- [ ] Add route transition animations
- [ ] Create navigation history tracking
- [ ] Add keyboard shortcuts for navigation
- [ ] Implement deep linking for analysis results
- [ ] Add route-level error boundaries
- [ ] Create navigation analytics tracking

---

## Related Documentation

- [Authentication Guide](./AUTHENTICATION_GUIDE.md)
- [Component Library](./COMPONENT_LIBRARY.md)
- [API Integration](./API_INTEGRATION.md)
- [Testing Guide](./TESTING_GUIDE.md)
