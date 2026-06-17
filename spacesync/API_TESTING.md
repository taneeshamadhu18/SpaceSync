# Project CRUD API Testing Guide

## Quick Start

### 1. Setup Test Data
```bash
bash setup_test_data.sh
```

This creates:
- Admin user: `admin` / `admin`
- Test user: `testuser` / `testpass123`
- Sample workspace and 3 projects

### 2. Get API Token
Replace credentials with test user credentials:

**Using curl:**
```bash
curl -X POST http://localhost:8000/api-token-auth/ \
  -H 'Content-Type: application/json' \
  -d '{"username": "testuser", "password": "testpass123"}'
```

**Response:**
```json
{
  "token": "b8c8e8f8f9c0d0e0f0g0h0i0j0k0l0m0n0o0p0"
}
```

Save the token for use in API calls.

---

## API Endpoints

### Authentication Header
For all requests, include:
```
Authorization: Token YOUR_TOKEN_HERE
```

### Base URL
```
http://localhost:8000/api/
```

---

## Project Endpoints

### 1. **CREATE Project** - POST /projects/
Create a new project in your workspace.

**Request:**
```bash
curl -X POST http://localhost:8000/api/projects/ \
  -H 'Authorization: Token YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Backend API",
    "description": "REST API for mobile app"
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "name": "Backend API",
  "description": "REST API for mobile app",
  "workspace": 1,
  "workspace_name": "My First Workspace",
  "spaces_count": 0,
  "created_at": "2026-06-17T07:45:00Z",
  "updated_at": "2026-06-17T07:45:00Z"
}
```

---

### 2. **LIST Projects** - GET /projects/
Get all projects in your workspace.

**Request:**
```bash
curl -X GET http://localhost:8000/api/projects/ \
  -H 'Authorization: Token YOUR_TOKEN'
```

**With Pagination:**
```bash
curl -X GET 'http://localhost:8000/api/projects/?page=1&page_size=10' \
  -H 'Authorization: Token YOUR_TOKEN'
```

**With Ordering:**
```bash
curl -X GET 'http://localhost:8000/api/projects/?ordering=-created_at' \
  -H 'Authorization: Token YOUR_TOKEN'
```

**Response (200 OK):**
```json
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Backend API",
      "description": "REST API for mobile app",
      "workspace": 1,
      "workspace_name": "My First Workspace",
      "spaces_count": 0,
      "created_at": "2026-06-17T07:45:00Z",
      "updated_at": "2026-06-17T07:45:00Z"
    }
  ]
}
```

---

### 3. **SEARCH Projects** - GET /projects/?search=query
Search projects by name or description.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/projects/?search=backend' \
  -H 'Authorization: Token YOUR_TOKEN'
```

**Alternative search endpoint:**
```bash
curl -X GET 'http://localhost:8000/api/projects/search/?q=backend' \
  -H 'Authorization: Token YOUR_TOKEN'
```

**Response:**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "name": "Backend API",
      "description": "REST API for mobile app",
      ...
    }
  ]
}
```

---

### 4. **GET Project Details** - GET /projects/{id}/
Get detailed information about a specific project.

**Request:**
```bash
curl -X GET http://localhost:8000/api/projects/1/ \
  -H 'Authorization: Token YOUR_TOKEN'
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Backend API",
  "description": "REST API for mobile app",
  "workspace": 1,
  "workspace_name": "My First Workspace",
  "spaces_count": 0,
  "spaces": [],
  "created_at": "2026-06-17T07:45:00Z",
  "updated_at": "2026-06-17T07:45:00Z"
}
```

---

### 5. **UPDATE Project** - PUT /projects/{id}/
Update an existing project.

**Request:**
```bash
curl -X PUT http://localhost:8000/api/projects/1/ \
  -H 'Authorization: Token YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Mobile API Backend",
    "description": "Updated description"
  }'
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Mobile API Backend",
  "description": "Updated description",
  ...
}
```

---

### 6. **DELETE Project** - DELETE /projects/{id}/
Delete a project permanently.

**Request:**
```bash
curl -X DELETE http://localhost:8000/api/projects/1/ \
  -H 'Authorization: Token YOUR_TOKEN'
```

**Response:** 204 No Content

---

### 7. **GET Project with Spaces** - GET /projects/{id}/with_spaces/
Get project details including all spaces.

**Request:**
```bash
curl -X GET http://localhost:8000/api/projects/1/with_spaces/ \
  -H 'Authorization: Token YOUR_TOKEN'
```

**Response:**
```json
{
  "id": 1,
  "name": "Backend API",
  "description": "REST API for mobile app",
  "spaces": [
    {
      "id": 1,
      "name": "Authentication",
      "description": "Auth module"
    },
    {
      "id": 2,
      "name": "Data Processing",
      "description": "Processing module"
    }
  ]
}
```

---

## Filtering Examples

### Search in name/description
```bash
curl -X GET 'http://localhost:8000/api/projects/?search=api' \
  -H 'Authorization: Token YOUR_TOKEN'
```

### Sort by created date (newest first)
```bash
curl -X GET 'http://localhost:8000/api/projects/?ordering=-created_at' \
  -H 'Authorization: Token YOUR_TOKEN'
```

### Sort by name (A-Z)
```bash
curl -X GET 'http://localhost:8000/api/projects/?ordering=name' \
  -H 'Authorization: Token YOUR_TOKEN'
```

### Combine filters
```bash
curl -X GET 'http://localhost:8000/api/projects/?search=backend&ordering=-created_at&page=1' \
  -H 'Authorization: Token YOUR_TOKEN'
```

---

## Error Responses

### 401 Unauthorized (Missing/Invalid Token)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 400 Bad Request
```json
{
  "name": ["This field may not be blank."],
  "workspace": ["This field is required."]
}
```

---

## Testing in Postman

1. **Create a new request collection** named "SpaceSync"
2. **Add token variable:**
   - Click on Variables tab
   - Add: `token = YOUR_TOKEN_VALUE`
3. **Create requests using:**
   ```
   Authorization: Bearer {{token}}
   ```

### Postman Collection Example

```json
{
  "info": {
    "name": "SpaceSync API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get Token",
      "request": {
        "method": "POST",
        "url": "http://localhost:8000/api-token-auth/",
        "body": {
          "mode": "raw",
          "raw": "{\"username\": \"testuser\", \"password\": \"testpass123\"}"
        }
      }
    },
    {
      "name": "List Projects",
      "request": {
        "method": "GET",
        "url": "http://localhost:8000/api/projects/",
        "header": {
          "Authorization": "Token {{token}}"
        }
      }
    }
  ]
}
```

---

## Multi-Tenancy Verification

Users can ONLY see their own projects:

```bash
# Login as testuser
curl -X POST http://localhost:8000/api-token-auth/ \
  -d '{"username": "testuser", "password": "testpass123"}'

# User can only see their projects
curl -X GET http://localhost:8000/api/projects/ \
  -H 'Authorization: Token testuser_token'

# If trying to access another user's project (404):
curl -X GET http://localhost:8000/api/projects/999/ \
  -H 'Authorization: Token testuser_token'
# Returns: 404 Not Found
```

---

## Next Steps

1. ✅ Project CRUD working
2. ⏭️ Implement Space CRUD
3. ⏭️ Implement Bulk Space Creation
4. ⏭️ Add permissions and sharing
