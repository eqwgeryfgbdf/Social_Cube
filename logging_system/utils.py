import sys
import traceback
from django.db import transaction
from .models import AuditLog, ErrorLog


def log_action(action, user=None, entity_type=None, entity_id=None, 
               entity_name=None, description=None, changes=None, additional_data=None, ip_address=None):
    """
    Create an audit log entry for a user action.
    
    Args:
        action (str): Type of action (create, update, delete, etc.)
        user (User): Django user who performed the action
        entity_type (str): The type of entity affected
        entity_id (str/int): Identifier for the affected entity
        entity_name (str): String representation of the entity
        description (str): Description of what happened
        changes (dict): Changes made to the entity
        additional_data (dict): Additional context information
        ip_address (str): IP address of the user
    
    Returns:
        AuditLog: The created audit log entry
    """
    try:
        return AuditLog.objects.create(
            action=action,
            user=user,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            description=description,
            changes=changes or {},
            additional_data=additional_data or {},
            ip_address=ip_address
        )
    except Exception as e:
        # If we can't log the action, at least log the error
        log_error(e, description=f"Failed to create audit log for {action}")
        return None


def log_error(exception=None, level="ERROR", exception_type=None, message=None, 
              request_path=None, logger_name="app", request=None, user=None, 
              ip_address=None, additional_data=None):
    """
    Create an error log entry for an exception or error.
    
    Args:
        exception (Exception): The exception that occurred
        level (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        exception_type (str): Type of error (if exception is None)
        message (str): Error message (if exception is None)
        request_path (str): Path where the error occurred
        logger_name (str): Name of the logger
        request (HttpRequest): Django request object
        user (User): Django user associated with the error
        ip_address (str): IP address of the user
        additional_data (dict): Additional context information
    
    Returns:
        ErrorLog: The created error log entry
    """
    # Handle case where called without an exception
    if exception is None and message is None:
        message = "Unknown error"
    
    # If we have an exception, extract info from it
    if exception:
        exception_type = exception_type or exception.__class__.__name__
        message = message or str(exception)
        tb = ''.join(traceback.format_exception(
            type(exception), exception, exception.__traceback__))
    else:
        tb = ''.join(traceback.format_stack())
    
    # Extract request data if available
    if request:
        request_path = request_path or request.path
        user = user or (request.user if hasattr(request, 'user') and 
                         request.user.is_authenticated else None)
        ip_address = ip_address or _get_client_ip(request)
        
        # Extract request data for additional context
        req_data = {
            'method': request.method,
            'path': request.path,
            'GET': dict(request.GET),
            'POST': dict(request.POST),
            'META': {k: str(v) for k, v in request.META.items() 
                    if k.startswith('HTTP_')},
        }
        
        # Merge with any provided additional data
        if additional_data:
            if isinstance(additional_data, dict):
                additional_data.update({'request': req_data})
            else:
                additional_data = {'request': req_data, 'original_data': additional_data}
        else:
            additional_data = {'request': req_data}
    
    # Create the error log - use transaction.atomic to ensure
    # we don't get in a recursive loop if there's a transaction error
    try:
        with transaction.atomic():
            return ErrorLog.objects.create(
                level=level,
                logger_name=logger_name,
                exception_type=exception_type or '',
                message=message,
                request_path=request_path,
                traceback=tb,
                additional_data=additional_data or {},
                user=user,
                ip_address=ip_address
            )
    except Exception as e:
        # If we can't log to the database, at least print to stderr
        print(f"Failed to log error to database: {e}", file=sys.stderr)
        print(f"Original error: {message}", file=sys.stderr)
        return None


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


class ErrorLoggingMixin:
    """
    Mixin for class-based views to automatically log exceptions.
    """
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            # Log the error
            log_error(e, request=request, logger_name=self.__class__.__name__)
            # Re-raise to let Django handle the exception
            raise