import time
import json
import logging
from django.utils.deprecation import MiddlewareMixin
from .models import RequestLog

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all requests to the application.
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Store the start time for duration calculation
        request.start_time = time.time()
        
        # Set a default value for response size
        request.response_size = 0
        
        return None
    
    def process_response(self, request, response):
        # Skip if no start_time (e.g., middleware not properly initialized)
        if not hasattr(request, 'start_time'):
            return response
            
        # Calculate request duration
        duration = time.time() - request.start_time
        
        # Get user if authenticated
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
        
        # Extract request body (if it's JSON)
        request_body = {}
        if request.content_type and 'application/json' in request.content_type:
            try:
                if hasattr(request, 'body') and request.body:
                    request_body = json.loads(request.body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning(f"Could not decode request body as JSON: {e}")
        
        # Get response size
        response_size = len(response.content) if hasattr(response, 'content') else 0
        
        # Create a RequestLog entry
        try:
            RequestLog.objects.create(
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                duration=duration,
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                query_params=dict(request.GET),
                request_body=request_body,
                response_size=response_size
            )
        except Exception as e:
            # Log the error but don't interrupt the response flow
            logger.error(f"Error logging request: {e}")
        
        return response
    
    def get_client_ip(self, request):
        """Extract the client IP address from request headers"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Get the first IP in case of proxy chains
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip