# Quick Start Guide - Backend Tests

## Running Tests

### Quick Commands

```bash
# Navigate to backend directory
cd backend

# Run all tests
./run_tests.sh all

# Run only unit tests
./run_tests.sh unit

# Run only integration tests
./run_tests.sh integration

# Run with detailed coverage report
./run_tests.sh coverage

# Run fast tests (exclude slow tests)
./run_tests.sh fast
```

### Using pytest Directly

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/unit/test_file_validation_service.py -v

# Run specific test class
python -m pytest tests/unit/test_admin_service.py::TestAdminService -v

# Run specific test
python -m pytest tests/unit/test_admin_service.py::TestAdminService::test_get_all_users_no_filters -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# Run without coverage (faster)
python -m pytest tests/ --no-cov

# Run with verbose output
python -m pytest tests/ -v

# Run with extra verbose output
python -m pytest tests/ -vv

# Stop on first failure
python -m pytest tests/ -x

# Show local variables on failure
python -m pytest tests/ -l

# Run tests matching pattern
python -m pytest tests/ -k "admin"
```

### Test Markers

```bash
# Run only unit tests
python -m pytest -m unit

# Run only integration tests
python -m pytest -m integration

# Run only API tests
python -m pytest -m api

# Run only async tests
python -m pytest -m asyncio

# Exclude slow tests
python -m pytest -m "not slow"
```

## Viewing Coverage Reports

### HTML Coverage Report

```bash
# Generate HTML report
python -m pytest tests/ --cov=app --cov-report=html

# Open in browser (Linux)
xdg-open htmlcov/index.html

# Open in browser (macOS)
open htmlcov/index.html

# Open in browser (Windows)
start htmlcov/index.html
```

### Terminal Coverage Report

```bash
# Show coverage in terminal
python -m pytest tests/ --cov=app --cov-report=term-missing
```

### XML Coverage Report (for CI/CD)

```bash
# Generate XML report
python -m pytest tests/ --cov=app --cov-report=xml
```

## Test Structure

```
backend/tests/
├── conftest.py                          # Shared fixtures
├── pytest.ini                           # Pytest configuration
├── unit/                                # Unit tests
│   ├── test_file_validation_service.py
│   ├── test_admin_service.py
│   ├── test_audit_logger.py
│   ├── test_global_analytics_service.py
│   └── test_file_upload_service.py
└── integration/                         # Integration tests
    ├── test_file_upload_api.py
    ├── test_admin_api.py
    └── test_auth_and_authorization.py
```

## Common Issues

### Issue: Tests fail with "username" attribute error
**Solution**: User model uses `email` and `full_name`, not `username`. This has been fixed.

### Issue: Coverage below 80%
**Solution**: Run tests for specific services only, or adjust coverage threshold in pytest.ini

### Issue: Tests are slow
**Solution**: Use `--no-cov` flag or run specific test files

### Issue: Import errors
**Solution**: Ensure you're in the backend directory and dependencies are installed

## Test Development

### Creating New Tests

1. **Unit Test Template**:
```python
import pytest
from unittest.mock import Mock

class TestMyService:
    @pytest.fixture
    def service(self):
        return MyService()
    
    @pytest.mark.unit
    def test_my_function(self, service):
        result = service.my_function()
        assert result is not None
```

2. **Integration Test Template**:
```python
import pytest
from fastapi.testclient import TestClient

class TestMyAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_my_endpoint(self, client):
        response = client.get("/api/v1/my-endpoint")
        assert response.status_code == 200
```

### Running New Tests

```bash
# Run your new test file
python -m pytest tests/unit/test_my_service.py -v

# Run with coverage
python -m pytest tests/unit/test_my_service.py --cov=app.services.my_service
```

## Debugging Tests

### Show Print Statements

```bash
# Show print output
python -m pytest tests/ -s

# Show print output with verbose
python -m pytest tests/ -sv
```

### Debug with pdb

```python
# Add breakpoint in test
def test_my_function():
    import pdb; pdb.set_trace()
    result = my_function()
    assert result is not None
```

```bash
# Run with pdb
python -m pytest tests/ --pdb
```

### Show Warnings

```bash
# Show all warnings
python -m pytest tests/ -W all

# Show specific warning
python -m pytest tests/ -W error::DeprecationWarning
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests
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
      - name: Run tests
        run: |
          cd backend
          ./run_tests.sh coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./backend/coverage.xml
```

## Performance Tips

1. **Run tests in parallel** (requires pytest-xdist):
```bash
pip install pytest-xdist
python -m pytest tests/ -n auto
```

2. **Run only failed tests**:
```bash
python -m pytest tests/ --lf
```

3. **Run failed tests first**:
```bash
python -m pytest tests/ --ff
```

4. **Cache test results**:
```bash
python -m pytest tests/ --cache-clear  # Clear cache
python -m pytest tests/ --cache-show   # Show cache
```

## Getting Help

### Pytest Help

```bash
# Show all options
python -m pytest --help

# Show markers
python -m pytest --markers

# Show fixtures
python -m pytest --fixtures
```

### Test Documentation

- **Coverage Report**: `tests/TEST_COVERAGE_REPORT.md`
- **Completion Summary**: `tests/TASK_11_COMPLETION_SUMMARY.md`
- **This Guide**: `tests/QUICK_START.md`

## Quick Reference

| Command | Description |
|---------|-------------|
| `./run_tests.sh all` | Run all tests with coverage |
| `./run_tests.sh unit` | Run unit tests only |
| `./run_tests.sh integration` | Run integration tests only |
| `python -m pytest tests/ -v` | Run all tests verbose |
| `python -m pytest tests/ -x` | Stop on first failure |
| `python -m pytest tests/ -k "admin"` | Run tests matching "admin" |
| `python -m pytest tests/ --no-cov` | Run without coverage (faster) |
| `python -m pytest tests/ --lf` | Run last failed tests |

---

**Need more help?** Check the full documentation in `TEST_COVERAGE_REPORT.md` and `TASK_11_COMPLETION_SUMMARY.md`
