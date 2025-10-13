# Health Check and Testing System

This document describes the comprehensive health check and testing system implemented for the CodeNova application.

## Overview

The health check system provides comprehensive monitoring and testing capabilities for all system integrations:

- **Digital Ocean Spaces** - File storage connectivity and operations
- **GitHub Integration** - OAuth, webhooks, and API connectivity
- **Job Queue System** - Background job processing and monitoring
- **Database Connectivity** - Database health and configuration
- **Configuration Validation** - Comprehensive configuration validation

## Components

### 1. Health Check API Endpoints

Located in `backend/app/api/v1/endpoints/health_check.py`

#### Available Endpoints:

- `GET /api/v1/health/health` - Basic system health (no auth required)
- `GET /api/v1/health/health/detailed` - Detailed health check (auth required)
- `GET /api/v1/health/test/spaces` - Test Digital Ocean Spaces (admin only)
- `GET /api/v1/health/test/github` - Test GitHub integration (admin only)
- `GET /api/v1/health/test/queue` - Test job queue system (admin only)
- `GET /api/v1/health/test/all` - Run comprehensive tests (admin only)

#### Basic Health Check

```bash
curl http://localhost:8000/api/v1/health/health
```

Returns basic system status without authentication - suitable for load balancers and monitoring systems.

#### Detailed Health Check

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/health/health/detailed
```

Returns comprehensive health information for all system components.

#### Spaces Connectivity Test

```bash
curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/api/v1/health/test/spaces
```

Performs comprehensive Digital Ocean Spaces testing:

- Configuration validation
- Connectivity test
- Upload/download/delete operations
- Service initialization

#### GitHub Integration Test

```bash
curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/api/v1/health/test/github
```

Tests GitHub integration components:

- OAuth configuration
- API connectivity
- Webhook configuration
- Rate limiting status

#### Queue System Test

```bash
curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/api/v1/health/test/queue
```

Tests job queue system health:

- Queue connectivity
- Worker status
- Performance metrics
- Queue depths and processing rates

#### Comprehensive Test Suite

```bash
curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/api/v1/health/test/all?include_performance=true
```

Runs all available tests and provides a comprehensive system health report.

### 2. Command Line Test Script

Located in `backend/test_system_health.py`

A comprehensive Python script for testing system health from the command line.

#### Usage:

```bash
# Run all tests
python test_system_health.py

# Test specific components
python test_system_health.py --config-only
python test_system_health.py --spaces-only
python test_system_health.py --github-only
python test_system_health.py --queue-only

# Output options
python test_system_health.py --verbose
python test_system_health.py --json

# Include performance tests
python test_system_health.py --performance
```

#### Exit Codes:

- `0` - All tests passed
- `1` - Some tests failed
- `2` - Tests completed with warnings

### 3. Windows Helper Scripts

#### Batch File: `run_health_tests.bat`

```cmd
# Run all tests
run_health_tests.bat

# Test specific components
run_health_tests.bat --config
run_health_tests.bat --spaces --verbose
run_health_tests.bat --github --json
```

#### PowerShell Script: `run_health_tests.ps1`

```powershell
# Run all tests
.\run_health_tests.ps1

# Test specific components
.\run_health_tests.ps1 -ConfigOnly -Verbose
.\run_health_tests.ps1 -SpacesOnly -Json
.\run_health_tests.ps1 -GitHubOnly
```

## Test Categories

### Configuration Validation Tests

- **Environment Variables** - Checks for required configuration
- **Format Validation** - Validates configuration formats
- **Credential Testing** - Tests actual credentials
- **Service Connectivity** - Tests connections to external services

### Digital Ocean Spaces Tests

- **Configuration Presence** - Verifies all required settings
- **Endpoint Format** - Validates endpoint URL format
- **Connectivity** - Tests connection to Digital Ocean Spaces
- **Credentials** - Validates access credentials
- **Bucket Access** - Tests bucket permissions
- **File Operations** - Tests upload/download/delete operations
- **Service Initialization** - Tests FileStorageService initialization

### GitHub Integration Tests

- **OAuth Configuration** - Validates OAuth app settings
- **API Connectivity** - Tests GitHub API access
- **Webhook Configuration** - Validates webhook settings
- **Rate Limiting** - Checks API rate limit status
- **Credential Validation** - Tests OAuth credentials

### Job Queue System Tests

- **Queue Health** - Tests queue system connectivity
- **Worker Status** - Checks active workers
- **Queue Statistics** - Retrieves queue metrics
- **Performance Metrics** - Gathers performance data
- **Queue Depths** - Monitors queue backlogs

### Database Tests

- **Connectivity** - Tests database connection
- **Configuration** - Validates database settings
- **Basic Operations** - Tests simple queries

## Integration with Existing Systems

The health check system integrates with existing services:

- **ConfigurationValidationService** - For configuration validation
- **FileStorageService** - For Spaces testing
- **GitHubAPIClient** - For GitHub testing
- **QueueMonitoringService** - For queue testing

## Monitoring and Alerting

### Health Check Endpoints for Monitoring

The basic health endpoint (`/api/v1/health/health`) is designed for:

- Load balancer health checks
- Monitoring system integration
- Automated health monitoring
- CI/CD pipeline health validation

### Response Formats

#### Healthy System Response:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "database": { "status": "healthy" },
    "configuration": { "status": "healthy" }
  }
}
```

#### Degraded System Response:

```json
{
  "status": "degraded",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "database": { "status": "healthy" },
    "configuration": {
      "status": "unhealthy",
      "missing": ["GITHUB_CLIENT_SECRET"]
    }
  }
}
```

## Usage Examples

### Development Environment Setup Validation

```bash
# Validate development environment setup
python test_system_health.py --config-only --verbose

# Test specific integrations during development
python test_system_health.py --spaces-only
python test_system_health.py --github-only
```

### Production Health Monitoring

```bash
# Quick health check for monitoring
curl http://localhost:8000/api/v1/health/health

# Detailed health check for troubleshooting
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/health/health/detailed
```

### CI/CD Pipeline Integration

```bash
# Run health tests in CI/CD pipeline
python test_system_health.py --json > health_report.json

# Check exit code for pipeline decisions
if [ $? -eq 0 ]; then
  echo "Health checks passed"
else
  echo "Health checks failed"
  exit 1
fi
```

### Troubleshooting Integration Issues

```bash
# Comprehensive testing with verbose output
python test_system_health.py --verbose

# Test specific problematic component
python test_system_health.py --spaces-only --verbose
python test_system_health.py --github-only --verbose
```

## Error Handling and Reporting

The health check system provides detailed error reporting:

- **Error Codes** - Specific error codes for different failure types
- **Suggestions** - Actionable suggestions for fixing issues
- **Detailed Messages** - Clear descriptions of what went wrong
- **Context Information** - Additional details for troubleshooting

## Security Considerations

- **Authentication Required** - Detailed health checks require authentication
- **Admin Only Tests** - Comprehensive tests require admin privileges
- **Credential Protection** - Sensitive information is masked in outputs
- **Rate Limiting** - Tests respect API rate limits

## Performance Considerations

- **Timeout Handling** - All network operations have timeouts
- **Concurrent Testing** - Tests run concurrently where possible
- **Resource Cleanup** - Proper cleanup of test resources
- **Minimal Impact** - Tests designed to have minimal system impact

## Future Enhancements

Potential future improvements:

- **Performance Benchmarking** - Automated performance testing
- **Historical Tracking** - Health check history and trends
- **Alerting Integration** - Integration with alerting systems
- **Custom Health Checks** - User-defined health check extensions
- **Metrics Export** - Export health metrics to monitoring systems
