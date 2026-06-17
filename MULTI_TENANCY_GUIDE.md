# Multi-Tenancy Implementation Guide

## Overview

Multi-tenancy ensures that each user/workspace only sees their own data. This is implemented through:
1. Custom QuerySet managers for filtering
2. Helper functions for access validation
3. Mandatory workspace filtering in all views

## Key Rules

**NEVER use:**
```python
# ❌ WRONG - Exposes data across workspaces
Project.objects.all()
Space.objects.all()
```

**ALWAYS use:**
```python
# ✅ CORRECT - Filters by user's workspace
Project.objects.for_user(request.user)
Space.objects.for_user(request.user)

# ✅ CORRECT - Filters by specific workspace
Project.objects.for_workspace(workspace)
Space.objects.for_project(project)
```

## Available Helper Functions

### In `core/helpers.py`:

#### `get_workspace(request)`
Returns the user's workspace. Raises `PermissionDenied` if user is anonymous or has no workspace.

```python
from core.helpers import get_workspace

def my_view(request):
    workspace = get_workspace(request)  # Safe to use anywhere
    projects = Project.objects.for_workspace(workspace)
```

#### `ensure_workspace_access(request, workspace)`
Validates that the user has access to a workspace. Raises `PermissionDenied` if not.

```python
from core.helpers import ensure_workspace_access

def my_view(request, workspace_id):
    workspace = Workspace.objects.get(id=workspace_id)
    ensure_workspace_access(request, workspace)  # Raises PermissionDenied if no access
```

#### `ensure_project_access(request, project)`
Validates that the user has access to a project's workspace.

```python
from core.helpers import ensure_project_access

def my_view(request, project_id):
    project = Project.objects.get(id=project_id)
    ensure_project_access(request, project)
```

#### `ensure_space_access(request, space)`
Validates that the user has access to a space's project's workspace.

```python
from core.helpers import ensure_space_access

def my_view(request, space_id):
    space = Space.objects.get(id=space_id)
    ensure_space_access(request, space)
```

## Custom Manager Methods

### Workspace Manager
```python
Workspace.objects.for_user(request.user)  # Get user's workspaces
```

### Project Manager
```python
Project.objects.for_user(request.user)           # All projects accessible to user
Project.objects.for_workspace(workspace)         # Projects in a specific workspace
```

### Space Manager
```python
Space.objects.for_user(request.user)             # All spaces accessible to user
Space.objects.for_workspace(workspace)           # Spaces in a workspace
Space.objects.for_project(project)               # Spaces in a project
```

## View Examples

### REST Framework View (Generic)

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.helpers import get_workspace, ensure_workspace_access
from core.models import Project
from core.serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only projects from the user's workspace."""
        return Project.objects.for_user(self.request.user)
    
    def perform_create(self, serializer):
        """Create project in user's workspace."""
        workspace = get_workspace(self.request)
        serializer.save(workspace=workspace)
```

### Function-Based View

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.helpers import ensure_project_access
from core.models import Project


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def project_detail(request, project_id):
    project = Project.objects.get(id=project_id)
    ensure_project_access(request, project)  # Check access before proceeding
    
    if request.method == 'GET':
        return Response({'id': project.id, 'name': project.name})
    # ... handle PUT and DELETE
```

### Bulk Operations

```python
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from core.models import Project, Space
from core.helpers import ensure_project_access


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_create_spaces(request, project_id):
    project = Project.objects.get(id=project_id)
    ensure_project_access(request, project)  # Validate access
    
    spaces_data = request.data.get('spaces', [])
    created_spaces = []
    
    for space_data in spaces_data:
        space = Space.objects.create(
            name=space_data['name'],
            description=space_data.get('description', ''),
            project=project
        )
        created_spaces.append(space)
    
    return Response({
        'created': len(created_spaces),
        'spaces': [{'id': s.id, 'name': s.name} for s in created_spaces]
    }, status=201)
```

## Database Security

All queries are filtered by workspace at the database level. Django QuerySet chaining ensures:
- `.filter()` calls add WHERE clauses
- Multiple filters use AND logic
- Unauthenticated users get `QuerySet.none()` (empty results)

## Testing Multi-Tenancy

```python
def test_user_sees_only_own_projects():
    # Create users and workspaces
    user1 = User.objects.create_user('user1', password='pass')
    user2 = User.objects.create_user('user2', password='pass')
    
    ws1 = Workspace.objects.create(name='Workspace 1', owner=user1)
    ws2 = Workspace.objects.create(name='Workspace 2', owner=user2)
    
    proj1 = Project.objects.create(name='Project 1', workspace=ws1)
    proj2 = Project.objects.create(name='Project 2', workspace=ws2)
    
    # User1 should only see their project
    assert Project.objects.for_user(user1).count() == 1
    assert proj1 in Project.objects.for_user(user1)
    assert proj2 not in Project.objects.for_user(user1)
```

## Migration from Old Code

When converting existing code to use multi-tenancy:

```python
# Before:
projects = Project.objects.all()

# After:
projects = Project.objects.for_user(request.user)
```

## Debugging

To check if a queryset is properly filtered:

```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as ctx:
    projects = Project.objects.for_workspace(workspace)
    projects_list = list(projects)

for query in ctx:
    print(query['sql'])
    # Should show: WHERE "workspace_id" = X
```
