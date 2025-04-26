"""
WSGI config for Social Cube project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Check if we're running on production environment (using environment variable)
if os.environ.get('DJANGO_ENV') == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_dev')

application = get_wsgi_application()