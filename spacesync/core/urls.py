from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, WorkspaceViewSet, SpaceViewSet

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')
router.register(r'spaces', SpaceViewSet, basename='space')

app_name = 'core'

urlpatterns = [
    path('', include(router.urls)),
]
