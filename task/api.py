from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.contrib.auth.models import User

from .models import Task, TaskDependency, TaskTag, TaskTagAssignment, TaskAuditLog
from .serializers import (
    TaskSerializer, 
    TaskCreateSerializer, 
    TaskDependencySerializer,
    TaskTagSerializer
)


class TaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing tasks.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Return different serializers based on the action."""
        if self.action == 'create' or self.action == 'create_batch':
            return TaskCreateSerializer
        return TaskSerializer
    
    def perform_create(self, serializer):
        """Create a new task and record in audit log."""
        # Extract and process metadata if provided
        metadata = self.request.data.get('metadata', {})
        audit_details = {'source': 'api'}
        
        # Add metadata to audit log if provided
        if metadata:
            audit_details['metadata'] = metadata
        
        task = serializer.save(
            created_by=self.request.user,
            source_type='api'
        )
        
        # Create dependencies if provided
        dependencies = self.request.data.get('dependencies', [])
        self._create_dependencies(task, dependencies)
        
        # Create task tags if provided
        tags = self.request.data.get('tags', [])
        self._create_tag_assignments(task, tags)
        
        # Record in audit log
        TaskAuditLog.objects.create(
            task=task,
            user=self.request.user,
            action='created',
            details=audit_details
        )
    
    def perform_update(self, serializer):
        """Update a task and record in audit log."""
        original_task = self.get_object()
        changes = {}
        
        # Track what fields will change
        for field, value in serializer.validated_data.items():
            original_value = getattr(original_task, field)
            if original_value != value:
                changes[field] = {
                    'from': original_value,
                    'to': value
                }
        
        # Save the task
        task = serializer.save()
        
        # Update dependencies if provided
        if 'dependencies' in self.request.data:
            # Clear existing dependencies
            TaskDependency.objects.filter(task=task).delete()
            # Create new dependencies
            dependencies = self.request.data.get('dependencies', [])
            self._create_dependencies(task, dependencies)
            changes['dependencies'] = {'updated': True}
        
        # Update tags if provided
        if 'tags' in self.request.data:
            # Clear existing tags
            TaskTagAssignment.objects.filter(task=task).delete()
            # Create new tags
            tags = self.request.data.get('tags', [])
            self._create_tag_assignments(task, tags)
            changes['tags'] = {'updated': True}
        
        # Record in audit log if there were changes
        if changes:
            TaskAuditLog.objects.create(
                task=task,
                user=self.request.user,
                action='updated',
                details=changes
            )
    
    @action(detail=False, methods=['post'])
    def create_batch(self, request):
        """Create multiple tasks in a single request."""
        tasks = request.data
        if not isinstance(tasks, list):
            return Response(
                {"error": "Expected a list of tasks"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_tasks = []
        errors = []
        
        with transaction.atomic():
            for i, task_data in enumerate(tasks):
                serializer = self.get_serializer(data=task_data)
                if serializer.is_valid():
                    # Set created_by and source
                    task = serializer.save(
                        created_by=request.user,
                        source_type='api'
                    )
                    
                    # Create dependencies if provided
                    dependencies = task_data.get('dependencies', [])
                    self._create_dependencies(task, dependencies)
                    
                    # Create task tags if provided
                    tags = task_data.get('tags', [])
                    self._create_tag_assignments(task, tags)
                    
                    # Extract and process metadata if provided
                    metadata = task_data.get('metadata', {})
                    audit_details = {'source': 'api', 'batch': True}
                    
                    # Add metadata to audit log if provided
                    if metadata:
                        audit_details['metadata'] = metadata
                    
                    # Record in audit log
                    TaskAuditLog.objects.create(
                        task=task,
                        user=request.user,
                        action='created',
                        details=audit_details
                    )
                    
                    created_tasks.append(serializer.data)
                else:
                    errors.append({
                        'index': i,
                        'errors': serializer.errors
                    })
        
        if errors:
            return Response({
                'created_tasks': created_tasks,
                'errors': errors
            }, status=status.HTTP_207_MULTI_STATUS)
        
        return Response(created_tasks, status=status.HTTP_201_CREATED)
    
    def _create_dependencies(self, task, dependencies):
        """Create dependencies for a task."""
        for dep_id in dependencies:
            try:
                depends_on = Task.objects.get(id=dep_id)
                TaskDependency.objects.get_or_create(
                    task=task,
                    depends_on=depends_on
                )
            except Task.DoesNotExist:
                # Skip invalid dependencies
                continue
    
    def _create_tag_assignments(self, task, tags):
        """Create tag assignments for a task."""
        for tag_data in tags:
            try:
                if isinstance(tag_data, int):
                    # If tag_data is just an ID
                    tag = TaskTag.objects.get(id=tag_data)
                elif isinstance(tag_data, str):
                    # If tag_data is a name string
                    tag, _ = TaskTag.objects.get_or_create(name=tag_data)
                elif isinstance(tag_data, dict) and 'name' in tag_data:
                    # If tag_data is a dictionary with at least a name
                    tag, _ = TaskTag.objects.get_or_create(
                        name=tag_data['name'],
                        defaults={'color': tag_data.get('color', '#1a73e8')}
                    )
                else:
                    continue
                
                TaskTagAssignment.objects.get_or_create(
                    task=task,
                    tag=tag
                )
            except Exception:
                # Skip invalid tags
                continue