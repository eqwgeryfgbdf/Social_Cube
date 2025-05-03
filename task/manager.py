#!/usr/bin/env python
"""
Task Manager CLI - Command-line interface for managing tasks in the task-master system.
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "social_cube.settings")
import django
django.setup()

# Now import Django models
from task.models import Task, TaskDependency, TaskStatus, TaskPriority, TaskAuditLog

# Constants
TASKS_FILE = Path("tasks/tasks.json")


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


def validate_task(title, description, dependencies=None):
    """Validate task input data."""
    errors = []
    
    # Validate title
    if not title:
        errors.append("Task title cannot be empty")
    elif len(title) > 200:
        errors.append("Task title cannot exceed 200 characters")
    
    # Validate dependencies
    if dependencies:
        tasks_data = load_tasks()
        task_ids = [task["id"] for task in tasks_data["tasks"]]
        
        for dep_id in dependencies:
            try:
                dep_id = int(dep_id)
                if dep_id not in task_ids:
                    errors.append(f"Dependency ID {dep_id} does not exist")
            except ValueError:
                errors.append(f"Invalid dependency ID format: {dep_id}")
    
    return errors


def add_task(title, description=None, dependencies=None, priority="medium", status="pending"):
    """Add a new task to the tasks.json file."""
    # Validate task data
    errors = validate_task(title, description, dependencies)
    if errors:
        for error in errors:
            print(f"Error: {error}")
        return None
    
    # Load existing tasks
    tasks_data = load_tasks()
    
    # Generate new task ID
    new_id = 1
    if tasks_data["tasks"]:
        new_id = max(task["id"] for task in tasks_data["tasks"]) + 1
    
    # Create new task
    new_task = {
        "id": new_id,
        "title": title,
        "description": description or "",
        "status": status,
        "dependencies": dependencies or [],
        "priority": priority,
        "details": "",
        "testStrategy": "",
        "subtasks": []
    }
    
    # Add task to task list
    tasks_data["tasks"].append(new_task)
    
    # Update metadata
    if "metadata" not in tasks_data:
        tasks_data["metadata"] = {}
    
    if "totalTasks" in tasks_data["metadata"]:
        tasks_data["metadata"]["totalTasks"] += 1
    else:
        tasks_data["metadata"]["totalTasks"] = len(tasks_data["tasks"])
    
    tasks_data["metadata"]["lastUpdated"] = datetime.now().isoformat()
    
    # Save updated tasks
    save_tasks(tasks_data)
    
    print(f"Task {new_id} created: {title}")
    return new_task


def create_task_in_db(title, description=None, dependencies=None, priority="medium", status="pending", 
                   details=None, test_strategy=None, user_id=None):
    """Create a task in the database."""
    from django.utils import timezone
    
    # Create the task
    task = Task.objects.create(
        title=title,
        description=description or "",
        priority=priority,
        status=status,
        details=details or "",
        test_strategy=test_strategy or "",
        created_by_id=user_id,
        source_type="cli",
        created_at=timezone.now()
    )
    
    # Add dependencies if provided
    if dependencies:
        task_ids = [dep_id for dep_id in dependencies if Task.objects.filter(id=dep_id).exists()]
        for dep_id in task_ids:
            TaskDependency.objects.create(
                task=task,
                depends_on_id=dep_id
            )
    
    # Record in audit log
    TaskAuditLog.objects.create(
        task=task,
        action='created',
        details={'source': 'cli'}
    )
    
    return task


def list_tasks(status=None, priority=None, with_subtasks=False):
    """List tasks, optionally filtered by status and priority."""
    tasks_data = load_tasks()
    tasks = tasks_data["tasks"]
    
    if status:
        tasks = [task for task in tasks if task["status"] == status]
    
    if priority:
        tasks = [task for task in tasks if task["priority"] == priority]
    
    if not tasks:
        print("No tasks found.")
        return
    
    print(f"{'ID':<5} {'Status':<12} {'Priority':<10} {'Dependencies':<15} {'Title':<50}")
    print("-" * 92)
    
    for task in sorted(tasks, key=lambda x: x["id"]):
        title = task["title"]
        if len(title) > 47:
            title = title[:44] + "..."
        
        # Format dependencies
        dependencies = ", ".join(str(dep) for dep in task.get("dependencies", []))
        dependencies = dependencies[:12] + "..." if len(dependencies) > 12 else dependencies
        
        print(f"{task['id']:<5} {task['status']:<12} {task['priority']:<10} {dependencies:<15} {title:<50}")
        
        # Print subtasks if requested
        if with_subtasks and task.get("subtasks"):
            for subtask in task["subtasks"]:
                subtask_title = subtask["title"]
                if len(subtask_title) > 44:
                    subtask_title = subtask_title[:41] + "..."
                    
                subtask_id = f"{task['id']}.{subtask.get('id', '?')}"
                subtask_status = subtask.get("status", "pending")
                print(f"  {subtask_id:<5} {subtask_status:<12} {'':<10} {'':<15} {subtask_title:<50}")


def main():
    """Main entry point for the task manager CLI."""
    parser = argparse.ArgumentParser(description="Task Manager CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Add task command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("--prompt", "--title", required=True,
                         help="Task title/description")
    add_parser.add_argument("--dependencies", help="Comma-separated list of task IDs that this task depends on")
    add_parser.add_argument("--priority", choices=["low", "medium", "high", "urgent"],
                         default="medium", help="Task priority (default: medium)")
    add_parser.add_argument("--status", choices=["pending", "in_progress", "completed", "deferred", "canceled"],
                         default="pending", help="Task status (default: pending)")
    add_parser.add_argument("--details", help="Implementation details for the task")
    add_parser.add_argument("--test-strategy", help="Test strategy for the task")
    add_parser.add_argument("--sync", action="store_true", help="Sync task with database")
    
    # List tasks command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--status", help="Filter tasks by status")
    list_parser.add_argument("--priority", help="Filter tasks by priority")
    list_parser.add_argument("--with-subtasks", action="store_true", help="Include subtasks in the listing")
    
    args = parser.parse_args()
    
    if args.command == "add":
        # Parse dependencies
        dependencies = None
        if args.dependencies:
            dependencies = [int(dep.strip()) for dep in args.dependencies.split(",")]
        
        # Extract title and description from prompt
        title = args.prompt
        description = None
        if "\n" in args.prompt:
            title, description = args.prompt.split("\n", 1)
        
        # Add the task to tasks.json
        task = add_task(title, description, dependencies, args.priority, args.status)
        
        # Sync to database if requested
        if args.sync and task:
            db_task = create_task_in_db(
                title=task["title"],
                description=task["description"],
                dependencies=task["dependencies"],
                priority=task["priority"],
                details=args.details,
                test_strategy=args.test_strategy
            )
            print(f"Task synced to database with ID: {db_task.id}")
    
    elif args.command == "list":
        list_tasks(args.status, args.priority, args.with_subtasks)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()