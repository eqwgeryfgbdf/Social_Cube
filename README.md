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

### Technologies

- **Backend Framework**: Django 4.x with Django REST Framework
- **Database**: SQLite (development), PostgreSQL (production)
- **Task Queue**: Celery with Redis for background processing
- **Frontend**: HTML, CSS, JavaScript with responsive design
- **Deployment**: Docker and Docker Compose
- **Authentication**: OAuth2 integration with Discord

### Data Models

Key models in the application include:

- **User**: Extended Django user model with Discord OAuth integration
- **Bot**: Discord bot configuration and credentials
- **Server**: Discord servers where bots are deployed
- **Command**: Bot commands and their usage statistics
- **Event**: Discord events tracked by bots

Refer to each app's `models.py` for detailed schema information.

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
   python scripts/run_dev.py
   ```
   Or directly:
   ```bash
   python manage.py runserver
   ```

### Running in Production

For production deployment:

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
   
3. Follow conventional commits for commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `style:` for formatting changes
   - `refactor:` for code refactoring
   - `test:` for adding tests
   - `chore:` for maintenance tasks
   
4. Push your changes to the remote repository:
   ```bash
   git push origin feature/descriptive-name
   ```
   
5. Create a pull request for code review

### Django Development Tips

1. Create new apps for discrete functionality:
   ```bash
   python manage.py startapp new_app_name
   ```
   
2. Always run migrations after model changes:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
   
3. Use Django's test framework for writing tests:
   ```bash
   python manage.py test app_name
   ```
   
4. Keep views lightweight by moving business logic to models and services

5. Use Django Debug Toolbar during development:
   ```bash
   pip install django-debug-toolbar
   ```
   
### Code Quality

1. Run linting before committing:
   ```bash
   flake8 .
   ```
   
2. Format code with black:
   ```bash
   black .
   ```
   
3. Check type hints with mypy:
   ```bash
   mypy .
   ```
   
### CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment:

1. **Continuous Integration**:
   - Automated testing runs on every pull request and push to main
   - Code quality checks (flake8, black, mypy) are performed
   - Test coverage reports are generated

2. **Continuous Deployment**:
   - Successful builds on the main branch trigger automatic deployment
   - Docker images are built and pushed to a registry
   - Deployment to staging/production is managed via deployment scripts

3. **Environment Management**:
   - Development environment: Local development with Django runserver
   - Staging environment: Deployed from the main branch
   - Production environment: Deployed from release tags

## Contributing

### Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/Social_Cube.git`
3. Create a virtual environment as described in the setup section
4. Install development dependencies: `pip install -r requirements-dev.txt`
5. Create your feature branch: `git checkout -b feature/amazing-feature`

### Development Process

1. Make your changes following the development workflow described above
2. Ensure all tests pass: `python manage.py test`
3. Add test coverage for your new feature
4. Update documentation if needed
5. Commit your changes with descriptive commit messages: `git commit -m 'Add some amazing feature'`
6. Push to your branch: `git push origin feature/amazing-feature`
7. Open a Pull Request with detailed description of changes

### Pull Request Process

1. Ensure your code passes all CI checks
2. Get at least one code review from a maintainer
3. Address any feedback from the review
4. Once approved, a maintainer will merge your PR

### Code of Conduct

Please follow our Code of Conduct in all your interactions with the project.

## Troubleshooting

### Common Issues

#### Database Migration Errors

If you encounter migration errors:

```bash
python manage.py migrate --fake-initial
python manage.py makemigrations
python manage.py migrate
```

#### Static Files Not Loading

Ensure you've collected static files:

```bash
python manage.py collectstatic
```

#### API Authentication Issues

Check your API key configuration in `.env` file and ensure your user has the correct permissions.

#### Docker Build Failures

Ensure Docker is running and try rebuilding with the `--no-cache` option:

```bash
docker-compose build --no-cache
```

### Getting Help

If you're experiencing issues not covered here:

1. Check the existing GitHub issues to see if it's a known problem
2. Join our community Discord channel for real-time support
3. Open a new GitHub issue with detailed information about your problem

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django
- Discord.py
- All contributors