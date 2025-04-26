"""
Base Django settings for Social Cube project.
Contains settings common to all environments.
"""

import os
from pathlib import Path
import environ
from cryptography.fernet import Fernet

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env(
    # Default values
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    DATABASE_URL=(str, 'sqlite:///db.sqlite3'),
)
# Read environment variables from .env file if it exists
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Application definition - core Django apps
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Third-party apps
THIRD_PARTY_APPS = [
    'crispy_forms',
    'crispy_bootstrap5',
    'corsheaders',
    'rest_framework',
]

# Project apps
PROJECT_APPS = [
    'dashboard.apps.DashboardConfig',
    'bot_management',
    'api',
]

# Combined apps list
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS

# Middleware configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # For CORS support
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URL configuration
ROOT_URLCONF = 'social_cube.urls'

# Template configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
        BASE_DIR / 'templates',
        BASE_DIR / 'dashboard' / 'templates',
        BASE_DIR / 'bot_management' / 'templates',
        BASE_DIR / 'api' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI application
WSGI_APPLICATION = 'social_cube.wsgi.application'

# Password validation settings
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Discord OAuth2 base settings (without credentials)
DISCORD_REDIRECT_URI = env('DISCORD_REDIRECT_URI', default='http://localhost:8000/oauth2/callback/')

# Authentication settings
LOGIN_URL = 'dashboard:oauth2_login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'dashboard:index'

# Bot settings - base configuration
BOT_TOKEN_KEY = env('BOT_TOKEN_KEY', default=Fernet.generate_key().decode())  # Auto-generate if not provided

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}