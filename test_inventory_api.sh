#!/bin/bash
#
# Test Inventory API Endpoints
# Run on Ubuntu server to verify API works
#

echo "=========================================="
echo "Testing Inventory API Endpoints"
echo "=========================================="
echo ""

# Test health check first
echo "1. Testing backend health..."
curl -s http://localhost:8000/api/health || echo "❌ Backend not responding"
echo -e "\n"

# Login to get token
echo "2. Getting auth token..."
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed - check credentials"
  exit 1
fi

echo "✅ Token obtained: ${TOKEN:0:20}..."
echo ""

# Test inventory endpoint
echo "3. Testing top-movers endpoint..."
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/dashboards/inventory/top-movers-and-dead-stock?limit=10")

HTTP_CODE=$(echo "$RESPONSE" | grep HTTP_STATUS | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "Status Code: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ API endpoint working!"
  echo ""
  echo "Sample response:"
  echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
  echo "❌ API returned error $HTTP_CODE"
  echo "$BODY"
fi

echo ""
echo "=========================================="
echo "Test completed"
echo "=========================================="
