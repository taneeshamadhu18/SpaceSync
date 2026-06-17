"""
Multi-tenancy helpers for workspace isolation.

This module ensures that all queries are properly scoped to the user's workspace(s).
"""

from django.core.exceptions import PermissionDenied
from .models import Workspace


def get_workspace(request):
    """
    Get the workspace for the current request.
    
    For now, assumes a user can be associated with one workspace.
    In the future, this could support:
    - Header-based workspace selection
    - Query parameter workspace selection
    - User profile with default workspace
    
    Args:
        request: Django HTTP request object
    
    Returns:
        Workspace object
    
    Raises:
        PermissionDenied: If user is anonymous or has no workspace
    """
    if not request.user.is_authenticated:
        raise PermissionDenied("User must be authenticated")
    
    # Try to get workspace from user's workspaces
    workspaces = request.user.workspaces.all()
    
    if not workspaces.exists():
        raise PermissionDenied("User has no associated workspace")
    
    # Return the first workspace (can be extended for multi-workspace support)
    return workspaces.first()


def ensure_workspace_access(request, workspace):
    """
    Ensure the user has access to the given workspace.
    
    Args:
        request: Django HTTP request object
        workspace: Workspace object to check access
    
    Raises:
        PermissionDenied: If user doesn't own/have access to this workspace
    """
    if not request.user.is_authenticated:
        raise PermissionDenied("User must be authenticated")
    
    if workspace not in request.user.workspaces.all():
        raise PermissionDenied("User does not have access to this workspace")


def ensure_project_access(request, project):
    """
    Ensure the user has access to the project's workspace.
    
    Args:
        request: Django HTTP request object
        project: Project object to check access
    
    Raises:
        PermissionDenied: If user doesn't have access to this project's workspace
    """
    ensure_workspace_access(request, project.workspace)


def ensure_space_access(request, space):
    """
    Ensure the user has access to the space's project's workspace.
    
    Args:
        request: Django HTTP request object
        space: Space object to check access
    
    Raises:
        PermissionDenied: If user doesn't have access to this space's workspace
    """
    ensure_project_access(request, space.project)
