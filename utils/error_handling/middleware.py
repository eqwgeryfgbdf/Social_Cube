"""
Error handling middleware for Social Cube project.

This middleware provides centralized error handling for the application,
catching exceptions and converting them to appropriate HTTP responses.
"""
import logging
import uuid
from typing import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import Resolver404
from django.utils.deprecation import MiddlewareMixin

from utils.common import json_response
from utils.error_handling.exceptions import SocialCubeError
from utils.error_handling.handlers import handle_exception

logger = logging.getLogger('error_handling')


class ErrorHandlingMiddleware(MiddlewareMixin):
    """Middleware for handling exceptions and providing consistent error responses."""
    
    def __init__(self, get_response: Callable):
        """Initialize the middleware.
        
        Args:
            get_response: Function that takes a request and returns a response
        """
        self.get_response = get_response
    
    def process_request(self, request: HttpRequest) -> None:
        """Process the incoming request.
        
        Adds a unique ID to each request for tracking through logs.
        
        Args:
            request: The HTTP request
        """
        # Add a unique ID to the request for tracking
        request.request_id = str(uuid.uuid4())
        
        # Store original path for logging
        request.original_path = request.path
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> HttpResponse:
        """Process exceptions raised during request handling.
        
        Args:
            request: The HTTP request
            exception: The exception that was raised
            
        Returns:
            Appropriate HTTP response for the exception
        """
        # Skip 404 errors from URL resolver
        if isinstance(exception, Resolver404):
            return None
        
        # Handle SocialCubeError exceptions
        if isinstance(exception, SocialCubeError):
            return handle_exception(
                request, 
                exception, 
                status_code=exception.status_code
            )
        
        # Handle other exceptions
        return handle_exception(request, exception)
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Process the outgoing response.
        
        Args:
            request: The HTTP request
            response: The HTTP response
            
        Returns:
            The processed HTTP response
        """
        # Add request ID to response headers for tracking
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id
        
        # Add the Django version to response headers
        response['X-Django-Version'] = getattr(settings, 'DJANGO_VERSION', '')
        
        return response


class APIErrorMiddleware(MiddlewareMixin):
    """Middleware for handling API-specific errors and formatting."""
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> HttpResponse:
        """Process exceptions for API requests.
        
        Args:
            request: The HTTP request
            exception: The exception that was raised
            
        Returns:
            JSON response for API errors
        """
        # Only process API requests
        if not (
            request.path.startswith('/api/') or
            request.headers.get('accept') == 'application/json' or
            request.headers.get('content-type') == 'application/json' or
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        ):
            return None
        
        # Handle SocialCubeError exceptions
        if isinstance(exception, SocialCubeError):
            return json_response(
                exception.to_dict(),
                status=exception.status_code
            )
        
        # Handle other exceptions with a generic error response
        if settings.DEBUG:
            error_message = str(exception)
            error_detail = {
                'type': exception.__class__.__name__,
                'message': error_message
            }
        else:
            error_message = "An unexpected error occurred."
            error_detail = None
        
        return json_response(
            {
                'error': 'server_error',
                'message': error_message,
                'status_code': 500,
                'detail': error_detail
            },
            status=500
        )