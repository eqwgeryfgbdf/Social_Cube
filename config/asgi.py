"""
ASGI config for Social Cube project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_dev')

application = get_asgi_application()