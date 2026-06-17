from django.db import models
from django.contrib.auth.models import User


# Custom Querysets and Managers for Multi-Tenancy


class WorkspaceQuerySet(models.QuerySet):
    """QuerySet for Workspace model."""
    def for_user(self, user):
        """Filter workspaces owned by the user."""
        if not user.is_authenticated:
            return self.none()
        return self.filter(owner=user)


class WorkspaceManager(models.Manager):
    """Manager for Workspace model."""
    def get_queryset(self):
        return WorkspaceQuerySet(self.model, using=self._db)
    
    def for_user(self, user):
        """Filter workspaces owned by the user."""
        return self.get_queryset().for_user(user)


class ProjectQuerySet(models.QuerySet):
    """QuerySet for Project model with workspace filtering."""
    def for_workspace(self, workspace):
        """Filter projects by workspace."""
        return self.filter(workspace=workspace)
    
    def for_user(self, user):
        """Filter projects accessible to the user."""
        if not user.is_authenticated:
            return self.none()
        return self.filter(workspace__owner=user)


class ProjectManager(models.Manager):
    """Manager for Project model with workspace filtering."""
    def get_queryset(self):
        return ProjectQuerySet(self.model, using=self._db)
    
    def for_workspace(self, workspace):
        """Filter projects by workspace."""
        return self.get_queryset().for_workspace(workspace)
    
    def for_user(self, user):
        """Filter projects accessible to the user."""
        return self.get_queryset().for_user(user)


class SpaceQuerySet(models.QuerySet):
    """QuerySet for Space model with workspace filtering."""
    def for_workspace(self, workspace):
        """Filter spaces by workspace."""
        return self.filter(project__workspace=workspace)
    
    def for_project(self, project):
        """Filter spaces by project."""
        return self.filter(project=project)
    
    def for_user(self, user):
        """Filter spaces accessible to the user."""
        if not user.is_authenticated:
            return self.none()
        return self.filter(project__workspace__owner=user)


class SpaceManager(models.Manager):
    """Manager for Space model with workspace filtering."""
    def get_queryset(self):
        return SpaceQuerySet(self.model, using=self._db)
    
    def for_workspace(self, workspace):
        """Filter spaces by workspace."""
        return self.get_queryset().for_workspace(workspace)
    
    def for_project(self, project):
        """Filter spaces by project."""
        return self.get_queryset().for_project(project)
    
    def for_user(self, user):
        """Filter spaces accessible to the user."""
        return self.get_queryset().for_user(user)


class Workspace(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(blank=True, default="")
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='workspaces'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = WorkspaceManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class Project(models.Model):
    """A project belongs to a workspace and contains spaces."""

    STATUS_CHOICES = [
        ('concept', 'Concept'),
        ('in_design', 'In Design'),
        ('review', 'Review'),
        ('completed', 'Completed'),
    ]

    name = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='concept'
    )

    circulation_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    max_buildable_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    description = models.TextField(blank=True)

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='projects'
    )

    version = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProjectManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class Space(models.Model):
    """A space belongs to a project and has physical dimensions."""

    SPACE_TYPES = [
        ('bedroom', 'Bedroom'),
        ('bathroom', 'Bathroom'),
        ('kitchen', 'Kitchen'),
        ('living', 'Living'),
        ('office', 'Office'),
        ('circulation', 'Circulation'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=255)

    space_type = models.CharField(
        max_length=20,
        choices=SPACE_TYPES,
        default='other'
    )

    floor = models.IntegerField(default=0)

    description = models.TextField(blank=True)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='spaces'
    )

    width = models.DecimalField(max_digits=10, decimal_places=2)
    length = models.DecimalField(max_digits=10, decimal_places=2)

    version = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SpaceManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']