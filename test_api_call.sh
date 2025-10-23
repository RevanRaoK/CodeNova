#!/bin/bash

# Test different endpoint paths
echo "Testing /api/v1/feedback/statistics"
curl -s "http://localhost:8000/api/v1/feedback/statistics?timeframe=week" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" | python -m json.tool | head -20

echo ""
echo "Testing /api/v1/feedback/feedback/statistics"
curl -s "http://localhost:8000/api/v1/feedback/feedback/statistics?timeframe=week" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" | python -m json.tool | head -20
