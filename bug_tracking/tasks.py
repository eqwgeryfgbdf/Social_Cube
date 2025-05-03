"""
Background tasks for the bug tracking application.

These tasks run asynchronously using Celery.
"""
import logging
from django.utils import timezone
from django.conf import settings

from bug_tracking.utils import send_digest_emails

logger = logging.getLogger(__name__)


def send_notification_digests():
    """
    Send notification digest emails to users.
    
    This function is intended to be run on a schedule (daily) using Celery.
    """
    try:
        logger.info("Starting notification digest email task")
        send_digest_emails()
        logger.info("Completed notification digest email task")
    except Exception as e:
        logger.error(f"Error sending notification digests: {e}")
        if settings.DEBUG:
            raise


def clean_old_notifications():
    """
    Remove old notifications to keep the database size manageable.
    
    This function is intended to be run on a schedule (weekly) using Celery.
    """
    from bug_tracking.models import BugNotification
    
    try:
        # Delete notifications older than 3 months
        cutoff_date = timezone.now() - timezone.timedelta(days=90)
        
        # Get count before deletion for logging
        count = BugNotification.objects.filter(created_at__lt=cutoff_date).count()
        
        # Delete old notifications
        deleted, _ = BugNotification.objects.filter(created_at__lt=cutoff_date).delete()
        
        logger.info(f"Cleaned {deleted} old notifications from before {cutoff_date}")
    except Exception as e:
        logger.error(f"Error cleaning old notifications: {e}")
        if settings.DEBUG:
            raise