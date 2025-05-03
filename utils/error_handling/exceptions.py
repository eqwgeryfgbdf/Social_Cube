"""
Custom exceptions for the Social Cube project.

This module defines a hierarchy of exceptions used throughout the application
to provide consistent error handling and reporting.
"""
from typing import Any, Dict, List, Optional


class SocialCubeError(Exception):
    """Base exception for all Social Cube exceptions."""
    
    def __init__(
        self, 
        message: str, 
        code: str = "error", 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize the exception.
        
        Args:
            message: Human-readable error message.
            code: Error code for API clients.
            status_code: HTTP status code for the response.
            details: Additional details about the error.
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for API responses."""
        result = {
            'error': self.code,
            'message': self.message,
            'status_code': self.status_code,
        }
        
        if self.details:
            result['details'] = self.details
            
        return result


# Authentication and authorization exceptions

class AuthenticationError(SocialCubeError):
    """Exception raised for authentication errors."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "authentication_error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, 401, details)


class PermissionDeniedError(SocialCubeError):
    """Exception raised when a user doesn't have permission to perform an action."""
    
    def __init__(
        self,
        message: str = "Permission denied",
        code: str = "permission_denied",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, 403, details)


# Resource exceptions

class ResourceNotFoundError(SocialCubeError):
    """Exception raised when a requested resource is not found."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        code: str = "not_found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        details = {}
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
            
        super().__init__(message, code, 404, details)


class ResourceAlreadyExistsError(SocialCubeError):
    """Exception raised when attempting to create a resource that already exists."""
    
    def __init__(
        self,
        message: str = "Resource already exists",
        code: str = "already_exists",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        details = {}
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
            
        super().__init__(message, code, 409, details)


# Validation exceptions

class ValidationError(SocialCubeError):
    """Exception raised for validation errors."""
    
    def __init__(
        self,
        message: str = "Validation error",
        code: str = "validation_error",
        errors: Optional[Dict[str, List[str]]] = None
    ):
        details = {}
        if errors:
            details['errors'] = errors
            
        super().__init__(message, code, 400, details)


# External service exceptions

class ExternalServiceError(SocialCubeError):
    """Exception raised when an external service fails."""
    
    def __init__(
        self,
        message: str = "External service error",
        code: str = "external_service_error",
        service_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if service_name:
            error_details['service_name'] = service_name
            
        super().__init__(message, code, 502, error_details)


class DiscordAPIError(ExternalServiceError):
    """Exception raised when the Discord API returns an error."""
    
    def __init__(
        self,
        message: str = "Discord API error",
        code: str = "discord_api_error",
        discord_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if discord_code:
            error_details['discord_code'] = discord_code
            
        super().__init__(message, code, 502, error_details)
        self.details['service_name'] = 'Discord'


# Rate limiting exceptions

class RateLimitError(SocialCubeError):
    """Exception raised when a rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        code: str = "rate_limit_exceeded",
        reset_at: Optional[int] = None
    ):
        details = {}
        if reset_at:
            details['reset_at'] = reset_at
            
        super().__init__(message, code, 429, details)


# Configuration exceptions

class ConfigurationError(SocialCubeError):
    """Exception raised for configuration errors."""
    
    def __init__(
        self,
        message: str = "Configuration error",
        code: str = "configuration_error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, 500, details)


# Database exceptions

class DatabaseError(SocialCubeError):
    """Exception raised for database errors."""
    
    def __init__(
        self,
        message: str = "Database error",
        code: str = "database_error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, 500, details)