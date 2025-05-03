"""
ASGI config for Social Cube project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django

# Check environment setting and set appropriate settings module
django_env = os.environ.get('DJANGO_ENV', 'development')
if django_env == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_prod')
elif django_env == 'test':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_test')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_dev')

# Initialize Django first
django.setup()

# Import after Django setup to avoid import errors
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# Import WebSocket URL patterns
import realtime.routing

# Create the ASGI application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                realtime.routing.websocket_urlpatterns
            )
        )
    ),
})