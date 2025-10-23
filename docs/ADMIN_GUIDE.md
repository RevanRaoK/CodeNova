# CodeNova Administrator Guide

## Table of Contents

1. [Admin Dashboard Overview](#admin-dashboard-overview)
2. [User Management](#user-management)
3. [Team Management](#team-management)
4. [Global Analytics](#global-analytics)
5. [Audit Logs](#audit-logs)
6. [Platform Monitoring](#platform-monitoring)
7. [Security and Permissions](#security-and-permissions)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Admin Dashboard Overview

### Accessing the Admin Dashboard

1. Log in with an administrator account
2. Click **"Admin"** in the navigation menu
3. You'll see the admin dashboard with multiple sections

### Dashboard Sections

The admin dashboard provides:

1. **Platform Overview**: Key metrics and statistics
2. **User Management**: View and manage all users
3. **Team Management**: Create and manage teams
4. **Global Analytics**: Platform-wide insights
5. **Audit Logs**: Track all administrative actions
6. **System Health**: Monitor platform performance

### Admin Roles

CodeNova has three user roles:

- **User**: Regular platform users
- **Team Lead**: Can view team analytics
- **Admin**: Full platform access (you!)

---

## User Management

### Viewing All Users

1. Navigate to **"User Management"** in the admin dashboard
2. See a table of all registered users
3. View key information:
   - Username and email
   - Role and status
   - Team assignment
   - Registration date
   - Last login

### Searching and Filtering Users

**Search**:
- Type in the search box to find users by username or email
- Results update in real-time

**Filter by**:
- **Team**: Show only users from a specific team
- **Role**: Filter by user, team_lead, or admin
- **Status**: Active or inactive users
- **Registration date**: Date range picker

**Sort by**:
- Username (A-Z or Z-A)
- Registration date (newest/oldest)
- Last login (most/least recent)
- Team name

### Viewing User Details

1. Click on any user in the table
2. See detailed information:
   - Contact information
   - Account status
   - Team membership
   - Activity statistics:
     - Total analyses performed
     - Feedback provided
     - Acceptance rate
     - Last activity date

### Managing User Roles

#### Promoting a User to Team Lead

1. Open the user's detail page
2. Click **"Change Role"**
3. Select **"Team Lead"**
4. Confirm the change
5. The user can now view team analytics

#### Promoting a User to Admin

⚠️ **Use with caution** - Admins have full platform access

1. Open the user's detail page
2. Click **"Change Role"**
3. Select **"Admin"**
4. Enter your password to confirm
5. The user now has admin privileges

#### Demoting a User

1. Open the user's detail page
2. Click **"Change Role"**
3. Select **"User"**
4. Confirm the change
5. Previous elevated permissions are removed

### Activating/Deactivating Users

#### Deactivate a User

When to deactivate:
- User leaves the organization
- Temporary suspension needed
- Account security concerns

Steps:
1. Open the user's detail page
2. Click **"Deactivate Account"**
3. Optionally add a reason
4. Confirm the action
5. User can no longer log in

#### Reactivate a User

1. Filter for inactive users
2. Open the user's detail page
3. Click **"Activate Account"**
4. Confirm the action
5. User can log in again

### Assigning Users to Teams

1. Open the user's detail page
2. Click **"Assign to Team"**
3. Select a team from the dropdown
4. Click **"Assign"**
5. User is now part of the team

### Removing Users from Teams

1. Open the user's detail page
2. Click **"Remove from Team"**
3. Confirm the action
4. User is no longer part of any team

### Bulk User Actions

Select multiple users to:
- Assign to a team
- Change status (activate/deactivate)
- Export user data
- Send notifications

---

## Team Management

### Creating a New Team

1. Navigate to **"Team Management"**
2. Click **"Create Team"**
3. Enter team information:
   - **Team Name**: Unique identifier (required)
   - **Description**: Purpose or focus area (optional)
4. Click **"Create"**
5. The team is now available for user assignment

### Viewing All Teams

The team list shows:
- Team name and description
- Number of members
- Creation date
- Team lead (if assigned)
- Activity metrics

### Managing Team Details

1. Click on a team to view details
2. See:
   - Team information
   - Member list
   - Team statistics:
     - Total analyses
     - Average issues per review
     - Feedback acceptance rate
     - Most active members

### Editing Team Information

1. Open the team's detail page
2. Click **"Edit Team"**
3. Update:
   - Team name
   - Description
4. Click **"Save Changes"**

### Managing Team Members

#### Adding Members to a Team

**Method 1: From Team Page**
1. Open the team's detail page
2. Click **"Add Members"**
3. Search for users
4. Select users to add
5. Click **"Add Selected"**

**Method 2: From User Page**
1. Open a user's detail page
2. Click **"Assign to Team"**
3. Select the team
4. Click **"Assign"**

#### Removing Members from a Team

1. Open the team's detail page
2. Find the member in the member list
3. Click **"Remove"** next to their name
4. Confirm the action

#### Assigning a Team Lead

1. Open the team's detail page
2. Find a team member
3. Click **"Make Team Lead"**
4. Confirm the action
5. The user's role is updated to team_lead

### Deleting a Team

⚠️ **Warning**: This action cannot be undone

Before deleting:
- Ensure all members are reassigned or removed
- Export team data if needed
- Notify team members

Steps:
1. Open the team's detail page
2. Click **"Delete Team"**
3. Type the team name to confirm
4. Enter your password
5. Click **"Delete Permanently"**

### Team Best Practices

1. **Naming Convention**: Use clear, descriptive names
   - ✅ "Backend Development Team"
   - ✅ "Frontend Team - Product A"
   - ❌ "Team 1"

2. **Team Size**: Keep teams manageable
   - Ideal: 5-10 members
   - Maximum: 20 members

3. **Team Structure**: Organize by:
   - Department (Backend, Frontend, DevOps)
   - Product (Product A, Product B)
   - Location (US Team, EU Team)
   - Function (Security, Performance)

4. **Regular Review**: Audit team membership quarterly

---

## Global Analytics

### Platform Statistics

The platform overview shows:

#### User Metrics
- **Total Users**: All registered users
- **Active Users (30d)**: Users who logged in recently
- **New Users (7d)**: Recent registrations
- **User Growth Rate**: Percentage increase

#### Team Metrics
- **Total Teams**: Number of teams
- **Average Team Size**: Members per team
- **Teams with Activity**: Teams with recent analyses

#### Analysis Metrics
- **Total Reviews**: All-time code reviews
- **Reviews (30d)**: Recent activity
- **Average Issues per Review**: Code quality indicator
- **Total Issues Found**: Cumulative issues detected

#### Feedback Metrics
- **Total Feedback**: All feedback provided
- **Feedback Participation Rate**: % of users providing feedback
- **Acceptance Rate**: % of suggestions accepted
- **Rejection Rate**: % of suggestions rejected

### Global Issue Trends

View platform-wide code quality trends:

#### Understanding the Graph

- **X-Axis**: Time periods
- **Y-Axis**: Issue counts
- **Lines**: Different issue types
  - Errors (red)
  - Warnings (yellow)
  - Security issues (blue)

#### Using the Graph

1. **Select Timeframe**: 7d, 30d, or 90d
2. **Filter by Team**: View specific team trends
3. **Compare Periods**: See month-over-month changes
4. **Export Data**: Download for reporting

#### What to Monitor

- **Increasing errors**: May indicate code quality issues
- **Security spikes**: Require immediate attention
- **Decreasing trends**: Positive sign of improvement
- **Team variations**: Identify teams needing support

### Global Criticality Distribution

See severity breakdown across the platform:

#### Severity Levels

- **Severe**: Critical issues (target: < 5%)
- **High**: Important issues (target: < 15%)
- **Medium**: Moderate issues (target: 30-40%)
- **Low**: Minor issues (target: 40-50%)

#### Using the Distribution

1. **Monitor severe issues**: Should be minimal
2. **Track improvements**: Over time
3. **Compare teams**: Identify outliers
4. **Set benchmarks**: For code quality

### Team Comparison

Compare performance across teams:

#### Metrics Compared

- **Total Reviews**: Activity level
- **Average Issues per Review**: Code quality
- **Feedback Acceptance Rate**: AI accuracy
- **Active Members**: Team engagement

#### Using Team Comparison

1. **Identify top performers**: Learn from them
2. **Find struggling teams**: Provide support
3. **Set benchmarks**: Based on top teams
4. **Track improvements**: Over time

### All Reviews Dashboard

View all code reviews across the platform:

#### Features

- **Searchable**: Find specific reviews
- **Filterable**: By team, date, user
- **Sortable**: By various criteria
- **Exportable**: Download data

#### Use Cases

- Audit code review activity
- Identify inactive users
- Track specific file types
- Generate reports

### All Feedback Dashboard

View all feedback across the platform:

#### Feedback Summary

- Total feedback count
- Acceptance rate
- Rejection rate
- Modification rate

#### Use Cases

- Monitor AI accuracy
- Identify feedback patterns
- Track user engagement
- Improve AI model

### Top Languages

See which programming languages are most used:

- Language name
- Number of analyses
- Percentage of total
- Trend (increasing/decreasing)

### Exporting Analytics Data

1. Navigate to any analytics view
2. Click **"Export"**
3. Choose format:
   - **PDF Report**: For presentations
   - **CSV Data**: For spreadsheets
   - **JSON**: For custom analysis
4. Select date range
5. Click **"Download"**

---

## Audit Logs

### What Are Audit Logs?

Audit logs track all administrative actions for:
- Security monitoring
- Compliance requirements
- Troubleshooting
- Accountability

### Viewing Audit Logs

1. Navigate to **"Audit Logs"** in admin dashboard
2. See chronological list of all actions
3. Each entry shows:
   - Timestamp
   - Admin user who performed action
   - Action type
   - Resource affected
   - Details of changes
   - IP address

### Filtering Audit Logs

**Filter by**:
- **User**: Specific administrator
- **Action Type**: 
  - User management (role changes, status updates)
  - Team management (create, update, delete)
  - System configuration
- **Resource Type**: User, team, system
- **Date Range**: Specific time period
- **IP Address**: Specific location

### Common Audit Log Actions

#### User Management Actions
- `update_user_role`: Role changed
- `update_user_status`: Account activated/deactivated
- `assign_user_to_team`: Team assignment
- `remove_user_from_team`: Team removal

#### Team Management Actions
- `create_team`: New team created
- `update_team`: Team information changed
- `delete_team`: Team deleted
- `add_team_member`: Member added
- `remove_team_member`: Member removed

#### System Actions
- `update_system_config`: Configuration changed
- `export_data`: Data exported
- `bulk_user_update`: Multiple users updated

### Audit Log Details

Click on any log entry to see:
- Full action details
- Before/after values
- User agent (browser)
- Session information
- Related actions

### Exporting Audit Logs

For compliance or reporting:

1. Apply desired filters
2. Click **"Export Audit Logs"**
3. Select format (CSV, PDF, JSON)
4. Choose date range
5. Download file

### Audit Log Retention

- **Standard**: 90 days
- **Compliance Mode**: 7 years
- **Archived**: Available on request

### Security Monitoring

Use audit logs to:

1. **Detect suspicious activity**:
   - Multiple failed login attempts
   - Unusual IP addresses
   - After-hours access
   - Bulk changes

2. **Track privilege escalation**:
   - Role changes
   - Permission grants
   - Admin account creation

3. **Monitor data access**:
   - User data exports
   - Bulk operations
   - Sensitive data access

---

## Platform Monitoring

### System Health Dashboard

Monitor platform performance:

#### Key Metrics

- **API Response Time**: Average latency
- **Error Rate**: Failed requests
- **Active Users**: Current sessions
- **Queue Status**: Background jobs
- **Database Performance**: Query times
- **Storage Usage**: Disk space

#### Health Indicators

- 🟢 **Green**: All systems operational
- 🟡 **Yellow**: Performance degraded
- 🔴 **Red**: Critical issues

### Background Job Queue

Monitor analysis queue:

- **Queued Jobs**: Waiting to process
- **Processing Jobs**: Currently running
- **Completed Jobs**: Finished successfully
- **Failed Jobs**: Errors occurred

#### Queue Management

- **Pause Queue**: Stop processing new jobs
- **Resume Queue**: Restart processing
- **Clear Failed**: Remove failed jobs
- **Retry Failed**: Reprocess failed jobs

### Database Monitoring

Track database health:

- **Connection Pool**: Available connections
- **Query Performance**: Slow queries
- **Table Sizes**: Storage usage
- **Index Health**: Optimization status

### Storage Monitoring

Monitor file storage:

- **Total Storage**: Used vs. available
- **File Count**: Number of uploaded files
- **Average File Size**: Storage patterns
- **Growth Rate**: Storage trends

### Performance Alerts

Configure alerts for:

- High error rates
- Slow response times
- Queue backlog
- Storage limits
- Database issues

---

## Security and Permissions

### Role-Based Access Control (RBAC)

#### User Permissions

Regular users can:
- ✅ Analyze their own code
- ✅ View their own analyses
- ✅ Provide feedback
- ❌ View other users' data
- ❌ Access admin features

#### Team Lead Permissions

Team leads can:
- ✅ All user permissions
- ✅ View team analytics
- ✅ See team member activity
- ❌ Modify team membership
- ❌ Access platform-wide data

#### Admin Permissions

Admins can:
- ✅ All team lead permissions
- ✅ Manage users and teams
- ✅ View platform analytics
- ✅ Access audit logs
- ✅ Configure system settings

### Security Best Practices

#### For Admin Accounts

1. **Use strong passwords**:
   - Minimum 12 characters
   - Mix of letters, numbers, symbols
   - No common words

2. **Enable 2FA**: Two-factor authentication

3. **Limit admin accounts**: Only create when necessary

4. **Regular audits**: Review admin access quarterly

5. **Separate accounts**: Don't use admin for daily work

#### For User Management

1. **Principle of least privilege**: Give minimum necessary access

2. **Regular reviews**: Audit user roles monthly

3. **Prompt deactivation**: Remove access immediately when users leave

4. **Team isolation**: Users should only see team data

5. **Audit logging**: Monitor all admin actions

#### For Data Privacy

1. **Anonymize analytics**: Remove PII from aggregated views

2. **Secure exports**: Encrypt exported data

3. **Access logging**: Track who views sensitive data

4. **Data retention**: Delete old data per policy

5. **Compliance**: Follow GDPR, CCPA, etc.

### Handling Security Incidents

#### Suspicious Activity Detected

1. **Investigate**: Check audit logs
2. **Contain**: Deactivate affected accounts
3. **Notify**: Inform security team
4. **Document**: Record all actions
5. **Review**: Update security policies

#### Compromised Account

1. **Immediate action**:
   - Deactivate account
   - Reset password
   - Revoke all sessions
   - Check audit logs

2. **Investigation**:
   - Review recent actions
   - Check for data access
   - Identify affected resources

3. **Recovery**:
   - Notify user
   - Secure account
   - Monitor for further issues

4. **Prevention**:
   - Require 2FA
   - Update security policies
   - Train users

---

## Best Practices

### Daily Admin Tasks

- ✅ Check system health dashboard
- ✅ Review overnight audit logs
- ✅ Monitor queue status
- ✅ Check for failed jobs

### Weekly Admin Tasks

- ✅ Review new user registrations
- ✅ Audit team memberships
- ✅ Check platform analytics
- ✅ Review security alerts
- ✅ Update documentation

### Monthly Admin Tasks

- ✅ User role audit
- ✅ Team structure review
- ✅ Performance analysis
- ✅ Storage cleanup
- ✅ Security review
- ✅ Generate reports

### Quarterly Admin Tasks

- ✅ Comprehensive security audit
- ✅ User access review
- ✅ Team reorganization (if needed)
- ✅ Policy updates
- ✅ Training sessions
- ✅ Disaster recovery test

### User Onboarding

1. **Create account**: Set up user profile
2. **Assign team**: Add to appropriate team
3. **Set role**: Assign correct permissions
4. **Send welcome**: Email with getting started guide
5. **Schedule training**: If needed

### User Offboarding

1. **Deactivate account**: Immediately
2. **Remove team membership**: Clean up teams
3. **Transfer ownership**: Reassign resources
4. **Export data**: If requested
5. **Document**: Record in audit log

### Team Management

1. **Regular reviews**: Check team composition
2. **Balance teams**: Keep sizes manageable
3. **Assign leads**: Ensure each team has leadership
4. **Monitor activity**: Track team engagement
5. **Facilitate collaboration**: Encourage best practices

---

## Troubleshooting

### Common Issues

#### Users Can't Log In

**Possible causes**:
- Account deactivated
- Password expired
- Email not verified
- System maintenance

**Solutions**:
1. Check user status in admin panel
2. Verify email confirmation
3. Reset password if needed
4. Check system status

#### Analysis Queue Backed Up

**Symptoms**:
- Long wait times
- Processing status stuck
- User complaints

**Solutions**:
1. Check queue status
2. Restart workers if needed
3. Clear failed jobs
4. Scale up resources

#### Team Members Can't See Team Data

**Possible causes**:
- Not assigned to team
- Wrong role
- Permission issue
- Cache problem

**Solutions**:
1. Verify team membership
2. Check user role
3. Clear cache
4. Review permissions

#### Analytics Not Updating

**Possible causes**:
- Cache issue
- Database lag
- Calculation job failed
- No new data

**Solutions**:
1. Refresh page
2. Clear cache
3. Check background jobs
4. Verify data exists

### Getting Help

#### Support Escalation

1. **Level 1**: Check documentation
2. **Level 2**: Contact support team
3. **Level 3**: Engineering team
4. **Level 4**: Emergency hotline

#### Emergency Contacts

- **System Down**: emergency@codenova.com
- **Security Issue**: security@codenova.com
- **Data Issue**: data@codenova.com
- **24/7 Hotline**: +1-555-CODE-911

---

## Appendix

### Keyboard Shortcuts

- `Ctrl+Shift+U`: User management
- `Ctrl+Shift+T`: Team management
- `Ctrl+Shift+A`: Analytics
- `Ctrl+Shift+L`: Audit logs
- `Ctrl+Shift+H`: System health

### API Access

Admins can access the API for automation:
- See API documentation
- Generate API keys
- Set up webhooks
- Automate reports

### Compliance

CodeNova complies with:
- GDPR (EU)
- CCPA (California)
- SOC 2 Type II
- ISO 27001

### Resources

- **Admin Forum**: forum.codenova.com/admin
- **Video Tutorials**: codenova.com/admin-training
- **API Docs**: api.codenova.com/docs
- **Status Page**: status.codenova.com

---

## Conclusion

As a CodeNova administrator, you play a crucial role in:
- Maintaining platform security
- Supporting users and teams
- Monitoring platform health
- Ensuring compliance
- Driving adoption

Thank you for keeping CodeNova running smoothly! 🚀
