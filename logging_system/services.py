import logging
import traceback
import uuid
from functools import wraps
from typing import Dict, Any, Optional, Callable, Type

from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import RequestLog, AuditLog, ErrorLog

User = get_user_model()
logger = logging.getLogger('social_cube.logging_system')


class LoggingService:
    """Service for handling application-wide logging needs"""
    
    @staticmethod
    def log_request(
        request_id: str,
        method: str,
        path: str,
        status_code: int,
        duration: int,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        query_params: Optional[Dict] = None,
        request_body: Optional[Dict] = None
    ) -> RequestLog:
        """Log an HTTP request to the database"""
        try:
            user = User.objects.get(id=user_id) if user_id else None
            
            return RequestLog.objects.create(
                request_id=request_id,
                method=method,
                path=path,
                status_code=status_code,
                duration=duration,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                query_params=query_params,
                request_body=request_body
            )
        except Exception as e:
            logger.error(f"Failed to log request: {e}")
            # Don't raise the exception to prevent affecting the main application flow
            return None

    @staticmethod
    def log_audit(
        action: str,
        entity_type: str,
        description: str,
        user_id: Optional[int] = None,
        request_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        data: Optional[Dict] = None
    ) -> AuditLog:
        """Log a user action or system event to the audit log"""
        try:
            user = User.objects.get(id=user_id) if user_id else None
            
            return AuditLog.objects.create(
                request_id=request_id,
                user=user,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description,
                data=data
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            return None

    @staticmethod
    def log_error(
        message: str,
        level: str = 'error',
        location: str = '',
        exception: Optional[Exception] = None,
        request_id: Optional[str] = None,
        user_id: Optional[int] = None,
        context: Optional[Dict] = None
    ) -> ErrorLog:
        """Log an error or exception to the database"""
        try:
            user = User.objects.get(id=user_id) if user_id else None
            tb = traceback.format_exc() if exception else None
            
            error_log = ErrorLog.objects.create(
                request_id=request_id,
                level=level,
                location=location,
                message=message,
                traceback=tb,
                user=user,
                context=context
            )
            
            # Also log to the conventional logger
            log_method = getattr(logger, level, logger.error)
            log_method(f"{message} - ID: {error_log.id}")
            
            return error_log
        except Exception as e:
            # Last resort fallback to standard logging
            logger.critical(f"Failed to log error to database: {e}")
            logger.critical(f"Original error: {message}")
            return None


def audit_log(
    action: str,
    entity_type: str,
    get_description: Callable = None,
    get_entity_id: Callable = None,
    get_data: Callable = None
):
    """
    Decorator for automatically logging actions to the audit log.
    
    Usage:
        @audit_log('create', 'User', 
                  get_description=lambda *args, **kwargs: f"Created user {kwargs['username']}",
                  get_entity_id=lambda self, user, *args, **kwargs: user.id,
                  get_data=lambda self, user, *args, **kwargs: {'username': user.username})
        def create_user(self, username, email, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get request from the first argument if it's a view function
            request = args[0] if args and hasattr(args[0], 'user') else None
            request_id = getattr(request, 'id', None) if request else None
            user_id = request.user.id if request and request.user.is_authenticated else None
            
            # Execute the original function
            try:
                result = func(*args, **kwargs)
                
                # Get dynamic values using the provided callables
                description = get_description(*args, **kwargs) if get_description else f"{action} {entity_type}"
                entity_id = str(get_entity_id(*args, **kwargs)) if get_entity_id else None
                data = get_data(*args, **kwargs) if get_data else None
                
                # Create the audit log
                with transaction.atomic():
                    LoggingService.log_audit(
                        action=action,
                        entity_type=entity_type,
                        description=description,
                        user_id=user_id,
                        request_id=request_id,
                        entity_id=entity_id,
                        data=data
                    )
                
                return result
            except Exception as e:
                # Log the exception but don't interfere with the normal exception handling
                LoggingService.log_error(
                    message=f"Error in {func.__name__} during audit logging: {str(e)}",
                    level='error',
                    location=f"{func.__module__}.{func.__name__}",
                    exception=e,
                    request_id=request_id,
                    user_id=user_id
                )
                raise
        
        return wrapper
    
    return decorator


def generate_request_id() -> str:
    """Generate a unique request ID"""
    return str(uuid.uuid4())