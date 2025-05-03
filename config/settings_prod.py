"""
Production environment settings for Social Cube project.
"""

import os
from .settings_base import *  # noqa

# Debug should be False in production
DEBUG = env.bool('DEBUG', default=False)

# Secret key - must be provided in environment
SECRET_KEY = env('SECRET_KEY')

# Allowed hosts - must be configured properly in production
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Production database settings
# Use DATABASE_URL if provided, otherwise construct from individual settings
if env('DATABASE_URL', default=None):
    DATABASES = {
        'default': env.db('DATABASE_URL'),
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': env('DB_ENGINE', default='django.db.backends.postgresql'),
            'NAME': env('DB_NAME', default='social_cube'),
            'USER': env('DB_USER', default='postgres'),
            'PASSWORD': env('DB_PASSWORD'),
            'HOST': env('DB_HOST', default='db'),
            'PORT': env('DB_PORT', default='5432'),
            'CONN_MAX_AGE': env.int('DB_CONN_MAX_AGE', default=60),
            'OPTIONS': {
                'connect_timeout': env.int('DB_CONNECT_TIMEOUT', default=10),
            }
        }
    }

# Discord OAuth2 credentials - required in production
DISCORD_CLIENT_ID = env('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = env('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = env('DISCORD_REDIRECT_URI')

# CORS settings - restrictive in production
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# Google OAuth2 settings
GOOGLE_OAUTH2_CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, 'client_secrets.json')
GOOGLE_OAUTH2_SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
]

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default=f"redis://{env('REDIS_HOST', default='redis')}:{env('REDIS_PORT', default='6379')}/1"),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
            'PARSER_CLASS': 'redis.connection.HiredisParser',
        }
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 1 day in seconds
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_NAME = 'social_cube_session'
SESSION_COOKIE_SECURE = True

# Security settings for production
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=2592000)  # 30 days
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=True)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# Static files configuration
STATIC_ROOT = env('STATIC_ROOT', default=os.path.join(BASE_DIR, 'staticfiles'))
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files configuration
MEDIA_ROOT = env('MEDIA_ROOT', default=os.path.join(BASE_DIR, 'media'))

# Channels configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(env('REDIS_HOST', default='redis'), env.int('REDIS_PORT', default=6379))],
        },
    },
}

# Logging - enhanced configuration for production environment
LOG_LEVEL = env('LOG_LEVEL', default='ERROR')
LOG_FILE = env('LOG_FILE', default=os.path.join(BASE_DIR, 'logs', 'django-errors.log'))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': LOG_LEVEL,
            'class': 'logging.FileHandler',
            'filename': LOG_FILE,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['mail_admins', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console', 'file'],
            'level': env('DB_LOG_LEVEL', default='ERROR'),
            'propagate': False,
        },
        'dashboard': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'bot_management': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'api': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'realtime': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
    },
}

# Email configuration (using environment variables)
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)

# Performance optimizations
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
ATOMIC_REQUESTS = True

# Custom settings for production
DISCORD_BOT_AUTO_START = env.bool('DISCORD_BOT_AUTO_START', default=True)
MAX_DISCORD_BOTS_PER_USER = env.int('MAX_DISCORD_BOTS_PER_USER', default=5)