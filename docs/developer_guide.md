# Developer Guide

This guide provides comprehensive information for developers working on the Social Cube project, including code organization, architecture, and extension points.

## Development Environment Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Docker and Docker Compose (optional for local development)
- PostgreSQL (optional, SQLite is used by default in development)
- Redis (optional, for channels and caching)

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd social_cube
   ```

2. **Create a Conda environment**:
   ```bash
   # Using Conda (recommended)
   conda env create -f environment.yml
   conda activate social_cube
   
   # Alternatively, using venv
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:
   ```bash
   # On Windows
   run_dev.bat
   
   # On macOS/Linux
   ./run_dev.sh
   
   # Or directly
   python manage.py runserver
   ```

### Discord Developer Setup

To work with Discord integration:

1. **Create a Discord application** at https://discord.com/developers/applications
2. **Create a bot** for your application
3. **Enable relevant Privileged Gateway Intents**:
   - Server Members Intent
   - Message Content Intent
4. **Configure OAuth2**:
   - Add redirect URL: `http://localhost:8000/oauth/callback`
   - Set scopes: `identify`, `email`, `guilds`, `bot`
   - Set bot permissions as needed
5. **Add OAuth2 credentials to your `.env` file**:
   ```
   DISCORD_CLIENT_ID=your_client_id
   DISCORD_CLIENT_SECRET=your_client_secret
   DISCORD_REDIRECT_URI=http://localhost:8000/oauth/callback
   ```

## Project Structure

The Social Cube project follows a modular architecture with multiple Django apps:

```
social_cube/
├── config/                 # Project configuration
├── api/                    # REST API endpoints
├── bot_management/         # Discord bot management
├── dashboard/              # Web interface
├── realtime/               # WebSocket/real-time features
├── logging_system/         # Comprehensive logging
├── scripts/                # Utility scripts
├── static/                 # Static files
├── media/                  # User-uploaded files
├── templates/              # Project-wide templates
├── .env.example            # Environment variables example
└── manage.py               # Django management script
```

### Key Components

#### `config/`

The `config` directory contains project-wide settings and configuration:

- `settings_base.py`: Base settings shared by all environments
- `settings_dev.py`: Development-specific settings
- `settings_prod.py`: Production-specific settings
- `settings_test.py`: Test-specific settings
- `urls.py`: Main URL routing
- `wsgi.py` and `asgi.py`: WSGI and ASGI entry points

#### `api/`

The `api` app provides REST API endpoints using Django REST Framework:

- `views.py`: API views and viewsets
- `serializers.py`: JSON serializers for models
- `urls.py`: API URL routing
- `permissions.py`: Custom API permissions

#### `bot_management/`

The `bot_management` app handles Discord bot configuration and operation:

- `models.py`: Bot, Guild, Command models
- `discord_bot/`: Discord bot implementation
  - `service.py`: Bot manager service
  - `client.py`: Bot client implementation
- `views.py`: Web views for bot management
- `admin.py`: Admin interface configuration

#### `dashboard/`

The `dashboard` app provides the web interface:

- `views.py`: Dashboard views
- `templatetags/`: Custom template tags
- `utils/`: Utility functions
- `templates/dashboard/`: Dashboard templates

#### `realtime/`

The `realtime` app handles WebSocket connections:

- `consumers.py`: WebSocket consumers
- `routing.py`: WebSocket URL routing
- `asgi.py`: ASGI configuration

#### `logging_system/`

The `logging_system` app provides comprehensive logging:

- `models.py`: RequestLog, AuditLog, ErrorLog models
- `middleware.py`: Logging middleware
- `utils.py`: Logging utilities

## Core Technologies

### Backend

- **Django**: Web framework
- **Django REST Framework**: API framework
- **Django Channels**: WebSocket support
- **PostgreSQL**: Production database
- **Redis**: Caching and channels backend
- **Celery**: Background task processing

### Frontend

- **HTML/CSS/JavaScript**: Base technologies
- **Tailwind CSS**: CSS framework
- **Alpine.js**: JavaScript framework
- **Chart.js**: Data visualization

### Integration

- **Discord API**: Discord integration
- **OAuth2**: Authentication
- **WebSockets**: Real-time updates

## Architecture Overview

Social Cube follows a modular architecture with clear separation of concerns. See [System Architecture](system_architecture.md) for a detailed overview.

### Key Patterns

- **Singleton Service**: The `BotManager` is implemented as a singleton service
- **Adapter Pattern**: Bot implementation uses adapters for flexibility
- **Repository Pattern**: Data access is abstracted through repositories
- **Factory Pattern**: Factories create complex objects
- **Observer Pattern**: Event handling uses observers

## Development Workflow

### Git Workflow

1. **Feature Branches**: Create a branch for each feature or bugfix
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Commit Conventions**: Use semantic commit messages
   ```bash
   git commit -m "feat: Add Discord OAuth integration"
   git commit -m "fix: Resolve command sync issue"
   git commit -m "docs: Update API documentation"
   ```

3. **Pull Requests**: Create PRs for code review before merging

### Testing

Run tests using:

```bash
# Run all tests
python manage.py test

# Run specific tests
python manage.py test bot_management.tests

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Code Style

Code style is enforced using:

- **Black**: Code formatter
- **Flake8**: Linter
- **isort**: Import sorter

Run code style checks:

```bash
# Format code
black .

# Check imports
isort .

# Lint code
flake8
```

## Extending the Application

### Creating a New App

To create a new Django app:

```bash
python manage.py startapp new_app
```

Then update `INSTALLED_APPS` in `config/settings_base.py`.

### Adding New Models

1. Create model classes in `models.py`:
   ```python
   from django.db import models
   
   class NewModel(models.Model):
       name = models.CharField(max_length=100)
       description = models.TextField(blank=True)
       created_at = models.DateTimeField(auto_now_add=True)
       
       def __str__(self):
           return self.name
   ```

2. Create migrations:
   ```bash
   python manage.py makemigrations
   ```

3. Apply migrations:
   ```bash
   python manage.py migrate
   ```

### Adding API Endpoints

1. Create serializers in `api/serializers.py`:
   ```python
   from rest_framework import serializers
   from new_app.models import NewModel
   
   class NewModelSerializer(serializers.ModelSerializer):
       class Meta:
           model = NewModel
           fields = ['id', 'name', 'description', 'created_at']
   ```

2. Create viewsets in `api/views.py`:
   ```python
   from rest_framework import viewsets
   from new_app.models import NewModel
   from api.serializers import NewModelSerializer
   
   class NewModelViewSet(viewsets.ModelViewSet):
       queryset = NewModel.objects.all()
       serializer_class = NewModelSerializer
   ```

3. Add URL routes in `api/urls.py`:
   ```python
   from django.urls import path, include
   from rest_framework.routers import DefaultRouter
   from api.views import NewModelViewSet
   
   router = DefaultRouter()
   router.register(r'new-models', NewModelViewSet)
   
   urlpatterns = [
       path('', include(router.urls)),
   ]
   ```

### Adding Web Views

1. Create view functions in `new_app/views.py`:
   ```python
   from django.shortcuts import render, get_object_or_404
   from new_app.models import NewModel
   
   def new_model_list(request):
       new_models = NewModel.objects.all()
       return render(request, 'new_app/new_model_list.html', {'new_models': new_models})
   
   def new_model_detail(request, pk):
       new_model = get_object_or_404(NewModel, pk=pk)
       return render(request, 'new_app/new_model_detail.html', {'new_model': new_model})
   ```

2. Create templates in `new_app/templates/new_app/`:
   ```html
   <!-- new_model_list.html -->
   {% extends "base.html" %}
   
   {% block content %}
   <h1>New Models</h1>
   <ul>
       {% for new_model in new_models %}
       <li><a href="{% url 'new_model_detail' new_model.pk %}">{{ new_model.name }}</a></li>
       {% endfor %}
   </ul>
   {% endblock %}
   ```

3. Add URL routes in `new_app/urls.py`:
   ```python
   from django.urls import path
   from new_app import views
   
   urlpatterns = [
       path('new-models/', views.new_model_list, name='new_model_list'),
       path('new-models/<int:pk>/', views.new_model_detail, name='new_model_detail'),
   ]
   ```

4. Include app URLs in main `config/urls.py`:
   ```python
   urlpatterns = [
       # Other paths...
       path('new-app/', include('new_app.urls')),
   ]
   ```

### Adding Admin Interface

Add admin configuration in `new_app/admin.py`:

```python
from django.contrib import admin
from new_app.models import NewModel

@admin.register(NewModel)
class NewModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']
```

### Adding WebSocket Consumers

1. Create WebSocket consumers in `new_app/consumers.py`:
   ```python
   from channels.generic.websocket import JsonWebsocketConsumer
   from asgiref.sync import async_to_sync
   
   class NewModelConsumer(JsonWebsocketConsumer):
       def connect(self):
           self.accept()
           async_to_sync(self.channel_layer.group_add)(
               "new_model_updates",
               self.channel_name
           )
       
       def disconnect(self, close_code):
           async_to_sync(self.channel_layer.group_discard)(
               "new_model_updates",
               self.channel_name
           )
       
       def receive_json(self, content):
           # Handle received message
           pass
       
       def new_model_update(self, event):
           # Send update to WebSocket
           self.send_json(event["content"])
   ```

2. Add WebSocket routing in `new_app/routing.py`:
   ```python
   from django.urls import re_path
   from new_app import consumers
   
   websocket_urlpatterns = [
       re_path(r'ws/new-models/$', consumers.NewModelConsumer.as_asgi()),
   ]
   ```

3. Include WebSocket routing in `realtime/routing.py`:
   ```python
   from channels.routing import ProtocolTypeRouter, URLRouter
   import new_app.routing
   
   websocket_urlpatterns = [
       # Other patterns...
   ] + new_app.routing.websocket_urlpatterns
   ```

### Adding Background Tasks

1. Create tasks in `new_app/tasks.py`:
   ```python
   from celery import shared_task
   from new_app.models import NewModel
   
   @shared_task
   def process_new_model(new_model_id):
       try:
           new_model = NewModel.objects.get(id=new_model_id)
           # Process the model
           new_model.save()
       except NewModel.DoesNotExist:
           pass
   ```

2. Call tasks from views or signals:
   ```python
   from new_app.tasks import process_new_model
   
   def create_new_model(request):
       # Create the model
       new_model = NewModel.objects.create(name="New Model")
       
       # Queue task for processing
       process_new_model.delay(new_model.id)
       
       return redirect('new_model_detail', pk=new_model.pk)
   ```

## Working with Discord Bots

### Bot Manager Service

The `BotManager` service in `bot_management/discord_bot/service.py` manages bot instances.

Example usage:

```python
from bot_management.discord_bot.service import bot_manager

# Start a bot
bot_manager.start_bot(bot_id)

# Stop a bot
bot_manager.stop_bot(bot_id)

# Restart a bot
bot_manager.restart_bot(bot_id)

# Get bot status
status = bot_manager.get_bot_status(bot_id)
```

### Adding Custom Commands

1. Define a command in the database using the admin interface or API

2. Implement command handler in a bot extension:
   ```python
   from bot_management.discord_bot.client import BotClient
   
   class CustomCommands:
       def __init__(self, bot):
           self.bot = bot
           self.bot.add_listener(self.on_ready, "on_ready")
       
       async def on_ready(self):
           print(f"Custom commands ready for {self.bot.user.name}")
       
       async def handle_custom_command(self, ctx, **options):
           """Handle a custom slash command."""
           await ctx.respond(f"Command executed with options: {options}")
   
   def setup(bot):
       bot.add_cog(CustomCommands(bot))
   ```

3. Register the extension in `bot_management/discord_bot/client.py`

## Database Schema

See [Database Schema](database_schema.md) for a detailed description of the database schema.

## API Reference

See [API Reference](api_reference.md) for documentation of the REST API endpoints.

## Logging and Monitoring

### Application Logging

Use Python's logging module for application logging:

```python
import logging

logger = logging.getLogger(__name__)

def some_function():
    try:
        # Do something
        logger.info("Operation completed successfully")
    except Exception as e:
        logger.error(f"Error in operation: {str(e)}", exc_info=True)
```

### Database Logging

Use the logging models for database logging:

```python
from logging_system.models import AuditLog, ErrorLog

# Log a user action
AuditLog.objects.create(
    user=request.user,
    action="create",
    entity_type="new_model",
    entity_id=str(new_model.id),
    description="Created a new model",
    context={
        "ip_address": request.META.get("REMOTE_ADDR"),
        "user_agent": request.META.get("HTTP_USER_AGENT"),
    }
)

# Log an error
ErrorLog.objects.create(
    level="error",
    message="Failed to process model",
    module=__name__,
    function="process_model",
    exception=str(e),
    stack_trace=traceback.format_exc(),
    user=request.user if hasattr(request, "user") else None,
    context={
        "model_id": model_id,
    }
)
```

## Testing Guidelines

### Unit Tests

Write unit tests for individual functions and methods:

```python
from django.test import TestCase
from new_app.models import NewModel

class NewModelTestCase(TestCase):
    def setUp(self):
        self.new_model = NewModel.objects.create(
            name="Test Model",
            description="Test Description"
        )
    
    def test_model_str(self):
        self.assertEqual(str(self.new_model), "Test Model")
    
    def test_model_description(self):
        self.assertEqual(self.new_model.description, "Test Description")
```

### Integration Tests

Write integration tests for API endpoints and views:

```python
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from new_app.models import NewModel

class NewModelAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.new_model = NewModel.objects.create(
            name="Test Model",
            description="Test Description"
        )
        self.url = reverse('new-model-detail', args=[self.new_model.id])
    
    def test_get_new_model(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], "Test Model")
```

### Mock Testing

Use `unittest.mock` for mocking external services:

```python
from unittest.mock import patch
from django.test import TestCase
from new_app.services import external_service

class ExternalServiceTestCase(TestCase):
    @patch('new_app.services.external_service.api_call')
    def test_api_call(self, mock_api_call):
        mock_api_call.return_value = {"status": "success"}
        result = external_service.call_api()
        self.assertEqual(result['status'], "success")
        mock_api_call.assert_called_once()
```

## Performance Optimization

### Database Optimization

Use the following techniques to optimize database queries:

- **Select Related**: Fetch related objects in a single query
  ```python
  # Instead of:
  for bot in Bot.objects.all():
      print(bot.owner.username)  # Separate query for each bot
  
  # Use:
  for bot in Bot.objects.select_related('owner').all():
      print(bot.owner.username)  # No additional queries
  ```

- **Prefetch Related**: Prefetch related objects for many-to-many or reverse foreign key relationships
  ```python
  # Instead of:
  for guild in Guild.objects.all():
      print(guild.channels.count())  # Separate query for each guild
  
  # Use:
  for guild in Guild.objects.prefetch_related('channels').all():
      print(guild.channels.count())  # No additional queries
  ```

- **Defer and Only**: Fetch only the fields you need
  ```python
  # Fetch only required fields
  users = User.objects.only('id', 'username').all()
  
  # Exclude large fields
  bots = Bot.objects.defer('description', 'avatar').all()
  ```

### Caching

Use Django's caching framework:

```python
from django.core.cache import cache

def get_bot_data(bot_id):
    cache_key = f"bot_data_{bot_id}"
    bot_data = cache.get(cache_key)
    
    if bot_data is None:
        # Fetch data from database
        bot = Bot.objects.get(id=bot_id)
        bot_data = {
            'id': bot.id,
            'name': bot.name,
            'status': bot.status,
        }
        # Cache data for 5 minutes
        cache.set(cache_key, bot_data, 300)
    
    return bot_data
```

### Task Queue

Use Celery for background tasks:

```python
from celery import shared_task

@shared_task
def process_large_dataset(dataset_id):
    # Process dataset in the background
    pass

# In your view
def process_dataset_view(request, dataset_id):
    # Queue task for background processing
    process_large_dataset.delay(dataset_id)
    return redirect('dataset_status', dataset_id=dataset_id)
```

## Deployment

See [Deployment Guide](deployment.md) for detailed deployment instructions.

## Troubleshooting

### Common Issues

- **Database Migrations**: If you encounter migration issues, try resetting the migrations
  ```bash
  python manage.py migrate app_name zero
  python manage.py makemigrations app_name
  python manage.py migrate app_name
  ```

- **Static Files**: If static files are not loading, check the `STATIC_URL` and `STATIC_ROOT` settings
  ```bash
  python manage.py collectstatic --noinput
  ```

- **Discord Bot Issues**: Check the bot token and intents
  ```bash
  # View bot status
  python manage.py shell -c "from bot_management.models import Bot; print('\n'.join([f'{bot.name} - {bot.status}' for bot in Bot.objects.all()]))"
  ```

### Debug Techniques

- **Django Debug Toolbar**: Install and configure for development
  ```bash
  pip install django-debug-toolbar
  ```

- **Logging**: Enable detailed logging
  ```python
  # In settings_dev.py
  LOGGING = {
      'version': 1,
      'disable_existing_loggers': False,
      'handlers': {
          'console': {
              'class': 'logging.StreamHandler',
          },
      },
      'root': {
          'handlers': ['console'],
          'level': 'DEBUG',
      },
  }
  ```

- **Django Shell**: Use for debugging
  ```bash
  python manage.py shell
  ```

## Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **Django REST Framework**: https://www.django-rest-framework.org/
- **Discord.py Documentation**: https://discordpy.readthedocs.io/
- **Django Channels**: https://channels.readthedocs.io/
- **Celery Documentation**: https://docs.celeryproject.org/