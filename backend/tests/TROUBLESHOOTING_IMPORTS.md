# Troubleshooting Import Errors

## Problem: "ModuleNotFoundError: No module named 'app'"

This error occurs when Python cannot find the `app` module during test execution.

### Error Message
```
ImportError while loading conftest '/path/to/backend/tests/conftest.py'.
tests/conftest.py:18: in <module>
    from app.main import app
E   ModuleNotFoundError: No module named 'app'
```

## Solutions

### Solution 1: Install Backend Package (Recommended)

Install the backend package in development mode:

```bash
cd backend
pip install -e .
```

This makes the `app` module discoverable by Python and pytest.

**Pros:**
- Permanent solution
- Works with all test runners
- Standard Python practice

**Cons:**
- Requires setup.py file (already created)

### Solution 2: Set PYTHONPATH Environment Variable

Set the PYTHONPATH to include the backend directory:

```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
./tests/run_e2e_tests.sh
```

Or for a single command:

```bash
cd backend
PYTHONPATH=. pytest tests/e2e/ -v
```

**Pros:**
- No installation needed
- Quick fix

**Cons:**
- Must be set each time
- May not work in all environments

### Solution 3: Use pytest.ini Configuration

The `pytest.ini` file has been updated to include:

```ini
[pytest]
pythonpath = .
```

This should automatically set the Python path when running pytest from the backend directory.

**Pros:**
- Automatic
- No manual setup needed

**Cons:**
- Only works with pytest
- Must run from backend directory

## Verification

After applying a solution, verify it works:

```bash
cd backend
python -c "from app.main import app; print('Import successful!')"
```

If this prints "Import successful!", the imports are working.

## Running Tests After Fix

### Using Test Runner Script

```bash
cd backend
./tests/run_e2e_tests.sh --e2e-only
```

### Using pytest Directly

```bash
cd backend
pytest tests/e2e/ -v
```

### Using pytest with Explicit Path

```bash
cd backend
PYTHONPATH=. pytest tests/e2e/ -v
```

## Common Issues

### Issue 1: Virtual Environment Not Activated

**Symptom**: Tests can't find dependencies

**Solution**:
```bash
source codenova_env/bin/activate  # Linux/Mac
# or
codenova_env\Scripts\activate  # Windows
```

### Issue 2: Wrong Directory

**Symptom**: pytest can't find tests

**Solution**: Make sure you're in the backend directory:
```bash
cd backend
pwd  # Should show .../CodeNova/backend
```

### Issue 3: Missing Dependencies

**Symptom**: Import errors for pytest or other packages

**Solution**:
```bash
pip install pytest pytest-asyncio pytest-mock pytest-cov
```

### Issue 4: Cached Python Files

**Symptom**: Changes not taking effect

**Solution**: Clear Python cache:
```bash
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## Testing the Fix

Run this simple test to verify everything works:

```bash
cd backend
python -c "
import sys
sys.path.insert(0, '.')
from app.main import app
from app.core.database import Base
print('✓ All imports working!')
"
```

## Still Having Issues?

If you're still experiencing import errors:

1. **Check Python version**: Ensure you're using Python 3.9+
   ```bash
   python --version
   ```

2. **Check directory structure**: Verify app directory exists
   ```bash
   ls -la app/
   ```

3. **Check for __init__.py files**: Ensure app is a package
   ```bash
   ls app/__init__.py
   ```

4. **Try absolute imports**: Modify conftest.py to use absolute imports
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent))
   ```

5. **Check for circular imports**: Look for circular dependencies

## Recommended Approach

For the best experience, use **Solution 1** (Install Backend Package):

```bash
cd backend
pip install -e .
./tests/run_e2e_tests.sh
```

This is the standard Python practice and will work reliably across all scenarios.

## Quick Reference

```bash
# Fix 1: Install package (recommended)
cd backend
pip install -e .

# Fix 2: Set PYTHONPATH
cd backend
export PYTHONPATH=.

# Fix 3: Run with PYTHONPATH inline
cd backend
PYTHONPATH=. pytest tests/e2e/ -v

# Verify fix
cd backend
python -c "from app.main import app; print('OK')"

# Run tests
cd backend
./tests/run_e2e_tests.sh --e2e-only
```
