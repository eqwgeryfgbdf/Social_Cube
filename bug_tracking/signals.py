"""
Signal handlers for the bug tracking application.

These signals automate various aspects of the bug tracking workflow,
such as creating bugs from error logs and sending notifications.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from logging_system.models import ErrorLog
from bug_tracking.models import Bug, BugComment, BugHistory, BugSubscription

User = get_user_model()
logger = logging.getLogger('bug_tracking')


@receiver(post_save, sender=ErrorLog)
def create_bug_from_error_log(sender, instance, created, **kwargs):
    """
    Automatically create a bug from a critical error log.
    
    This signal handler creates a new bug entry when a critical error
    is logged in the system.
    """
    # Only create bugs for newly created, critical error logs
    if not created or instance.level != 'CRITICAL':
        return
    
    # Check if a bug already exists for this error log
    if Bug.objects.filter(error_log=instance).exists():
        return
    
    try:
        # Get a system admin user as the reporter
        admin_user = User.objects.filter(is_staff=True, is_active=True).first()
        
        # Create bug with error details
        bug = Bug.objects.create(
            title=f"Critical Error: {instance.message[:100]}",
            description=f"Automatically generated from error log {instance.id}.\n\n{instance.message}",
            severity=Bug.SEVERITY_HIGH,
            status=Bug.STATUS_NEW,
            reporter=admin_user,
            error_log=instance,
            stacktrace=instance.traceback,
            environment=instance.context.get('environment', ''),
            browser=instance.context.get('browser', ''),
            operating_system=instance.context.get('os', '')
        )
        
        # Record in history
        BugHistory.objects.create(
            bug=bug,
            action=BugHistory.ACTION_CREATE,
            changes={'source': 'error_log', 'error_log_id': str(instance.id)}
        )
        
        logger.info(f"Created bug #{bug.id} from error log #{instance.id}")
    except Exception as e:
        logger.error(f"Failed to create bug from error log #{instance.id}: {str(e)}")


@receiver(post_save, sender=BugComment)
def notify_bug_subscribers_of_comment(sender, instance, created, **kwargs):
    """
    Notify subscribers when a new comment is added to a bug.
    """
    if not created:
        return
    
    bug = instance.bug
    commenter = instance.author
    
    # Skip notification for internal comments if the user isn't staff
    if instance.is_internal and (not commenter or not commenter.is_staff):
        return
    
    try:
        from realtime.consumers import send_notification
        
        # Get all subscribers except the comment author
        subscriptions = BugSubscription.objects.filter(bug=bug)
        if commenter:
            subscriptions = subscriptions.exclude(user=commenter)
        
        for subscription in subscriptions:
            # Only notify if in-app notifications are enabled
            if subscription.in_app_notifications:
                notification_data = {
                    'type': 'bug_comment',
                    'bug_id': str(bug.id),
                    'bug_title': bug.title,
                    'comment_id': str(instance.id),
                    'comment_excerpt': instance.content[:100] + ('...' if len(instance.content) > 100 else ''),
                    'comment_author': commenter.username if commenter else 'System',
                    'timestamp': instance.created_at.isoformat()
                }
                
                send_notification(subscription.user.id, notification_data)
        
        logger.info(f"Sent comment notifications for bug #{bug.id} to {subscriptions.count()} subscribers")
    except ImportError:
        logger.warning("Realtime notification module not available")
    except Exception as e:
        logger.error(f"Failed to send comment notifications for bug #{bug.id}: {str(e)}")


@receiver(post_save, sender=Bug)
def notify_bug_status_change(sender, instance, **kwargs):
    """
    Notify subscribers when a bug's status changes.
    """
    # Skip if this is a new bug
    if kwargs.get('created', False):
        return
    
    # Get the previous state from history
    previous_status = None
    latest_status_change = BugHistory.objects.filter(
        bug=instance,
        action=BugHistory.ACTION_STATUS_CHANGE
    ).order_by('-timestamp').first()
    
    if latest_status_change and latest_status_change.changes:
        previous_status = latest_status_change.changes.get('old_status')
    
    # Skip if status hasn't changed or can't determine
    if not previous_status or previous_status == instance.status:
        return
    
    try:
        from realtime.consumers import send_notification
        
        # Get all subscribers
        subscriptions = BugSubscription.objects.filter(bug=instance)
        
        # Get the user who made the change
        changer = latest_status_change.user.username if latest_status_change.user else 'System'
        
        for subscription in subscriptions:
            # Only notify if in-app notifications are enabled
            if subscription.in_app_notifications:
                notification_data = {
                    'type': 'bug_status_change',
                    'bug_id': str(instance.id),
                    'bug_title': instance.title,
                    'old_status': previous_status,
                    'new_status': instance.status,
                    'changed_by': changer,
                    'timestamp': latest_status_change.timestamp.isoformat()
                }
                
                send_notification(subscription.user.id, notification_data)
        
        logger.info(f"Sent status change notifications for bug #{instance.id} to {subscriptions.count()} subscribers")
    except ImportError:
        logger.warning("Realtime notification module not available")
    except Exception as e:
        logger.error(f"Failed to send status change notifications for bug #{instance.id}: {str(e)}")


@receiver(post_save, sender=Bug)
def notify_bug_assignment(sender, instance, **kwargs):
    """
    Notify when a bug is assigned to a user.
    """
    # Skip if this is a new bug
    if kwargs.get('created', False):
        return
    
    # Get the previous state from history
    previous_assignee = None
    latest_assignment = BugHistory.objects.filter(
        bug=instance,
        action=BugHistory.ACTION_ASSIGN
    ).order_by('-timestamp').first()
    
    if latest_assignment and latest_assignment.changes:
        previous_assignee = latest_assignment.changes.get('old_assignee')
    
    # Skip if assignee hasn't changed or can't determine
    current_assignee = instance.assignee.username if instance.assignee else None
    if previous_assignee == current_assignee:
        return
    
    try:
        from realtime.consumers import send_notification
        
        # If there's a new assignee, notify them
        if instance.assignee:
            notification_data = {
                'type': 'bug_assigned',
                'bug_id': str(instance.id),
                'bug_title': instance.title,
                'assigned_by': latest_assignment.user.username if latest_assignment and latest_assignment.user else 'System',
                'timestamp': latest_assignment.timestamp.isoformat() if latest_assignment else instance.updated_at.isoformat()
            }
            
            send_notification(instance.assignee.id, notification_data)
            logger.info(f"Sent assignment notification for bug #{instance.id} to {instance.assignee.username}")
    except ImportError:
        logger.warning("Realtime notification module not available")
    except Exception as e:
        logger.error(f"Failed to send assignment notification for bug #{instance.id}: {str(e)}")