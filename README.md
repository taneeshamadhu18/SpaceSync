# SpaceSync

SpaceSync is a Django REST Framework backend application designed for managing architectural workspaces, projects, and spaces. The system supports multi-tenancy, authentication, version-controlled updates, bulk operations, and area calculations.

## Features

### Multi-Tenant Architecture

* Users can own multiple workspaces.
* Workspaces contain projects.
* Projects contain spaces.
* Custom QuerySets and Managers ensure users can only access their own data.

### Authentication

* Token-based authentication using Django REST Framework.
* Protected API endpoints.
* User-specific data access.

### Workspace Management

* Create, retrieve, update, and delete workspaces.
* Track workspace ownership.
* Workspace metadata support.

### Project Management

* Create, retrieve, update, and delete projects.
* Store project information including:

  * Name
  * Client Name
  * Status
  * Circulation Percentage
  * Maximum Buildable Area
  * Description
* Version tracking for optimistic concurrency control.

### Space Management

* Create, retrieve, update, and delete spaces.
* Store:

  * Name
  * Space Type
  * Floor
  * Width
  * Length
  * Description
* Area calculations based on dimensions.

### Optimistic Concurrency Control

* Version-based conflict detection.
* Prevents accidental overwriting of updates.
* Returns HTTP 409 Conflict when version mismatches occur.

### Bulk Operations

Supports atomic bulk operations:

* Bulk Create Spaces
* Bulk Update Spaces
* Bulk Delete Spaces

All bulk operations are executed within database transactions using `transaction.atomic()`.

### Area Aggregation

* Project-level area calculations.
* Database-level aggregation using Django ORM.
* Efficient computation of total project area.

### Search & Filtering

* Search projects and spaces.
* Ordering and filtering support.
* User-specific querysets.

---

## Technology Stack

### Backend

* Python 3.8+
* Django 4.2
* Django REST Framework

### Database

* SQLite (development)

### Authentication

* DRF Token Authentication

### API

* RESTful APIs using ViewSets and Routers

---

## Project Structure

```text
core/
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── migrations/
```

### Core Models

#### Workspace

Represents a tenant or organization.

```text
Workspace
 └── Projects
      └── Spaces
```

#### Project

Stores project-level information.

Fields:

* name
* client_name
* status
* circulation_percent
* max_buildable_area
* version

#### Space

Stores room-level information.

Fields:

* name
* space_type
* floor
* width
* length
* version

---

## Setup Instructions

### Clone Repository

```bash
git clone https://github.com/taneeshamadhu18/SpaceSync.git
cd SpaceSync
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Apply Migrations

```bash
python manage.py migrate
```

### Create Superuser

```bash
python manage.py createsuperuser
```

### Run Server

```bash
python manage.py runserver
```

---

## API Endpoints

### Workspaces

```text
GET    /api/workspaces/
POST   /api/workspaces/
GET    /api/workspaces/{id}/
PUT    /api/workspaces/{id}/
DELETE /api/workspaces/{id}/
```

### Projects

```text
GET    /api/projects/
POST   /api/projects/
GET    /api/projects/{id}/
PUT    /api/projects/{id}/
DELETE /api/projects/{id}/
```

### Spaces

```text
GET    /api/spaces/
POST   /api/spaces/
GET    /api/spaces/{id}/
PUT    /api/spaces/{id}/
DELETE /api/spaces/{id}/
```

### Bulk Operations

```text
POST /api/spaces/bulk_create/
POST /api/spaces/bulk_update/
POST /api/spaces/bulk_delete/
```

### Aggregation

```text
GET /api/projects/{id}/total_area/
GET /api/spaces/total_area/
```

---

## Key Concepts Demonstrated

* Django ORM
* Django REST Framework
* Authentication & Authorization
* Multi-Tenant Design
* Custom Managers & QuerySets
* REST API Design
* Transactions
* Bulk Operations
* Optimistic Locking
* Database Aggregation
* Validation & Serialization

---

## Author

**Taneesha M**

Built as a backend engineering assignment demonstrating scalable API design, multi-tenant architecture, transactional operations, and version-controlled resource management.
