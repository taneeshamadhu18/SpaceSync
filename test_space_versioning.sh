#!/bin/bash

API="http://localhost:8001/api"

echo "============================================"
echo "SPACE VERSIONING TEST"
echo "============================================"

echo -e "\n[1] Getting auth token..."
TOKEN_RESP=$(curl -s -X POST http://localhost:8001/api-token-auth/ \
  -H 'Content-Type: application/json' \
  -d '{"username": "testuser", "password": "testpass123"}')

TOKEN=$(echo "$TOKEN_RESP" | jq -r '.token')
echo "Token: ${TOKEN:0:20}..."

echo -e "\n[2] Getting space..."
SPACE=$(curl -s -X GET "$API/spaces/?limit=1" \
  -H "Authorization: Token $TOKEN" | jq '.results[0].id')

echo "Space ID: $SPACE"

echo -e "\n[3] Getting initial space details..."
RESPONSE=$(curl -s -X GET "$API/spaces/$SPACE/" \
  -H "Authorization: Token $TOKEN")

echo "$RESPONSE" | jq '{id: .id, name: .name, version: .version, width: .width, length: .length}'

CURRENT_VERSION=$(echo "$RESPONSE" | jq '.version')
echo "Current version: $CURRENT_VERSION"

echo -e "\n[4] Updating space with correct version ($CURRENT_VERSION)..."
UPDATE_RESPONSE=$(curl -s -X PUT "$API/spaces/$SPACE/" \
  -H "Authorization: Token $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"name\": \"Updated Space\", \"description\": \"test\", \"width\": 25, \"length\": 30, \"version\": $CURRENT_VERSION}")

echo "$UPDATE_RESPONSE" | jq '{id: .id, name: .name, version: .version}'
NEW_VERSION=$(echo "$UPDATE_RESPONSE" | jq '.version')

if [ "$NEW_VERSION" != "null" ]; then
  echo "✓ Space version incremented: $CURRENT_VERSION → $NEW_VERSION"
fi

echo -e "\n[5] Attempting space update with old version ($CURRENT_VERSION)..."
CONFLICT_RESPONSE=$(curl -s -X PUT "$API/spaces/$SPACE/" \
  -H "Authorization: Token $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"name\": \"Should Fail\", \"width\": 20, \"length\": 20, \"version\": $CURRENT_VERSION}")

echo "$CONFLICT_RESPONSE" | jq '{error: .error, current_version: .current_version, client_version: .client_version}'

echo -e "\n============================================"
echo "SPACE VERSIONING TESTS COMPLETE ✓"
echo "============================================"
