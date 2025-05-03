"""
Middleware for automated bug tracking from application errors.

This middleware captures unhandled exceptions, logs them to the logging system,
and automatically creates bug reports in the bug tracking system.
"""
import json
import traceback
import logging
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from logging_system.models import ErrorLog
from bug_tracking.models import Bug, BugHistory, BugTag

logger = logging.getLogger(__name__)


class AutomaticBugReportingMiddleware:
    """
    Middleware that automatically creates bug reports for unhandled exceptions.
    
    This middleware captures unhandled exceptions, logs them to the logging system,
    and automatically creates bug reports in the bug tracking system.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as exc:
            # Let the standard error handling continue after we've captured the error
            self._process_exception(request, exc)
            raise
    
    def process_exception(self, request, exception):
        """Handle the exception by capturing it and creating a bug report."""
        return self._process_exception(request, exception)
    
    def _process_exception(self, request, exception):
        """
        Process an exception by logging it and creating a bug report.
        
        Args:
            request: The HTTP request that caused the exception
            exception: The exception that was raised
            
        Returns:
            None, but creates an ErrorLog entry and a Bug entry if appropriate
        """
        try:
            # Extract exception information
            exc_type = type(exception).__name__
            exc_message = str(exception)
            exc_traceback = traceback.format_exc()
            
            # Log the error to the logging system
            error_log = self._create_error_log(
                request=request,
                exception_type=exc_type,
                message=exc_message,
                traceback=exc_traceback
            )
            
            if error_log and self._should_create_bug_report(error_log):
                # Create or update a bug report
                self._create_or_update_bug_report(error_log, request)
                
            return None
        except Exception as e:
            # Don't let errors in our error handling middleware cause issues
            logger.error(f"Error in AutomaticBugReportingMiddleware: {e}")
            return None
    
    def _create_error_log(self, request, exception_type, message, traceback):
        """
        Create an error log entry in the logging system.
        
        Args:
            request: The HTTP request that caused the exception
            exception_type: The type of the exception
            message: The exception message
            traceback: The exception traceback
            
        Returns:
            The created ErrorLog instance or None if creation failed
        """
        try:
            # Extract additional context from the request
            user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
            ip_address = self._get_client_ip(request)
            
            # Create context data for better debugging
            additional_data = {
                'method': request.method,
                'path': request.path,
                'query_params': dict(request.GET),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'referer': request.META.get('HTTP_REFERER', ''),
            }
            
            # Try to add request body for API requests
            if request.content_type and 'application/json' in request.content_type:
                try:
                    if hasattr(request, 'body') and request.body:
                        additional_data['request_body'] = json.loads(request.body.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    additional_data['request_body'] = '[Error decoding JSON body]'
            
            # Create the error log
            error_log = ErrorLog.objects.create(
                level='ERROR',
                logger_name=__name__,
                message=message,
                exception_type=exception_type,
                traceback=traceback,
                request_path=request.path,
                user=user,
                ip_address=ip_address,
                additional_data=additional_data
            )
            return error_log
        except Exception as e:
            logger.error(f"Failed to create error log: {e}")
            return None
    
    def _should_create_bug_report(self, error_log):
        """
        Determine if a bug report should be created for this error.
        
        Args:
            error_log: The ErrorLog instance
            
        Returns:
            bool: True if a bug report should be created, False otherwise
        """
        # Skip if we're in debug mode and auto bug reporting is disabled
        if settings.DEBUG and not getattr(settings, 'AUTO_BUG_REPORTING_IN_DEBUG', False):
            return False
        
        # Skip errors from specific paths that tend to be noisy
        excluded_paths = getattr(settings, 'BUG_REPORTING_EXCLUDED_PATHS', [])
        if any(error_log.request_path.startswith(path) for path in excluded_paths):
            return False
        
        # Get bug reporting settings
        min_occurrence_threshold = getattr(settings, 'BUG_REPORTING_MIN_OCCURRENCES', 1)
        
        # Check if this error has occurred multiple times
        similar_errors_count = ErrorLog.objects.filter(
            exception_type=error_log.exception_type,
            message=error_log.message
        ).count()
        
        # Only create a bug if we've seen this error enough times
        return similar_errors_count >= min_occurrence_threshold
    
    def _create_or_update_bug_report(self, error_log, request):
        """
        Create a new bug report or update an existing one.
        
        Args:
            error_log: The ErrorLog instance
            request: The HTTP request
            
        Returns:
            The created or updated Bug instance
        """
        try:
            with transaction.atomic():
                # Check if a bug already exists for this type of error
                existing_bug = Bug.objects.filter(
                    error_log__exception_type=error_log.exception_type,
                    error_log__message=error_log.message,
                    status__in=[Bug.STATUS_NEW, Bug.STATUS_TRIAGED, Bug.STATUS_IN_PROGRESS]
                ).first()
                
                if existing_bug:
                    # Update the existing bug
                    existing_bug.stacktrace = error_log.traceback
                    existing_bug.updated_at = timezone.now()
                    existing_bug.error_log = error_log
                    existing_bug.save()
                    
                    # Add a history entry
                    BugHistory.objects.create(
                        bug=existing_bug,
                        user=None,  # System-generated
                        action=BugHistory.ACTION_UPDATE,
                        changes={'error_log_id': str(error_log.id)}
                    )
                    
                    return existing_bug
                else:
                    # Create a new bug
                    # Try to get the automatic bugs tag
                    auto_tag, _ = BugTag.objects.get_or_create(
                        name='Automatic',
                        defaults={'color': '#FF5722', 'description': 'Automatically detected bugs'}
                    )
                    
                    # Create the bug
                    new_bug = Bug.objects.create(
                        title=f"[AUTO] {error_log.exception_type}: {error_log.message[:100]}",
                        description=f"Automatically generated bug report for an unhandled exception.\n\n"
                                    f"**Exception Type:** {error_log.exception_type}\n\n"
                                    f"**Error Message:** {error_log.message}\n\n"
                                    f"**Request Path:** {error_log.request_path}\n\n"
                                    f"**Date and Time:** {error_log.timestamp}\n",
                        status=Bug.STATUS_NEW,
                        severity=Bug.SEVERITY_HIGH,  # Default to high for unhandled exceptions
                        stacktrace=error_log.traceback,
                        environment=self._determine_environment(),
                        error_log=error_log,
                    )
                    
                    # Add the automatic tag
                    new_bug.tags.add(auto_tag)
                    
                    # Add a history entry
                    BugHistory.objects.create(
                        bug=new_bug,
                        user=None,  # System-generated
                        action=BugHistory.ACTION_CREATE
                    )
                    
                    return new_bug
        except Exception as e:
            logger.error(f"Failed to create or update bug report: {e}")
            return None
    
    def _get_client_ip(self, request):
        """Extract the client IP address from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Get the first IP in case of proxy chains
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _determine_environment(self):
        """Determine the current environment (development, staging, production)."""
        if settings.DEBUG:
            return 'development'
        
        # Check for custom environment setting
        return getattr(settings, 'ENVIRONMENT', 'production')