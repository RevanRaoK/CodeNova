# Implementation Plan

- [x] 1. Remove system health status bar and update dashboard metrics display
  - Remove system health status bar component from AdminAnalyticsDashboard.jsx
  - Update dashboard metrics cards to display real data from API
  - Implement proper empty state handling for zero values
  - _Requirements: 2.1, 2.2, 2.3, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 2. Create backend endpoint for dashboard metrics with reviews today
  - Add new endpoint `GET /api/v1/admin/analytics/dashboard-metrics` in admin.py
  - Implement service method to calculate reviews completed today
  - Return accurate counts for total_users, active_teams, reviews_today, and recent_activities
  - Write unit tests for dashboard metrics calculation
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 3. Update frontend to fetch and display real dashboard data
  - Modify AdminAnalyticsDashboard.jsx to call new dashboard metrics endpoint
  - Remove all hardcoded values (1234 users, etc.)
  - Display actual data from API response
  - Handle loading and error states properly
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 4. Implement user role editing modal component
  - Create UserEditModal.jsx component with role dropdown, team selector, and status toggle
  - Add modal state management in UserManagementPanel.jsx
  - Implement form validation (prevent self-role modification)
  - Add save and cancel handlers
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

- [x] 5. Connect user role editing to backend API
  - Integrate PUT /api/v1/admin/users/{user_id}/role endpoint
  - Integrate PUT /api/v1/admin/users/{user_id}/team/{team_id} endpoint
  - Integrate PUT /api/v1/admin/users/{user_id}/status endpoint
  - Display success/error toast notifications
  - Refresh user list after successful update
  - _Requirements: 4.4, 4.5, 4.6, 4.7, 4.8_

- [x] 6. Verify and enhance audit logging for user role changes
  - Verify audit log entries are created when roles are updated
  - Ensure audit logs include before/after values
  - Test audit log creation for team assignment changes
  - Test audit log creation for status changes
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 7. Add "All Users" option to analytics team filter
  - Update AdminAnalyticsDashboard.jsx team filter dropdown
  - Add "All Users" as first option with value null
  - Set "All Users" as default selection
  - Update filter state management to handle null team_id
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 8. Update backend analytics endpoints to support "All Users" filtering
  - Modify GlobalAnalyticsService.get_platform_stats to accept optional team_id parameter
  - Modify GlobalAnalyticsService.get_global_issue_trends to filter by team when team_id provided
  - When team_id is null, aggregate data across all users
  - Update API endpoints to pass team_id parameter to service methods
  - Write unit tests for team filtering logic
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 9. Update frontend analytics to respect team filter selection
  - Pass selected team_id to all analytics API calls
  - Update charts and metrics when team filter changes
  - Maintain date range filter functionality
  - Show loading state during filter changes
  - _Requirements: 7.5, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [-] 10. Create feedback statistics API endpoint
  - Add endpoint `GET /api/v1/admin/analytics/feedback-stats` in admin.py
  - Implement service method to calculate feedback statistics (acceptance rate, rejection rate, modification rate)
  - Support team_id parameter for filtering
  - Return feedback counts and percentages
  - Write unit tests for feedback statistics calculation
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 11. Integrate feedback dashboard into admin analytics view
  - Add feedback statistics cards to AdminAnalyticsDashboard.jsx
  - Display total feedback, acceptance rate, rejection rate, modification rate
  - Integrate GlobalFeedbackTable component into feedback view tab
  - Apply team filter to feedback data
  - Add feedback patterns visualization
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 12. Remove "platform" option from audit logs filters
  - Update AuditLogPanel.jsx to remove "platform" from action type options
  - Simplify action type filter to only include actual admin actions
  - Update filter state management
  - Test filtering with simplified options
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [ ] 13. Verify user management displays accurate data
  - Test UserManagementPanel.jsx with real database data
  - Verify user count matches database
  - Verify team assignments display correctly
  - Verify role badges display correctly
  - Test search and filter functionality with real data
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 14. Verify team management displays accurate data
  - Test TeamManagementPanel.jsx with real database data
  - Verify team count matches database
  - Verify member counts are accurate
  - Test team deletion functionality
  - Verify empty state when no teams exist
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 15. Implement comprehensive error handling for all API calls
  - Add try-catch blocks to all API calls in admin components
  - Display user-friendly error messages via toast notifications
  - Log errors to console for debugging
  - Maintain previous state on error (don't clear data)
  - Test error scenarios (network failure, 500 errors, 403 errors)
  - _Requirements: 12.5_

- [ ] 16. Add empty state components for zero data scenarios
  - Create EmptyState component for reuse across admin panels
  - Display "0" for zero counts in metrics (not hide them)
  - Show helpful messages when no data exists (e.g., "No users yet")
  - Add empty state to user management, team management, and audit logs
  - _Requirements: 1.6, 3.3, 12.3_

- [ ] 17. Write integration tests for user role editing workflow
  - Test complete flow: open modal → change role → save → verify update
  - Test validation: prevent self-role modification
  - Test audit log creation after role change
  - Test error handling when update fails
  - Test UI updates after successful change
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

- [ ] 18. Write integration tests for analytics filtering
  - Test "All Users" filter shows aggregated data
  - Test specific team filter shows only that team's data
  - Test date range filter affects data correctly
  - Test combining team and date filters
  - Verify chart data updates when filters change
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ] 19. Write integration tests for feedback dashboard integration
  - Test feedback statistics display correctly
  - Test feedback data filters by team
  - Test GlobalFeedbackTable integration
  - Verify feedback patterns visualization
  - Test empty state when no feedback exists
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 20. Perform data accuracy validation tests
  - Create test script to verify user counts match database
  - Verify review counts match database
  - Verify team counts match database
  - Verify calculated metrics (acceptance rate, avg issues per review)
  - Test with various data scenarios (empty, small, large datasets)
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 21. Add loading states and optimize performance
  - Add skeleton loaders for dashboard metrics
  - Add loading spinners for table data
  - Implement debouncing for search inputs
  - Add pagination to large data tables
  - Test performance with large datasets (1000+ users, 10000+ reviews)
  - _Requirements: 5.4, 6.4_

- [ ] 22. Final end-to-end testing and bug fixes
  - Test complete admin dashboard workflow from login to all features
  - Verify no dummy data appears anywhere
  - Test all user interactions (clicks, filters, edits)
  - Fix any discovered bugs
  - Verify accessibility (keyboard navigation, screen readers)
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
