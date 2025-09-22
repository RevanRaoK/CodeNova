# Dependency Update Guide

## 🔄 Updated Dependencies

### Python Backend Dependencies (requirements.txt)

#### Major Updates:
- **FastAPI**: `0.104.1` → `0.115.6` (Latest stable with performance improvements)
- **SQLAlchemy**: `2.0.23` → `2.0.36` (Bug fixes and performance improvements)
- **Uvicorn**: `0.24.0` → `0.32.1` (Better async handling)
- **Google Generative AI**: `0.3.1` → `0.8.3` (Latest API features)
- **Redis**: `5.0.1` → `5.2.1` (Performance improvements)
- **Celery**: `5.3.4` → `5.4.0` (Latest stable)
- **PyJWT**: `2.8.0` → `2.10.1` (Security updates)
- **Pytest**: `7.4.3` → `8.3.4` (Latest testing framework)
- **Black**: `23.11.0` → `24.10.0` (Code formatting improvements)
- **MyPy**: `1.7.0` → `1.13.0` (Better type checking)

#### New Additions:
- **httpx**: `0.28.1` (Modern async HTTP client)
- **pydantic**: `2.10.3` (Data validation)
- **pydantic-settings**: `2.6.1` (Settings management)

### Node.js Frontend Dependencies (package.json)

#### Major Updates:
- **Monaco Editor React**: `4.7.0` → `4.8.0` (Latest editor features)
- **Axios**: `1.12.2` → `1.7.9` (Security and performance fixes)
- **Lucide React**: `0.525.0` → `0.468.0` (Icon library updates)
- **Monaco Editor**: `0.53.0` → `0.56.0` (Editor core improvements)
- **React Router DOM**: `6.22.3` → `7.1.1` (Latest routing features)

## 🚀 Installation Instructions

### Backend (Python)

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create/activate virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install updated dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Verify installation:**
   ```bash
   python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"
   ```

### Frontend (Node.js)

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Clear npm cache (recommended):**
   ```bash
   npm cache clean --force
   ```

3. **Remove existing node_modules and package-lock.json:**
   ```bash
   rm -rf node_modules package-lock.json
   ```

4. **Install updated dependencies:**
   ```bash
   npm install
   ```

5. **Verify installation:**
   ```bash
   npm list --depth=0
   ```

## 🔍 Breaking Changes & Migration Notes

### Backend Changes

#### FastAPI 0.115.x
- Improved async performance
- Better error handling
- Enhanced OpenAPI documentation
- **No breaking changes** for basic usage

#### SQLAlchemy 2.0.36
- Performance improvements in ORM queries
- Better async support
- **No breaking changes** for existing code

#### Pytest 8.x
- New assertion introspection
- Better async test support
- **Potential breaking change**: Some deprecated features removed
- Update test configurations if needed

### Frontend Changes

#### React Router DOM 7.x
- **Breaking changes** in routing API
- New data loading patterns
- Enhanced type safety
- **Migration needed** for complex routing

#### Monaco Editor 0.56.x
- New language features
- Better TypeScript support
- Performance improvements
- **No breaking changes** for basic usage

## 🧪 Testing After Update

### Backend Testing
```bash
cd backend
python -m pytest tests/ -v
python setup_test_user.py  # Test database connectivity
uvicorn app.main:app --reload  # Test server startup
```

### Frontend Testing
```bash
cd frontend
npm run test:all  # Run all tests
npm run dev  # Test development server
npm run build  # Test production build
```

## 🐛 Common Issues & Solutions

### Backend Issues

#### Import Errors
If you get import errors after updating:
```bash
pip install --force-reinstall -r requirements.txt
```

#### Database Connection Issues
Update your database connection string if using new SQLAlchemy features:
```python
# Old format might need updating
DATABASE_URL = "postgresql://user:pass@localhost/db"
# New format (if needed)
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"
```

### Frontend Issues

#### Module Resolution Errors
Clear cache and reinstall:
```bash
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### React Router Issues
If using complex routing, check the [React Router v7 migration guide](https://reactrouter.com/en/main/upgrading/v6).

#### TypeScript Errors
Update TypeScript configurations if needed:
```bash
npx tsc --noEmit  # Check for type errors
```

## 📋 Verification Checklist

- [ ] Backend dependencies installed successfully
- [ ] Frontend dependencies installed successfully
- [ ] Backend server starts without errors
- [ ] Frontend development server starts
- [ ] All tests pass
- [ ] Authentication still works
- [ ] Database connections work
- [ ] API endpoints respond correctly

## 🔄 Rollback Plan

If issues occur, you can rollback to previous versions:

### Backend Rollback
```bash
git checkout HEAD~1 -- backend/requirements.txt
pip install -r backend/requirements.txt
```

### Frontend Rollback
```bash
git checkout HEAD~1 -- frontend/package.json
rm -rf node_modules package-lock.json
npm install
```

## 📚 Additional Resources

- [FastAPI Release Notes](https://fastapi.tiangolo.com/release-notes/)
- [React Router v7 Migration Guide](https://reactrouter.com/en/main/upgrading/v6)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Pytest 8.x Documentation](https://docs.pytest.org/en/stable/)

---

**Note**: Always test in a development environment before applying updates to production!