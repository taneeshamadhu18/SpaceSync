#!/bin/bash
# Test script for Step 9: Bulk Endpoints with transaction.atomic
# Usage: bash test_bulk_operations.sh
# Requires: Django dev server running on localhost:8000

BASE_URL="http://localhost:8000/api"

echo "============================================"
echo "  Step 9: Bulk Operations Test Suite"
echo "  (transaction.atomic rollback behavior)"
echo "============================================"

# Get auth token (adjust credentials as needed)
echo ""
echo "[1] Authenticating..."
TOKEN=$(curl -s -X POST "$BASE_URL/api-token-auth/" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "  WARNING: Could not get token. Using hardcoded auth header."
  AUTH_HEADER="Authorization: Basic YWRtaW46YWRtaW4xMjM="
else
  AUTH_HEADER="Authorization: Token $TOKEN"
  echo "  Got token: ${TOKEN:0:20}..."
fi

echo ""
echo "============================================"
echo "  TEST 1: Bulk Create (happy path)"
echo "============================================"
echo ""
echo "POST /spaces/bulk_create/"
curl -s -X POST "$BASE_URL/spaces/bulk_create/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "project": 1,
    "spaces": [
      {"name": "Bulk Room A", "description": "First bulk space", "width": 10, "length": 20},
      {"name": "Bulk Room B", "description": "Second bulk space", "width": 15, "length": 25},
      {"name": "Bulk Room C", "description": "Third bulk space", "width": 8, "length": 12}
    ]
  }' | python -m json.tool 2>/dev/null
echo ""

echo "============================================"
echo "  TEST 2: Bulk Create (rollback on error)"
echo "  One space has invalid dimensions -> ALL rejected"
echo "============================================"
echo ""
echo "POST /spaces/bulk_create/"
curl -s -X POST "$BASE_URL/spaces/bulk_create/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "project": 1,
    "spaces": [
      {"name": "Good Space", "width": 10, "length": 20},
      {"name": "Bad Space", "width": -5, "length": 20}
    ]
  }' | python -m json.tool 2>/dev/null
echo ""

echo "============================================"
echo "  TEST 3: Bulk Update (happy path)"
echo "============================================"
echo ""
echo "PUT /spaces/bulk_update/"
curl -s -X PUT "$BASE_URL/spaces/bulk_update/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "spaces": [
      {"id": 1, "name": "Updated Space 1", "width": 99},
      {"id": 2, "description": "Bulk updated description"}
    ]
  }' | python -m json.tool 2>/dev/null
echo ""

echo "============================================"
echo "  TEST 4: Bulk Update (rollback on not found)"
echo "  One space ID doesn't exist -> ALL updates rolled back"
echo "============================================"
echo ""
echo "PUT /spaces/bulk_update/"
curl -s -X PUT "$BASE_URL/spaces/bulk_update/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "spaces": [
      {"id": 1, "name": "This would work"},
      {"id": 99999, "name": "This space does not exist"}
    ]
  }' | python -m json.tool 2>/dev/null
echo ""

echo "============================================"
echo "  TEST 5: Bulk Update (version conflict rollback)"
echo "  Wrong version -> ALL updates rolled back"
echo "============================================"
echo ""
echo "PUT /spaces/bulk_update/"
curl -s -X PUT "$BASE_URL/spaces/bulk_update/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "spaces": [
      {"id": 1, "name": "Good update", "version": 1},
      {"id": 2, "name": "Wrong version", "version": 999}
    ]
  }' | python -m json.tool 2>/dev/null
echo ""

echo "============================================"
echo "  TEST 6: Bulk Delete (happy path)"
echo "============================================"
echo ""
echo "POST /spaces/bulk_delete/"
curl -s -X POST "$BASE_URL/spaces/bulk_delete/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "ids": [1, 2]
  }' | python -m json.tool 2>/dev/null
echo ""

echo "============================================"
echo "  TEST 7: Bulk Delete (rollback on not found)"
echo "  One ID doesn't exist -> NO spaces deleted"
echo "============================================"
echo ""
echo "POST /spaces/bulk_delete/"
curl -s -X POST "$BASE_URL/spaces/bulk_delete/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "ids": [3, 99999]
  }' | python -m json.tool 2>/dev/null
echo ""

echo "============================================"
echo "  TEST 8: Bulk Delete (empty list)"
echo "============================================"
echo ""
echo "POST /spaces/bulk_delete/"
curl -s -X POST "$BASE_URL/spaces/bulk_delete/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "ids": []
  }' | python -m json.tool 2>/dev/null
echo ""

echo "============================================"
echo "  All tests complete!"
echo "============================================"
