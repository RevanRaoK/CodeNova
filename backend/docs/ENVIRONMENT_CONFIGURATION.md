# Environment Configuration Guide

## Overview

This document describes all environment variables used by the CodeNova platform and how to configure them for different environments (development, staging, production).

## Configuration Files

### Development
- File: `backend/.env`
- Purpose: Local development
- Security: Not committed to git

### Staging
- File: `backend/.env.staging`
- Purpose: Pre-production testing
- Security: Stored in secure vault

### Production
- File: `backend/.env.production`
- Purpose: Live production environment
- Security: Stored in secure vault, encrypted

## Required Environment Variables

### Database Configuration

```bash
# PostgreSQL Database URL
DATABASE_URL=postgresql://username:password@host:port/database

# Example - Development
DATABASE_URL=postgresql://codenova:dev_password@localhost:5432/codenova_dev

# Example - Production
DATABASE_URL=postgresql://codenova_prod:secure_password@db.example.com:5432/codenova_prod

# Connection Pool Settings
DB_POOL_SIZE=20                    # Number of connections in pool
DB_MAX_OVERFLOW=10                 # Max connections beyond pool size
DB_POOL_TIMEOUT=30                 # Timeout for getting connection (seconds)
DB_POOL_RECYCLE=3600              # Recycle connections after (seconds)
```

### Redis Configuration

```bash
# Redis URL for caching and queue
REDIS_URL=redis://host:port/db

# Example - Development
REDIS_URL=redis://localhost:6379/0

# Example - Production
REDIS_URL=redis://:password@redis.example.com:6379/0

# Redis Settings
REDIS_MAX_CONNECTIONS=50           # Max connections in pool
REDIS_SOCKET_TIMEOUT=5             # Socket timeout (seconds)
REDIS_SOCKET_CONNECT_TIMEOUT=5     # Connection timeout (seconds)
```

### Application Settings

```bash
# Application Name
APP_NAME=CodeNova

# Environment (development, staging, production)
ENVIRONMENT=development

# Debug Mode (true/false)
DEBUG=true

# API Version
API_VERSION=v1

# Server Host and Port
HOST=0.0.0.0
PORT=8000

# Base URL
BASE_URL=http://localhost:8000

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

### Security Settings

```bash
# Secret Key for JWT tokens (MUST be unique and secure)
SECRET_KEY=your-super-secret-key-change-this-in-production

# JWT Settings
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Hashing
PASSWORD_HASH_ALGORITHM=bcrypt
PASSWORD_MIN_LENGTH=8

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=20
```

### AI Service Configuration

```bash
# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=2048
GEMINI_TIMEOUT=30

# AI Service Settings
AI_MAX_RETRIES=3
AI_RETRY_DELAY=2
AI_RATE_LIMIT_PER_MINUTE=60
```

### File Storage Configuration

```bash
# Storage Type (local, s3, spaces)
STORAGE_TYPE=local

# Local Storage
LOCAL_STORAGE_PATH=/var/codenova/uploads
LOCAL_STORAGE_MAX_SIZE_MB=5

# Digital Ocean Spaces (if using)
SPACES_REGION=nyc3
SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
SPACES_BUCKET=codenova-files
SPACES_ACCESS_KEY=your-access-key
SPACES_SECRET_KEY=your-secret-key
SPACES_PUBLIC_URL=https://codenova-files.nyc3.digitaloceanspaces.com

# AWS S3 (if using)
AWS_REGION=us-east-1
AWS_S3_BUCKET=codenova-files
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# File Upload Settings
MAX_FILE_SIZE_MB=5
MAX_BATCH_SIZE=20
MAX_BATCH_TOTAL_SIZE_MB=50
ALLOWED_FILE_EXTENSIONS=.py,.js,.ts,.jsx,.tsx,.java,.cpp,.c,.cs,.go,.rs,.php,.rb,.swift,.kt,.scala
```

### Background Job Configuration

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Worker Settings
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=4
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000

# Task Settings
CELERY_TASK_SOFT_TIME_LIMIT=300
CELERY_TASK_TIME_LIMIT=600
CELERY_TASK_ACKS_LATE=true
CELERY_TASK_REJECT_ON_WORKER_LOST=true

# Queue Names
CELERY_QUEUE_DEFAULT=default
CELERY_QUEUE_ANALYSIS=analysis
CELERY_QUEUE_NOTIFICATIONS=notifications
```

### Email Configuration (Optional)

```bash
# SMTP Settings
SMTP_ENABLED=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@codenova.com
SMTP_PASSWORD=your-email-password
SMTP_FROM_EMAIL=noreply@codenova.com
SMTP_FROM_NAME=CodeNova

# Email Templates
EMAIL_TEMPLATES_DIR=/app/templates/email
```

### Logging Configuration

```bash
# Log Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log Format
LOG_FORMAT=json

# Log Output
LOG_TO_FILE=true
LOG_FILE_PATH=/var/log/codenova/app.log
LOG_FILE_MAX_SIZE_MB=100
LOG_FILE_BACKUP_COUNT=10

# Sentry (Error Tracking)
SENTRY_ENABLED=false
SENTRY_DSN=your-sentry-dsn
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Monitoring Configuration

```bash
# Prometheus Metrics
METRICS_ENABLED=true
METRICS_PORT=9090

# Health Check
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_PATH=/health

# Performance Monitoring
APM_ENABLED=false
APM_SERVICE_NAME=codenova-api
APM_SERVER_URL=http://apm-server:8200
```

## Environment-Specific Configurations

### Development Environment

```bash
# .env (development)
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

DATABASE_URL=postgresql://codenova:dev_password@localhost:5432/codenova_dev
REDIS_URL=redis://localhost:6379/0

SECRET_KEY=dev-secret-key-not-for-production
FRONTEND_URL=http://localhost:3000

STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./uploads

GEMINI_API_KEY=your-dev-api-key

SMTP_ENABLED=false
SENTRY_ENABLED=false
METRICS_ENABLED=false
```

### Staging Environment

```bash
# .env.staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

DATABASE_URL=postgresql://codenova_staging:staging_password@staging-db.internal:5432/codenova_staging
REDIS_URL=redis://:staging_redis_password@staging-redis.internal:6379/0

SECRET_KEY=staging-secret-key-change-this
FRONTEND_URL=https://staging.codenova.com
BASE_URL=https://api-staging.codenova.com

STORAGE_TYPE=spaces
SPACES_BUCKET=codenova-staging-files
SPACES_ACCESS_KEY=staging-access-key
SPACES_SECRET_KEY=staging-secret-key

GEMINI_API_KEY=your-staging-api-key

SMTP_ENABLED=true
SMTP_HOST=smtp.sendgrid.net
SMTP_USER=apikey
SMTP_PASSWORD=staging-sendgrid-key

SENTRY_ENABLED=true
SENTRY_DSN=your-staging-sentry-dsn
SENTRY_ENVIRONMENT=staging

METRICS_ENABLED=true
```

### Production Environment

```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

DATABASE_URL=postgresql://codenova_prod:super_secure_password@prod-db.internal:5432/codenova_prod
REDIS_URL=redis://:super_secure_redis_password@prod-redis.internal:6379/0

SECRET_KEY=production-secret-key-very-long-and-random-change-this
FRONTEND_URL=https://codenova.com
BASE_URL=https://api.codenova.com

STORAGE_TYPE=spaces
SPACES_BUCKET=codenova-prod-files
SPACES_ACCESS_KEY=prod-access-key
SPACES_SECRET_KEY=prod-secret-key

GEMINI_API_KEY=your-production-api-key

# Enhanced Security
RATE_LIMIT_PER_MINUTE=60
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
PASSWORD_MIN_LENGTH=12

# Email
SMTP_ENABLED=true
SMTP_HOST=smtp.sendgrid.net
SMTP_USER=apikey
SMTP_PASSWORD=production-sendgrid-key

# Monitoring
SENTRY_ENABLED=true
SENTRY_DSN=your-production-sentry-dsn
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

METRICS_ENABLED=true
APM_ENABLED=true

# Logging
LOG_TO_FILE=true
LOG_FILE_PATH=/var/log/codenova/app.log
```

## Security Best Practices

### Secret Key Generation

Generate secure secret keys:

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Using OpenSSL
openssl rand -base64 64
```

### Password Requirements

Production passwords should:
- Be at least 32 characters long
- Include uppercase, lowercase, numbers, and symbols
- Be unique (not reused)
- Be stored in a secure vault (e.g., AWS Secrets Manager, HashiCorp Vault)

### Environment Variable Security

1. **Never commit** `.env` files to git
2. **Use environment variable management** tools:
   - AWS Secrets Manager
   - HashiCorp Vault
   - Kubernetes Secrets
   - Docker Secrets
3. **Rotate secrets** regularly (every 90 days)
4. **Audit access** to environment variables
5. **Encrypt** sensitive values at rest

## Validation

### Startup Validation

The application validates environment variables on startup:

```python
# app/core/config.py
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    # Required fields
    DATABASE_URL: str
    SECRET_KEY: str
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters')
        return v
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError('DATABASE_URL must be a PostgreSQL URL')
        return v
```

### Manual Validation

Validate your configuration:

```bash
# Check required variables
python -c "from app.core.config import settings; print('✓ Configuration valid')"

# Test database connection
python -c "from app.db.session import engine; engine.connect(); print('✓ Database connected')"

# Test Redis connection
python -c "from app.core.cache import redis_client; redis_client.ping(); print('✓ Redis connected')"
```

## Troubleshooting

### Common Issues

#### Database Connection Failed

```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check network connectivity
nc -zv db-host 5432
```

#### Redis Connection Failed

```bash
# Check REDIS_URL format
echo $REDIS_URL

# Test connection
redis-cli -u $REDIS_URL ping

# Check network connectivity
nc -zv redis-host 6379
```

#### File Upload Fails

```bash
# Check storage configuration
echo $STORAGE_TYPE
echo $LOCAL_STORAGE_PATH

# Check permissions
ls -la $LOCAL_STORAGE_PATH

# Check disk space
df -h
```

#### AI Service Timeout

```bash
# Check API key
echo $GEMINI_API_KEY | cut -c1-10

# Test API connection
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models
```

## Migration Guide

### From Development to Production

1. **Copy template**:
   ```bash
   cp .env .env.production
   ```

2. **Update all values**:
   - Change DEBUG to false
   - Update DATABASE_URL
   - Generate new SECRET_KEY
   - Update FRONTEND_URL and BASE_URL
   - Configure production storage
   - Enable monitoring

3. **Validate**:
   ```bash
   python -c "from app.core.config import settings; print(settings.dict())"
   ```

4. **Test**:
   ```bash
   # Dry run
   python app/main.py --validate-config
   ```

### Updating Existing Environment

1. **Backup current config**:
   ```bash
   cp .env .env.backup
   ```

2. **Update variables**:
   ```bash
   # Edit .env file
   nano .env
   ```

3. **Restart services**:
   ```bash
   # Docker
   docker-compose restart

   # Systemd
   sudo systemctl restart codenova
   ```

4. **Verify**:
   ```bash
   # Check logs
   tail -f /var/log/codenova/app.log

   # Test health endpoint
   curl http://localhost:8000/health
   ```

## Reference

### Complete Example

See `backend/.env.example` for a complete example with all variables.

### Configuration Schema

See `backend/app/core/config.py` for the complete configuration schema and validation rules.

### Docker Compose

See `docker-compose.yml` for how environment variables are used in containerized deployments.

## Support

For configuration issues:
- Email: devops@codenova.com
- Slack: #codenova-devops
- Documentation: https://docs.codenova.com/configuration
