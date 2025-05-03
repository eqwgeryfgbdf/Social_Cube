from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Task, TaskDependency, TaskTag, TaskTagAssignment


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model (simplified)."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class TaskTagSerializer(serializers.ModelSerializer):
    """Serializer for the TaskTag model."""
    
    class Meta:
        model = TaskTag
        fields = ['id', 'name', 'color']


class TaskDependencySerializer(serializers.ModelSerializer):
    """Serializer for the TaskDependency model."""
    
    class Meta:
        model = TaskDependency
        fields = ['id', 'depends_on']


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for retrieving tasks."""
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    tags = TaskTagSerializer(source='tags.all', many=True, read_only=True)
    dependencies = serializers.SerializerMethodField()
    dependent_tasks = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'details', 'test_strategy',
            'status', 'priority', 'source_type', 
            'created_by', 'assigned_to',
            'created_at', 'updated_at', 'due_date',
            'tags', 'dependencies', 'dependent_tasks',
            'external_id'
        ]
    
    def get_dependencies(self, obj):
        """Get list of task IDs that this task depends on."""
        return [
            dep.depends_on_id for dep in obj.dependencies.all()
        ]
    
    def get_dependent_tasks(self, obj):
        """Get list of task IDs that depend on this task."""
        return [
            dep.task_id for dep in obj.dependent_tasks.all()
        ]


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new tasks."""
    dependencies = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    tags = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        write_only=True
    )
    assigned_to_id = serializers.IntegerField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, write_only=True)
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'details', 'test_strategy',
            'status', 'priority', 'due_date',
            'dependencies', 'tags', 'assigned_to_id',
            'external_id', 'metadata'
        ]
        extra_kwargs = {
            'title': {'required': True},
            'description': {'required': False},
            'details': {'required': False},
            'test_strategy': {'required': False},
        }
    
    def validate_title(self, value):
        """Validate that the title is not empty or too long."""
        if not value:
            raise serializers.ValidationError("Task title cannot be empty")
        if len(value) > 200:
            raise serializers.ValidationError("Task title cannot exceed 200 characters")
        return value
    
    def validate_dependencies(self, value):
        """Validate that all dependencies exist."""
        if not value:
            return value
        
        invalid_ids = []
        for dep_id in value:
            if not Task.objects.filter(id=dep_id).exists():
                invalid_ids.append(dep_id)
        
        if invalid_ids:
            raise serializers.ValidationError(
                f"The following dependency IDs do not exist: {invalid_ids}"
            )
        
        return value
    
    def validate_assigned_to_id(self, value):
        """Validate that the assigned user exists."""
        if value is not None and not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Assigned user does not exist")
        return value
    
    def create(self, validated_data):
        """Create a new task."""
        # Extract and remove non-model fields
        dependencies = validated_data.pop('dependencies', [])
        tags = validated_data.pop('tags', [])
        assigned_to_id = validated_data.pop('assigned_to_id', None)
        
        # Set assigned_to if provided
        if assigned_to_id:
            validated_data['assigned_to_id'] = assigned_to_id
        
        # Create the task
        task = Task.objects.create(**validated_data)
        
        # Dependencies and tags are handled in the viewset
        
        return task