from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.db import close_old_connections


@database_sync_to_async
def get_user(scope):
    from django.contrib.auth import get_user_model
    
    if "session" not in scope:
        return AnonymousUser()
    
    User = get_user_model()
    user_id = scope["session"].get("_auth_user_id")
    
    if not user_id:
        return AnonymousUser()
    
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class WebSocketAuthMiddleware(BaseMiddleware):
    """
    Middleware for WebSocket authentication.
    
    Attaches user info to WebSocket scope based on the Django session.
    """
    
    async def __call__(self, scope, receive, send):
        # Close database connections to prevent them from being shared
        # between threads
        close_old_connections()
        
        # Get the user from the Django session
        scope['user'] = await get_user(scope)
        
        # Continue processing
        return await super().__call__(scope, receive, send)