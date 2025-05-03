# Social Cube - Discord Bot Management System

A Django application for managing Discord bots, allowing users to create, configure, and monitor Discord bots through a web interface.

## Features

- Discord bot creation and management
- Command monitoring and statistics
- Server management and insights
- OAuth2 integration with Discord
- User-friendly dashboard
- Responsive design

## Project Structure

The project has been structured following Django best practices:

```
social_cube/
├── config/              # Project configuration
│   ├── settings_base.py # Base settings
│   ├── settings_dev.py  # Development settings
│   ├── settings_prod.py # Production settings
│   ├── settings_test.py # Test settings
├── api/                 # REST API endpoints for frontend and bots
├── bot_management/      # Discord bot creation and management
├── dashboard/           # Web interface and task management system
│   ├── taskmaster/      # Task management subsystem
│   ├── templatetags/    # Custom template tags
├── scripts/             # Utility scripts
├── static/              # Static files (CSS, JS)
├── logs/                # Log files
├── media/               # User-uploaded files
├── templates/           # Project-wide templates
├── .env.example         # Environment variables example
├── manage.py            # Django management script
├── setup.py             # Package setup script
```

## Architecture Overview

### Core Components

- **API Layer**: RESTful API endpoints for frontend communication and bot interactions
- **Bot Management**: Services for Discord bot creation, configuration, and monitoring
- **Dashboard**: Web interface including analytics, monitoring, and task management
- **Configuration**: Core settings and environment-specific configurations
- **Logging System**: Comprehensive logging for HTTP requests, user actions, and application errors
- **Real-time Updates**: WebSocket-based real-time updates for bot status and events

### Technologies

- **Backend Framework**: Django 4.x with Django REST Framework
- **Database**: SQLite (development), PostgreSQL (production)
- **Task Queue**: Celery with Redis for background processing
- **WebSockets**: Django Channels with Redis as the backing store
- **Frontend**: HTML, CSS, JavaScript with Tailwind CSS for responsive design
- **Deployment**: Docker and Docker Compose
- **Authentication**: OAuth2 integration with Discord

### Data Models

Key models in the application include:

- **User**: Extended Django user model with Discord OAuth integration
- **Bot**: Discord bot configuration and credentials
- **Guild**: Discord servers (guilds) where bots are deployed
- **GuildSettings**: Server-specific settings and configurations
- **Command**: Bot commands with options and permissions
- **CommandLog**: Usage tracking for bot commands
- **RequestLog**: HTTP request logging with metadata
- **AuditLog**: User action tracking for security and auditing
- **ErrorLog**: Application error tracking and monitoring

Refer to each app's `models.py` for detailed schema information.

### Application Flow

1. **User Authentication**: Users authenticate via Discord OAuth
2. **Bot Creation**: Users create and configure Discord bots
3. **Server Management**: Bots join Discord servers with appropriate permissions
4. **Command Configuration**: Users define custom commands for their bots
5. **Real-time Monitoring**: WebSocket connections provide live updates on bot activity
6. **Analytics**: Usage statistics and insights are generated from logs

## Getting Started

### Prerequisites

- Python 3.11 or higher
- pip or conda

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/social_cube.git
   cd social_cube
   ```

2. Create a Conda environment:
   ```bash
   # Option 1: Using Conda (recommended)
   conda env create -f environment.yml
   conda activate social_cube
   
   # Option 2: Using Python venv
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   python scripts/setup_env.py
   ```
   Edit the `.env` file to add your Discord OAuth2 credentials.
   
   > **Important**: For Discord OAuth2 setup, follow the detailed instructions in [Discord Application Setup Guide](docs/discord_app_setup.md).

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```bash
   # On Windows
   run_dev.bat
   
   # On macOS/Linux
   ./run_dev.sh
   ```
   Or directly:
   ```bash
   python manage.py runserver
   ```

### Docker Deployment

For production or testing with Docker:

1. Set up the environment file:
   ```bash
   cp docker.env.example .env
   ```
   Edit the `.env` file to update necessary settings like SECRET_KEY, database credentials, and Discord OAuth details.

2. Start the services:
   ```bash
   docker-compose up -d
   ```

3. To deploy with SSL:
   ```bash
   # Make the script executable
   chmod +x scripts/setup_ssl.sh
   
   # Run the SSL setup script with your domain and email
   ./scripts/setup_ssl.sh yourdomain.com your@email.com
   
   # Follow the instructions printed by the script to complete SSL setup
   ```

4. For backup and maintenance:
   ```bash
   # Backup the database and media files
   ./scripts/backup.sh
   
   # View logs
   docker-compose logs -f web
   ```

5. For detailed deployment instructions, see [Deployment Guide](docs/deployment.md)

### Running in Production

For traditional production deployment:

1. Set the `DJANGO_ENV` environment variable to `production`:
   ```bash
   export DJANGO_ENV=production
   ```

2. Make sure to configure all required environment variables in your production environment.

3. Collect static files:
   ```bash
   python manage.py collectstatic
   ```

4. Use gunicorn or other WSGI server:
   ```bash
   gunicorn config.wsgi:application
   ```

## Testing

Run tests using:

```bash
python manage.py test
```

Or with pytest:

```bash
pytest
```

## Development Workflow

### Setting Up Your Development Environment

1. Follow the installation steps above to set up your local environment
2. Activate your conda environment: `conda activate social_cube`
3. Make sure your `.env` file is properly configured with necessary credentials

### Git Workflow

1. Create a feature branch for your work:
   ```bash
   git checkout -b feature/descriptive-name
   ```
   
2. Make regular, atomic commits with descriptive messages:
   ```bash
   git commit -m "feat: Add Discord OAuth integration"
   ```