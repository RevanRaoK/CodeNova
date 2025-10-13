# CodeNova Development Tasks

## Implementation Plan

### Phase 1: Fix GitHub Integration Issues

- [ ] **Fix notification undefined error in GitHub OAuth flow**

  - Investigate "can't access property 'type', notification is undefined" error
  - Check notification context and state management in GitHub integration components
  - Add proper error handling for notification state

- [ ] **Fix 405 Method Not Allowed for OAuth authorize endpoint**

  - Debug "POST /api/v1/github/oauth/authorize HTTP/1.1" 405 error
  - Check backend route configuration for GitHub OAuth endpoints
  - Verify HTTP method handlers (GET vs POST) for OAuth authorization
  - Update frontend to use correct HTTP methods for OAuth flow

- [ ] **Test complete GitHub OAuth flow**
  - Verify OAuth initiation works correctly
  - Test OAuth callback handling
  - Ensure token storage and user association functions properly
  - Validate repository connection after OAuth completion

### Phase 2: Implement Multiple File Uploads with Message Queuing

- [ ] **Implement proper filename handling**

  - Allow users to specify custom filenames in Monaco editor
  - Preserve actual filenames for uploaded files
  - Update analysis history to show correct filenames instead of "code.extension"
  - Modify file metadata storage to include user-specified names

- [ ] **Integrate multiple file uploads into main code review route**

  - Remove separate multiple file upload route
  - Consolidate all file uploads into `/code-review` page
  - Update FileUploadZone component to handle both single and multiple files
  - Ensure message queuing works for batch file processing

- [ ] **Implement message queuing for file analysis**

  - Set up Redis-based job queue for background file analysis
  - Create job tracking system for multiple file processing
  - Add progress indicators for batch file analysis
  - Implement proper error isolation for individual files in batch operations

- [ ] **Update code review page UI**
  - Remove or minimize GitHub repository connection from `/code-review` page
  - Focus on file upload and analysis functionality
  - Add batch processing status and results display
  - Implement proper file management (add, remove, reorder)

### Phase 3: Implement Realtime Dashboards

- [ ] **Update user dashboard with realtime data**

  - Replace dummy data with actual user-specific metrics
  - Implement WebSocket or polling for realtime updates
  - Show user's personal review count, not global totals
  - Add realtime activity feed for user's actions

- [ ] **Update admin dashboard with realtime data**

  - Implement realtime user metrics (active users, not total users)
  - Add realtime system performance monitoring
  - Show actual review analytics instead of dummy data
  - Implement admin-specific realtime notifications

- [ ] **Update pattern library dashboard**

  - Add realtime pattern discovery and learning metrics
  - Implement live pattern usage statistics
  - Show actual pattern performance data

- [ ] **Implement WebSocket/real-time infrastructure**
  - Set up WebSocket server for realtime updates
  - Create client-side realtime update system
  - Add fallback polling mechanism for reliability
  - Implement proper connection management and error handling

## Technical Requirements

### Backend Requirements

- Redis message queue for job processing
- WebSocket server for realtime updates
- Enhanced file storage with metadata support
- Proper error handling and logging

### Frontend Requirements

- Realtime data synchronization
- Enhanced file upload interface
- Improved dashboard components
- Better error handling and user feedback

### Database Requirements

- File metadata storage with custom names
- User-specific analytics tracking
- Job queue status persistence
- Realtime event logging

## Testing Requirements

- Integration tests for GitHub OAuth flow
- Tests for multiple file upload and queuing
- Realtime dashboard update tests
- Error handling and edge case testing

## Deployment Considerations

- Redis server setup for message queuing
- WebSocket server configuration
- Database schema updates for new features
- Environment configuration for all new services</content>
  <parameter name="filePath">c:\Users\Revan Rao\Desktop\CodeNova\CodeNova-1\todo.md
