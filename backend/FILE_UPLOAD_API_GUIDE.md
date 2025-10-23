# File Upload and Batch Analysis API Guide

## Quick Start

### 1. Upload Multiple Files for Batch Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/files/upload-batch" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@file1.py" \
  -F "files=@file2.js" \
  -F "files=@file3.java"
```

**Response:**
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_files": 3,
  "successful_uploads": 3,
  "failed_uploads": 0,
  "status": "pending",
  "files": [
    {
      "file_id": "...",
      "filename": "file1.py",
      "status": "uploaded",
      "language": "python",
      "size_bytes": 1024,
      "size_kb": 1.0
    }
  ],
  "created_at": "2025-10-21T13:39:11.417638",
  "validation_errors": null
}
```

### 2. Monitor Batch Status (WebSocket)

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/analysis/ws/batch/BATCH_ID');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Status update:', data);
  
  if (data.type === 'status_update') {
    console.log(`Progress: ${data.progress_percentage}%`);
    console.log(`Processed: ${data.processed_files}/${data.total_files}`);
  }
  
  if (data.type === 'final') {
    console.log('Batch complete!');
    console.log(`Success: ${data.successful_files}, Failed: ${data.failed_files}`);
  }
};
```

### 3. Monitor Batch Status (Polling Fallback)

```bash
curl -X GET "http://localhost:8000/api/v1/files/batch/BATCH_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "total_files": 3,
  "processed_files": 2,
  "successful_files": 2,
  "failed_files": 0,
  "progress_percentage": 66.67,
  "created_at": "2025-10-21T13:39:11.417638",
  "started_at": "2025-10-21T13:39:12.000000",
  "completed_at": null,
  "processing_time_seconds": null,
  "files": [
    {
      "file_id": "...",
      "filename": "file1.py",
      "status": "completed",
      "language": "python",
      "size_bytes": 1024,
      "analysis_id": "...",
      "issues_count": 5,
      "errors_count": 2,
      "warnings_count": 3,
      "error_message": null,
      "processing_time_seconds": 2.5
    }
  ]
}
```

### 4. Get User's Batches

```bash
curl -X GET "http://localhost:8000/api/v1/files/batches?skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Get File Details

```bash
curl -X GET "http://localhost:8000/api/v1/files/batch/BATCH_ID/files/FILE_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. Analyze Code with Filename (Updated)

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/analyze-code" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello():\n    print(\"Hello\")",
    "language": "python",
    "filename": "hello.py"
  }'
```

**Note:** `filename` is now **required**. The API will return a 422 error if not provided.

### 7. Monitor Analysis Status (WebSocket)

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/analysis/ws/analysis/ANALYSIS_ID');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'status_update') {
    console.log('Status:', data.status);
  }
  
  if (data.type === 'final') {
    console.log('Analysis complete!');
    if (data.results_available) {
      console.log(`Found ${data.issues_count} issues`);
    }
  }
};
```

### 8. Monitor Analysis Status (Polling)

```bash
curl -X GET "http://localhost:8000/api/v1/analysis/direct/ANALYSIS_ID/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Supported File Types

### Programming Languages (41 types)
- **Python**: .py, .pyw, .pyi
- **JavaScript**: .js, .jsx, .mjs, .cjs
- **TypeScript**: .ts, .tsx
- **Java**: .java
- **C/C++**: .c, .cpp, .cc, .cxx, .h, .hpp, .hxx
- **C#**: .cs
- **Go**: .go
- **Rust**: .rs
- **PHP**: .php
- **Ruby**: .rb
- **Swift**: .swift
- **Kotlin**: .kt, .kts
- **Scala**: .scala
- **HTML**: .html, .htm
- **CSS**: .css, .scss, .sass, .less
- **SQL**: .sql
- **Shell**: .sh, .bash
- **YAML**: .yaml, .yml
- **JSON**: .json
- **XML**: .xml
- **Markdown**: .md, .markdown

## File Limits

- **Maximum file size**: 5MB per file
- **Maximum lines**: 10,000 lines per file
- **Maximum batch size**: 10 files per batch
- **Supported encodings**: UTF-8, latin-1, cp1252

## Error Codes

| Code | Description |
|------|-------------|
| `MISSING_FILENAME` | No filename provided |
| `NO_EXTENSION` | File has no extension |
| `UNSUPPORTED_EXTENSION` | File type not supported |
| `DANGEROUS_EXTENSION` | Security risk file type |
| `EMPTY_FILE` | File has no content |
| `FILE_TOO_LARGE` | Exceeds 5MB limit |
| `INVALID_MIME_TYPE` | Unsupported MIME type |
| `INVALID_TEXT_CONTENT` | Not valid text |
| `BINARY_CONTENT` | Contains binary data |
| `EMPTY_CONTENT` | Only whitespace |
| `TOO_MANY_LINES` | Exceeds 10,000 lines |
| `ANALYSIS_ERROR` | Analysis failed |
| `MAX_RETRIES_EXCEEDED` | All retries failed |

## Status Values

### Batch Status
- `pending`: Batch created, not yet processing
- `processing`: Files being analyzed
- `completed`: All files processed successfully
- `failed`: All files failed
- `partial`: Some files succeeded, some failed

### File Status
- `pending`: File queued for processing
- `uploading`: File being uploaded
- `uploaded`: File uploaded successfully
- `analyzing`: Analysis in progress
- `completed`: Analysis complete
- `failed`: Analysis failed

## Best Practices

### 1. File Upload
- Validate files client-side before upload
- Show upload progress to users
- Handle validation errors gracefully
- Limit batch size to 10 files

### 2. Status Monitoring
- Use WebSocket for real-time updates when possible
- Fall back to polling if WebSocket unavailable
- Poll every 2-3 seconds for active jobs
- Stop polling when job completes

### 3. Error Handling
- Display user-friendly error messages
- Provide retry option for failed files
- Log errors for debugging
- Show validation errors before upload

### 4. Performance
- Upload files in batches rather than individually
- Use compression for large files
- Implement client-side file size checks
- Show progress indicators

## Example: Complete Upload Flow

```javascript
// 1. Upload files
async function uploadFiles(files) {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  const response = await fetch('/api/v1/files/upload-batch', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  const data = await response.json();
  return data.batch_id;
}

// 2. Monitor progress
function monitorBatch(batchId, onUpdate, onComplete) {
  const ws = new WebSocket(`ws://localhost:8000/api/v1/analysis/ws/batch/${batchId}`);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'status_update') {
      onUpdate(data);
    }
    
    if (data.type === 'final') {
      onComplete(data);
      ws.close();
    }
  };
  
  ws.onerror = () => {
    // Fallback to polling
    pollBatchStatus(batchId, onUpdate, onComplete);
  };
}

// 3. Polling fallback
async function pollBatchStatus(batchId, onUpdate, onComplete) {
  const interval = setInterval(async () => {
    const response = await fetch(`/api/v1/files/batch/${batchId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const data = await response.json();
    onUpdate(data);
    
    if (['completed', 'failed', 'partial'].includes(data.status)) {
      clearInterval(interval);
      onComplete(data);
    }
  }, 2000);
}

// 4. Usage
const files = document.getElementById('fileInput').files;
const batchId = await uploadFiles(files);

monitorBatch(
  batchId,
  (data) => {
    console.log(`Progress: ${data.progress_percentage}%`);
    updateProgressBar(data.progress_percentage);
  },
  (data) => {
    console.log('Complete!');
    showResults(data);
  }
);
```

## Testing

### Test File Validation
```bash
python backend/test_file_upload_service.py
```

### Test API Endpoints
```bash
# Upload test files
curl -X POST "http://localhost:8000/api/v1/files/upload-batch" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@test.py" \
  -F "files=@test.js"

# Check batch status
curl -X GET "http://localhost:8000/api/v1/files/batch/BATCH_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### Issue: Files not uploading
- Check file size (max 5MB)
- Verify file extension is supported
- Ensure file is text-based, not binary
- Check authentication token

### Issue: WebSocket not connecting
- Verify WebSocket URL format
- Check CORS settings
- Fall back to polling
- Check firewall/proxy settings

### Issue: Analysis stuck in "processing"
- Check worker logs
- Verify AI service is running
- Check database connection
- Look for timeout errors

### Issue: Validation errors
- Review error_code in response
- Check file content encoding
- Verify file is not empty
- Ensure filename is valid

## Support

For issues or questions:
1. Check error codes in response
2. Review server logs
3. Test with sample files
4. Verify API authentication
5. Check service status
