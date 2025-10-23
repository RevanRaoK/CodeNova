# Quick Start: E2E and Performance Testing

## Prerequisites

1. **Backend dependencies installed**:
   ```bash
   cd backend
   pip install -r requirements.txt
   pip install pytest pytest-asyncio pytest-mock pytest-cov
   ```

2. **Install backend package in development mode** (fixes import issues):
   ```bash
   cd backend
   pip install -e .
   ```

3. **Database setup**:
   ```bash
   # Test database will be created automatically
   # Ensure PostgreSQL is running for integration tests
   ```

4. **Make test script executable**:
   ```bash
   chmod +x tests/run_e2e_tests.sh
   ```

## Running Tests

### Quick Test Run

```bash
# From backend directory
cd backend

# Run all E2E and performance tests
./tests/run_e2e_tests.sh
```

### Selective Testing

```bash
# E2E tests only (faster)
./tests/run_e2e_tests.sh --e2e-only

# Performance tests only
./tests/run_e2e_tests.sh --performance-only

# Security tests only
./tests/run_e2e_tests.sh --security-only
```

### Using pytest Directly

```bash
# All E2E tests
pytest tests/e2e/ -v

# All performance tests
pytest tests/performance/ -v

# All security tests
pytest tests/security/ -v

# Specific test file
pytest tests/e2e/test_user_workflows.py -v

# Specific test class
pytest tests/e2e/test_user_workflows.py::TestFileUploadAndAnalysisWorkflow -v

# Specific test method
pytest tests/e2e/test_user_workflows.py::TestFileUploadAndAnalysisWorkflow::test_single_file_upload_and_analysis -v
```

## Test Markers

Run tests by marker:

```bash
# All E2E tests
pytest -m e2e -v

# All performance tests
pytest -m performance -v

# All security tests
pytest -m security -v

# Slow tests only
pytest -m slow -v

# Exclude slow tests
pytest -m "not slow" -v
```

## Viewing Results

### Console Output

Tests display results in the console with:
- ✓ Green checkmarks for passing tests
- ✗ Red X for failing tests
- Test duration
- Performance metrics

### HTML Report

```bash
# Generate HTML report
pytest tests/e2e/ --html=reports/e2e-report.html --self-contained-html

# Open in browser
open reports/e2e-report.html  # macOS
xdg-open reports/e2e-report.html  # Linux
```

### Coverage Report

```bash
# Generate coverage report
pytest tests/e2e/ --cov=app --cov-report=html

# View coverage
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Understanding Test Output

### E2E Test Output

```
tests/e2e/test_user_workflows.py::TestFileUploadAndAnalysisWorkflow::test_single_file_upload_and_analysis PASSED [10%]
```

- **PASSED**: Test succeeded
- **FAILED**: Test failed (see traceback)
- **SKIPPED**: Test was skipped
- **[10%]**: Progress indicator

### Performance Test Output

```
Concurrent uploads: 10 files in 8.45s
Upload throughput: 5.92 uploads/second
```

Performance tests include timing information.

### Security Test Output

```
Note: Login rate limiting may not be implemented
```

Security tests may include notes about optional features.

## Troubleshooting

### Tests Fail to Start

```bash
# Check dependencies
pip install pytest pytest-asyncio pytest-mock

# Check database
python -c "from app.core.database import engine; print('DB OK')"
```

### Database Errors

```bash
# Clean test database
rm -f test.db

# Recreate tables
python -c "from app.core.database import Base, engine; Base.metadata.create_all(engine)"
```

### Import Errors

```bash
# Ensure you're in the backend directory
cd backend

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Timeout Errors

If tests timeout:
- Increase timeout values in test files
- Check if background workers are running
- Verify AI service is accessible

### Permission Errors

```bash
# Make script executable
chmod +x tests/run_e2e_tests.sh

# Check file permissions
ls -la tests/run_e2e_tests.sh
```

## Performance Testing Tips

### Running Performance Tests

Performance tests can take several minutes:

```bash
# Run with output to see progress
pytest tests/performance/ -v -s

# Run specific performance test
pytest tests/performance/test_load_testing.py::TestConcurrentFileUploads -v -s
```

### Interpreting Results

- **Target**: Ideal performance
- **Acceptable**: Acceptable performance
- **Critical**: Performance issue

If tests exceed critical thresholds, investigate bottlenecks.

## Security Testing Tips

### Running Security Tests

```bash
# Run all security tests
pytest tests/security/ -v

# Run specific security category
pytest tests/security/test_security.py::TestAuthenticationSecurity -v
```

### Expected Behavior

- Most security tests should PASS
- Some tests may note features "may not be implemented" - this is OK
- Any FAILED security test should be investigated immediately

## CI/CD Integration

### GitHub Actions

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-mock
      - name: Run E2E tests
        run: |
          cd backend
          pytest tests/e2e/ -v
      - name: Run security tests
        run: |
          cd backend
          pytest tests/security/ -v
```

## Next Steps

1. **Run the tests**: `./tests/run_e2e_tests.sh`
2. **Review results**: Check for any failures
3. **Fix issues**: Address any failing tests
4. **Integrate**: Add to CI/CD pipeline
5. **Monitor**: Track performance over time

## Getting Help

- **E2E Tests**: See `tests/e2e/README.md`
- **Performance Tests**: See `tests/performance/README.md`
- **Security Tests**: See `tests/security/README.md`
- **Full Report**: See `tests/TASK_13_COMPLETION_REPORT.md`

## Common Commands Reference

```bash
# Quick test run
./tests/run_e2e_tests.sh

# E2E only
pytest tests/e2e/ -v

# Performance only
pytest tests/performance/ -v

# Security only
pytest tests/security/ -v

# With coverage
pytest tests/e2e/ --cov=app --cov-report=html

# Specific test
pytest tests/e2e/test_user_workflows.py::TestFileUploadAndAnalysisWorkflow::test_single_file_upload_and_analysis -v

# Generate HTML report
pytest tests/e2e/ --html=reports/e2e-report.html --self-contained-html
```
