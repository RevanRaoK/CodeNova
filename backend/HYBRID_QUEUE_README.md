# Hybrid Queue System - Comprehensive Guide

## Overview

The Hybrid Queue System is a sophisticated, high-performance task processing architecture that combines the speed of Redis with the reliability of RabbitMQ. This system provides fast task enqueueing with guaranteed processing and comprehensive monitoring capabilities.

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Application   │───▶│   Redis Queue    │───▶│  RabbitMQ Queue │
│   (Fast Enqueue)│    │  (Immediate      │    │  (Reliable      │
└─────────────────┘    │   Response)      │    │   Processing)   │
                       └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Forwarder      │    │    Workers      │
                       │   Process        │    │   (Consumers)   │
                       └──────────────────┘    └─────────────────┘
```

### Key Features

- **Dual Queue Architecture**: Redis for fast enqueueing, RabbitMQ for reliable processing
- **Priority-Based Processing**: High, Medium, Low, and Default priority queues
- **Automatic Forwarding**: Background process moves tasks from Redis to RabbitMQ
- **Delayed Task Scheduling**: Support for delayed task execution
- **Comprehensive Monitoring**: Health checks, metrics, and performance monitoring
- **Fault Tolerance**: Automatic retries, error handling, and graceful degradation
- **Scalable Workers**: Multiple worker processes with configurable concurrency

## Quick Start

### 1. Installation and Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis and RabbitMQ (using Docker)
docker-compose up -d redis rabbitmq

# Or install manually (see QUEUE_SYSTEM_SETUP_GUIDE.md)
```

### 2. Environment Configuration

Add to your `.env` file:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_DB_QUEUE=1
REDIS_DB_RESULTS=2

# RabbitMQ Configuration  
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Worker Configuration
WORKER_CONCURRENCY=4
TASK_TIMEOUT=600
TASK_MAX_RETRIES=3
```

### 3. Start the System

```bash
# Start both forwarder and worker
python start_hybrid_queue.py --mode both

# Or start components separately
python start_hybrid_queue.py --mode forwarder  # In one terminal
python start_hybrid_queue.py --mode worker     # In another terminal

# Check system status
python start_hybrid_queue.py --mode status
```

## Usage Examples

### Basic Task Enqueueing

```python
from app.core.hybrid_queue import hybrid_queue
from app.core.queue_config import QueuePriority

# Initialize the system
await hybrid_queue.initialize()

# Enqueue a task
task_id = await hybrid_queue.enqueue_task(
    "analyze_file",
    args=["file_123", "/path/to/file.py", "full"],
    priority=QueuePriority.HIGH
)

# Get task result
result = await hybrid_queue.get_task_result(task_id)
print(f"Task status: {result.status.value}")
```

### Registering Custom Tasks

```python
from app.core.hybrid_queue import hybrid_queue

# Using decorator
@hybrid_queue.task("custom_calculation", priority=QueuePriority.MEDIUM)
async def custom_calculation(numbers: list, operation: str):
    if operation == "sum":
        return sum(numbers)
    elif operation == "average":
        return sum(numbers) / len(numbers)
    return 0

# Enqueue the custom task
task_id = await hybrid_queue.enqueue_task(
    "custom_calculation",
    args=[[1, 2, 3, 4, 5], "average"]
)
```

### Delayed Tasks

```python
# Schedule a task to run in 5 minutes
task_id = await hybrid_queue.enqueue_task(
    "cleanup_temp_files",
    args=["/tmp/uploads"],
    priority=QueuePriority.LOW,
    delay=300  # 5 minutes
)
```

### Batch Processing

```python
# Process multiple files in batch
task_id = await hybrid_queue.enqueue_task(
    "batch_analyze_files",
    args=[["file1", "file2", "file3"], "quick"],
    priority=QueuePriority.MEDIUM
)
```

## Task Types and Modules

The system includes several pre-built task modules:

### File Analysis Tasks (`app.tasks.file_analysis_tasks`)

- `analyze_file`: Analyze individual files for code quality
- `batch_analyze_files`: Process multiple files efficiently
- `generate_file_report`: Create formatted analysis reports

### Feedback Tasks (`app.tasks.feedback_tasks`)

- `process_feedback`: Handle user feedback on suggestions
- `update_learning_model`: Update ML models based on feedback
- `generate_feedback_report`: Create feedback analytics

### GitHub Webhook Tasks (`app.tasks.github_webhook_tasks`)

- `process_webhook`: Handle GitHub webhook events
- `analyze_pull_request`: Analyze PR changes
- `update_repository_status`: Update repo analysis status

### Analytics Tasks (`app.tasks.analytics_tasks`)

- `generate_usage_report`: Create usage analytics
- `calculate_metrics`: Compute performance metrics
- `update_dashboard_data`: Refresh dashboard information

### Cache Tasks (`app.tasks.cache_tasks`)

- `warm_cache`: Pre-populate cache with frequently accessed data
- `invalidate_cache`: Remove stale cache entries
- `optimize_cache`: Optimize cache performance

## Configuration

### Queue Configuration (`app.core.queue_config`)

```python
# Priority levels
class QueuePriority(Enum):
    HIGH = "high_priority"      # Critical tasks (webhooks, real-time)
    MEDIUM = "medium_priority"  # Standard tasks (file analysis)
    LOW = "low_priority"        # Background tasks (analytics, cleanup)
    DEFAULT = "default"         # Default priority
```

### Task Routing

Tasks are automatically routed to appropriate queues based on type:

```python
TASK_ROUTES = {
    'github_webhook_tasks': QueuePriority.HIGH,
    'urgent_feedback_tasks': QueuePriority.HIGH,
    'file_analysis_tasks': QueuePriority.MEDIUM,
    'feedback_tasks': QueuePriority.MEDIUM,
    'analytics_tasks': QueuePriority.LOW,
    'cache_tasks': QueuePriority.LOW,
}
```

### Performance Tuning

```bash
# Worker Configuration
WORKER_CONCURRENCY=8          # Number of concurrent workers
WORKER_BATCH_SIZE=20          # Tasks processed per batch
WORKER_MAX_MEMORY_MB=1024     # Memory limit per worker

# Forwarding Configuration  
FORWARDING_BATCH_SIZE=10      # Tasks forwarded per batch
FORWARDING_INTERVAL=1.0       # Forwarding frequency (seconds)

# Task Configuration
TASK_TIMEOUT=600              # Task timeout (seconds)
TASK_MAX_RETRIES=3            # Maximum retry attempts
RESULT_TTL=3600               # Result storage time (seconds)
```

## Monitoring and Health Checks

### API Endpoints

The system provides comprehensive monitoring through REST API endpoints:

```bash
# System health
GET /api/v1/monitoring/queue/health

# Detailed statistics
GET /api/v1/monitoring/queue/stats

# Worker status
GET /api/v1/monitoring/workers/status

# Performance metrics
GET /api/v1/monitoring/workers/performance

# Configuration validation
GET /api/v1/monitoring/queue/config/validate

# System overview
GET /api/v1/monitoring/system/overview
```

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "systems": {
    "redis_queue": {
      "status": "healthy",
      "stats": {
        "high_priority": {"pending": 0, "processing": 1, "total": 1},
        "medium_priority": {"pending": 5, "processing": 2, "total": 7}
      }
    },
    "hybrid_queue": {
      "status": "healthy",
      "metrics": {
        "redis_tasks_enqueued": 150,
        "rabbitmq_tasks_processed": 145,
        "forwarding_rate": 0.97,
        "redis_queue_depth": 5,
        "rabbitmq_queue_depth": 2
      }
    }
  }
}
```

### Metrics Collection

```python
# Get comprehensive metrics
metrics = await hybrid_queue.get_metrics()

print(f"Status: {metrics['status']}")
print(f"Forwarding Rate: {metrics['forwarding_rate']:.2%}")
print(f"Queue Depths - Redis: {metrics['redis_queue_depth']}, RabbitMQ: {metrics['rabbitmq_queue_depth']}")
```

## Management Scripts

### Start Hybrid Queue (`start_hybrid_queue.py`)

```bash
# Start both forwarder and worker
python start_hybrid_queue.py --mode both

# Start only forwarder
python start_hybrid_queue.py --mode forwarder

# Start only worker
python start_hybrid_queue.py --mode worker

# Check system status
python start_hybrid_queue.py --mode status

# Validate configuration before starting
python start_hybrid_queue.py --validate-config
```

### Example Usage Script (`example_hybrid_queue_usage.py`)

```bash
# Run comprehensive examples
python example_hybrid_queue_usage.py
```

This script demonstrates:
- Basic task enqueueing and result retrieval
- Batch processing examples
- Custom task registration
- Monitoring and metrics collection

## Testing

### Integration Tests (`test_hybrid_queue_integration.py`)

```bash
# Run comprehensive test suite
python test_hybrid_queue_integration.py
```

Test coverage includes:
- Basic task enqueueing and retrieval
- Task forwarding from Redis to RabbitMQ
- Priority queue functionality
- Delayed task scheduling
- Metrics collection and health monitoring
- Error handling and fault tolerance
- Queue purging and cleanup

### Test Results

```
=== Test Results ===
Passed: 8
Failed: 0
Total: 8
🎉 All tests passed!
```

## Production Deployment

### Systemd Service Configuration

Create `/etc/systemd/system/codenova-hybrid-queue.service`:

```ini
[Unit]
Description=CodeNova Hybrid Queue System
After=network.target redis.service rabbitmq-server.service
Requires=redis.service rabbitmq-server.service

[Service]
Type=simple
User=codenova
WorkingDirectory=/path/to/codenova/backend
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python start_hybrid_queue.py --mode both
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  hybrid-queue:
    build: .
    command: python start_hybrid_queue.py --mode both
    environment:
      - REDIS_URL=redis://redis:6379/0
      - RABBITMQ_URL=amqp://rabbitmq:5672/
      - WORKER_CONCURRENCY=4
    depends_on:
      - redis
      - rabbitmq
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  rabbitmq:
    image: rabbitmq:3-management-alpine
    environment:
      - RABBITMQ_DEFAULT_USER=codenova
      - RABBITMQ_DEFAULT_PASS=secure_password
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    restart: unless-stopped

volumes:
  redis_data:
  rabbitmq_data:
```

### Scaling Configuration

```bash
# Horizontal scaling - multiple worker instances
docker-compose up --scale hybrid-queue=3

# Vertical scaling - increase worker concurrency
export WORKER_CONCURRENCY=16
export WORKER_MAX_MEMORY_MB=2048
```

## Troubleshooting

### Common Issues

1. **Connection Refused Errors**
   ```bash
   # Check Redis
   redis-cli ping
   
   # Check RabbitMQ
   rabbitmqctl status
   ```

2. **High Queue Depths**
   ```bash
   # Check metrics
   curl http://localhost:8000/api/v1/monitoring/queue/stats
   
   # Increase worker concurrency
   export WORKER_CONCURRENCY=8
   ```

3. **Failed Task Forwarding**
   ```bash
   # Check RabbitMQ connectivity
   python -c "import aio_pika; print('RabbitMQ OK')"
   
   # Check forwarder logs
   tail -f /var/log/codenova/hybrid-queue.log
   ```

### Performance Optimization

1. **Redis Optimization**
   ```conf
   # redis.conf
   maxmemory 2gb
   maxmemory-policy allkeys-lru
   save 900 1
   ```

2. **RabbitMQ Optimization**
   ```conf
   # rabbitmq.conf
   vm_memory_high_watermark.relative = 0.8
   disk_free_limit.relative = 1.0
   ```

3. **Worker Optimization**
   ```bash
   # Environment variables
   WORKER_CONCURRENCY=8
   WORKER_BATCH_SIZE=20
   ENABLE_COMPRESSION=true
   ```

### Monitoring and Alerting

```bash
# Set up monitoring thresholds
export ALERT_QUEUE_DEPTH_THRESHOLD=1000
export ALERT_TASK_FAILURE_RATE_THRESHOLD=0.1
export SLOW_TASK_THRESHOLD=300

# Enable alerting
export QUEUE_ALERTING_ENABLED=true
```

## Security Considerations

### Redis Security

```bash
# Enable authentication
requirepass your_strong_password

# Bind to specific interfaces
bind 127.0.0.1 10.0.0.1

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command CONFIG ""
```

### RabbitMQ Security

```bash
# Create dedicated user
rabbitmqctl add_user codenova_app secure_password
rabbitmqctl set_permissions -p / codenova_app "^codenova\." "^codenova\." "^codenova\."

# Enable SSL
rabbitmq-plugins enable rabbitmq_auth_mechanism_ssl
```

### Network Security

```bash
# Firewall configuration
ufw allow from 10.0.0.0/8 to any port 6379  # Redis
ufw allow from 10.0.0.0/8 to any port 5672  # RabbitMQ
ufw deny 6379  # Block external access
ufw deny 5672  # Block external access
```

## API Reference

### Core Classes

#### `HybridQueue`
Main queue system class providing task management and processing.

**Methods:**
- `initialize()`: Initialize Redis and RabbitMQ connections
- `enqueue_task(name, args, kwargs, priority, delay)`: Enqueue a task
- `get_task_result(task_id)`: Retrieve task result
- `start_forwarder()`: Start task forwarding process
- `start_worker()`: Start task processing worker
- `get_metrics()`: Get system metrics
- `purge_queues()`: Clear all queues

#### `QueuePriority`
Enumeration of queue priority levels.

**Values:**
- `HIGH`: Critical tasks requiring immediate processing
- `MEDIUM`: Standard tasks with normal priority
- `LOW`: Background tasks with lower priority
- `DEFAULT`: Default priority level

### Task Decorators

```python
# Register task with hybrid queue
@hybrid_queue.task("task_name", priority=QueuePriority.MEDIUM)
async def my_task(arg1, arg2):
    return {"result": "success"}

# Register with both Redis and hybrid queues
@redis_queue.task("task_name", priority=QueuePriority.MEDIUM)
@hybrid_queue.task("task_name", priority=QueuePriority.MEDIUM)
async def dual_registered_task():
    pass
```

## Best Practices

### Task Design

1. **Keep tasks idempotent**: Tasks should produce the same result when run multiple times
2. **Handle errors gracefully**: Use try-catch blocks and meaningful error messages
3. **Limit task duration**: Break long-running tasks into smaller chunks
4. **Use appropriate priorities**: Reserve HIGH priority for truly critical tasks

### Performance

1. **Batch related operations**: Group similar tasks together
2. **Use delayed tasks for scheduling**: Avoid polling by using delay parameter
3. **Monitor queue depths**: Set up alerts for high queue depths
4. **Scale workers based on load**: Increase concurrency during peak times

### Monitoring

1. **Set up health checks**: Monitor system status regularly
2. **Track key metrics**: Queue depths, processing rates, error rates
3. **Configure alerting**: Get notified of system issues promptly
4. **Log important events**: Maintain detailed logs for troubleshooting

## Contributing

### Adding New Task Types

1. Create task module in `app/tasks/`
2. Register tasks with appropriate decorators
3. Add task routing configuration
4. Update documentation and tests

### Extending Monitoring

1. Add new metrics to `HybridQueue.get_metrics()`
2. Create monitoring endpoints in `monitoring.py`
3. Update health check logic
4. Add alerting rules

## Support and Resources

- **Setup Guide**: `QUEUE_SYSTEM_SETUP_GUIDE.md`
- **Implementation Details**: `HYBRID_QUEUE_IMPLEMENTATION.md`
- **Example Usage**: `example_hybrid_queue_usage.py`
- **Integration Tests**: `test_hybrid_queue_integration.py`
- **Management Script**: `start_hybrid_queue.py`

For additional support, check the monitoring endpoints for system health and consult the comprehensive test suite for usage examples.