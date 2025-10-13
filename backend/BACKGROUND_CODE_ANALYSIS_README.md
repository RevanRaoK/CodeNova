# Background Code Analysis Service

## Overview

The Background Code Analysis Service provides comprehensive asynchronous code analysis capabilities for the CodeNova platform. This service enables scalable, non-blocking code analysis with real-time progress tracking, intelligent caching, and comprehensive result management.

## Features

### Core Functionality

- **Asynchronous Code Analysis**: Non-blocking analysis processing using background job queues
- **Multiple Analysis Types**: Support for quick, full, security, performance, style, and comprehensive analysis
- **AI-Powered Insights**: Integration with AI services for intelligent code suggestions and insights
- **Real-time Progress Tracking**: Live progress updates with WebSocket support
- **Intelligent Caching**: Result caching with deduplication to avoid redundant analysis
- **Batch Processing**: Efficient batch analysis for multiple files or code snippets

### Advanced Features

- **Job Queuing**: Priority-based job queuing with Redis and RabbitMQ support
- **Progress Notifications**: Real-time notifications via WebSocket and email
- **Result Persistence**: Cached results with configurable TTL
- **Error Handling**: Comprehensive error handling with retry logic
- **Metrics Collection**: Performance metrics and analytics
- **User Management**: Per-user analysis tracking and preferences

## Architecture

### Service Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Background Code Analysis Service          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Analysis      │  │   Job Queue     │  │    Cache     │ │
│  │   Engine        │  │   Manager       │  │   Manager    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Notification   │  │   Progress      │  │   Metrics    │ │
│  │   Service       │  │   Tracker       │  │  Collector   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Integration Layer                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   AI Service    │  │  Background     │  │    Redis     │ │
│  │   (Gemini)      │  │  Job Service    │  │    Cache     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Analysis      │  │   Notification  │  │   Database   │ │
│  │   Service       │  │   Service       │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Analysis Request**: User submits code for analysis via API
2. **Job Queuing**: Request is queued with appropriate priority
3. **Background Processing**: Worker processes the analysis job
4. **AI Integration**: AI service provides intelligent insights
5. **Result Caching**: Results are cached for future use
6. **Notification**: User receives real-time progress updates
7. **Completion**: Final results are delivered to user

## API Endpoints

### Analysis Management

#### Queue Analysis

```http
POST /api/analysis/queue
Content-Type: application/json

{
  "content": "def hello_world():\n    print('Hello, World!')",
  "language": "python",
  "analysis_type": "full",
  "priority": "normal",
  "metadata": {"source": "api_request"}
}
```

#### Get Analysis Status

```http
GET /api/analysis/status/{analysis_id}
```

#### Get Analysis Results

```http
GET /api/analysis/results/{analysis_id}
```

#### Cancel Analysis

```http
DELETE /api/analysis/cancel/{analysis_id}
```

### Batch Analysis

#### Queue Batch Analysis

```http
POST /api/analysis/batch
Content-Type: application/json

{
  "analyses": [
    {
      "content": "def func1(): pass",
      "language": "python",
      "analysis_type": "quick"
    },
    {
      "file_path": "/path/to/file.js",
      "language": "javascript",
      "analysis_type": "full"
    }
  ],
  "batch_priority": "normal"
}
```

#### Get Batch Status

```http
GET /api/analysis/batch/status/{batch_id}
```

### User Management

#### Get User Analyses

```http
GET /api/analysis/user/analyses?status=completed&limit=50
```

#### Get Analysis Metrics

```http
GET /api/analysis/metrics
```

## Analysis Types

### Quick Analysis

- **Duration**: ~30-60 seconds
- **Features**: Basic syntax checking, simple style issues
- **Use Case**: Real-time feedback during development

### Full Analysis

- **Duration**: ~2-5 minutes
- **Features**: Comprehensive analysis with AI insights
- **Use Case**: Pre-commit analysis, code reviews

### Security Analysis

- **Duration**: ~1-3 minutes
- **Features**: Security vulnerability detection
- **Use Case**: Security audits, compliance checks

### Performance Analysis

- **Duration**: ~2-4 minutes
- **Features**: Performance bottleneck detection
- **Use Case**: Optimization recommendations

### Style Analysis

- **Duration**: ~1-2 minutes
- **Features**: Code style and formatting issues
- **Use Case**: Code consistency enforcement

### Comprehensive Analysis

- **Duration**: ~5-10 minutes
- **Features**: All analysis types combined
- **Use Case**: Thorough code quality assessment

## Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# AI Service Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=models/gemini-1.5-flash

# Analysis Configuration
ANALYSIS_CACHE_TTL=3600
ANALYSIS_MAX_TIMEOUT=600
ANALYSIS_BATCH_SIZE_LIMIT=50

# Notification Configuration
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_WEBSOCKET_NOTIFICATIONS=true
```

### Service Configuration

```python
# Analysis service settings
ANALYSIS_SETTINGS = {
    'default_timeout': 300,  # 5 minutes
    'max_batch_size': 50,
    'cache_ttl': 3600,  # 1 hour
    'enable_ai_analysis': True,
    'enable_progress_tracking': True,
    'enable_notifications': True
}
```

## Usage Examples

### Python SDK Usage

```python
from app.services.background_code_analysis_service import (
    background_code_analysis_service,
    AnalysisType
)

# Queue a simple analysis
analysis_id = await background_code_analysis_service.queue_analysis(
    content="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
    language="python",
    analysis_type=AnalysisType.FULL,
    user_id="user123"
)

# Check status
result = await background_code_analysis_service.get_analysis_status(analysis_id)
print(f"Status: {result.status}")

# Get results when completed
if result.status == AnalysisStatus.COMPLETED:
    print(f"Issues found: {len(result.issues)}")
    print(f"Suggestions: {len(result.suggestions)}")
```

### Batch Analysis

```python
# Queue batch analysis
batch_requests = [
    {
        'content': 'def func1(): pass',
        'language': 'python',
        'analysis_type': 'quick'
    },
    {
        'content': 'function func2() { return "test"; }',
        'language': 'javascript',
        'analysis_type': 'quick'
    }
]

batch_id = await background_code_analysis_service.queue_batch_analysis(
    analysis_requests=batch_requests,
    user_id="user123"
)

# Monitor batch progress
batch_status = await background_code_analysis_service.get_batch_status(batch_id)
print(f"Progress: {batch_status['completed_count']}/{batch_status['total_count']}")
```

### Progress Tracking

```python
# Add progress callback
def progress_callback(analysis_id, message, percentage):
    print(f"Analysis {analysis_id}: {percentage:.1f}% - {message}")

background_code_analysis_service.add_progress_callback(analysis_id, progress_callback)
```

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
cd backend
python test_background_code_analysis.py
```

### Integration Tests

Run integration tests with all services:

```bash
cd backend
python test_integration_background_analysis.py
```

### API Tests

Test API endpoints using curl or Postman:

```bash
# Queue analysis
curl -X POST "http://localhost:8000/api/analysis/queue" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "content": "def hello(): print(\"Hello, World!\")",
    "language": "python",
    "analysis_type": "quick"
  }'

# Check status
curl -X GET "http://localhost:8000/api/analysis/status/{analysis_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Performance Considerations

### Optimization Strategies

1. **Caching**: Intelligent result caching reduces redundant analysis
2. **Batch Processing**: Efficient batch analysis for multiple files
3. **Priority Queuing**: High-priority analyses are processed first
4. **Resource Management**: Configurable timeouts and limits
5. **Async Processing**: Non-blocking analysis execution

### Scaling Guidelines

- **Horizontal Scaling**: Add more worker processes for increased throughput
- **Cache Optimization**: Tune cache TTL based on usage patterns
- **Queue Management**: Monitor queue depths and adjust worker counts
- **Resource Limits**: Set appropriate memory and CPU limits

## Monitoring and Metrics

### Key Metrics

- **Analysis Throughput**: Analyses completed per minute
- **Average Processing Time**: Mean analysis duration
- **Cache Hit Rate**: Percentage of cached results served
- **Error Rate**: Percentage of failed analyses
- **Queue Depth**: Number of pending analyses

### Health Checks

```python
# Get service metrics
metrics = await background_code_analysis_service.get_analysis_metrics()

# Check service health
health_status = {
    'healthy': metrics['analysis_metrics']['failed_analyses'] == 0,
    'cache_hit_rate': metrics['cache_metrics']['hit_rate'],
    'queue_depth': metrics['queue_metrics']['total_jobs']
}
```

## Troubleshooting

### Common Issues

1. **Analysis Timeout**: Increase timeout settings for complex code
2. **Cache Misses**: Check Redis connectivity and configuration
3. **Queue Backlog**: Add more worker processes or increase processing capacity
4. **AI Service Errors**: Verify API keys and service availability

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger('app.services.background_code_analysis_service').setLevel(logging.DEBUG)
```

### Performance Profiling

Monitor analysis performance:

```python
# Get detailed metrics
metrics = await background_code_analysis_service.get_analysis_metrics()
print(f"Average processing time: {metrics['analysis_metrics']['avg_processing_time']:.2f}s")
print(f"Cache hit rate: {metrics['cache_metrics']['hit_rate']:.1%}")
```

## Requirements Covered

This implementation addresses the following requirements:

- **2.1**: Enable multiple file upload support with background processing
- **2.6**: Queue code analysis jobs for uploaded files instead of synchronous processing

## Future Enhancements

1. **Machine Learning**: Implement ML-based analysis improvements
2. **Custom Rules**: Allow users to define custom analysis rules
3. **Integration APIs**: Provide webhooks for external integrations
4. **Advanced Caching**: Implement semantic caching for similar code patterns
5. **Distributed Processing**: Support for distributed analysis across multiple nodes

## Contributing

When contributing to the Background Code Analysis Service:

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure backward compatibility
5. Monitor performance impact of changes

## License

This service is part of the CodeNova platform and follows the same licensing terms.
