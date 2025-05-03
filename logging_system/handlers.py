import logging
import traceback
from datetime import datetime
from typing import Optional, Dict, Any

from django.db import transaction
from django.utils.module_loading import import_string

# Import ErrorLog model lazily to avoid circular imports
ErrorLog = None


class DatabaseLogHandler(logging.Handler):
    """Custom log handler that writes logs to the database"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_import_path = kwargs.get(
            'model', 'logging_system.models.ErrorLog'
        )
        self._model = None
    
    @property
    def model(self):
        """Lazy import of the ErrorLog model"""
        global ErrorLog
        if ErrorLog is None:
            ErrorLog = import_string(self.model_import_path)
        return ErrorLog
    
    def emit(self, record):
        """
        Save the log record to the database
        """
        if not record:
            return
            
        try:
            # Format the record
            message = self.format(record)
            
            # Extract log record data
            log_data = self._extract_log_data(record)
            
            # Get exception traceback if present
            if record.exc_info:
                log_data['traceback'] = self._format_traceback(record.exc_info)
            
            # Save to database
            with transaction.atomic():
                self.model.objects.create(
                    message=message,
                    level=record.levelname.lower(),
                    **log_data
                )
        except Exception as e:
            # Use standard logging as a fallback to avoid infinite loops
            fallback_logger = logging.getLogger('fallback')
            fallback_logger.error(f"Error in DatabaseLogHandler: {e}")
            fallback_logger.error(f"Original log message: {record.getMessage()}")
    
    def _extract_log_data(self, record) -> Dict[str, Any]:
        """Extract relevant data from a log record"""
        data = {}
        
        # Extract location information
        if hasattr(record, 'pathname') and record.pathname:
            data['location'] = f"{record.pathname}:{record.lineno}"
        
        # Extract request_id from record if available
        if hasattr(record, 'request_id'):
            data['request_id'] = record.request_id
        
        # Extract user from record if available
        if hasattr(record, 'user_id'):
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                data['user'] = User.objects.get(id=record.user_id)
            except User.DoesNotExist:
                pass
        
        # Extract context data
        context = {}
        for key, value in record.__dict__.items():
            # Skip standard log record attributes
            if key not in {
                'args', 'asctime', 'created', 'exc_info', 'exc_text', 
                'filename', 'funcName', 'levelname', 'levelno', 'lineno',
                'module', 'msecs', 'message', 'msg', 'name', 'pathname',
                'process', 'processName', 'relativeCreated', 'thread', 
                'threadName', 'stack_info'
            } and not key.startswith('_'):
                # Try to include the value in context
                try:
                    # Serialize simple values
                    if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        context[key] = value
                    # For other types, just store the string representation
                    else:
                        context[key] = str(value)
                except Exception:
                    # If serialization fails, skip this value
                    pass
        
        if context:
            data['context'] = context
        
        return data
    
    def _format_traceback(self, exc_info) -> str:
        """Format an exception traceback as a string"""
        return ''.join(traceback.format_exception(*exc_info))


class EmailCriticalErrorHandler(logging.Handler):
    """
    Handler that sends emails for critical errors
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recipients = kwargs.get('recipients', [])
        self.subject_prefix = kwargs.get('subject_prefix', '[CRITICAL ERROR]')
    
    def emit(self, record):
        """
        Send an email for the log record
        """
        if not record or record.levelno < logging.CRITICAL:
            return
            
        try:
            from django.core.mail import mail_admins
            
            # Format the record
            message = self.format(record)
            
            # Add traceback if present
            if record.exc_info:
                message += '\n\n' + self._format_traceback(record.exc_info)
            
            # Add timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Customize subject
            subject = f"{self.subject_prefix} {record.getMessage()[:50]}"
            
            # Send email
            mail_admins(subject, message)
        except Exception as e:
            # Use standard logging as a fallback
            fallback_logger = logging.getLogger('fallback')
            fallback_logger.error(f"Error in EmailCriticalErrorHandler: {e}")
    
    def _format_traceback(self, exc_info) -> str:
        """Format an exception traceback as a string"""
        return ''.join(traceback.format_exception(*exc_info))