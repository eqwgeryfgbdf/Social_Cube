"""
Decorators for the bug tracking application.

These decorators provide common functionality for views and API endpoints.
"""
import functools
import logging
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save, post_delete, m2m_changed

from bug_tracking.models import Bug, BugHistory, BugComment
from bug_tracking.utils import (
    notify_new_bug, notify_bug_status_change, notify_bug_assignment, notify_bug_comment
)

logger = logging.getLogger(__name__)


def track_bug_changes(view_func):
    """
    Decorator to track changes to a bug and create history entries and notifications.
    
    This decorator should be applied to views that modify bugs, like status updates
    or assignment changes.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Find the bug ID from kwargs
        bug_id = kwargs.get('pk')
        
        if not bug_id:
            # If no bug ID is found, just call the view
            return view_func(request, *args, **kwargs)
        
        try:
            # Get the bug before changes
            bug_before = Bug.objects.get(pk=bug_id)
            old_status = bug_before.status
            old_assignee = bug_before.assignee
            
            # Call the view function
            response = view_func(request, *args, **kwargs)
            
            # Get the bug after changes
            bug_after = Bug.objects.get(pk=bug_id)
            new_status = bug_after.status
            new_assignee = bug_after.assignee
            
            # Check if status changed
            if old_status != new_status:
                # Create history entry
                BugHistory.objects.create(
                    bug=bug_after,
                    user=request.user,
                    action=BugHistory.ACTION_STATUS_CHANGE,
                    changes={
                        'old_status': old_status,
                        'new_status': new_status
                    }
                )
                
                # Send notifications
                notify_bug_status_change(bug_after, old_status, new_status, request.user)
            
            # Check if assignee changed
            if old_assignee != new_assignee:
                # Create history entry
                BugHistory.objects.create(
                    bug=bug_after,
                    user=request.user,
                    action=BugHistory.ACTION_ASSIGN,
                    changes={
                        'old_assignee': old_assignee.username if old_assignee else None,
                        'new_assignee': new_assignee.username if new_assignee else None
                    }
                )
                
                # Send notifications
                notify_bug_assignment(bug_after, old_assignee, new_assignee, request.user)
            
            return response
            
        except Bug.DoesNotExist:
            # If bug doesn't exist, just call the view
            return view_func(request, *args, **kwargs)
        except Exception as e:
            # Log any errors but still call the view
            logger.error(f"Error in track_bug_changes decorator: {e}")
            return view_func(request, *args, **kwargs)
            
    return wrapper


def connect_notification_signals():
    """
    Connect signals for automatic notifications on model changes.
    
    This function should be called in the app's ready() method.
    """
    # Connect signal for new bugs
    post_save.connect(_bug_post_save, sender=Bug)
    
    # Connect signal for new comments
    post_save.connect(_comment_post_save, sender=BugComment)


def _bug_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Bug post_save.
    
    Args:
        sender: The model class (Bug)
        instance: The saved Bug instance
        created: Boolean indicating if this is a new instance
    """
    if created:
        # New bug created, send notification
        notify_new_bug(instance)


def _comment_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for BugComment post_save.
    
    Args:
        sender: The model class (BugComment)
        instance: The saved BugComment instance
        created: Boolean indicating if this is a new instance
    """
    if created:
        # New comment created, send notification
        notify_bug_comment(instance)