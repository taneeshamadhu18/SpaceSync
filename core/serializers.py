from rest_framework import serializers
from .models import Project, Workspace, Space


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model."""
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    spaces_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
        'id',
        'name',
        'client_name',
        'status',
        'circulation_percent',
        'max_buildable_area',
        'description',
        'workspace',
        'workspace_name',
        'spaces_count',
        'version',
        'created_at',
        'updated_at',
    ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'workspace_name', 'workspace', 'version']
    
    def get_spaces_count(self, obj):
        """Return the count of spaces in this project."""
        return obj.spaces.count()


class ProjectDetailSerializer(ProjectSerializer):
    """Extended serializer for detailed project view with nested spaces."""
    from .models import Space
    
    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['spaces']
    
    def to_representation(self, instance):
        """Override to include spaces data."""
        data = super().to_representation(instance)
        # Add spaces if needed in detail view
        spaces = instance.spaces.all().values('id', 'name', 'description', 'created_at')
        data['spaces'] = list(spaces)
        return data


class WorkspaceSerializer(serializers.ModelSerializer):
    """Serializer for Workspace model."""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    projects_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Workspace
        fields = [
        'id',
        'name',
        'slug',
        'description',
        'owner',
        'owner_username',
        'projects_count',
        'created_at',
        'updated_at',
    ]
        read_only_fields = ['id', 'owner', 'owner_username', 'created_at', 'updated_at']
    
    def get_projects_count(self, obj):
        """Return the count of projects in this workspace."""
        return obj.projects.count()


class SpaceSerializer(serializers.ModelSerializer):
    """Serializer for Space model with validation for dimensions."""
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = Space
        fields = [
        'id',
        'name',
        'space_type',
        'floor',
        'description',
        'project',
        'project_name',
        'width',
        'length',
        'version',
        'created_at',
        'updated_at',
    ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'project_name', 'project', 'version']
    
    def validate_width(self, value):
        """Validate that width is >= 0. Will check with length in validate()."""
        if value < 0:
            raise serializers.ValidationError("Width cannot be negative.")
        return value
    
    def validate_length(self, value):
        """Validate that length is >= 0. Will check with width in validate()."""
        if value < 0:
            raise serializers.ValidationError("Length cannot be negative.")
        return value
    
    def validate(self, data):
        """
        Validate dimension constraints:
        - Both must be 0 (no dimensions)
        - Both must be > 0 (has dimensions)
        - Cannot have only one > 0
        """
        width = data.get('width', 0)
        length = data.get('length', 0)
        
        # Check if one is > 0 and the other is not
        if (width > 0 and length <= 0) or (width <= 0 and length > 0):
            raise serializers.ValidationError(
                "Both width and length must be greater than 0, or both should be 0 (no dimensions)."
            )
        
        return data


class SpaceDetailSerializer(SpaceSerializer):
    """Extended serializer for detailed space view."""
    project_details = serializers.SerializerMethodField()
    
    class Meta(SpaceSerializer.Meta):
        fields = SpaceSerializer.Meta.fields + ['project_details']
    
    def get_project_details(self, obj):
        """Include basic project information."""
        return {
            'id': obj.project.id,
            'name': obj.project.name,
            'workspace_id': obj.project.workspace.id,
        }


class BulkSpaceSerializer(serializers.Serializer):
    """Serializer for bulk space creation operations."""
    spaces = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of space objects with name, description, width, length"
    )
    
    def validate_spaces(self, value):
        """Validate each space in the list."""
        if not value:
            raise serializers.ValidationError("Spaces list cannot be empty.")
        
        if len(value) > 100:
            raise serializers.ValidationError("Cannot create more than 100 spaces at once.")
        
        for i, space in enumerate(value):
            # Check required fields
            if 'name' not in space or not space.get('name'):
                raise serializers.ValidationError(
                    f"Space {i}: 'name' is required."
                )
            
            # Validate dimensions if provided
            width = space.get('width', 0)
            length = space.get('length', 0)
            
            try:
                width = float(width)
                length = float(length)
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Space {i}: width and length must be numbers."
                )
            
            if width < 0 or length < 0:
                raise serializers.ValidationError(
                    f"Space {i}: width and length cannot be negative."
                )
            
            if (width > 0 and length == 0) or (width == 0 and length > 0):
                raise serializers.ValidationError(
                    f"Space {i}: both width and length must be provided or both should be 0."
                )
        
        return value


class BulkUpdateSpaceSerializer(serializers.Serializer):
    """Serializer for bulk space update operations."""
    spaces = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of space objects with id and fields to update"
    )
    
    def validate_spaces(self, value):
        """Validate each space update in the list."""
        if not value:
            raise serializers.ValidationError("Spaces list cannot be empty.")
        
        if len(value) > 100:
            raise serializers.ValidationError("Cannot update more than 100 spaces at once.")
        
        for i, space in enumerate(value):
            # id is required for updates
            if 'id' not in space:
                raise serializers.ValidationError(
                    f"Space {i}: 'id' is required for updates."
                )
            
            try:
                int(space['id'])
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Space {i}: 'id' must be an integer."
                )
            
            # Validate dimensions if provided
            if 'width' in space or 'length' in space:
                width = space.get('width')
                length = space.get('length')
                
                if width is not None:
                    try:
                        width = float(width)
                    except (ValueError, TypeError):
                        raise serializers.ValidationError(
                            f"Space {i}: width must be a number."
                        )
                    if width < 0:
                        raise serializers.ValidationError(
                            f"Space {i}: width cannot be negative."
                        )
                
                if length is not None:
                    try:
                        length = float(length)
                    except (ValueError, TypeError):
                        raise serializers.ValidationError(
                            f"Space {i}: length must be a number."
                        )
                    if length < 0:
                        raise serializers.ValidationError(
                            f"Space {i}: length cannot be negative."
                        )
        
        return value


class BulkDeleteSpaceSerializer(serializers.Serializer):
    """Serializer for bulk space deletion operations."""
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of space IDs to delete"
    )
    
    def validate_ids(self, value):
        """Validate the list of IDs."""
        if not value:
            raise serializers.ValidationError("IDs list cannot be empty.")
        
        if len(value) > 100:
            raise serializers.ValidationError("Cannot delete more than 100 spaces at once.")
        
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate IDs are not allowed.")
        
        return value
