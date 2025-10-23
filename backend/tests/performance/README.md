# Performance and Load Testing Guide

## Overview

This directory contains performance and load tests to ensure the CodeNova platform can handle production workloads efficiently.

## Test Suites

### 1. Concurrent File Uploads (`test_load_testing.py`)

Tests system performance under concurrent upload load:
- **Concurrent Single Files**: 10+ simultaneous uploads
- **Large Batch Uploads**: 20+ files in single batch
- **Upload Throughput**: Sustained upload rate measurement

### 2. Analysis Queue Performance

Tests background job processing:
- **Queue Processing Rate**: How fast analyses complete
- **Queue Under Load**: Behavior with 30+ concurrent submissions
- **Backlog Handling**: Recovery from queue backlog

### 3. Database Query Performance

Tests database operation speed:
- **History Queries**: Pagination with 100+ records
- **Analytics Aggregation**: Platform-wide statistics
- **Search Performance**: User search with 200+ records

### 4. API Response Times

Tests endpoint performance:
- **Individual Endpoints**: Response time for each endpoint
- **Concurrent Requests**: 20+ simultaneous API calls
- **Average Response Time**: Overall API performance

## Running Performance Tests

### Run All Performance Tests

```bash
# From backend directory
pytest tests/performance/ -v -m performance

# Or use the test runner script
./tests/run_e2e_tests.sh --performance-only
```

### Run Specific Test Classes

```bash
# Concurrent uploads only
pytest tests/performance/test_load_testing.py::TestConcurrentFileUploads -v

# Database performance only
pytest tests/performance/test_load_testing.py::TestDatabaseQueryPerformance -v
```

### Run with Performance Profiling

```bash
# With profiling
pytest tests/performance/ -v --profile

# With detailed timing
pytest tests/performance/ -v --durations=10
```

## Performance Benchmarks

### Target Metrics

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| File Upload (single) | < 1s | < 2s | > 5s |
| File Upload (batch 10) | < 5s | < 10s | > 20s |
| Analysis Completion | < 10s | < 30s | > 60s |
| History Query (50 records) | < 0.5s | < 1s | > 2s |
| Analytics Aggregation | < 1s | < 2s | > 5s |
| API Response (avg) | < 0.5s | < 1s | > 2s |
| Concurrent Requests (20) | 95% success | 90% success | < 80% |

### Current Performance

Run tests to see current performance:
```bash
pytest tests/performance/ -v -s
```

Output includes timing information for each test.

## Load Testing Scenarios

### Scenario 1: Normal Load

Simulates typical daily usage:
- 10 concurrent users
- 50 file uploads per hour
- 100 API requests per minute

```bash
pytest tests/performance/test_load_testing.py::TestConcurrentFileUploads::test_concurrent_single_file_uploads -v
```

### Scenario 2: Peak Load

Simulates peak usage periods:
- 30 concurrent users
- 200 file uploads per hour
- 500 API requests per minute

```bash
pytest tests/performance/test_load_testing.py::TestConcurrentFileUploads::test_large_batch_upload -v
pytest tests/performance/test_load_testing.py::TestAnalysisQueuePerformance::test_queue_under_load -v
```

### Scenario 3: Stress Test

Tests system limits:
- 50+ concurrent users
- 500+ file uploads per hour
- 1000+ API requests per minute

```bash
# Modify test parameters for stress testing
# Edit test files to increase num_concurrent values
```

## Performance Optimization

### Identifying Bottlenecks

1. **Run Performance Tests**:
   ```bash
   pytest tests/performance/ -v -s > performance_results.txt
   ```

2. **Analyze Results**:
   - Look for tests that exceed target metrics
   - Identify patterns in failures
   - Check resource usage during tests

3. **Profile Slow Operations**:
   ```bash
   python -m cProfile -o profile.stats your_script.py
   python -m pstats profile.stats
   ```

### Common Bottlenecks

1. **Database Queries**:
   - Add indexes on frequently queried columns
   - Optimize JOIN operations
   - Use query result caching

2. **File Uploads**:
   - Implement chunked uploads
   - Use async file processing
   - Optimize storage backend

3. **Analysis Queue**:
   - Increase worker count
   - Optimize AI service calls
   - Implement request batching

4. **API Responses**:
   - Add response caching
   - Optimize serialization
   - Reduce payload sizes

## Monitoring Performance

### During Tests

Monitor system resources:
```bash
# CPU and Memory
htop

# Database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Redis queue
redis-cli INFO stats
```

### Continuous Monitoring

Set up monitoring for production:
- Response time tracking
- Error rate monitoring
- Queue depth monitoring
- Database query performance

## Performance Testing Best Practices

1. **Consistent Environment**: Run tests in consistent environment
2. **Warm-up Period**: Allow system to warm up before measuring
3. **Multiple Runs**: Run tests multiple times for accuracy
4. **Realistic Data**: Use production-like data volumes
5. **Monitor Resources**: Track CPU, memory, disk, network
6. **Document Results**: Keep performance test results over time

## Troubleshooting

### Tests Fail Under Load

If tests fail with high concurrency:
- Check connection pool sizes
- Verify worker count is sufficient
- Look for resource exhaustion (memory, connections)
- Check for deadlocks or race conditions

### Inconsistent Results

If performance varies significantly:
- Ensure no other processes are running
- Check for background tasks
- Verify network stability
- Run tests multiple times

### Memory Issues

If tests cause memory issues:
- Check for memory leaks
- Verify proper cleanup in tests
- Monitor memory usage during tests
- Reduce test data size if needed

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run Performance Tests
  run: |
    cd backend
    pytest tests/performance/ -v -m performance --junitxml=test-results/performance-results.xml
  
- name: Check Performance Thresholds
  run: |
    # Parse results and fail if metrics exceed thresholds
    python scripts/check_performance_thresholds.py
```

### Performance Regression Detection

Track performance over time:
```bash
# Save results
pytest tests/performance/ --benchmark-save=baseline

# Compare with baseline
pytest tests/performance/ --benchmark-compare=baseline
```

## Advanced Load Testing

For more comprehensive load testing, consider:

1. **Locust**: Distributed load testing
   ```python
   from locust import HttpUser, task, between
   
   class CodeNovaUser(HttpUser):
       wait_time = between(1, 3)
       
       @task
       def upload_file(self):
           self.client.post("/api/v1/files/upload-batch", files=...)
   ```

2. **Apache JMeter**: GUI-based load testing
3. **k6**: Modern load testing tool

## Reporting

Generate performance reports:
```bash
# HTML report
pytest tests/performance/ --html=reports/performance-report.html

# JSON report for analysis
pytest tests/performance/ --json-report --json-report-file=reports/performance.json
```

## Performance Goals

### Short-term (Current Sprint)
- All tests pass with target metrics
- No critical performance issues
- 95%+ success rate under normal load

### Medium-term (Next Quarter)
- Handle 2x current load
- Reduce average response time by 20%
- Implement caching for common queries

### Long-term (Annual)
- Handle 10x current load
- Sub-second response for all endpoints
- Auto-scaling based on load
