"""
Utility functions for the bug tracking application.

This module provides helper functions for sending notifications,
generating reports, and other utility tasks.
"""
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from bug_tracking.models import (
    Bug, BugNotification, BugSubscription, NotificationPreference, BugComment
)


def create_bug_notification(bug, user, notification_type, title, message, related_comment=None):
    """
    Create a notification for a bug and send it to the user.
    
    Args:
        bug: The Bug instance.
        user: The User who should receive the notification.
        notification_type: Type of notification (see BugNotification.NOTIFICATION_TYPES)
        title: Title of the notification.
        message: Detailed notification message.
        related_comment: Optional BugComment that triggered this notification.
        
    Returns:
        The created BugNotification instance, or None if notification should be skipped.
    """
    # Skip notification if it's for the same user who triggered the event
    if bug.reporter == user and notification_type == BugNotification.TYPE_NEW_BUG:
        return None
        
    # Get user preferences
    try:
        prefs = NotificationPreference.objects.get(user=user)
    except NotificationPreference.DoesNotExist:
        # Create default preferences
        prefs = NotificationPreference.get_or_create_for_user(user)
    
    # Check if web notification is enabled for this type
    should_notify_web = True
    if notification_type == BugNotification.TYPE_NEW_BUG and not prefs.web_notify_new_bugs:
        should_notify_web = False
    elif notification_type == BugNotification.TYPE_STATUS_CHANGE and not prefs.web_notify_status_changes:
        should_notify_web = False
    elif notification_type == BugNotification.TYPE_COMMENT and not prefs.web_notify_comments:
        should_notify_web = False
    elif notification_type == BugNotification.TYPE_ASSIGNMENT and not prefs.web_notify_assignments:
        should_notify_web = False
    elif notification_type == BugNotification.TYPE_MENTION and not prefs.web_notify_mentions:
        should_notify_web = False
    
    # Create notification if web notifications are enabled
    notification = None
    if should_notify_web:
        notification = BugNotification.objects.create(
            user=user,
            bug=bug,
            notification_type=notification_type,
            title=title,
            message=message,
            related_comment=related_comment
        )
    
    # Check if email notification is enabled for this type
    should_email = True
    if notification_type == BugNotification.TYPE_NEW_BUG and not prefs.email_notify_new_bugs:
        should_email = False
    elif notification_type == BugNotification.TYPE_STATUS_CHANGE and not prefs.email_notify_status_changes:
        should_email = False
    elif notification_type == BugNotification.TYPE_COMMENT and not prefs.email_notify_comments:
        should_email = False
    elif notification_type == BugNotification.TYPE_ASSIGNMENT and not prefs.email_notify_assignments:
        should_email = False
    elif notification_type == BugNotification.TYPE_MENTION and not prefs.email_notify_mentions:
        should_email = False
    
    # Send email if enabled and frequency is immediate
    if should_email and prefs.email_digest_frequency == NotificationPreference.FREQUENCY_IMMEDIATELY:
        send_bug_notification_email(user, bug, notification_type, title, message)
    
    return notification


def notify_bug_subscribers(bug, notification_type, title, message, exclude_user=None, related_comment=None):
    """
    Notify all subscribers of a bug.
    
    Args:
        bug: The Bug instance.
        notification_type: Type of notification (see BugNotification.NOTIFICATION_TYPES)
        title: Title of the notification.
        message: Detailed notification message.
        exclude_user: User to exclude from notifications (typically the triggering user)
        related_comment: Optional BugComment that triggered this notification.
    """
    # Get all subscribers
    subscriptions = BugSubscription.objects.filter(bug=bug)
    
    # Filter out the excluded user
    if exclude_user:
        subscriptions = subscriptions.exclude(user=exclude_user)
    
    # Notify each subscriber
    for subscription in subscriptions:
        # Only notify if in-app notifications are enabled for this subscription
        if subscription.in_app_notifications:
            create_bug_notification(
                bug, subscription.user, notification_type, title, message, related_comment
            )


def notify_new_bug(bug):
    """
    Send notifications for a new bug.
    
    Args:
        bug: The newly created Bug instance.
    """
    title = f"New bug reported: {bug.title}"
    message = f"A new bug has been reported by {bug.reporter or 'Anonymous'}: {bug.title}"
    
    # Notify users who want to be notified of all new bugs
    all_prefs = NotificationPreference.objects.filter(web_notify_new_bugs=True)
    for pref in all_prefs:
        if pref.user != bug.reporter:  # Don't notify the reporter
            create_bug_notification(
                bug, pref.user, BugNotification.TYPE_NEW_BUG, title, message
            )


def notify_bug_status_change(bug, old_status, new_status, changed_by):
    """
    Send notifications when a bug's status changes.
    
    Args:
        bug: The Bug instance.
        old_status: Previous status value.
        new_status: New status value.
        changed_by: User who changed the status.
    """
    old_status_display = dict(Bug.STATUS_CHOICES).get(old_status, old_status)
    new_status_display = dict(Bug.STATUS_CHOICES).get(new_status, new_status)
    
    title = f"Bug status changed: {bug.title}"
    message = f"The status of bug '{bug.title}' has been changed from {old_status_display} to {new_status_display} by {changed_by}."
    
    # Notify subscribers
    notify_bug_subscribers(
        bug, BugNotification.TYPE_STATUS_CHANGE, title, message, exclude_user=changed_by
    )


def notify_bug_assignment(bug, old_assignee, new_assignee, changed_by):
    """
    Send notifications when a bug is assigned to someone.
    
    Args:
        bug: The Bug instance.
        old_assignee: Previous assignee (may be None).
        new_assignee: New assignee (may be None).
        changed_by: User who changed the assignment.
    """
    title = f"Bug assignment updated: {bug.title}"
    
    if new_assignee:
        if old_assignee:
            message = f"Bug '{bug.title}' has been reassigned from {old_assignee} to {new_assignee} by {changed_by}."
        else:
            message = f"Bug '{bug.title}' has been assigned to {new_assignee} by {changed_by}."
            
        # Notify the assignee
        create_bug_notification(
            bug, new_assignee, BugNotification.TYPE_ASSIGNMENT, title, message
        )
    else:
        message = f"Bug '{bug.title}' is no longer assigned to {old_assignee}."
    
    # Notify subscribers
    notify_bug_subscribers(
        bug, BugNotification.TYPE_ASSIGNMENT, title, message, 
        exclude_user=changed_by if changed_by != new_assignee else None
    )


def notify_bug_comment(comment):
    """
    Send notifications when a comment is added to a bug.
    
    Args:
        comment: The BugComment instance.
    """
    bug = comment.bug
    commenter = comment.author or "Anonymous"
    
    title = f"New comment on bug: {bug.title}"
    message = f"{commenter} commented on bug '{bug.title}': {comment.content[:100]}..."
    
    # Notify subscribers
    notify_bug_subscribers(
        bug, BugNotification.TYPE_COMMENT, title, message, 
        exclude_user=comment.author, related_comment=comment
    )
    
    # Check for @mentions in the comment and notify mentioned users
    process_comment_mentions(comment)


def process_comment_mentions(comment):
    """
    Process @mentions in a comment and send notifications.
    
    Args:
        comment: The BugComment instance.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Basic @username mention parsing - could be more sophisticated
    words = comment.content.split()
    mentions = [word[1:] for word in words if word.startswith('@') and len(word) > 1]
    
    # Get unique usernames
    unique_mentions = set(mentions)
    
    # Find users by username
    for username in unique_mentions:
        try:
            user = User.objects.get(username=username)
            
            # Skip if the user is the comment author
            if user == comment.author:
                continue
                
            title = f"You were mentioned in a bug comment: {comment.bug.title}"
            message = f"{comment.author or 'Anonymous'} mentioned you in a comment on bug '{comment.bug.title}': {comment.content[:100]}..."
            
            create_bug_notification(
                comment.bug, user, BugNotification.TYPE_MENTION, title, message, comment
            )
            
        except User.DoesNotExist:
            # Username doesn't exist, skip
            pass


def send_bug_notification_email(user, bug, notification_type, title, message):
    """
    Send a single bug notification email.
    
    Args:
        user: User recipient.
        bug: Related Bug instance.
        notification_type: Type of notification.
        title: Email subject/title.
        message: Email content.
    """
    if not user.email:
        return
        
    subject = f"[Bug Tracker] {title}"
    
    # Render email body using template
    context = {
        'user': user,
        'bug': bug,
        'notification_type': notification_type,
        'title': title,
        'message': message,
        'bug_url': settings.BASE_URL + bug.get_absolute_url() if hasattr(settings, 'BASE_URL') else bug.get_absolute_url(),
    }
    
    # Plain text email
    txt_message = render_to_string('bug_tracking/emails/notification.txt', context)
    
    # HTML email
    html_message = render_to_string('bug_tracking/emails/notification.html', context)
    
    # Send the email
    send_mail(
        subject,
        txt_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=not settings.DEBUG
    )


def send_digest_emails():
    """
    Send digest emails to users according to their preferences.
    This should be run by a scheduled task (e.g., Celery).
    """
    now = timezone.now()
    
    # Find users due for daily digest
    daily_users = NotificationPreference.objects.filter(
        email_digest_frequency=NotificationPreference.FREQUENCY_DAILY,
        last_digest_sent__lt=now - timezone.timedelta(hours=23)  # Give a little buffer
    )
    
    # Find users due for weekly digest
    weekly_users = NotificationPreference.objects.filter(
        email_digest_frequency=NotificationPreference.FREQUENCY_WEEKLY,
        last_digest_sent__lt=now - timezone.timedelta(days=6, hours=23)  # Give a little buffer
    )
    
    # Combine the lists
    users_to_notify = list(daily_users) + list(weekly_users)
    
    # Send digest for each user
    for prefs in users_to_notify:
        user = prefs.user
        
        # Get notifications since last digest
        since = prefs.last_digest_sent or (now - timezone.timedelta(days=7))
        
        # Get notifications based on preferences
        notifications = []
        
        notifications_query = Q(created_at__gt=since)
        
        if prefs.email_notify_new_bugs:
            notifications_query |= Q(notification_type=BugNotification.TYPE_NEW_BUG)
            
        if prefs.email_notify_status_changes:
            notifications_query |= Q(notification_type=BugNotification.TYPE_STATUS_CHANGE)
            
        if prefs.email_notify_comments:
            notifications_query |= Q(notification_type=BugNotification.TYPE_COMMENT)
            
        if prefs.email_notify_assignments:
            notifications_query |= Q(notification_type=BugNotification.TYPE_ASSIGNMENT)
            
        if prefs.email_notify_mentions:
            notifications_query |= Q(notification_type=BugNotification.TYPE_MENTION)
        
        # Get the notifications
        if notifications_query:
            notifications = BugNotification.objects.filter(
                user=user
            ).filter(notifications_query).order_by('-created_at')
        
        # Skip if no notifications
        if not notifications:
            # Update last digest sent time anyway
            prefs.last_digest_sent = now
            prefs.save(update_fields=['last_digest_sent'])
            continue
        
        # Render digest email
        context = {
            'user': user,
            'notifications': notifications,
            'digest_period': 'daily' if prefs.email_digest_frequency == NotificationPreference.FREQUENCY_DAILY else 'weekly',
            'since_date': since,
        }
        
        subject = f"[Bug Tracker] Your {'Daily' if prefs.email_digest_frequency == NotificationPreference.FREQUENCY_DAILY else 'Weekly'} Bug Digest"
        txt_message = render_to_string('bug_tracking/emails/digest.txt', context)
        html_message = render_to_string('bug_tracking/emails/digest.html', context)
        
        # Send the email
        if user.email:
            send_mail(
                subject,
                txt_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=not settings.DEBUG
            )
        
        # Update last digest sent time
        prefs.last_digest_sent = now
        prefs.save(update_fields=['last_digest_sent'])