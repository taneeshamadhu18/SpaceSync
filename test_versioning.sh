#!/bin/bash

API="http://localhost:8001/api"

echo "============================================"
echo "VERSIONING API TEST"
echo "============================================"

echo -e "\n[1] Getting auth token..."
TOKEN_RESP=$(curl -s -X POST http://localhost:8001/api-token-auth/ \
  -H 'Content-Type: application/json' \
  -d '{"username": "testuser", "password": "testpass123"}')

TOKEN=$(echo "$TOKEN_RESP" | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "ERROR: Could not get token"
  echo "Response: $TOKEN_RESP"
  exit 1
fi

echo "Token: ${TOKEN:0:20}..."

echo -e "\n[2] Getting project..."
PROJECT=$(curl -s -X GET "$API/projects/?limit=1" \
  -H "Authorization: Token $TOKEN" | jq '.results[0].id')

if [ "$PROJECT" = "null" ] || [ -z "$PROJECT" ]; then
  PROJECT=1
fi

echo "Project ID: $PROJECT"

echo -e "\n[3] Getting initial project details..."
RESPONSE=$(curl -s -X GET "$API/projects/$PROJECT/" \
  -H "Authorization: Token $TOKEN")

echo "$RESPONSE" | jq '{id: .id, name: .name, version: .version}'

CURRENT_VERSION=$(echo "$RESPONSE" | jq '.version')
echo "Current version: $CURRENT_VERSION"

echo -e "\n[4] Updating with correct version ($CURRENT_VERSION)..."
UPDATE_RESPONSE=$(curl -s -X PUT "$API/projects/$PROJECT/" \
  -H "Authorization: Token $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"name\": \"Updated $(date +%s)\", \"description\": \"test\", \"version\": $CURRENT_VERSION}")

echo "$UPDATE_RESPONSE" | jq '{id: .id, name: .name, version: .version, error: .error}'
NEW_VERSION=$(echo "$UPDATE_RESPONSE" | jq '.version')

if [ "$NEW_VERSION" != "null" ]; then
  echo "✓ Version incremented: $CURRENT_VERSION → $NEW_VERSION"
else
  echo "Response: $UPDATE_RESPONSE"
fi

echo -e "\n[5] Attempting update with old version ($CURRENT_VERSION)..."
CONFLICT_RESPONSE=$(curl -s -X PUT "$API/projects/$PROJECT/" \
  -H "Authorization: Token $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"name\": \"Should Fail\", \"description\": \"test\", \"version\": $CURRENT_VERSION}")

echo "$CONFLICT_RESPONSE" | jq '{error: .error, current_version: .current_version, client_version: .client_version}'

echo -e "\n============================================"
echo "VERSIONING TESTS COMPLETE"
echo "============================================"
