#!/bin/bash

echo "Testing platform analytics endpoint..."
echo "URL: http://localhost:8000/api/v1/admin/analytics/platform"
echo ""

# Test without authentication (should fail)
echo "1. Testing without authentication (should return 401):"
curl -X GET "http://localhost:8000/api/v1/admin/analytics/platform" -w "\nStatus: %{http_code}\n\n"

echo "2. Testing dashboard metrics endpoint (should return 401):"
curl -X GET "http://localhost:8000/api/v1/admin/analytics/dashboard-metrics" -w "\nStatus: %{http_code}\n\n"

echo "Done!"