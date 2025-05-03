"""
ASGI application for WebSocket integration.

This module provides the ASGI application for handling both HTTP and WebSocket protocols.
"""
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

import realtime.routing

# Initialize the Django ASGI application
django_asgi_app = get_asgi_application()

# Configure the ASGI application
application = ProtocolTypeRouter({
    # Django's ASGI application handles HTTP requests
    "http": django_asgi_app,
    
    # WebSocket handler with authentication and allowed hosts validation
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                realtime.routing.websocket_urlpatterns
            )
        )
    ),
})