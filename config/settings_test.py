"""
Test environment settings for Social Cube project.
"""

from .settings_base import *  # noqa

# Debug should be False in tests to match production
DEBUG = False

# Use a consistent secret key for tests
SECRET_KEY = 'test-secret-key-not-for-production'

# Allow all hosts in test environment
ALLOWED_HOSTS = ['*']

# Use in-memory SQLite database for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Mock Discord OAuth2 values
DISCORD_CLIENT_ID = 'test-discord-client-id'
DISCORD_CLIENT_SECRET = 'test-discord-client-secret'
DISCORD_REDIRECT_URI = 'http://testserver/oauth2/callback/'

# Simplified CORS settings for tests
CORS_ALLOWED_ORIGINS = ['http://testserver']
CSRF_TRUSTED_ORIGINS = ['http://testserver']

# Disable password hashing to speed up tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging to console during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': False,
            'level': 'ERROR',
        },
        'dashboard': {
            'handlers': ['null'],
            'propagate': False,
            'level': 'ERROR',
        },
    },
}

# No email sending during tests
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'