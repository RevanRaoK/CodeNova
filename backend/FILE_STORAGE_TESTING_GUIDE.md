# File Storage Testing Guide

This guide shows you how to test the file storage functionality at different levels, from unit tests to full integration with Digital Ocean Spaces.

## 🧪 Testing Levels

### 1. Unit Tests (No External Dependencies)

These tests mock the S3 client and test the core logic:

```bash
# Run basic functionality tests
python test_file_storage_simple.py
```

**What it tests:**

- Service initialization
- Filename sanitization
- File key generation
- File hash calculation
- File validation logic
- Mock upload workflow

### 2. Integration Tests (Requires Database)

These tests use a real database but mock S3:

```bash
# Install pytest if not already installed
pip install pytest pytest-asyncio

# Run integration tests
pytest test_file_storage_integration.py -v
```

**What it tests:**

- Database operations
- User authentication
- Complete service workflows
- Error handling scenarios

### 3. API Tests (Requires Running Server)

These tests hit the actual API endpoints:

```bash
# First, start the FastAPI server
uvicorn app.main:app --reload

# In another terminal, run API tests
python test_file_storage_api.py
```

**What it tests:**

- HTTP endpoints
- Authentication flow
- File upload/download via API
- Error responses
- Complete user workflows

### 4. Manual Testing with Postman/curl

Test individual endpoints manually:

```bash
# 1. Login to get token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your@email.com&password=yourpassword"

# 2. Upload a file
curl -X POST "http://localhost:8000/api/v1/storage/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.py" \
  -F "metadata={\"description\": \"test file\"}"

# 3. List files
curl -X GET "http://localhost:8000/api/v1/storage/list" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. Download file
curl -X GET "http://localhost:8000/api/v1/storage/download/FILE_ID" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output downloaded_file.py
```

## 🔧 Testing with Real Digital Ocean Spaces

### Prerequisites

1. **Create Digital Ocean Spaces bucket**
2. **Generate API keys**
3. **Update environment variables**

### Setup Steps

1. **Configure environment variables in `.env`:**

```env
DO_SPACES_KEY=your_actual_spaces_key
DO_SPACES_SECRET=your_actual_spaces_secret
DO_SPACES_BUCKET=your_actual_bucket_name
DO_SPACES_REGION=nyc3
DO_SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
```

2. **Test connection:**

```bash
python -c "
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client(
    's3',
    endpoint_url=os.getenv('DO_SPACES_ENDPOINT'),
    aws_access_key_id=os.getenv('DO_SPACES_KEY'),
    aws_secret_access_key=os.getenv('DO_SPACES_SECRET')
)

try:
    response = client.list_objects_v2(Bucket=os.getenv('DO_SPACES_BUCKET'))
    print('✅ Connection successful!')
    print(f'Bucket contents: {len(response.get(\"Contents\", []))} objects')
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

3. **Run full integration tests:**

```bash
# This will use real Digital Ocean Spaces
python test_file_storage_api.py
```

## 🚀 Quick Test Commands

### Test Everything (Recommended Order)

```bash
# 1. Basic unit tests (fastest)
python test_file_storage_simple.py

# 2. Start the server
uvicorn app.main:app --reload &

# 3. Wait a moment for server to start, then test API
sleep 3
python test_file_storage_api.py

# 4. Stop the server
pkill -f uvicorn
```

### Test Specific Functionality

```bash
# Test only service initialization
python -c "
from test_file_storage_simple import test_service_initialization
test_service_initialization()
"

# Test only file validation
python -c "
from test_file_storage_simple import test_file_validation
test_file_validation()
"
```

## 🐛 Troubleshooting

### Common Issues

1. **"Module not found" errors:**

```bash
# Make sure you're in the backend directory
cd backend

# Install dependencies
pip install -r requirements.txt
```

2. **Database connection errors:**

```bash
# Check if PostgreSQL is running
# Update DATABASE_URL in .env if needed
```

3. **Authentication errors in API tests:**

```bash
# Make sure the server is running
# Check if test user can be created/logged in
```

4. **Digital Ocean Spaces connection errors:**

```bash
# Verify your credentials
# Check bucket name and region
# Ensure bucket exists and is accessible
```

### Debug Mode

Run tests with debug output:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run tests with verbose output
python test_file_storage_simple.py
pytest test_file_storage_integration.py -v -s
```

## 📊 Expected Test Results

### Unit Tests (test_file_storage_simple.py)

- ✅ Service initialization
- ✅ Filename sanitization
- ✅ File key generation
- ✅ File hash calculation
- ✅ File validation
- ✅ Mock upload workflow

### API Tests (test_file_storage_api.py)

- ✅ Authentication setup
- ✅ Storage info retrieval
- ✅ File upload
- ✅ File listing
- ✅ File info retrieval
- ✅ Signed URL generation
- ✅ File download
- ✅ File deletion
- ✅ Error handling

## 🎯 Performance Testing

For load testing:

```bash
# Install locust
pip install locust

# Create a simple load test
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between
import tempfile
import os

class FileStorageUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login and get token
        response = self.client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def upload_file(self):
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(b"print('load test file')")
            f.flush()

            with open(f.name, 'rb') as upload_file:
                self.client.post(
                    "/api/v1/storage/upload",
                    headers=self.headers,
                    files={"file": upload_file}
                )
            os.unlink(f.name)

    @task(1)
    def list_files(self):
        self.client.get("/api/v1/storage/list", headers=self.headers)
EOF

# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

## 🔍 Monitoring

Monitor file storage operations:

```bash
# Check server logs
tail -f app.log

# Monitor database
psql -d your_db -c "SELECT COUNT(*) FROM stored_files;"

# Check Digital Ocean Spaces usage (if configured)
# Use DO dashboard or API
```

This comprehensive testing approach ensures your file storage system works correctly at all levels!
