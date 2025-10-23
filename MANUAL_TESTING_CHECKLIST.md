# Manual Testing Checklist - CodeNova Platform Enhancements

## Overview
This document provides a comprehensive manual testing checklist for all 15 requirements of the CodeNova platform enhancements.

---

## Requirement 1: Multi-File Upload and Background Analysis

### Test Cases

#### TC1.1: Single File Upload
- [ ] Navigate to file upload interface
- [ ] Select a single Python file (.py)
- [ ] Verify file appears in upload queue
- [ ] Verify background job is created
- [ ] Check analysis history shows the filename
- [ ] Verify analysis completes successfully

#### TC1.2: Multiple File Upload
- [ ] Select 3-5 files simultaneously
- [ ] Verify all files appear in queue
- [ ] Verify UI remains responsive (non-blocking)
- [ ] Check all files are queued for analysis
- [ ] Verify each file has independent status

#### TC1.3: Filename Preservation
- [ ] Upload file named "test_module.py"
- [ ] Navigate to analysis history
- [ ] Verify exact filename "test_module.py" is displayed
- [ ] Check filename is associated with correct analysis

---

## Requirement 2: Filename Requirement for Monaco Editor

### Test Cases

#### TC2.1: Filename Prompt Display
- [ ] Open Monaco editor
- [ ] Write sample code
- [ ] Click "Analyze Code" button
- [ ] Verify filename prompt modal appears
- [ ] Verify analysis does NOT proceed without filename

#### TC2.2: Filename Validation
- [ ] Try submitting empty filename
- [ ] Verify validation error message appears
- [ ] Enter valid filename "example.js"
- [ ] Verify analysis proceeds

#### TC2.3: Filename in History
- [ ] Analyze code with filename "editor_test.py"
- [ ] Navigate to analysis history
- [ ] Verify "editor_test.py" appears in history
- [ ] Verify it's distinguishable from uploaded files

---

## Requirement 3: Enhanced Analysis History with Feedback

### Test Cases

#### TC3.1: View Analysis History
- [ ] Navigate to analysis history page
- [ ] Verify all previous analyses are displayed
- [ ] Verify filenames are shown for each analysis
- [ ] Check sorting and filtering options work

#### TC3.2: View Suggestions
- [ ] Click on an analysis from history
- [ ] Verify all suggestions/issues are displayed
- [ ] Check each suggestion has clear description
- [ ] Verify code snippets are properly formatted

#### TC3.3: Provide Feedback - Accept
- [ ] Select a suggestion
- [ ] Click "Accept" button
- [ ] Verify feedback is recorded
- [ ] Check suggestion status updates to "Accepted"

#### TC3.4: Provide Feedback - Reject
- [ ] Select a suggestion
- [ ] Click "Reject" button
- [ ] Optionally add comment
- [ ] Verify feedback is recorded
- [ ] Check suggestion status updates to "Rejected"

#### TC3.5: Provide Feedback - Modify
- [ ] Select a suggestion
- [ ] Click "Modify" button
- [ ] Edit the suggestion text
- [ ] Submit modified version
- [ ] Verify modified feedback is stored

---

## Requirement 4: Issue Trends Visualization

### Test Cases

#### TC4.1: Display Issue Trends Graph
- [ ] Navigate to user dashboard
- [ ] Verify Issue Trends Graph is displayed
- [ ] Check time-series data is shown
- [ ] Verify X-axis shows time periods
- [ ] Verify Y-axis shows issue counts

#### TC4.2: Issue Type Visualization
- [ ] Verify errors are shown in distinct color
- [ ] Verify security issues have distinct color
- [ ] Verify warnings have distinct color
- [ ] Check legend is clear and accurate

#### TC4.3: Interactive Features
- [ ] Hover over data points
- [ ] Verify tooltip shows detailed information
- [ ] Check date and issue counts are accurate
- [ ] Test time range selector (7d, 30d, 90d)

#### TC4.4: Insufficient Data Handling
- [ ] Test with new user account (no data)
- [ ] Verify appropriate message is displayed
- [ ] Check message indicates more analyses needed

---

## Requirement 5: Criticality Distribution Visualization

### Test Cases

#### TC5.1: Display Criticality Graph
- [ ] Navigate to user dashboard
- [ ] Verify Criticality Distribution Graph is displayed
- [ ] Check severity categories are shown (Severe, High, Medium, Low)
- [ ] Verify counts or percentages are displayed

#### TC5.2: Severity Categorization
- [ ] Verify color coding for each severity level
- [ ] Check severe issues are highlighted appropriately
- [ ] Verify percentages add up to 100%

#### TC5.3: Interactive Breakdown
- [ ] Click on a severity category
- [ ] Verify detailed breakdown is shown
- [ ] Check issue types within category are listed
- [ ] Test drill-down functionality

#### TC5.4: Empty State
- [ ] Test with account having no issues
- [ ] Verify appropriate empty state message
- [ ] Check UI handles zero issues gracefully

---

## Requirement 6: AI Suggestion Output Refinement

### Test Cases

#### TC6.1: Text-Only Suggestions
- [ ] Analyze code and get suggestions
- [ ] Verify suggestion descriptions are pure text
- [ ] Check no code is embedded in description text
- [ ] Verify readability of explanations

#### TC6.2: Code Extraction
- [ ] Find suggestion with code example
- [ ] Verify code is extracted and separated
- [ ] Check code appears in dedicated component
- [ ] Verify syntax highlighting is applied

#### TC6.3: Diff Viewer
- [ ] View suggestion with code changes
- [ ] Verify diff viewer shows original vs suggested
- [ ] Check side-by-side or inline diff display
- [ ] Verify changes are clearly highlighted

---

## Requirement 7: Admin User Management

### Test Cases

#### TC7.1: Access Admin Dashboard
- [ ] Login as admin user
- [ ] Navigate to Admin Dashboard
- [ ] Verify User Management interface is displayed
- [ ] Check non-admin users cannot access

#### TC7.2: View User List
- [ ] View list of all registered users
- [ ] Verify username, email, registration date shown
- [ ] Check role is displayed for each user
- [ ] Verify pagination works for large user lists

#### TC7.3: Search and Filter Users
- [ ] Use search box to find specific user
- [ ] Filter by role (user, admin, team_lead)
- [ ] Filter by team
- [ ] Filter by status (active/inactive)

#### TC7.4: View User Details
- [ ] Click on a user from the list
- [ ] Verify detailed user information is shown
- [ ] Check activity statistics are displayed
- [ ] Verify analysis history is accessible

#### TC7.5: Update User Role
- [ ] Select a user
- [ ] Change role from "user" to "team_lead"
- [ ] Verify confirmation prompt appears
- [ ] Confirm change
- [ ] Verify role is updated in database
- [ ] Check audit log entry is created

#### TC7.6: Activate/Deactivate User
- [ ] Select an active user
- [ ] Click "Deactivate" button
- [ ] Verify confirmation prompt
- [ ] Confirm deactivation
- [ ] Verify user cannot login
- [ ] Reactivate and verify login works

---

## Requirement 8: Admin Team Management

### Test Cases

#### TC8.1: Access Team Management
- [ ] Navigate to Team Management interface
- [ ] Verify team list is displayed
- [ ] Check "Create Team" button is visible

#### TC8.2: Create New Team
- [ ] Click "Create Team" button
- [ ] Enter team name "Backend Team"
- [ ] Enter optional description
- [ ] Submit form
- [ ] Verify team is created
- [ ] Check team appears in team list

#### TC8.3: View Team Details
- [ ] Click on a team from the list
- [ ] Verify team name and description shown
- [ ] Check list of team members is displayed
- [ ] Verify member count is accurate

#### TC8.4: Add User to Team
- [ ] Open team details
- [ ] Click "Add Member" button
- [ ] Select user from dropdown
- [ ] Confirm addition
- [ ] Verify user appears in team member list
- [ ] Check user's profile shows team association

#### TC8.5: Remove User from Team
- [ ] Open team details
- [ ] Select a team member
- [ ] Click "Remove" button
- [ ] Verify confirmation prompt
- [ ] Confirm removal
- [ ] Check user is removed from team
- [ ] Verify user's team_id is cleared

#### TC8.6: Delete Team
- [ ] Select a team
- [ ] Click "Delete Team" button
- [ ] Verify strong confirmation prompt
- [ ] Confirm deletion
- [ ] Check team is removed
- [ ] Verify team members' team_id is cleared

---

## Requirement 9: Global Platform Analytics

### Test Cases

#### TC9.1: View Platform Metrics
- [ ] Navigate to Admin Analytics Dashboard
- [ ] Verify total users count is displayed
- [ ] Check total teams count is shown
- [ ] Verify total code reviews count is accurate
- [ ] Check active users (last 30 days) is shown

#### TC9.2: Issue Statistics
- [ ] Verify total errors count is displayed
- [ ] Check total warnings count
- [ ] Verify total security issues count
- [ ] Check aggregation is across all users

#### TC9.3: Activity Trends
- [ ] Verify time-series chart for platform activity
- [ ] Check trends over time are displayed
- [ ] Verify data is aggregated from all users
- [ ] Test different time ranges

---

## Requirement 10: Global Code Review Insights

### Test Cases

#### TC10.1: View All Reviews
- [ ] Navigate to global reviews section
- [ ] Verify all code reviews are listed
- [ ] Check reviews from all users are included
- [ ] Verify pagination works

#### TC10.2: Feedback Aggregation
- [ ] View aggregated feedback data
- [ ] Verify total acceptances count
- [ ] Check total rejections count
- [ ] Verify acceptance rate calculation is correct

#### TC10.3: Drill-Down Functionality
- [ ] Click on a specific review
- [ ] Verify detailed view opens
- [ ] Check user information is shown
- [ ] Verify code and suggestions are accessible

#### TC10.4: Privacy Compliance
- [ ] Verify aggregated data is shown by default
- [ ] Check raw code is not visible without authorization
- [ ] Test access to individual user data
- [ ] Verify audit log entry when accessing private data

---

## Requirement 11: Global Issue Visualization

### Test Cases

#### TC11.1: Platform-Wide Issue Trends
- [ ] View global Issue Trends Graph
- [ ] Verify data is aggregated from all users
- [ ] Check all issue types are represented
- [ ] Verify time-series visualization

#### TC11.2: Platform-Wide Criticality Distribution
- [ ] View global Criticality Distribution Graph
- [ ] Verify severity levels across all analyses
- [ ] Check aggregation is accurate
- [ ] Verify percentages are calculated correctly

#### TC11.3: Filtering Options
- [ ] Filter by specific team
- [ ] Filter by date range
- [ ] Filter by user (if authorized)
- [ ] Verify filtered data is accurate

#### TC11.4: Insufficient Data Handling
- [ ] Test with minimal platform activity
- [ ] Verify appropriate message is shown
- [ ] Check UI handles edge cases gracefully

---

## Requirement 12: Input and System Validation

### Test Cases

#### TC12.1: File Type Validation
- [ ] Try uploading .exe file
- [ ] Verify rejection with clear error message
- [ ] Try uploading .zip file
- [ ] Verify rejection
- [ ] Upload valid .py file
- [ ] Verify acceptance

#### TC12.2: File Size Validation
- [ ] Try uploading file > 5MB
- [ ] Verify rejection with size limit message
- [ ] Upload file < 5MB
- [ ] Verify acceptance

#### TC12.3: Code Content Validation
- [ ] Submit malformed code
- [ ] Verify descriptive error message
- [ ] Check error indicates the issue
- [ ] Submit valid code
- [ ] Verify analysis proceeds

#### TC12.4: Analysis Failure Handling
- [ ] Trigger analysis failure (e.g., timeout)
- [ ] Verify status shows "Failed" in history
- [ ] Check user-friendly error message is displayed
- [ ] Verify error is logged

#### TC12.5: High-Risk Action Confirmation
- [ ] Attempt to delete a team
- [ ] Verify confirmation dialog appears
- [ ] Check warning message is clear
- [ ] Cancel and verify no action taken
- [ ] Confirm and verify action completes

---

## Requirement 13: Real-Time Job Status Updates

### Test Cases

#### TC13.1: Initial Job Status
- [ ] Upload file for analysis
- [ ] Verify job appears in "Processing" state immediately
- [ ] Check status is visible in analysis history

#### TC13.2: Real-Time Updates (WebSocket)
- [ ] Start analysis job
- [ ] Keep analysis history page open
- [ ] Verify status updates in real-time
- [ ] Check no manual refresh is needed
- [ ] Verify WebSocket connection is established

#### TC13.3: Polling Fallback
- [ ] Disable WebSocket (if possible)
- [ ] Start analysis job
- [ ] Verify polling mechanism activates
- [ ] Check status updates periodically
- [ ] Verify updates occur every few seconds

#### TC13.4: Completion Status
- [ ] Wait for analysis to complete
- [ ] Verify status automatically updates to "Completed"
- [ ] Check results are automatically refreshed
- [ ] Verify no manual refresh needed

#### TC13.5: Timeout Handling
- [ ] Trigger long-running analysis
- [ ] Wait for timeout period
- [ ] Verify status changes to "Timeout"
- [ ] Check user is notified

---

## Requirement 14: Data Privacy and Access Control

### Test Cases

#### TC14.1: User Data Isolation
- [ ] Login as User A
- [ ] Verify only User A's analyses are visible
- [ ] Try to access User B's analysis (via URL manipulation)
- [ ] Verify access is denied (403 error)

#### TC14.2: Admin Data Access
- [ ] Login as admin
- [ ] View global analytics
- [ ] Verify aggregated data is shown by default
- [ ] Check raw code is not immediately visible

#### TC14.3: Audit Logging
- [ ] Perform admin action (e.g., change user role)
- [ ] Check audit log
- [ ] Verify entry exists with timestamp
- [ ] Check admin user ID is recorded
- [ ] Verify action details are logged

#### TC14.4: Role-Based Access Control
- [ ] Login as regular user
- [ ] Try to access admin endpoints
- [ ] Verify 403 Forbidden error
- [ ] Login as admin
- [ ] Verify admin endpoints are accessible

#### TC14.5: Secure Data Storage
- [ ] Check database for user data
- [ ] Verify passwords are hashed
- [ ] Check sensitive data is encrypted
- [ ] Verify no plain-text secrets

---

## Requirement 15: Comprehensive Testing Suite

### Test Cases

#### TC15.1: Backend Unit Tests
- [ ] Run: `cd backend && python -m pytest`
- [ ] Verify all unit tests pass
- [ ] Check test coverage report
- [ ] Verify coverage > 80% for new code

#### TC15.2: Frontend Component Tests
- [ ] Run: `cd frontend && npm test`
- [ ] Verify all component tests pass
- [ ] Check test coverage
- [ ] Verify coverage > 70% for new components

#### TC15.3: Integration Tests
- [ ] Run integration test suite
- [ ] Verify file upload workflow tests pass
- [ ] Check analysis workflow tests pass
- [ ] Verify feedback workflow tests pass

#### TC15.4: Admin Feature Tests
- [ ] Run admin-specific tests
- [ ] Verify user management tests pass
- [ ] Check team management tests pass
- [ ] Verify analytics tests pass

#### TC15.5: End-to-End Tests
- [ ] Run E2E test suite
- [ ] Verify critical user journeys pass
- [ ] Check complete workflows function
- [ ] Verify cross-feature integration

---

## Cross-Browser Testing

### Browsers to Test
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Key Features to Test in Each Browser
- [ ] File upload functionality
- [ ] Charts and visualizations render correctly
- [ ] WebSocket connections work
- [ ] Admin dashboard displays properly
- [ ] Responsive design works on different screen sizes

---

## Performance Testing

### Load Testing
- [ ] Test with 10 concurrent file uploads
- [ ] Test with 50 concurrent users
- [ ] Verify system remains responsive
- [ ] Check database query performance
- [ ] Monitor memory usage

### Response Time Testing
- [ ] File upload response < 2 seconds
- [ ] Analysis completion < 30 seconds (typical file)
- [ ] Dashboard load time < 3 seconds
- [ ] API endpoint response < 500ms

---

## Security Testing

### Authentication Testing
- [ ] Test login with invalid credentials
- [ ] Test session timeout
- [ ] Test token expiration
- [ ] Verify logout clears session

### Authorization Testing
- [ ] Test unauthorized endpoint access
- [ ] Test privilege escalation attempts
- [ ] Verify RBAC enforcement
- [ ] Test cross-user data access

### Input Validation Testing
- [ ] Test SQL injection attempts
- [ ] Test XSS attempts
- [ ] Test file upload exploits
- [ ] Test API parameter tampering

---

## Deployment Readiness

### Pre-Deployment Checklist
- [ ] All tests passing
- [ ] No critical bugs
- [ ] Documentation complete
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] Backup strategy in place
- [ ] Rollback plan documented
- [ ] Monitoring configured
- [ ] Logging configured
- [ ] SSL certificates valid

---

## Sign-Off

### Testing Team
- [ ] Manual testing completed
- [ ] All critical issues resolved
- [ ] Test report generated
- [ ] Sign-off date: ___________

### Development Team
- [ ] All features implemented
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Sign-off date: ___________

### Product Owner
- [ ] Requirements verified
- [ ] Acceptance criteria met
- [ ] Ready for production
- [ ] Sign-off date: ___________

---

## Notes and Issues

### Issues Found During Testing
1. 
2. 
3. 

### Resolved Issues
1. 
2. 
3. 

### Known Limitations
1. 
2. 
3. 

---

**Testing Completed By:** ___________
**Date:** ___________
**Version:** ___________
