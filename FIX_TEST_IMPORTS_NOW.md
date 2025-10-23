# 🔧 Fix Test Import Error

## The Problem

You're seeing this error:
```
ModuleNotFoundError: No module named 'app'
```

## The Quick Fix (Choose One)

### Option 1: Run the Fix Script (Easiest)

```bash
cd backend
chmod +x fix_test_imports.sh
./fix_test_imports.sh
```

This script will automatically fix the import issue.

### Option 2: Install Backend Package (Recommended)

```bash
cd backend
pip install -e .
```

This installs the backend as a package, making imports work properly.

### Option 3: Set PYTHONPATH (Quick)

```bash
cd backend
export PYTHONPATH=.
./tests/run_e2e_tests.sh --e2e-only
```

This sets the Python path for the current session.

## Verify the Fix

Test that imports work:

```bash
cd backend
python -c "from app.main import app; print('✓ Imports working!')"
```

If you see "✓ Imports working!", you're good to go!

## Run Tests Again

```bash
cd backend
./tests/run_e2e_tests.sh --e2e-only
```

## Why This Happened

Python couldn't find the `app` module because:
1. The backend directory wasn't in Python's search path
2. The backend wasn't installed as a package

The fixes above solve this by either:
- Installing the backend as a package (Option 2)
- Adding the backend directory to Python's path (Option 3)

## Still Having Issues?

See the detailed troubleshooting guide:
```bash
cat backend/tests/TROUBLESHOOTING_IMPORTS.md
```

Or check the quick start guide:
```bash
cat backend/tests/QUICK_START_E2E.md
```

## Summary

**Quickest Fix:**
```bash
cd backend
pip install -e .
./tests/run_e2e_tests.sh --e2e-only
```

That's it! 🎉
