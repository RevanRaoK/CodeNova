#!/bin/bash

# Test script for the enhanced API endpoints
# Make sure the backend server is running on localhost:8000

BASE_URL="http://localhost:8000/api/v1"

echo "=== Testing Enhanced API Endpoints ==="
echo

# First, you need to register/login to get an access token
echo "1. Register a test user (or login if already exists)"
echo "POST $BASE_URL/auth/register"

# Register user
curl -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "TestPassword123"
  }' | jq '.'

echo
echo "2. Login to get access token"
echo "POST $BASE_URL/auth/login"

# Login (using OAuth2 form format)
TOKEN_RESPONSE=$(curl -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPassword123")

echo $TOKEN_RESPONSE | jq '.'

# Extract access token
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
    echo "Failed to get access token. Please check your credentials."
    exit 1
fi

echo
echo "Access token obtained: ${ACCESS_TOKEN:0:20}..."
echo

# Test 3: Direct Code Analysis
echo "3. Test Direct Code Analysis"
echo "POST $BASE_URL/analysis/analyze-code"

curl -X POST "$BASE_URL/analysis/analyze-code" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "function add(a, b) {\n  return a + b;\n}\n\nfunction multiply(x, y) {\n  return x * y;\n}",
    "language": "javascript",
    "filename": "math.js"
  }' | jq '.'

echo
echo

# Test 4: File Upload
echo "4. Test File Upload"
echo "POST $BASE_URL/files/upload"

# Create a temporary test file
cat > /tmp/test_code.py << 'EOF'
def calculate_factorial(n):
    if n < 0:
        return None
    elif n == 0:
        return 1
    else:
        result = 1
        for i in range(1, n + 1):
            result *= i
        return result

# Test the function
print(calculate_factorial(5))
EOF

curl -X POST "$BASE_URL/files/upload" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@/tmp/test_code.py" \
  -F "language=python" | jq '.'

echo
echo

# Test 5: Get Supported Extensions
echo "5. Test Get Supported Extensions"
echo "GET $BASE_URL/files/supported-extensions"

curl -X GET "$BASE_URL/files/supported-extensions" | jq '.'

echo
echo

# Test 6: Get Analysis History
echo "6. Test Analysis History"
echo "GET $BASE_URL/analysis/direct/history"

curl -X GET "$BASE_URL/analysis/direct/history?page=1&page_size=10" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

echo
echo

# Test 7: Get Analysis Statistics
echo "7. Test Analysis Statistics"
echo "GET $BASE_URL/analysis/direct/stats"

curl -X GET "$BASE_URL/analysis/direct/stats" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

echo
echo

# Clean up
rm -f /tmp/test_code.py

echo "=== Testing Complete ==="