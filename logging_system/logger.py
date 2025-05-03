import logging
import json
import threading
import uuid
from datetime import datetime
from django.conf import settings

# Get loggers
request_logger = logging.getLogger('logging_system.requests')
audit_logger = logging.getLogger('logging_system.audit')
error_logger = logging.getLogger('logging_system.errors')

# Thread local storage for request context
_thread_locals = threading.local()


class LoggingService:
    """Service for centralized logging functionality"""
    
    @staticmethod
    def set_request_context(request_id=None, user_id=None, session_id=None, ip=None):
        """Store request context in thread local storage"""
        if not hasattr(_thread_locals, 'logging_context'):
            _thread_locals.logging_context = {}
        
        ctx = _thread_locals.logging_context
        
        if request_id:
            ctx['request_id'] = request_id
        if user_id:
            ctx['user_id'] = user_id
        if session_id:
            ctx['session_id'] = session_id
        if ip:
            ctx['ip'] = ip
    
    @staticmethod
    def get_request_context():
        """Get the current request context from thread local storage"""
        if not hasattr(_thread_locals, 'logging_context'):
            return {}
        return _thread_locals.logging_context.copy()
    
    @staticmethod
    def clear_request_context():
        """Clear request context from thread local storage"""
        if hasattr(_thread_locals, 'logging_context'):
            del _thread_locals.logging_context
    
    @staticmethod
    def get_log_data(**kwargs):
        """Get standard log data enriched with request context"""
        data = LoggingService.get_request_context()
        
        # Add timestamp
        data['timestamp'] = datetime.utcnow().isoformat()
        
        # Add environment if configured
        env = getattr(settings, 'ENVIRONMENT', 'development')
        data['environment'] = env
        
        # Add application name if configured
        app_name = getattr(settings, 'APPLICATION_NAME', 'Social_Cube')
        data['application'] = app_name
        
        # Add additional data
        data.update(kwargs)
        
        return data
    
    @staticmethod
    def request_log(method, path, status_code, duration, ip=None, user_agent=None, 
                    params=None, data=None, user_id=None, extra=None):
        """Log HTTP request information"""
        log_data = LoggingService.get_log_data(
            event_type='http_request',
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration,
            ip=ip,
            user_agent=user_agent,
            user_id=user_id
        )
        
        # Add request parameters if configured to log them
        if getattr(settings, 'LOG_REQUEST_PARAMS', False) and params:
            # Filter sensitive parameters
            sensitive_params = getattr(settings, 'SENSITIVE_PARAM_NAMES', 
                                     ['password', 'token', 'secret', 'key'])
            filtered_params = {}
            
            for key, value in params.items():
                if any(s in key.lower() for s in sensitive_params):
                    filtered_params[key] = '*****'
                else:
                    filtered_params[key] = value
                    
            log_data['request_params'] = filtered_params
        
        # Add request body if configured to log it
        if getattr(settings, 'LOG_REQUEST_BODY', False) and data:
            # Try to mask sensitive data
            if isinstance(data, dict):
                sensitive_fields = getattr(settings, 'SENSITIVE_FIELD_NAMES', 
                                         ['password', 'token', 'secret', 'key'])
                filtered_data = {}
                
                for key, value in data.items():
                    if any(s in key.lower() for s in sensitive_fields):
                        filtered_data[key] = '*****'
                    else:
                        filtered_data[key] = value
                        
                log_data['request_body'] = filtered_data
            else:
                # Just note we received data but don't log it
                log_data['request_body_size'] = len(str(data))
        
        # Add extra data
        if extra:
            log_data.update(extra)
            
        # Log as JSON
        request_logger.info(json.dumps(log_data))
        
        # Log specific status codes to error logger
        if status_code >= 400:
            log_level = logging.ERROR if status_code >= 500 else logging.WARNING
            error_logger.log(log_level, f"HTTP {status_code}: {method} {path}", extra=log_data)
    
    @staticmethod
    def audit_log(action, entity_type=None, entity_id=None, user_id=None, 
                 message=None, changes=None, extra=None):
        """Log audit events for security and compliance tracking"""
        log_data = LoggingService.get_log_data(
            event_type='audit',
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
            user_id=user_id
        )
        
        # Add details about changes
        if changes:
            log_data['changes'] = changes
            
        # Add extra data
        if extra:
            log_data.update(extra)
            
        # Log as JSON
        audit_logger.info(json.dumps(log_data))
    
    @staticmethod
    def error_log(message, exc_info=None, level='error', context=None):
        """Log application errors with context"""
        log_data = LoggingService.get_log_data(
            event_type='application_error',
            message=message
        )
        
        # Add context
        if context:
            log_data['context'] = context
            
        # Map string level to logging level
        log_level = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL
        }.get(level.lower(), logging.ERROR)
        
        # Log with appropriate level
        error_logger.log(log_level, message, exc_info=exc_info, extra=log_data)
    
    @staticmethod
    def generate_request_id():
        """Generate a unique request ID"""
        return str(uuid.uuid4())