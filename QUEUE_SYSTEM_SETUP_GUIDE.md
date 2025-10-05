# Queue System Setup Guide

This guide provides comprehensive instructions for setting up the message queuing and caching system for CodeNova, which includes RabbitMQ for message queuing and Redis for caching and background task processing.

## Overview

The CodeNova platform uses a hybrid approach for background task processing:

- **Redis**: Primary queue system for fast task enqueueing and processing
- **RabbitMQ**: Optional secondary queue for high-reliability scenarios
- **Redis Cache**: Caching layer for analytics and file metadata

## Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.8+ with pip
- Access to modify environment variables

## Quick Setup with Docker Compose

### 1. Update docker-compose.yml

Add the following services to your `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # ... existing services ...

  redis:
    image: redis:7-alpine
    container_name: codenova_redis
    ports:
      - '6379:6379'
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    environment:
      - REDIS_PASSWORD=codenova_redis_password
    networks:
      - codenova_network

  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: codenova_rabbitmq
    ports:
      - '5672:5672' # AMQP port
      - '15672:15672' # Management UI
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    environment:
      - RABBITMQ_DEFAULT_USER=codenova
      - RABBITMQ_DEFAULT_PASS=rabbitmq_password
      - RABBITMQ_DEFAULT_VHOST=/
    networks:
      - codenova_network

volumes:
  redis_data:
  rabbitmq_data:
  # ... existing volumes ...

networks:
  codenova_network:
    driver: bridge
```

### 2. Update Environment Variables

Add these variables to your `.env` file:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_DB_QUEUE=1
REDIS_DB_RESULTS=2
REDIS_DB_CACHE=0

# RabbitMQ Configuration
RABBITMQ_URL=amqp://codenova:rabbitmq_password@localhost:5672/
RABBITMQ_MANAGEMENT_URL=http://localhost:15672

# Queue Configuration
WORKER_CONCURRENCY=4
TASK_TIMEOUT=600
TASK_MAX_RETRIES=3
RESULT_TTL=3600

# Cache Configuration
DEFAULT_CACHE_TTL=3600
CACHE_WARMING_ENABLED=true
CACHE_INVALIDATION_ENABLED=true

# Monitoring Configuration
QUEUE_MONITORING_ENABLED=true
QUEUE_HEALTH_CHECK_INTERVAL=60
QUEUE_ALERTING_ENABLED=false
```

### 3. Start Services

```bash
# Start Redis and RabbitMQ
docker-compose up -d redis rabbitmq

# Wait for services to be ready
sleep 10

# Verify Redis connection
docker exec codenova_redis redis-cli ping

# Verify RabbitMQ connection
curl -u codenova:rabbitmq_password http://localhost:15672/api/overview
```

## Manual Installation

### Redis Installation

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

#### macOS

```bash
brew install redis
brew services start redis
```

#### Windows

Download and install from: https://github.com/microsoftarchive/redis/releases

### RabbitMQ Installation

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install rabbitmq-server
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server

# Enable management plugin
sudo rabbitmq-plugins enable rabbitmq_management

# Create user
sudo rabbitmqctl add_user codenova rabbitmq_password
sudo rabbitmqctl set_user_tags codenova administrator
sudo rabbitmqctl set_permissions -p / codenova ".*" ".*" ".*"
```

#### macOS

```bash
brew install rabbitmq
brew services start rabbitmq

# Enable management plugin
rabbitmq-plugins enable rabbitmq_management

# Create user
rabbitmqctl add_user codenova rabbitmq_password
rabbitmqctl set_user_tags codenova administrator
rabbitmqctl set_permissions -p / codenova ".*" ".*" ".*"
```

## Configuration

### Redis Configuration

Create `/etc/redis/redis.conf` (Linux) or modify the configuration:

```conf
# Basic configuration
bind 127.0.0.1
port 6379
timeout 0
tcp-keepalive 300

# Memory management
maxmemory 512mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Security (optional)
# requirepass codenova_redis_password
```

### RabbitMQ Configuration

Create `/etc/rabbitmq/rabbitmq.conf`:

```conf
# Network configuration
listeners.tcp.default = 5672
management.tcp.port = 15672

# Memory and disk limits
vm_memory_high_watermark.relative = 0.6
disk_free_limit.relative = 2.0

# Clustering (if needed)
cluster_formation.peer_discovery_backend = rabbit_peer_discovery_classic_config
```

## Starting the Queue Worker

### Development Mode

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Start the Redis queue worker
python -m app.core.redis_worker

# Or use the provided script
python start_worker.py
```

### Production Mode

Create a systemd service file `/etc/systemd/system/codenova-worker.service`:

```ini
[Unit]
Description=CodeNova Queue Worker
After=network.target redis.service

[Service]
Type=simple
User=codenova
WorkingDirectory=/path/to/codenova/backend
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python -m app.core.redis_worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable codenova-worker
sudo systemctl start codenova-worker
```

## Monitoring and Health Checks

### Redis Monitoring

```bash
# Check Redis status
redis-cli ping

# Monitor Redis performance
redis-cli --latency-history

# Check memory usage
redis-cli info memory

# Monitor commands
redis-cli monitor
```

### RabbitMQ Monitoring

```bash
# Check RabbitMQ status
sudo rabbitmqctl status

# List queues
sudo rabbitmqctl list_queues

# Monitor connections
sudo rabbitmqctl list_connections

# Web interface
# Visit http://localhost:15672
# Login: codenova / rabbitmq_password
```

### Application Monitoring

The application provides built-in monitoring endpoints:

```bash
# Check queue health
curl http://localhost:8000/api/v1/monitoring/queue/health

# Get queue statistics
curl http://localhost:8000/api/v1/monitoring/queue/stats

# Get worker status
curl http://localhost:8000/api/v1/monitoring/workers/status

# Get cache performance
curl http://localhost:8000/api/v1/monitoring/cache/performance
```

## Performance Tuning

### Redis Performance

```conf
# Increase max clients
maxclients 10000

# Optimize for memory
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
set-max-intset-entries 512

# Disable slow operations in production
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
```

### RabbitMQ Performance

```conf
# Increase file descriptors
ulimit -n 65536

# Optimize memory
vm_memory_high_watermark.relative = 0.8

# Optimize disk I/O
disk_free_limit.relative = 1.0

# Enable lazy queues for large queues
default_queue_type = quorum
```

### Worker Performance

Environment variables for optimization:

```bash
# Increase worker concurrency
WORKER_CONCURRENCY=8

# Optimize batch processing
WORKER_BATCH_SIZE=20

# Increase memory limit
WORKER_MAX_MEMORY_MB=1024

# Enable compression for large payloads
ENABLE_COMPRESSION=true
```

## Troubleshooting

### Common Issues

1. **Redis Connection Refused**

   ```bash
   # Check if Redis is running
   sudo systemctl status redis

   # Check Redis logs
   sudo journalctl -u redis -f

   # Test connection
   redis-cli ping
   ```

2. **RabbitMQ Connection Failed**

   ```bash
   # Check RabbitMQ status
   sudo systemctl status rabbitmq-server

   # Check RabbitMQ logs
   sudo journalctl -u rabbitmq-server -f

   # Reset RabbitMQ (if needed)
   sudo rabbitmqctl stop_app
   sudo rabbitmqctl reset
   sudo rabbitmqctl start_app
   ```

3. **High Memory Usage**

   ```bash
   # Check Redis memory
   redis-cli info memory

   # Clear Redis cache (development only)
   redis-cli flushall

   # Check RabbitMQ memory
   sudo rabbitmqctl status
   ```

4. **Slow Task Processing**

   ```bash
   # Check queue depths
   redis-cli llen codenova:queue:high_priority

   # Monitor worker performance
   curl http://localhost:8000/api/v1/monitoring/workers/performance

   # Increase worker concurrency
   export WORKER_CONCURRENCY=8
   ```

### Log Analysis

```bash
# Worker logs
tail -f /var/log/codenova/worker.log

# Redis logs
tail -f /var/log/redis/redis-server.log

# RabbitMQ logs
tail -f /var/log/rabbitmq/rabbit@hostname.log
```

## Security Considerations

### Redis Security

```conf
# Enable authentication
requirepass your_strong_password

# Bind to specific interfaces
bind 127.0.0.1 10.0.0.1

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
```

### RabbitMQ Security

```bash
# Create dedicated user
rabbitmqctl add_user codenova_app secure_password
rabbitmqctl set_permissions -p / codenova_app "^codenova\." "^codenova\." "^codenova\."

# Enable SSL (production)
rabbitmq-plugins enable rabbitmq_auth_mechanism_ssl
```

### Network Security

```bash
# Firewall rules (Ubuntu/Debian)
sudo ufw allow from 10.0.0.0/8 to any port 6379  # Redis
sudo ufw allow from 10.0.0.0/8 to any port 5672  # RabbitMQ
sudo ufw deny 6379  # Block external Redis access
sudo ufw deny 5672  # Block external RabbitMQ access
```

## Backup and Recovery

### Redis Backup

```bash
# Create backup
redis-cli --rdb /backup/redis-backup-$(date +%Y%m%d).rdb

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backup/redis"
DATE=$(date +%Y%m%d_%H%M%S)
redis-cli --rdb "$BACKUP_DIR/redis-$DATE.rdb"
find "$BACKUP_DIR" -name "redis-*.rdb" -mtime +7 -delete
```

### RabbitMQ Backup

```bash
# Export definitions
rabbitmqctl export_definitions /backup/rabbitmq-definitions.json

# Backup data directory
tar -czf /backup/rabbitmq-data-$(date +%Y%m%d).tar.gz /var/lib/rabbitmq/
```

## Scaling Considerations

### Horizontal Scaling

1. **Multiple Workers**

   ```bash
   # Start multiple worker processes
   for i in {1..4}; do
     python -m app.core.redis_worker &
   done
   ```

2. **Redis Clustering**

   ```conf
   # redis.conf for cluster mode
   cluster-enabled yes
   cluster-config-file nodes.conf
   cluster-node-timeout 5000
   ```

3. **RabbitMQ Clustering**
   ```bash
   # Join cluster
   rabbitmqctl stop_app
   rabbitmqctl join_cluster rabbit@node1
   rabbitmqctl start_app
   ```

### Vertical Scaling

```bash
# Increase Redis memory
redis-cli config set maxmemory 2gb

# Increase RabbitMQ memory
rabbitmqctl set_vm_memory_high_watermark 0.8

# Increase worker resources
export WORKER_MAX_MEMORY_MB=2048
export WORKER_CONCURRENCY=16
```

This setup guide provides a comprehensive foundation for the message queuing and caching system. Follow the steps appropriate for your environment and adjust configurations based on your specific requirements.
