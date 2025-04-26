"""
Development environment settings for Social Cube project.
"""

from .settings_base import *  # noqa

# Set DEBUG to True in development
DEBUG = True

# Django Secret Key - in dev can use a placeholder if not in env
SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-only-key-change-in-production')

# Allowed hosts - less restrictive in development
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# Database - use SQLite for development by default
DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3'),
}

# CORS settings - more permissive in development
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',  # For frontend dev server if used
])

# CSRF settings
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'http://localhost:8000',
    'http://127.0.0.1:8000',
])

# Discord OAuth2 settings - get from env or use placeholders
DISCORD_CLIENT_ID = env('DISCORD_CLIENT_ID', default='your-discord-client-id')
DISCORD_CLIENT_SECRET = env('DISCORD_CLIENT_SECRET', default='your-discord-client-secret')

# Google OAuth2 settings
GOOGLE_OAUTH2_CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, 'client_secrets.json')
GOOGLE_OAUTH2_SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
]

# Logging - more verbose in development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'dashboard': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Email configuration for development (print to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'