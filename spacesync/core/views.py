from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Project, Workspace, Space
from .serializers import (
    ProjectSerializer, ProjectDetailSerializer, WorkspaceSerializer,
    SpaceSerializer, SpaceDetailSerializer, BulkSpaceSerializer
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
        
        # Create spaces
        spaces_data = bulk_serializer.validated_data['spaces']
        created_spaces = []
        errors = []
        
        for i, space_data in enumerate(spaces_data):
            try:
                # Create individual space with validation
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
                    space = space_serializer.save(project=project)
                    created_spaces.append(space_serializer.data)
                else:
                    errors.append({
                        'index': i,
                        'name': space_data.get('name'),
                        'errors': space_serializer.errors
                    })
            except Exception as e:
                errors.append({
                    'index': i,
                    'name': space_data.get('name'),
                    'error': str(e)
                })
        
        response_data = {
            'created': len(created_spaces),
            'spaces': created_spaces,
        }
        
        if errors:
            response_data['errors'] = errors
        
        status_code = status.HTTP_201_CREATED if created_spaces else status.HTTP_400_BAD_REQUEST
        return Response(response_data, status=status_code)
    
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

