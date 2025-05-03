"""
Exception handlers for the Social Cube project.

This module contains functions to handle exceptions and convert them to
appropriate HTTP responses.
"""
import logging
import traceback
from typing import Any, Dict, Optional, Type, Union

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from utils.common import format_datetime, json_response
from utils.error_handling.exceptions import SocialCubeError

logger = logging.getLogger('error_handling')


def handle_exception(
    request: HttpRequest,
    exception: Exception,
    template_name: Optional[str] = None,
    status_code: int = 500,
    context: Optional[Dict[str, Any]] = None
) -> Union[TemplateResponse, JsonResponse]:
    """Handle exceptions and return appropriate responses.
    
    This function handles exceptions by:
    1. Logging the exception details
    2. Creating appropriate error response based on request type (Ajax/API or regular)
    3. Returning template response for regular requests or JSON response for API requests
    
    Args:
        request: The HTTP request that caused the exception
        exception: The exception object
        template_name: Template to render for regular requests
        status_code: HTTP status code to return
        context: Additional context variables for template
        
    Returns:
        HTTP response appropriate for the request type
    """
    # Log the exception
    log_exception(request, exception)
    
    # Create error report
    error_report = create_error_report(request, exception, status_code)
    
    # Store exception details in the request for middleware
    request.exception_report = error_report
    
    # Determine if it's an API/Ajax request
    is_api_request = (
        request.headers.get('accept') == 'application/json' or
        request.headers.get('content-type') == 'application/json' or
        request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        request.path.startswith('/api/')
    )
    
    # For API requests, return JSON response
    if is_api_request:
        return json_response(error_report, status=status_code)
    
    # For regular requests, render template
    error_template = template_name or 'error.html'
    template_context = context or {}
    template_context.update({
        'error': error_report,
        'status_code': status_code,
    })
    
    return TemplateResponse(request, error_template, template_context, status=status_code)


def log_exception(request: HttpRequest, exception: Exception) -> None:
    """Log exception details for debugging and monitoring.
    
    Args:
        request: The HTTP request that caused the exception
        exception: The exception object
    """
    if isinstance(exception, SocialCubeError):
        # For known app exceptions, use the defined status code
        status_code = exception.status_code
        
        # Log with appropriate level based on status code
        if status_code >= 500:
            logger.error(
                f"Application error: {str(exception)}",
                exc_info=exception,
                extra={
                    'request_path': request.path,
                    'status_code': status_code,
                    'error_code': getattr(exception, 'code', 'error'),
                    'user_id': getattr(request.user, 'id', None),
                }
            )
        else:
            logger.warning(
                f"Application warning: {str(exception)}",
                extra={
                    'request_path': request.path,
                    'status_code': status_code,
                    'error_code': getattr(exception, 'code', 'error'),
                    'user_id': getattr(request.user, 'id', None),
                }
            )
    else:
        # For unexpected exceptions, always log as error with traceback
        logger.error(
            f"Unexpected error: {str(exception)}",
            exc_info=exception,
            extra={
                'request_path': request.path,
                'user_id': getattr(request.user, 'id', None),
            }
        )


def create_error_report(
    request: HttpRequest, 
    exception: Exception,
    status_code: int
) -> Dict[str, Any]:
    """Create a structured error report for the exception.
    
    Args:
        request: The HTTP request that caused the exception
        exception: The exception object
        status_code: HTTP status code to return
        
    Returns:
        Dictionary with error report details
    """
    # Get basic error details
    timestamp = format_datetime()
    request_id = getattr(request, 'request_id', None)
    
    # Handle known application exceptions
    if isinstance(exception, SocialCubeError):
        error_report = exception.to_dict()
    else:
        # Create generic error report for unknown exceptions
        error_message = str(exception)
        if not error_message and hasattr(exception, '__class__'):
            error_message = f"An error of type {exception.__class__.__name__} occurred."
        
        error_report = {
            'error': 'server_error',
            'message': error_message or _("An unexpected error occurred."),
            'status_code': status_code,
        }
    
    # Add common metadata
    error_report.update({
        'timestamp': timestamp,
        'request_id': request_id,
        'path': request.path,
    })
    
    # Add traceback in debug mode
    if settings.DEBUG:
        error_report['traceback'] = traceback.format_exc()
    
    return error_report


def get_exception_handler(exception_class: Type[Exception]):
    """Get a handler function for a specific exception class.
    
    Args:
        exception_class: The exception class to handle
        
    Returns:
        Handler function for the exception
    """
    def handler(request, exception, *args, **kwargs):
        if isinstance(exception, SocialCubeError):
            status_code = exception.status_code
        elif hasattr(exception, 'status_code'):
            status_code = exception.status_code
        else:
            status_code = 500
            
        return handle_exception(request, exception, status_code=status_code)
        
    return handler