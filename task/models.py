from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TaskStatus(models.TextChoices):
    """Task status choices."""
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress' 
    COMPLETED = 'completed', 'Completed'
    DEFERRED = 'deferred', 'Deferred'
    CANCELED = 'canceled', 'Canceled'


class TaskPriority(models.TextChoices):
    """Task priority choices."""
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    URGENT = 'urgent', 'Urgent'


class TaskSourceType(models.TextChoices):
    """Source type choices for tracking where tasks were created from."""
    CLI = 'cli', 'Command Line'
    API = 'api', 'API'
    WEB = 'web', 'Web Interface'
    SYSTEM = 'system', 'System Generated'


class Task(models.Model):
    """
    Task model representing a single task in the system.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    test_strategy = models.TextField(blank=True, null=True)
    
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING
    )
    
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM
    )
    
    # New fields
    source_type = models.CharField(
        max_length=20,
        choices=TaskSourceType.choices,
        default=TaskSourceType.SYSTEM
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='created_tasks',
        null=True, 
        blank=True
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='assigned_tasks',
        null=True, 
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(blank=True, null=True)
    
    # Task ID from tasks.json for synchronization
    external_id = models.IntegerField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['external_id']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_overdue(self):
        """Check if the task is overdue."""
        if self.due_date and self.status != TaskStatus.COMPLETED:
            return self.due_date < timezone.now()
        return False
    
    @property
    def dependency_count(self):
        """Get the number of dependencies for this task."""
        return self.dependencies.count()


class TaskDependency(models.Model):
    """
    Model representing a dependency relationship between tasks.
    """
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='dependencies'
    )
    depends_on = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='dependent_tasks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('task', 'depends_on')
        verbose_name_plural = 'Task Dependencies'
    
    def __str__(self):
        return f"{self.task.title} depends on {self.depends_on.title}"


class TaskTag(models.Model):
    """
    Model representing a tag that can be applied to tasks.
    """
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default="#1a73e8")  # Hex color code
    
    def __str__(self):
        return self.name


class TaskTagAssignment(models.Model):
    """
    Model representing a tag assignment to a task.
    """
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='tags'
    )
    tag = models.ForeignKey(
        TaskTag, 
        on_delete=models.CASCADE, 
        related_name='tasks'
    )
    
    class Meta:
        unique_together = ('task', 'tag')
    
    def __str__(self):
        return f"{self.task.title} - {self.tag.name}"


class TaskAuditLog(models.Model):
    """
    Model for tracking changes to tasks.
    """
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='audit_logs'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='task_audit_logs',
        null=True, 
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50)  # e.g., 'created', 'updated', 'status_changed'
    details = models.JSONField(default=dict)  # Store details of what changed
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} on {self.task.title} at {self.timestamp}"