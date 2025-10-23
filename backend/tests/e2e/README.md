# End-to-End Testing Guide

## Overview

This directory contains comprehensive end-to-end tests for the CodeNova platform, covering complete user workflows and admin operations.

## Test Suites

### 1. User Workflows (`test_user_workflows.py`)

Tests complete user journeys including:
- **File Upload and Analysis**: Single and multi-file uploads with background processing
- **Feedback Submission**: Accepting, rejecting, and modifying AI suggestions
- **Monaco Editor Workflow**: Code analysis with filename requirements
- **Complete User Journey**: Registration through analysis and feedback

### 2. Admin Workflows (`test_admin_workflows.py`)

Tests complete admin operations including:
- **Team Management**: Creating teams, adding/removing members
- **User Management**: Role updates, status changes, search/filter
- **Analytics Viewing**: Platform stats, trends, team comparisons
- **Audit Logging**: Tracking sensitive operations

## Running E2E Tests

### Run All E2E Tests

```bash
# From backend directory
pytest tests/e2e/ -v -m e2e

# Or use the test runner script
./tests/run_e2e_tests.sh --e2e-only
```

### Run Specific Test Classes

```bash
# User workflows only
pytest tests/e2e/test_user_workflows.py::TestFileUploadAndAnalysisWorkflow -v

# Admin workflows only
pytest tests/e2e/test_admin_workflows.py::TestAdminTeamManagementWorkflow -v
```

### Run Individual Tests

```bash
# Specific test
pytest tests/e2e/test_user_workflows.py::TestFileUploadAndAnalysisWorkflow::test_single_file_upload_and_analysis -v
```

## Test Requirements

### Prerequisites

1. **Database**: Tests use SQLite test database (configured in conftest.py)
2. **Dependencies**: All backend dependencies installed
3. **Environment**: Test environment variables set

### Setup

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Ensure test database is clean
rm -f test.db
```

## Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.integration` - Integration tests

## Expected Behavior

### File Upload Tests

- **Single File**: Should upload, queue for analysis, and complete within 30 seconds
- **Multi-File Batch**: Should accept all files and process them asynchronously
- **Validation**: Should reject invalid file types and oversized files

### Feedback Tests

- **Accept/Reject**: Should store feedback and update issue status
- **Modify**: Should store modified suggestions for learning

### Admin Tests

- **Team Management**: Should create teams, manage members, and track changes
- **User Management**: Should update roles, status, and team assignments
- **Analytics**: Should aggregate data across users and teams

## Troubleshooting

### Tests Timeout

If tests timeout waiting for analysis completion:
- Check background worker is running
- Increase timeout values in tests
- Check AI service availability

### Database Errors

If you see database errors:
```bash
# Clean test database
rm -f test.db

# Run migrations
python -m alembic upgrade head
```

### Authentication Errors

If authentication fails:
- Check mock user fixtures in conftest.py
- Verify dependency overrides are working
- Check JWT token generation

## Writing New E2E Tests

### Template

```python
@pytest.mark.e2e
class TestNewWorkflow:
    """Test description."""
    
    def test_workflow_step(self, authenticated_client, db_session):
        """Test specific workflow step."""
        # Step 1: Setup
        # Create test data
        
        # Step 2: Execute
        response = authenticated_client.post("/api/endpoint", json=data)
        
        # Step 3: Verify
        assert response.status_code == 200
        
        # Step 4: Check side effects
        # Verify database changes, etc.
```

### Best Practices

1. **Test Complete Workflows**: Test entire user journeys, not just individual endpoints
2. **Use Realistic Data**: Create test data that mimics real usage
3. **Verify Side Effects**: Check database changes, audit logs, notifications
4. **Clean Up**: Ensure tests clean up after themselves
5. **Add Timeouts**: Use reasonable timeouts for async operations
6. **Document Steps**: Comment each step of the workflow

## Performance Considerations

E2E tests can be slow. To optimize:

1. **Use Fixtures**: Share setup between tests
2. **Parallel Execution**: Run tests in parallel with pytest-xdist
3. **Mock External Services**: Mock AI service calls when appropriate
4. **Database Transactions**: Use transaction rollback for cleanup

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run E2E Tests
  run: |
    cd backend
    pytest tests/e2e/ -v -m e2e --junitxml=test-results/e2e-results.xml
```

### Test Reports

Generate HTML reports:
```bash
pytest tests/e2e/ --html=reports/e2e-report.html --self-contained-html
```

## Coverage

Check E2E test coverage:
```bash
pytest tests/e2e/ --cov=app --cov-report=html
```

Target: 80%+ coverage of critical user workflows
