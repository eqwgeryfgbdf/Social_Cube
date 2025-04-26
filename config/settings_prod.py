"""
Production environment settings for Social Cube project.
"""

from .settings_base import *  # noqa

# Debug should be False in production
DEBUG = False

# Secret key - must be provided in environment
SECRET_KEY = env('SECRET_KEY')

# Allowed hosts - must be configured properly in production
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Production database settings - must be configured
DATABASES = {
    'default': env.db('DATABASE_URL'),
}

# Discord OAuth2 credentials - required in production
DISCORD_CLIENT_ID = env('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = env('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = env('DISCORD_REDIRECT_URI')

# CORS settings - restrictive in production
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS')

# Google OAuth2 settings
GOOGLE_OAUTH2_CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, 'client_secrets.json')
GOOGLE_OAUTH2_SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
]

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

# Static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging - configuration for production environment
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django-errors.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'dashboard': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# Email configuration (using environment variables)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)