# Authentication Troubleshooting Guide

## Issues Fixed

### 1. ✅ Endpoint Mismatch Fixed
**Problem**: Frontend was calling `/auth/refresh` but backend endpoint is `/auth/refresh-token`
**Solution**: Updated frontend services to use correct endpoint

### 2. ✅ Docker Compose Updated
**Problem**: Backend build was included in docker-compose.yml
**Solution**: Commented out backend service in docker-compose.yml

## Current Issues & Solutions

### 3. 🔧 Missing Test User (401 Login Error)

The 401 error on login suggests there's no user in the database to authenticate against.

**Solution**: Create a test user using the provided script.

#### Step 1: Run the Database Setup
```bash
cd backend
python create_tables.py
```

#### Step 2: Create Test User
```bash
cd backend
python setup_test_user.py
```

This will create a test user with:
- **Email**: `test@example.com`
- **Password**: `TestPass123!`

#### Step 3: Test the Login
You can now use these credentials in your frontend application.

### 4. 🔧 Backend API Endpoints

Make sure your backend is running on `http://localhost:8000` and the following endpoints are available:

- `POST /api/v1/auth/login` - Login endpoint
- `POST /api/v1/auth/register` - Registration endpoint  
- `POST /api/v1/auth/refresh-token` - Token refresh endpoint
- `POST /api/v1/auth/logout` - Logout endpoint

### 5. 🔧 Frontend Configuration

Ensure your frontend is configured to call the correct API base URL. Check:

- `frontend/services/httpClient.js` - Should point to `http://localhost:8000/api/v1`
- All auth endpoints should use `/auth/refresh-token` (not `/auth/refresh`)

## Testing the Fix

### Manual Testing
1. Start your backend server: `cd backend && uvicorn app.main:app --reload`
2. Start your frontend: `cd frontend && npm run dev`
3. Try logging in with: `test@example.com` / `TestPass123!`

### Automated Testing
Run the updated tests:
```bash
cd frontend
npm run test
```

## Common Issues

### Database Connection
If you get database connection errors:
1. Make sure PostgreSQL is running (via Docker Compose)
2. Check the DATABASE_URL in your environment variables
3. Run the table creation script: `python create_tables.py`

### CORS Issues
If you get CORS errors:
1. Check that your backend CORS settings allow your frontend origin
2. Ensure the frontend is making requests to the correct backend URL

### Token Issues
If tokens aren't working:
1. Check that the SECRET_KEY is set in your backend environment
2. Verify that tokens are being stored correctly in localStorage
3. Check the browser's Network tab for failed requests

## Environment Variables

Make sure these are set in your backend:
```bash
DATABASE_URL=postgresql://postgres:codenova_secure_password@localhost:5432/codenova_db
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars
ENVIRONMENT=development
```

## Next Steps

1. ✅ Run `python setup_test_user.py` to create test user
2. ✅ Test login with `test@example.com` / `TestPass123!`
3. ✅ Verify all authentication flows work
4. ✅ Run frontend tests to ensure they pass

If you continue to have issues, check the backend logs for detailed error messages.