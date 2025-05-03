"""
API endpoints for client-side error reporting.

These endpoints allow clients to report errors from the browser
or other client applications, which are then logged and converted
to bugs in the bug tracking system.
"""
import json
import logging
from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

from logging_system.models import ErrorLog
from bug_tracking.models import Bug, BugHistory, BugTag
from utils.error_handling.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ClientErrorReportView(views.APIView):
    """
    API endpoint for reporting client-side errors.
    
    This endpoint accepts error reports from client applications and converts
    them into bug reports in the bug tracking system.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests to report errors."""
        try:
            # Validate the error report data
            error_data = self._validate_error_data(request.data)
            
            # Create an error log entry
            error_log = self._create_error_log(request, error_data)
            
            # Create or update a bug report
            bug = self._create_or_update_bug_report(error_log, error_data)
            
            return Response({
                'success': True,
                'message': 'Error reported successfully',
                'bug_id': str(bug.id) if bug else None,
                'error_log_id': str(error_log.id) if error_log else None,
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e),
                'errors': e.details.get('errors', {})
            }, status=e.status_code)
        except Exception as e:
            logger.error(f"Unexpected error in ClientErrorReportView: {str(e)}")
            return Response({
                'success': False,
                'message': 'An unexpected error occurred while processing your error report'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _validate_error_data(self, data):
        """
        Validate the error report data.
        
        Args:
            data: The error report data
            
        Returns:
            The validated error data
            
        Raises:
            ValidationError: If the data is invalid
        """
        errors = {}
        
        # Required fields
        required_fields = ['message', 'source', 'type']
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = [f'{field} is required']
        
        # Validate message
        if 'message' in data and len(data['message']) > 1000:
            errors.setdefault('message', []).append('Message must be 1000 characters or less')
            
        # Validate source URL format
        if 'source' in data and len(data['source']) > 500:
            errors.setdefault('source', []).append('Source URL must be 500 characters or less')
        
        # Validate error type
        if 'type' in data and len(data['type']) > 100:
            errors.setdefault('type', []).append('Error type must be 100 characters or less')
        
        # Check for errors
        if errors:
            raise ValidationError(
                message="Invalid error report data",
                errors=errors
            )
        
        return data
    
    def _create_error_log(self, request, error_data):
        """
        Create an error log entry in the logging system.
        
        Args:
            request: The HTTP request
            error_data: The validated error data
            
        Returns:
            The created ErrorLog instance
        """
        try:
            # Extract traceback if provided
            traceback = error_data.get('stackTrace', '')
            if isinstance(traceback, list):
                traceback = '\n'.join(traceback)
            
            # Prepare additional data
            additional_data = {
                'client_data': {k: v for k, v in error_data.items() if k not in ['message', 'type', 'stackTrace']},
                'browser': request.META.get('HTTP_USER_AGENT', ''),
                'referer': request.META.get('HTTP_REFERER', ''),
                'source': error_data.get('source', 'client-side'),
                'line': error_data.get('line'),
                'column': error_data.get('column')
            }
            
            # Create the error log
            error_log = ErrorLog.objects.create(
                level='ERROR',
                logger_name='client.error',
                message=error_data['message'],
                exception_type=error_data['type'],
                traceback=traceback,
                request_path=error_data.get('source', ''),
                user=request.user if request.user.is_authenticated else None,
                ip_address=self._get_client_ip(request),
                additional_data=additional_data
            )
            return error_log
        except Exception as e:
            logger.error(f"Failed to create error log for client error: {e}")
            return None
    
    def _create_or_update_bug_report(self, error_log, error_data):
        """
        Create a new bug report or update an existing one.
        
        Args:
            error_log: The ErrorLog instance
            error_data: The validated error data
            
        Returns:
            The created or updated Bug instance
        """
        if not error_log:
            return None
            
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
                    # Try to get the client-side bugs tag
                    client_tag, _ = BugTag.objects.get_or_create(
                        name='Client-Side',
                        defaults={'color': '#2196F3', 'description': 'Errors reported from client applications'}
                    )
                    
                    # Create the bug
                    new_bug = Bug.objects.create(
                        title=f"[CLIENT] {error_log.exception_type}: {error_log.message[:100]}",
                        description=f"Bug report from client-side error.\n\n"
                                    f"**Error Type:** {error_log.exception_type}\n\n"
                                    f"**Error Message:** {error_log.message}\n\n"
                                    f"**Source:** {error_data.get('source', 'Unknown')}\n\n"
                                    f"**Line/Column:** {error_data.get('line', 'N/A')}/{error_data.get('column', 'N/A')}\n\n"
                                    f"**Date and Time:** {error_log.timestamp}\n\n"
                                    f"**Browser:** {error_log.additional_data.get('browser', 'Unknown')}\n",
                        status=Bug.STATUS_NEW,
                        severity=Bug.SEVERITY_MEDIUM,  # Default to medium for client-side errors
                        stacktrace=error_log.traceback,
                        environment='client',
                        error_log=error_log,
                        browser=error_log.additional_data.get('browser', '')
                    )
                    
                    # Add the client-side tag
                    new_bug.tags.add(client_tag)
                    
                    # Add a history entry
                    BugHistory.objects.create(
                        bug=new_bug,
                        user=None,  # System-generated
                        action=BugHistory.ACTION_CREATE
                    )
                    
                    return new_bug
        except Exception as e:
            logger.error(f"Failed to create or update bug report for client error: {e}")
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