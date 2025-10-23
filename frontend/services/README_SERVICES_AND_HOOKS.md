# Frontend Services and Hooks Documentation

This document provides an overview of the frontend services and custom hooks implemented for the CodeNova platform enhancements.

## Services

### 1. fileUploadService

Handles batch file uploads and analysis with comprehensive validation and progress tracking.

**Key Features:**
- Batch file upload with progress tracking
- File validation (size, type, content)
- Language detection from file extensions
- Upload time estimation
- Retry mechanism for failed uploads

**Usage Example:**
```javascript
import fileUploadService from './services/fileUploadService';

// Upload files
const result = await fileUploadService.uploadFilesBatch(files, {
  language: 'python',
  onProgress: (progress) => console.log(`Upload: ${progress}%`)
});

// Validate files before upload
const validation = fileUploadService.validateFiles(files);
if (!validation.isValid) {
  console.log('Invalid files:', validation.invalid);
}

// Get batch status
const status = await fileUploadService.getBatchStatus(batchId);
```

**API Methods:**
- `uploadFilesBatch(files, options)` - Upload multiple files
- `getBatchStatus(batchId)` - Get batch upload status
- `getBatchFiles(batchId)` - Get files in a batch
- `getFileStatus(batchId, fileId)` - Get individual file status
- `cancelBatch(batchId)` - Cancel batch upload
- `retryFailedFiles(batchId, fileIds)` - Retry failed files
- `validateFiles(files, options)` - Validate files before upload
- `detectLanguage(filename)` - Detect programming language
- `getSupportedExtensions()` - Get supported file extensions
- `estimateUploadTime(files, uploadSpeed)` - Estimate upload time

### 2. adminService (Enhanced)

Extended admin service with additional methods for user management, team management, analytics, and audit logs.

**New Methods:**
- `getUserDetails(userId)` - Get detailed user information
- `updateUserStatus(userId, isActive)` - Activate/deactivate user
- `assignUserToTeam(userId, teamId)` - Assign user to team
- `removeUserFromTeam(userId)` - Remove user from team
- `getTeamDetails(teamId)` - Get team details
- `getTeamMembers(teamId, options)` - Get team members
- `getPlatformStats(options)` - Get platform-wide statistics
- `getGlobalTrends(options)` - Get global analytics trends
- `getAllReviews(options)` - Get all code reviews
- `getAllFeedback(options)` - Get all feedback data
- `getTeamComparison(options)` - Compare team performance

**Usage Example:**
```javascript
import adminService from './services/adminService';

// Get platform statistics
const stats = await adminService.getPlatformStats({ dateRange: '30d' });

// Assign user to team
await adminService.assignUserToTeam(userId, teamId);

// Get all reviews with filters
const reviews = await adminService.getAllReviews({
  page: 1,
  page_size: 50,
  team_id: 'team-123',
  date_from: '2025-01-01'
});
```

## Custom Hooks

### 1. useAnalysisStatus

Tracks analysis status with WebSocket support and polling fallback for real-time updates.

**Features:**
- WebSocket connection for real-time updates
- Automatic fallback to HTTP polling
- Reconnection logic with exponential backoff
- Status change callbacks
- Progress tracking

**Usage Example:**
```javascript
import { useAnalysisStatus } from './hooks/useAnalysisStatus';

function AnalysisTracker({ analysisId }) {
  const {
    status,
    progress,
    isConnected,
    isComplete,
    isProcessing,
    refresh
  } = useAnalysisStatus(analysisId, {
    onStatusChange: (status, progress) => {
      console.log(`Status: ${status}, Progress: ${progress}%`);
    },
    onComplete: () => {
      console.log('Analysis completed!');
    }
  });

  return (
    <div>
      <p>Status: {status}</p>
      <p>Progress: {progress}%</p>
      <p>Connected: {isConnected ? 'Yes' : 'No'}</p>
      <button onClick={refresh}>Refresh</button>
    </div>
  );
}
```

**Options:**
- `enabled` - Start tracking immediately (default: true)
- `useWebSocket` - Use WebSocket connection (default: true)
- `pollingInterval` - Polling interval in ms (default: 3000)
- `onStatusChange` - Callback when status changes
- `onComplete` - Callback when analysis completes
- `onError` - Callback when analysis fails

**Return Values:**
- `status` - Current analysis status
- `progress` - Progress percentage (0-100)
- `error` - Error message if any
- `isConnected` - WebSocket connection status
- `lastUpdated` - Last update timestamp
- `isComplete` - Whether analysis is complete
- `isProcessing` - Whether analysis is in progress
- `isFailed` - Whether analysis failed
- `isSuccess` - Whether analysis succeeded
- `refresh()` - Manually refresh status
- `start()` - Start tracking
- `stop()` - Stop tracking

### 2. useFileUpload

Manages file selection, validation, and upload with progress tracking.

**Features:**
- File selection and validation
- Upload progress tracking
- Error handling with retry
- File statistics and estimation
- Cancellation support

**Usage Example:**
```javascript
import { useFileUpload } from './hooks/useFileUpload';

function FileUploader() {
  const {
    selectedFiles,
    uploadProgress,
    isUploading,
    hasFiles,
    selectFiles,
    uploadFiles,
    removeFile,
    clearFiles,
    getUploadStats
  } = useFileUpload({
    onUploadComplete: (result) => {
      console.log('Upload complete:', result);
    },
    onUploadError: (error) => {
      console.error('Upload failed:', error);
    }
  });

  const handleFileSelect = (e) => {
    selectFiles(e.target.files);
  };

  const handleUpload = async () => {
    await uploadFiles({ language: 'python' });
  };

  const stats = getUploadStats();

  return (
    <div>
      <input type="file" multiple onChange={handleFileSelect} />
      <p>Selected: {selectedFiles.length} files</p>
      {stats && <p>Total size: {stats.totalSizeMB} MB</p>}
      <button onClick={handleUpload} disabled={!hasFiles || isUploading}>
        Upload
      </button>
      {isUploading && <p>Progress: {uploadProgress}%</p>}
    </div>
  );
}
```

**Options:**
- `onUploadComplete` - Callback when upload completes
- `onUploadError` - Callback when upload fails
- `onValidationError` - Callback when validation fails
- `maxFileSize` - Maximum file size in bytes (default: 5MB)
- `allowedExtensions` - Allowed file extensions

**Return Values:**
- `selectedFiles` - Array of selected files
- `uploadProgress` - Upload progress (0-100)
- `isUploading` - Whether upload is in progress
- `uploadError` - Error message if any
- `batchId` - Batch ID after upload
- `uploadResult` - Upload result data
- `validationErrors` - Array of validation errors
- `hasFiles` - Whether files are selected
- `hasValidationErrors` - Whether validation errors exist
- `selectFiles(files)` - Select files for upload
- `addFiles(files)` - Add files to selection
- `removeFile(index)` - Remove file by index
- `clearFiles()` - Clear all files
- `uploadFiles(options)` - Upload selected files
- `cancelUpload()` - Cancel ongoing upload
- `retryUpload(options)` - Retry upload
- `validateFile(file)` - Validate single file
- `getUploadStats()` - Get upload statistics

### 3. useAdminAnalytics

Fetches and caches admin analytics data with automatic refresh capabilities.

**Features:**
- Data caching with configurable TTL
- Automatic refresh intervals
- Parallel data fetching
- Error handling per data type
- Cache status monitoring

**Usage Example:**
```javascript
import { useAdminAnalytics } from './hooks/useAdminAnalytics';

function AdminDashboard() {
  const {
    platformStats,
    globalTrends,
    teamComparison,
    isLoading,
    hasError,
    fetchPlatformStats,
    refreshAll,
    clearCache
  } = useAdminAnalytics({
    autoFetch: true,
    cacheTime: 5 * 60 * 1000, // 5 minutes
    refreshInterval: 60 * 1000, // 1 minute
    dateRange: '30d'
  });

  if (isLoading) return <div>Loading...</div>;
  if (hasError) return <div>Error loading analytics</div>;

  return (
    <div>
      <h1>Platform Statistics</h1>
      <p>Total Users: {platformStats?.total_users}</p>
      <p>Total Reviews: {platformStats?.total_reviews}</p>
      <button onClick={refreshAll}>Refresh All</button>
      <button onClick={clearCache}>Clear Cache</button>
    </div>
  );
}
```

**Options:**
- `autoFetch` - Fetch data on mount (default: true)
- `cacheTime` - Cache duration in ms (default: 5 minutes)
- `refreshInterval` - Auto-refresh interval in ms (default: null)
- `dateRange` - Default date range (default: '30d')
- `onError` - Error callback

**Return Values:**
- `platformStats` - Platform statistics data
- `globalTrends` - Global trends data
- `teamComparison` - Team comparison data
- `allReviews` - All reviews data
- `allFeedback` - All feedback data
- `isLoadingStats` - Loading state for stats
- `isLoadingTrends` - Loading state for trends
- `isLoadingTeams` - Loading state for teams
- `isLoadingReviews` - Loading state for reviews
- `isLoadingFeedback` - Loading state for feedback
- `isLoading` - Overall loading state
- `statsError` - Stats error message
- `trendsError` - Trends error message
- `teamsError` - Teams error message
- `reviewsError` - Reviews error message
- `feedbackError` - Feedback error message
- `hasError` - Whether any error exists
- `fetchPlatformStats(options)` - Fetch platform stats
- `fetchGlobalTrends(options)` - Fetch global trends
- `fetchTeamComparison(options)` - Fetch team comparison
- `fetchAllReviews(options)` - Fetch all reviews
- `fetchAllFeedback(options)` - Fetch all feedback
- `fetchAll(options)` - Fetch all data
- `refreshAll()` - Refresh all cached data
- `clearCache()` - Clear all cached data
- `getCacheStatus()` - Get cache status info

## Error Handling

All services and hooks implement comprehensive error handling:

1. **Network Errors**: Detected and reported with user-friendly messages
2. **Validation Errors**: Caught before API calls with detailed feedback
3. **API Errors**: Parsed and transformed into actionable messages
4. **Retry Logic**: Automatic retry for transient failures
5. **Fallback Mechanisms**: WebSocket → Polling fallback in useAnalysisStatus

## Testing

Tests are provided for all services and hooks:

- `frontend/services/__tests__/fileUploadService.test.js`
- `frontend/hooks/__tests__/useFileUpload.test.js`

Run tests with:
```bash
npm test
```

## Best Practices

1. **Always validate files** before uploading
2. **Use caching** in useAdminAnalytics to reduce API calls
3. **Handle errors gracefully** with user notifications
4. **Clean up resources** when components unmount
5. **Use WebSocket** for real-time updates when available
6. **Monitor cache status** to ensure data freshness

## Requirements Coverage

This implementation covers the following requirements:

- **Requirement 1.1, 1.2, 1.3**: Multi-file upload with background analysis
- **Requirement 7.1, 8.1**: Admin user and team management
- **Requirement 9.1, 9.2, 9.3**: Global platform analytics
- **Requirement 10.1**: Global code review insights
- **Requirement 13.1, 13.2, 13.3, 13.4**: Real-time job status updates
- **Requirement 12.1, 12.2, 12.4**: Input validation and error handling
- **Requirement 14.4**: Audit logging support
