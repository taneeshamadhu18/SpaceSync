from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, F, Count, DecimalField
from django.db import transaction

from .models import Project, Workspace, Space
from .serializers import (
    ProjectSerializer, ProjectDetailSerializer, WorkspaceSerializer,
    SpaceSerializer, SpaceDetailSerializer, BulkSpaceSerializer,
    BulkUpdateSpaceSerializer, BulkDeleteSpaceSerializer
)
from .helpers import get_workspace, ensure_project_access, ensure_space_access


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Project CRUD operations.
    
    Automatically filters projects to the user's workspace(s).
    
    Filters:
        - ?q=search_term - Search in project name and description
        - ?ordering=-created_at - Order by field (prefix with - for descending)
    
    Examples:
        GET /projects/ - List all projects
        POST /projects/ - Create new project
        GET /projects/1/ - Get project details
        PUT /projects/1/ - Update project
        DELETE /projects/1/ - Delete project
        GET /projects/?q=backend - Search projects
    """
    
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return only projects from the user's workspace(s).
        This is the critical multi-tenancy enforcement point.
        """
        return Project.objects.for_user(self.request.user)
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action."""
        if self.action == 'retrieve':
            return ProjectDetailSerializer
        return ProjectSerializer
    
    def perform_create(self, serializer):
        """
        Create project in the user's workspace.
        Ensures the workspace belongs to the user.
        """
        workspace = get_workspace(self.request)
        serializer.save(workspace=workspace)
    
    def perform_update(self, serializer):
        """
        Update project with access validation.
        """
        project = self.get_object()
        ensure_project_access(self.request, project)
        serializer.save()
    
    def update(self, request, *args, **kwargs):
        """
        Override update to implement optimistic locking (versioning).
        
        Client must send the current version. If it doesn't match DB version,
        return 409 Conflict. Otherwise, update and increment version.
        """
        instance = self.get_object()
        ensure_project_access(request, instance)
        
        # Get client version from request
        client_version = request.data.get('version')
        
        # If client provided a version, check it matches current
        if client_version is not None:
            try:
                client_version = int(client_version)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'version must be an integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Refresh from DB to get latest version
            instance.refresh_from_db()
            
            if client_version != instance.version:
                return Response(
                    {
                        'error': 'Version conflict. Resource has been modified.',
                        'current_version': instance.version,
                        'client_version': client_version,
                        'resource': self.get_serializer(instance).data
                    },
                    status=status.HTTP_409_CONFLICT
                )
        
        # Perform the update
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Increment version before saving
        instance.version += 1
        self.perform_update(serializer)
        
        return Response(serializer.data)
        """
        Delete project with access validation.
        """
        ensure_project_access(self.request, instance)
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Advanced search endpoint.
        Query parameters:
            - q: Search term for name/description
            - status: Project status (future use)
        
        Example:
            GET /projects/search/?q=my_project
        """
        queryset = self.get_queryset()
        search_query = request.query_params.get('q', '')
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def with_spaces(self, request, pk=None):
        """
        Get project with all its spaces.
        
        Example:
            GET /projects/1/with_spaces/
        """
        project = self.get_object()
        ensure_project_access(request, project)
        
        serializer = ProjectDetailSerializer(project)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def total_area(self, request, pk=None):
        """
        Get the total area of all spaces in a project using DB-level aggregation.
        
        Uses Sum(F('width') * F('length')) for performance — no Python loops.
        
        Example:
            GET /projects/1/total_area/
        
        Returns:
        {
            "project_id": 1,
            "project_name": "My Project",
            "total_area": 1250.00,
            "spaces_count": 5
        }
        """
        project = self.get_object()
        ensure_project_access(request, project)
        
        # Database-level aggregation — NOT a Python loop
        aggregation = project.spaces.aggregate(
            total_area=Sum(
                F('width') * F('length'),
                output_field=DecimalField(max_digits=20, decimal_places=2)
            ),
            spaces_count=Count('id')
        )
        
        return Response({
            'project_id': project.id,
            'project_name': project.name,
            'total_area': aggregation['total_area'] or 0,
            'spaces_count': aggregation['spaces_count'],
        })


class WorkspaceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Workspace operations.
    Users can only view/manage their own workspaces.
    """
    
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return only workspaces owned by the user."""
        return Workspace.objects.for_user(self.request.user)
    
    def perform_create(self, serializer):
        """Create workspace with user as owner."""
        serializer.save(owner=self.request.user)


class SpaceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Space CRUD operations.
    
    Automatically filters spaces to the user's workspace(s).
    
    Filters:
        - ?q=search_term - Search in space name and description
        - ?ordering=-created_at - Order by field
        - ?project=project_id - Filter by project
    
    Examples:
        GET /spaces/ - List all spaces
        POST /spaces/ - Create new space
        GET /spaces/1/ - Get space details
        PUT /spaces/1/ - Update space
        DELETE /spaces/1/ - Delete space
    """
    
    serializer_class = SpaceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at', 'width', 'length']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return only spaces from the user's workspace(s).
        Multi-tenancy enforcement at database level.
        """
        return Space.objects.for_user(self.request.user)
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action."""
        if self.action == 'retrieve':
            return SpaceDetailSerializer
        return SpaceSerializer
    
    def perform_create(self, serializer):
        """
        Create space in a project within the user's workspace.
        Requires project_id in the request.
        """
        project_id = self.request.data.get('project')
        if not project_id:
            raise serializers.ValidationError({'project': 'This field is required.'})
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise serializers.ValidationError({'project': 'Project not found.'})
        
        # Validate user has access to this project
        ensure_project_access(self.request, project)
        
        serializer.save(project=project)
    
    def perform_update(self, serializer):
        """Update space with access validation."""
        space = self.get_object()
        ensure_space_access(self.request, space)
        serializer.save()
    
    def update(self, request, *args, **kwargs):
        """
        Override update to implement optimistic locking (versioning).
        
        Client must send the current version. If it doesn't match DB version,
        return 409 Conflict. Otherwise, update and increment version.
        """
        instance = self.get_object()
        ensure_space_access(request, instance)
        
        # Get client version from request
        client_version = request.data.get('version')
        
        # If client provided a version, check it matches current
        if client_version is not None:
            try:
                client_version = int(client_version)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'version must be an integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Refresh from DB to get latest version
            instance.refresh_from_db()
            
            if client_version != instance.version:
                return Response(
                    {
                        'error': 'Version conflict. Resource has been modified.',
                        'current_version': instance.version,
                        'client_version': client_version,
                        'resource': self.get_serializer(instance).data
                    },
                    status=status.HTTP_409_CONFLICT
                )
        
        # Perform the update
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Increment version before saving
        instance.version += 1
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    def perform_destroy(self, instance):
        """Delete space with access validation."""
        ensure_space_access(self.request, instance)
        instance.delete()
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Bulk create multiple spaces in a project.
        
        Uses @transaction.atomic for all-or-nothing semantics:
        if any single space fails validation, the entire batch is rolled back.
        
        Request body:
        {
            "project": 1,
            "spaces": [
                {"name": "Space 1", "description": "...", "width": 10, "length": 20},
                {"name": "Space 2", "description": "...", "width": 15, "length": 25}
            ]
        }
        
        Returns:
        {
            "created": 2,
            "spaces": [...]
        }
        """
        project_id = request.data.get('project')
        if not project_id:
            return Response(
                {'error': 'project field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': f'Project {project_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate user has access to this project
        try:
            ensure_project_access(request, project)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate the spaces list
        bulk_serializer = BulkSpaceSerializer(data=request.data)
        if not bulk_serializer.is_valid():
            return Response(
                bulk_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        spaces_data = bulk_serializer.validated_data['spaces']
        
        # Atomic transaction: validate + create all or nothing
        with transaction.atomic():
            # Phase 1: Validate ALL spaces before creating any
            space_serializers = []
            errors = []
            
            for i, space_data in enumerate(spaces_data):
                space_serializer = SpaceSerializer(
                    data={
                        'name': space_data.get('name'),
                        'description': space_data.get('description', ''),
                        'width': space_data.get('width', 0),
                        'length': space_data.get('length', 0),
                        'project': project.id,
                    }
                )
                
                if space_serializer.is_valid():
                    space_serializers.append(space_serializer)
                else:
                    errors.append({
                        'index': i,
                        'name': space_data.get('name'),
                        'errors': space_serializer.errors
                    })
            
            # If any space failed validation, raise to roll back entire transaction
            if errors:
                raise serializers.ValidationError({
                    'error': 'Bulk creation failed. No spaces were created.',
                    'detail': 'One or more spaces failed validation. The entire operation has been rolled back.',
                    'validation_errors': errors
                })
            
            # Phase 2: Create all spaces
            created_spaces = []
            for space_serializer in space_serializers:
                space = space_serializer.save(project=project)
                created_spaces.append(SpaceSerializer(space).data)
        
        return Response(
            {
                'created': len(created_spaces),
                'spaces': created_spaces,
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['put', 'patch'])
    def bulk_update(self, request):
        """
        Bulk update multiple spaces atomically.
        
        Uses @transaction.atomic: if ANY single space fails validation
        or is not found, the entire batch is rolled back — no partial updates.
        
        Request body:
        {
            "spaces": [
                {"id": 1, "name": "Updated Name", "width": 20},
                {"id": 2, "description": "New desc", "length": 30}
            ]
        }
        
        Returns:
        {
            "updated": 2,
            "spaces": [...]
        }
        """
        # Validate the input structure
        bulk_serializer = BulkUpdateSpaceSerializer(data=request.data)
        if not bulk_serializer.is_valid():
            return Response(
                bulk_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        spaces_data = bulk_serializer.validated_data['spaces']
        
        # Atomic transaction: all updates succeed or none do
        with transaction.atomic():
            updated_spaces = []
            errors = []
            
            for i, space_data in enumerate(spaces_data):
                space_id = space_data.pop('id')
                
                # Look up the space
                try:
                    space = Space.objects.get(id=space_id)
                except Space.DoesNotExist:
                    raise serializers.ValidationError({
                        'error': 'Bulk update failed. No spaces were updated.',
                        'detail': f'Space with id {space_id} not found (item {i}).',
                    })
                
                # Validate user has access to this space
                try:
                    ensure_space_access(request, space)
                except Exception:
                    raise serializers.ValidationError({
                        'error': 'Bulk update failed. No spaces were updated.',
                        'detail': f'Access denied for space {space_id} (item {i}).',
                    })
                
                # Check version if provided (optimistic locking)
                client_version = space_data.pop('version', None)
                if client_version is not None:
                    try:
                        client_version = int(client_version)
                    except (ValueError, TypeError):
                        raise serializers.ValidationError({
                            'error': 'Bulk update failed. No spaces were updated.',
                            'detail': f'Space {space_id} (item {i}): version must be an integer.',
                        })
                    
                    space.refresh_from_db()
                    if client_version != space.version:
                        raise serializers.ValidationError({
                            'error': 'Bulk update failed. No spaces were updated.',
                            'detail': f'Version conflict for space {space_id} (item {i}). '
                                      f'Expected version {client_version}, current is {space.version}.',
                        })
                
                # Build update data — only include fields that were provided
                update_data = {}
                for field in ['name', 'description', 'width', 'length']:
                    if field in space_data:
                        update_data[field] = space_data[field]
                
                if not update_data:
                    raise serializers.ValidationError({
                        'error': 'Bulk update failed. No spaces were updated.',
                        'detail': f'Space {space_id} (item {i}): no updateable fields provided.',
                    })
                
                # Validate with SpaceSerializer (partial update)
                space_serializer = SpaceSerializer(
                    space, data=update_data, partial=True
                )
                
                if not space_serializer.is_valid():
                    raise serializers.ValidationError({
                        'error': 'Bulk update failed. No spaces were updated.',
                        'detail': f'Validation failed for space {space_id} (item {i}).',
                        'validation_errors': space_serializer.errors
                    })
                
                # Increment version and save
                space.version += 1
                space_serializer.save()
                updated_spaces.append(SpaceSerializer(space).data)
        
        return Response(
            {
                'updated': len(updated_spaces),
                'spaces': updated_spaces,
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """
        Bulk delete multiple spaces atomically.
        
        Uses @transaction.atomic: if ANY single space is not found or
        access is denied, the entire batch is rolled back — no partial deletes.
        
        Request body:
        {
            "ids": [1, 2, 3]
        }
        
        Returns:
        {
            "deleted": 3,
            "ids": [1, 2, 3]
        }
        """
        # Validate the input structure
        bulk_serializer = BulkDeleteSpaceSerializer(data=request.data)
        if not bulk_serializer.is_valid():
            return Response(
                bulk_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        space_ids = bulk_serializer.validated_data['ids']
        
        # Atomic transaction: all deletes succeed or none do
        with transaction.atomic():
            deleted_ids = []
            
            for i, space_id in enumerate(space_ids):
                # Look up the space
                try:
                    space = Space.objects.get(id=space_id)
                except Space.DoesNotExist:
                    raise serializers.ValidationError({
                        'error': 'Bulk delete failed. No spaces were deleted.',
                        'detail': f'Space with id {space_id} not found (item {i}).',
                    })
                
                # Validate user has access to this space
                try:
                    ensure_space_access(request, space)
                except Exception:
                    raise serializers.ValidationError({
                        'error': 'Bulk delete failed. No spaces were deleted.',
                        'detail': f'Access denied for space {space_id} (item {i}).',
                    })
                
                space.delete()
                deleted_ids.append(space_id)
        
        return Response(
            {
                'deleted': len(deleted_ids),
                'ids': deleted_ids,
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def by_project(self, request):
        """
        Get spaces for a specific project.
        
        Query parameter:
            - project: Project ID (required)
        
        Example:
            GET /spaces/by_project/?project=1
        """
        project_id = request.query_params.get('project')
        if not project_id:
            return Response(
                {'error': 'project query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': f'Project {project_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate user has access to this project
        try:
            ensure_project_access(request, project)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        
        spaces = Space.objects.for_project(project)
        serializer = self.get_serializer(spaces, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def total_area(self, request):
        """
        Aggregate total area of spaces using DB-level aggregation.
        
        Uses Sum(F('width') * F('length')) for performance — no Python loops.
        
        Query parameters:
            - project (optional): Filter by project ID
        
        Examples:
            GET /spaces/total_area/              - Total area across all user's spaces
            GET /spaces/total_area/?project=1    - Total area for a specific project
        
        Returns:
        {
            "total_area": 2500.00,
            "spaces_count": 10,
            "project_id": 1       // only if project filter was used
        }
        """
        queryset = self.get_queryset()
        
        # Optional project filter
        project_id = request.query_params.get('project')
        project = None
        
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                return Response(
                    {'error': f'Project {project_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            try:
                ensure_project_access(request, project)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            queryset = queryset.filter(project=project)
        
        # Database-level aggregation — NOT a Python loop
        aggregation = queryset.aggregate(
            total_area=Sum(
                F('width') * F('length'),
                output_field=DecimalField(max_digits=20, decimal_places=2)
            ),
            spaces_count=Count('id')
        )
        
        response_data = {
            'total_area': aggregation['total_area'] or 0,
            'spaces_count': aggregation['spaces_count'],
        }
        
        if project:
            response_data['project_id'] = project.id
            response_data['project_name'] = project.name
        
        return Response(response_data)

