from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TaskStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELED = 'canceled', 'Canceled'


class TaskPriority(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    URGENT = 'urgent', 'Urgent'


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
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
    due_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    
    def __str__(self):
        return self.title
    
    @property
    def is_overdue(self):
        if self.due_date and self.status != TaskStatus.COMPLETED:
            return self.due_date < timezone.now()
        return False


class TaskTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default="#1a73e8")  # Hex color code
    
    def __str__(self):
        return self.name


class TaskTagAssignment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='tag_assignments')
    tag = models.ForeignKey(TaskTag, on_delete=models.CASCADE, related_name='task_assignments')
    
    class Meta:
        unique_together = ('task', 'tag')
    
    def __str__(self):
        return f"{self.task.title} - {self.tag.name}"