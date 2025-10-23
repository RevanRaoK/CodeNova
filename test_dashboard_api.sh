#!/bin/bash

# Test script to verify dashboard API endpoints
# Usage: ./test_dashboard_api.sh <auth_token>

if [ -z "$1" ]; then
    echo "Usage: $0 <auth_token>"
    echo "Example: $0 eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    exit 1
fi

TOKEN="$1"
BASE_URL="http://localhost:8000/api/v1"

echo "Testing Dashboard API Endpoints"
echo "================================"
echo ""

echo "1. Testing /analytics/user-stats"
echo "---------------------------------"
curl -s -X GET "${BASE_URL}/analytics/user-stats" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq '.'
echo ""
echo ""

echo "2. Testing /analytics/usage-trends?timeframe=30d"
echo "------------------------------------------------"
curl -s -X GET "${BASE_URL}/analytics/usage-trends?timeframe=30d" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq '.'
echo ""
echo ""

echo "3. Testing /analytics/feedback-distribution?timeframe=30d"
echo "---------------------------------------------------------"
curl -s -X GET "${BASE_URL}/analytics/feedback-distribution?timeframe=30d" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq '.'
echo ""
echo ""

echo "4. Testing /feedback/statistics?timeframe=month"
echo "-----------------------------------------------"
curl -s -X GET "${BASE_URL}/feedback/statistics?timeframe=month" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq '.'
echo ""
echo ""

echo "Test complete!"
