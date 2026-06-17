from django.contrib import admin
from .models import Workspace, Project, Space


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    list_filter = ('created_at', 'owner')
    search_fields = ('name', 'description')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'workspace', 'created_at')
    list_filter = ('workspace', 'created_at')
    search_fields = ('name', 'description')


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'created_at')
    list_filter = ('project', 'created_at')
    search_fields = ('name', 'description')
