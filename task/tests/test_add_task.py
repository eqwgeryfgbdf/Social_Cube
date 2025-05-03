import json
import os
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from task.models import Task, TaskDependency, TaskStatus, TaskSourceType
import subprocess
from unittest.mock import patch


class TaskCliTests(TestCase):
    def setUp(self):
        self.tasks_file = "tasks/tasks.json"
        # Create a backup if file exists
        if os.path.exists(self.tasks_file):
            with open(self.tasks_file, "r") as f:
                self.backup_data = json.load(f)
        else:
            self.backup_data = {"tasks": [], "metadata": {}}
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.tasks_file), exist_ok=True)
            with open(self.tasks_file, "w") as f:
                json.dump(self.backup_data, f)

    def tearDown(self):
        # Restore backup data
        with open(self.tasks_file, "w") as f:
            json.dump(self.backup_data, f)

    @patch('task.manager.add_task')
    def test_cli_add_task(self, mock_add_task):
        mock_add_task.return_value = {"id": 1, "title": "Test Task"}
        
        # Test running the CLI command
        result = subprocess.run(
            ["python", "task/manager.py", "add", "--prompt", "Test Task"],
            capture_output=True,
            text=True
        )
        
        # Assert the command was successful
        self.assertIn("Task", result.stdout)
        mock_add_task.assert_called_once()

    @patch('task.manager.add_task')
    def test_cli_add_task_with_dependencies(self, mock_add_task):
        mock_add_task.return_value = {"id": 2, "title": "Test Task with Dependencies"}
        
        # Test running the CLI command with dependencies
        result = subprocess.run(
            [
                "python", "task/manager.py", "add", 
                "--prompt", "Test Task with Dependencies", 
                "--dependencies", "1"
            ],
            capture_output=True,
            text=True
        )
        
        # Assert the command was successful
        self.assertIn("Task", result.stdout)
        mock_add_task.assert_called_once()


class TaskApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create a task for dependency tests
        self.task = Task.objects.create(
            title="Existing Task",
            description="This is a test task",
            created_by=self.user,
            source_type=TaskSourceType.API
        )

    def test_api_add_task(self):
        response = self.client.post(
            reverse('task:api-tasks-list'), 
            {
                "title": "New API Task",
                "description": "Task created via API",
                "priority": "high"
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.count(), 2)
        self.assertEqual(Task.objects.filter(title="New API Task").count(), 1)
        
        task = Task.objects.get(title="New API Task")
        self.assertEqual(task.priority, "high")
        self.assertEqual(task.source_type, TaskSourceType.API)
        self.assertEqual(task.created_by, self.user)

    def test_api_add_task_with_dependencies(self):
        response = self.client.post(
            reverse('task:api-tasks-list'), 
            {
                "title": "Dependent Task",
                "description": "Task with dependencies",
                "dependencies": [self.task.id]
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.count(), 2)
        
        new_task = Task.objects.get(title="Dependent Task")
        self.assertEqual(new_task.dependencies.count(), 1)
        self.assertEqual(new_task.dependencies.first().depends_on, self.task)
    
    def test_api_batch_add_tasks(self):
        response = self.client.post(
            reverse('task:api-tasks-create-batch'), 
            [
                {
                    "title": "Batch Task 1",
                    "description": "First batch task"
                },
                {
                    "title": "Batch Task 2",
                    "description": "Second batch task",
                    "dependencies": [self.task.id]
                }
            ],
            format='json'
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.count(), 3)
        self.assertEqual(Task.objects.filter(title__startswith="Batch Task").count(), 2)


class TaskWebUITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Create a task for dependency tests
        self.task = Task.objects.create(
            title="Existing Task",
            description="This is a test task",
            created_by=self.user,
            source_type=TaskSourceType.WEB
        )

    def test_web_ui_add_task(self):
        response = self.client.post(
            reverse('task:create'), 
            {
                "title": "New Web Task",
                "description": "Task created via web",
                "status": TaskStatus.PENDING,
                "priority": "high",
                "save_action": "save"
            }
        )
        
        self.assertEqual(response.status_code, 302)  # Redirects on success
        self.assertEqual(Task.objects.count(), 2)
        self.assertEqual(Task.objects.filter(title="New Web Task").count(), 1)
        
        task = Task.objects.get(title="New Web Task")
        self.assertEqual(task.priority, "high")
        self.assertEqual(task.source_type, TaskSourceType.WEB)
        self.assertEqual(task.created_by, self.user)

    def test_web_ui_add_task_with_dependencies(self):
        response = self.client.post(
            reverse('task:create'), 
            {
                "title": "Dependent Web Task",
                "description": "Task with dependencies",
                "status": TaskStatus.PENDING,
                "priority": "medium",
                "dependencies": [str(self.task.id)],
                "save_action": "save"
            }
        )
        
        self.assertEqual(response.status_code, 302)  # Redirects on success
        self.assertEqual(Task.objects.count(), 2)
        
        new_task = Task.objects.get(title="Dependent Web Task")
        self.assertEqual(new_task.dependencies.count(), 1)
        self.assertEqual(new_task.dependencies.first().depends_on, self.task)