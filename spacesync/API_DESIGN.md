# SpaceSync API Design

## Project Endpoints

### 1. POST /projects/
**Purpose:** Create a new project  
**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "workspace": integer
}
```
**Response:** 201 Created
```json
{
  "id": integer,
  "name": "string",
  "description": "string",
  "workspace": integer,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```
**Auth:** Required (Token)

---

### 2. GET /projects/
**Purpose:** List all projects (with filtering/pagination)  
**Query Parameters:**
- `workspace` - Filter by workspace ID
- `page` - Pagination page
- `page_size` - Items per page

**Response:** 200 OK
```json
{
  "count": integer,
  "next": "url",
  "previous": "url",
  "results": [
    {
      "id": integer,
      "name": "string",
      "description": "string",
      "workspace": integer,
      "created_at": "timestamp",
      "updated_at": "timestamp"
    }
  ]
}
```
**Auth:** Required (Token)

---

### 3. GET /projects/{id}
**Purpose:** Get project details  
**Response:** 200 OK
```json
{
  "id": integer,
  "name": "string",
  "description": "string",
  "workspace": integer,
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "spaces": [
    {
      "id": integer,
      "name": "string",
      "description": "string"
    }
  ]
}
```
**Auth:** Required (Token)

---

### 4. PUT /projects/{id}
**Purpose:** Update project  
**Request Body:**
```json
{
  "name": "string",
  "description": "string"
}
```
**Response:** 200 OK (Same as GET /projects/{id})  
**Auth:** Required (Token)

---

### 5. DELETE /projects/{id}
**Purpose:** Delete project  
**Response:** 204 No Content  
**Auth:** Required (Token)

---

## Space Endpoints

### 6. POST /projects/{id}/spaces/bulk/
**Purpose:** Create multiple spaces in a project (bulk operation)  
**Request Body:**
```json
{
  "spaces": [
    {
      "name": "string",
      "description": "string"
    },
    {
      "name": "string",
      "description": "string"
    }
  ]
}
```
**Response:** 201 Created
```json
{
  "created": integer,
  "spaces": [
    {
      "id": integer,
      "name": "string",
      "description": "string",
      "project": integer,
      "created_at": "timestamp"
    }
  ]
}
```
**Auth:** Required (Token)

---

### 7. GET /projects/{id}/areas/
**Purpose:** Get all areas/spaces in a project  
**Query Parameters:**
- `page` - Pagination page
- `page_size` - Items per page

**Response:** 200 OK
```json
{
  "count": integer,
  "next": "url",
  "previous": "url",
  "results": [
    {
      "id": integer,
      "name": "string",
      "description": "string",
      "project": integer,
      "created_at": "timestamp",
      "updated_at": "timestamp"
    }
  ]
}
```
**Auth:** Required (Token)

---

## Authentication
- **Type:** Token Authentication (DRF authtoken)
- **Header:** `Authorization: Token <token>`
- **Obtain Token:** POST /api-token-auth/ (to be implemented)

## Error Responses
- `400 Bad Request` - Invalid data
- `401 Unauthorized` - Missing/invalid token
- `403 Forbidden` - No permission
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Database Relationships
```
User (Django built-in)
  ├── Workspace (owner)
  │   └── Project
  │       └── Space
```
