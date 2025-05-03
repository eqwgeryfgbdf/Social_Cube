"""
Signal handlers for the Task app.
"""
import json
from pathlib import Path

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

from .models import Task, TaskDependency, TaskAuditLog

# Constants
TASKS_FILE = Path(getattr(settings, 'TASKS_JSON_PATH', 'tasks/tasks.json'))


def load_tasks():
    """Load tasks from the tasks.json file."""
    if not TASKS_FILE.exists():
        return {"tasks": [], "metadata": {}}
    
    with open(TASKS_FILE, "r") as f:
        return json.load(f)


def save_tasks(tasks_data):
    """Save tasks to the tasks.json file."""
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks_data, f, indent=2)


@receiver(post_save, sender=Task)
def sync_task_to_json(sender, instance, created, **kwargs):
    """Sync task changes to the tasks.json file."""
    # Skip if the task doesn't have an external_id and wasn't created from tasks.json
    if not instance.external_id and instance.source_type not in ['system', 'cli']:
        return
    
    try:
        # Load tasks data
        tasks_data = load_tasks()
        
        if instance.external_id:
            # Update existing task in JSON
            for i, task in enumerate(tasks_data["tasks"]):
                if task["id"] == instance.external_id:
                    # Update task data
                    task["title"] = instance.title
                    task["description"] = instance.description or ""
                    task["status"] = instance.status
                    task["priority"] = instance.priority
                    task["details"] = instance.details or ""
                    task["testStrategy"] = instance.test_strategy or ""
                    
                    # Handle dependencies
                    dependencies = []
                    for dep in instance.dependencies.all():
                        if dep.depends_on.external_id:
                            dependencies.append(dep.depends_on.external_id)
                    
                    task["dependencies"] = dependencies
                    
                    # Save updated tasks data
                    save_tasks(tasks_data)
                    return
        
        # If we reach here and the task wasn't found but has an external_id,
        # log this inconsistency
        if instance.external_id:
            TaskAuditLog.objects.create(
                task=instance,
                action='sync_error',
                details={
                    'error': f'Task with external_id {instance.external_id} not found in tasks.json'
                }
            )
    
    except Exception as e:
        # Log any errors during sync
        TaskAuditLog.objects.create(
            task=instance,
            action='sync_error',
            details={'error': str(e)}
        )


@receiver(post_delete, sender=Task)
def remove_task_from_json(sender, instance, **kwargs):
    """Remove a deleted task from tasks.json."""
    # Skip if the task doesn't have an external_id
    if not instance.external_id:
        return
    
    try:
        # Load tasks data
        tasks_data = load_tasks()
        
        # Find and remove the task
        tasks_data["tasks"] = [
            task for task in tasks_data["tasks"] 
            if task["id"] != instance.external_id
        ]
        
        # Update metadata
        if "totalTasks" in tasks_data["metadata"]:
            tasks_data["metadata"]["totalTasks"] = len(tasks_data["tasks"])
        
        # Save updated tasks data
        save_tasks(tasks_data)
    
    except Exception:
        # Just pass if there's an error - the task is already deleted
        pass