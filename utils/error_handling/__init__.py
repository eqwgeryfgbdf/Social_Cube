"""
Error handling package for Social Cube project.

This package provides standardized error handling components including
custom exceptions, handlers, and middleware.
"""

from utils.error_handling.exceptions import (
    SocialCubeError,
    AuthenticationError,
    PermissionDeniedError,
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    ValidationError,
    ExternalServiceError,
    DiscordAPIError,
    RateLimitError,
    ConfigurationError,
    DatabaseError,
)
from utils.error_handling.handlers import (
    handle_exception,
    log_exception,
    create_error_report,
    get_exception_handler,
)
from utils.error_handling.middleware import (
    ErrorHandlingMiddleware,
    APIErrorMiddleware,
)

__all__ = [
    # Exceptions
    'SocialCubeError',
    'AuthenticationError',
    'PermissionDeniedError',
    'ResourceNotFoundError',
    'ResourceAlreadyExistsError',
    'ValidationError',
    'ExternalServiceError',
    'DiscordAPIError',
    'RateLimitError',
    'ConfigurationError',
    'DatabaseError',
    
    # Handlers
    'handle_exception',
    'log_exception',
    'create_error_report',
    'get_exception_handler',
    
    # Middleware
    'ErrorHandlingMiddleware',
    'APIErrorMiddleware',
]