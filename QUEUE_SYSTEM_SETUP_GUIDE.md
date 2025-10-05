# Queue System Setup Guide

This guide provides comprehensive instructions for setting up and configuring the message queuing and caching system for CodeNova.

## Overview

The queue system consists of:

- **RabbitMQ**: Message broker for task queuing
- **Redis**: In-memory cache and session storage
- **Celery**: Distributed task queue framework
- **Queue Monitoring**: Real-time monitoring and management

## Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ with pip
- Access to the project repository

## Quick Start

### 1. Environment Setup

First, ensure your environment variables are configured in `backend/.env`:

```bash
# Queue Configuration
RABBITMQ_URL=amqp://guest:guest@localhost:5672//
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Queue Monitoring
QUEUE_MONITORING_ENABLED=true
QUEUE_METRICS_RETENTION_HOURS=24
```

### 2. Start Services with Docker Compose

```bash
# Start all services including RabbitMQ and Redis
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 3. Start Celery Workers

```bash
# Navigate to backend directory
cd backend

# Start Celery worker
celery -A app.core.celery_app worker --loglevel=info

# In another terminal, start Celery beat (for scheduled tasks)
celery -A app.core.celery_app beat --loglevel=info
```

## Detailed Configuration

### RabbitMQ Setup

RabbitMQ is configured in `docker-compose.yml` with the following settings:

```yaml
rabbitmq:
  image: rabbitmq:3-management
  ports:
    - '5672:5672' # AMQP port
    - '15672:15672' # Management UI
  environment:
    RABBITMQ_DEFAULT_USER: guest
    RABBITMQ_DEFAULT_PASS: guest
```

**Access RabbitMQ Management UI**: http://localhost:15672

- Username: `guest`
- Password: `guest`

### Redis Setup

Redis configuration in `docker-compose.yml`:

```yaml
redis:
  image: redis:7-alpine
  ports:
    - '6379:6379'
  command: redis-server --appendonly yes
```

### Celery Configuration

The Celery app is configured in `backend/app/core/celery_app.py`:

```python
from celery import Celery
from app.core.queue_config import get_queue_config

config = get_queue_config()
celery_app = Celery("codenova")

celery_app.conf.update(
    broker_url=config.broker_url,
    result_backend=config.result_backend,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
```

## Task Types and Queues

### Available Task Queues

1. **GitHub Webhook Tasks** (`github_webhook_tasks.py`)

   - Repository analysis
   - Webhook processing
   - Code change detection

2. **Feedback Tasks** (`feedback_tasks.py`)

   - Feedback processing
   - Notification sending
   - Analytics updates

3. **Analytics Tasks** (`analytics_tasks.py`)

   - Performance metrics
   - Usage statistics
   - Report generation

4. **File Analysis Tasks** (`file_analysis_tasks.py`)

   - Code analysis
   - AST parsing
   - Quality metrics

5. **Cache Tasks** (`cache_tasks.py`)
   - Cache warming
   - Cache invalidation
   - Data synchronization

### Queue Routing

Tasks are routed to specific queues based on priority and type:

```python
# High priority tasks
CELERY_ROUTES = {
    'app.tasks.github_webhook_tasks.*': {'queue': 'high_priority'},
    'app.tasks.feedback_tasks.*': {'queue': 'medium_priority'},
    'app.tasks.analytics_tasks.*': {'queue': 'low_priority'},
}
```

## Monitoring and Management

### Queue Monitoring Service

The queue monitoring service provides real-time insights:

```python
# Access monitoring endpoints
GET /api/v1/queue/status          # Overall queue status
GET /api/v1/queue/metrics         # Performance metrics
GET /api/v1/queue/workers         # Worker information
POST /api/v1/queue/tasks/retry    # Retry failed tasks
```

### Key Metrics Monitored

- **Queue Length**: Number of pending tasks
- **Worker Status**: Active/idle workers
- **Task Success Rate**: Completed vs failed tasks
- **Processing Time**: Average task execution time
- **Memory Usage**: Worker memory consumption

### Monitoring Dashboard

Access the monitoring dashboard at: `/queue-monitoring`

Features:

- Real-time queue statistics
- Worker health status
- Failed task management
- Performance graphs

## Production Deployment

### Scaling Workers

```bash
# Scale workers based on load
celery -A app.core.celery_app worker --concurrency=4 --loglevel=info

# Auto-scaling with Celery
celery -A app.core.celery_app worker --autoscale=10,3
```

### High Availability Setup

For production environments:

1. **RabbitMQ Cluster**:

   ```yaml
   rabbitmq-1:
     image: rabbitmq:3-management
     environment:
       RABBITMQ_ERLANG_COOKIE: 'secret_cookie'

   rabbitmq-2:
     image: rabbitmq:3-management
     environment:
       RABBITMQ_ERLANG_COOKIE: 'secret_cookie'
   ```

2. **Redis Sentinel**:

   ```yaml
   redis-master:
     image: redis:7-alpine
     command: redis-server --appendonly yes

   redis-sentinel:
     image: redis:7-alpine
     command: redis-sentinel /etc/redis/sentinel.conf
   ```

### Environment Variables for Production

```bash
# Production Queue Configuration
RABBITMQ_URL=amqp://user:password@rabbitmq-cluster:5672//
REDIS_URL=redis://redis-cluster:6379/0
CELERY_BROKER_URL=amqp://user:password@rabbitmq-cluster:5672//
CELERY_RESULT_BACKEND=redis://redis-cluster:6379/0

# Security
QUEUE_AUTH_ENABLED=true
QUEUE_SSL_ENABLED=true

# Performance
CELERY_WORKER_CONCURRENCY=8
CELERY_TASK_SOFT_TIME_LIMIT=300
CELERY_TASK_TIME_LIMIT=600
```

## Troubleshooting

### Common Issues

1. **Connection Refused**

   ```bash
   # Check if services are running
   docker-compose ps

   # Restart services
   docker-compose restart rabbitmq redis
   ```

2. **Tasks Not Processing**

   ```bash
   # Check worker status
   celery -A app.core.celery_app inspect active

   # Purge queue if needed
   celery -A app.core.celery_app purge
   ```

3. **Memory Issues**

   ```bash
   # Monitor worker memory
   celery -A app.core.celery_app inspect stats

   # Restart workers periodically
   celery -A app.core.celery_app control pool_restart
   ```

### Debugging Commands

```bash
# View queue contents
celery -A app.core.celery_app inspect reserved

# Check failed tasks
celery -A app.core.celery_app events

# Monitor in real-time
celery -A app.core.celery_app monitor
```

### Log Analysis

Check logs for issues:

```bash
# Docker logs
docker-compose logs rabbitmq
docker-compose logs redis

# Celery logs
tail -f celery.log

# Application logs
tail -f app.log | grep -i queue
```

## Performance Optimization

### Queue Configuration Tuning

```python
# Optimize for throughput
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_DISABLE_RATE_LIMITS = True

# Optimize for memory
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 200000  # 200MB
```

### Monitoring Performance

```python
# Custom metrics collection
from app.services.queue_monitoring_service import QueueMonitoringService

monitor = QueueMonitoringService()
metrics = monitor.get_performance_metrics()
```

## Security Considerations

### Authentication

```bash
# RabbitMQ user management
docker exec rabbitmq rabbitmqctl add_user codenova secure_password
docker exec rabbitmq rabbitmqctl set_permissions codenova ".*" ".*" ".*"
```

### Network Security

```yaml
# Docker network isolation
networks:
  queue_network:
    driver: bridge
    internal: true
```

### Data Encryption

```python
# Enable SSL/TLS
CELERY_BROKER_USE_SSL = {
    'keyfile': '/path/to/key.pem',
    'certfile': '/path/to/cert.pem',
    'ca_certs': '/path/to/ca.pem',
}
```

## Maintenance

### Regular Tasks

1. **Queue Cleanup**

   ```bash
   # Clean old results
   celery -A app.core.celery_app purge

   # Clear expired cache
   redis-cli FLUSHDB
   ```

2. **Health Checks**

   ```bash
   # Automated health check script
   ./scripts/queue_health_check.sh
   ```

3. **Backup**

   ```bash
   # Backup RabbitMQ definitions
   rabbitmqctl export_definitions backup.json

   # Backup Redis data
   redis-cli BGSAVE
   ```

## Integration Testing

### Test Queue Functionality

```python
# Test task execution
from app.tasks.feedback_tasks import process_feedback_task

result = process_feedback_task.delay(feedback_id=123)
print(f"Task ID: {result.id}")
print(f"Result: {result.get(timeout=10)}")
```

### Load Testing

```bash
# Generate test load
python scripts/queue_load_test.py --tasks=1000 --workers=4
```

## Support and Resources

- **RabbitMQ Documentation**: https://www.rabbitmq.com/documentation.html
- **Redis Documentation**: https://redis.io/documentation
- **Celery Documentation**: https://docs.celeryproject.org/
- **Queue Monitoring API**: `/api/v1/queue/docs`

For additional support, check the project's issue tracker or contact the development team.
