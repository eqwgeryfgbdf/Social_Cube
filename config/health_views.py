from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
import redis
from django.conf import settings
import socket


def health_check(request):
    """
    Health check endpoint for container orchestration.
    
    Checks:
    1. Database connection
    2. Redis connection (if used)
    3. Basic application status
    """
    health_status = {
        'status': 'ok',
        'components': {
            'database': True,
            'redis': True,
            'application': True
        },
        'errors': []
    }
    
    # Check database connection
    try:
        db_conn = connections['default']
        db_conn.cursor()
    except OperationalError as e:
        health_status['components']['database'] = False
        health_status['status'] = 'error'
        health_status['errors'].append(f"Database error: {str(e)}")
    
    # Check Redis connection if configured
    try:
        redis_host = getattr(settings, 'REDIS_HOST', 'redis')
        redis_port = getattr(settings, 'REDIS_PORT', 6379)
        redis_client = redis.Redis(host=redis_host, port=redis_port, socket_timeout=1)
        redis_client.ping()
    except (redis.exceptions.RedisError, socket.error) as e:
        health_status['components']['redis'] = False
        # Only mark as error if Redis is actually required
        if hasattr(settings, 'CHANNEL_LAYERS') and settings.CHANNEL_LAYERS.get('default', {}).get('BACKEND', '').endswith('RedisChannelLayer'):
            health_status['status'] = 'error'
            health_status['errors'].append(f"Redis error: {str(e)}")
    
    # Return appropriate status code
    status_code = 200 if health_status['status'] == 'ok' else 500
    return JsonResponse(health_status, status=status_code)