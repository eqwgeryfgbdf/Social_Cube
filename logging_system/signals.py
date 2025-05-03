from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from .utils import log_action


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log when a user logs in"""
    log_action(
        action='login',
        user=user,
        entity_type='User',
        entity_id=user.id,
        entity_name=str(user),
        description=f"User logged in: {user.username}",
        additional_data={
            'sender': sender.__name__ if hasattr(sender, '__name__') else str(sender)
        },
        ip_address=_get_client_ip(request) if request else None
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log when a user logs out"""
    if user:  # User might be None in some cases
        log_action(
            action='logout',
            user=user,
            entity_type='User',
            entity_id=user.id,
            entity_name=str(user),
            description=f"User logged out: {user.username}",
            additional_data={
                'sender': sender.__name__ if hasattr(sender, '__name__') else str(sender)
            },
            ip_address=_get_client_ip(request) if request else None
        )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Log when a login attempt fails"""
    log_action(
        action='auth_failure',
        user=None,
        entity_type='User',
        entity_id=None,
        entity_name=credentials.get('username', 'unknown'),
        description=f"Failed login attempt for username: {credentials.get('username', 'unknown')}",
        additional_data={
            'sender': sender.__name__ if hasattr(sender, '__name__') else str(sender),
            'credentials': {k: '******' if k == 'password' else v 
                           for k, v in credentials.items()}
        },
        ip_address=_get_client_ip(request) if request else None
    )


def _get_client_ip(request):
    """Extract the client IP address from request headers"""
    if not request:
        return None
        
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Get the first IP in case of proxy chains
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip