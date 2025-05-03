"""
Models for the bug tracking application.

These models define the data structures for tracking and managing bugs
in the Social Cube application.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Bug(models.Model):
    """
    Model representing a bug or issue in the application.
    """
    # Severity choices
    SEVERITY_LOW = 'low'
    SEVERITY_MEDIUM = 'medium'
    SEVERITY_HIGH = 'high'
    SEVERITY_CRITICAL = 'critical'
    
    SEVERITY_CHOICES = [
        (SEVERITY_LOW, _('Low')),
        (SEVERITY_MEDIUM, _('Medium')),
        (SEVERITY_HIGH, _('High')),
        (SEVERITY_CRITICAL, _('Critical')),
    ]
    
    # Status choices
    STATUS_NEW = 'new'
    STATUS_TRIAGED = 'triaged'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_RESOLVED = 'resolved'
    STATUS_CLOSED = 'closed'
    STATUS_REOPENED = 'reopened'
    
    STATUS_CHOICES = [
        (STATUS_NEW, _('New')),
        (STATUS_TRIAGED, _('Triaged')),
        (STATUS_IN_PROGRESS, _('In Progress')),
        (STATUS_RESOLVED, _('Resolved')),
        (STATUS_CLOSED, _('Closed')),
        (STATUS_REOPENED, _('Reopened')),
    ]
    
    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField(_('Description'))
    
    # Classification fields
    severity = models.CharField(
        _('Severity'),
        max_length=10,
        choices=SEVERITY_CHOICES,
        default=SEVERITY_MEDIUM
    )
    status = models.CharField(
        _('Status'),
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )
    
    # Relations
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_bugs'
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_bugs'
    )
    error_log = models.ForeignKey(
        'logging_system.ErrorLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bugs',
        help_text=_('Associated error log entry that triggered this bug report')
    )
    
    # Field to track count of occurrences
    occurrence_count = models.PositiveIntegerField(_('Occurrence Count'), default=1, help_text=_('Number of times this error has occurred'))
    
    # Fields for better error classification
    error_hash = models.CharField(_('Error Hash'), max_length=64, blank=True, help_text=_('Hash of the error signature for deduplication'))
    error_type = models.CharField(_('Error Type'), max_length=100, blank=True, help_text=_('Type of error (e.g., SyntaxError, TypeError)'))
    error_location = models.CharField(_('Error Location'), max_length=255, blank=True, help_text=_('File or module where the error occurred'))
    error_line = models.PositiveIntegerField(_('Error Line'), null=True, blank=True, help_text=_('Line number where the error occurred'))
    
    # Metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    resolved_at = models.DateTimeField(_('Resolved At'), null=True, blank=True)
    closed_at = models.DateTimeField(_('Closed At'), null=True, blank=True)
    
    # Additional information
    environment = models.CharField(_('Environment'), max_length=100, blank=True)
    browser = models.CharField(_('Browser'), max_length=100, blank=True)
    operating_system = models.CharField(_('Operating System'), max_length=100, blank=True)
    stacktrace = models.TextField(_('Stack Trace'), blank=True)
    steps_to_reproduce = models.TextField(_('Steps to Reproduce'), blank=True)
    expected_behavior = models.TextField(_('Expected Behavior'), blank=True)
    actual_behavior = models.TextField(_('Actual Behavior'), blank=True)
    
    # Tags for categorization
    tags = models.ManyToManyField('BugTag', blank=True, related_name='bugs')
    
    class Meta:
        verbose_name = _('Bug')
        verbose_name_plural = _('Bugs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['severity']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-update resolved_at when status changes to resolved
        if self.status == self.STATUS_RESOLVED and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        # Auto-update closed_at when status changes to closed
        if self.status == self.STATUS_CLOSED and not self.closed_at:
            self.closed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('bug_tracking:bug_detail', kwargs={'pk': self.pk})


class BugComment(models.Model):
    """
    Model representing a comment on a bug.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bug = models.ForeignKey(
        Bug,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bug_comments'
    )
    content = models.TextField(_('Content'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    # Allow comments to be marked as internal for team-only discussions
    is_internal = models.BooleanField(_('Internal Comment'), default=False)
    
    class Meta:
        verbose_name = _('Bug Comment')
        verbose_name_plural = _('Bug Comments')
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author or 'Unknown'} on {self.bug}"


class BugAttachment(models.Model):
    """
    Model representing a file attachment for a bug.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bug = models.ForeignKey(
        Bug,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bug_attachments'
    )
    file = models.FileField(_('File'), upload_to='bug_attachments/%Y/%m/')
    filename = models.CharField(_('Filename'), max_length=255)
    content_type = models.CharField(_('Content Type'), max_length=100)
    size = models.PositiveIntegerField(_('Size (bytes)'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Bug Attachment')
        verbose_name_plural = _('Bug Attachments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} ({self.bug})"
    
    def save(self, *args, **kwargs):
        # Auto-populate filename if not provided
        if not self.filename and self.file:
            self.filename = self.file.name.split('/')[-1]
        
        # Auto-calculate size if not provided
        if not self.size and self.file:
            self.size = self.file.size
        
        super().save(*args, **kwargs)


class BugTag(models.Model):
    """
    Model representing a tag for categorizing bugs.
    """
    name = models.CharField(_('Name'), max_length=50, unique=True)
    color = models.CharField(_('Color'), max_length=7, default='#FFFFFF')
    description = models.CharField(_('Description'), max_length=200, blank=True)
    
    class Meta:
        verbose_name = _('Bug Tag')
        verbose_name_plural = _('Bug Tags')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class BugHistory(models.Model):
    """
    Model representing the history of changes to a bug.
    """
    # Action types
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_COMMENT = 'comment'
    ACTION_ATTACH = 'attach'
    ACTION_ASSIGN = 'assign'
    ACTION_STATUS_CHANGE = 'status_change'
    
    ACTION_CHOICES = [
        (ACTION_CREATE, _('Created')),
        (ACTION_UPDATE, _('Updated')),
        (ACTION_COMMENT, _('Commented')),
        (ACTION_ATTACH, _('Attached File')),
        (ACTION_ASSIGN, _('Assigned')),
        (ACTION_STATUS_CHANGE, _('Status Changed')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bug = models.ForeignKey(
        Bug,
        on_delete=models.CASCADE,
        related_name='history'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bug_history'
    )
    action = models.CharField(
        _('Action'),
        max_length=20,
        choices=ACTION_CHOICES
    )
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    
    # Store changes as JSON
    changes = models.JSONField(_('Changes'), null=True, blank=True)
    
    # Related object references
    comment = models.ForeignKey(
        BugComment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_entries'
    )
    attachment = models.ForeignKey(
        BugAttachment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_entries'
    )
    
    class Meta:
        verbose_name = _('Bug History')
        verbose_name_plural = _('Bug Histories')
        ordering = ['-timestamp']
    
    def __str__(self):
        action_display = dict(self.ACTION_CHOICES).get(self.action, self.action)
        return f"{self.bug}: {action_display} by {self.user or 'System'}"


class BugSubscription(models.Model):
    """
    Model for users to subscribe to bug notifications.
    """
    bug = models.ForeignKey(
        Bug,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bug_subscriptions'
    )
    created_at = models.DateTimeField(_('Subscribed At'), auto_now_add=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(_('Email Notifications'), default=True)
    in_app_notifications = models.BooleanField(_('In-app Notifications'), default=True)
    
    class Meta:
        verbose_name = _('Bug Subscription')
        verbose_name_plural = _('Bug Subscriptions')
        unique_together = ['bug', 'user']
    
    def __str__(self):
        return f"{self.user} subscribed to {self.bug}"


class BugNotification(models.Model):
    """
    Model for bug-related notifications sent to users.
    """
    # Notification types
    TYPE_NEW_BUG = 'new_bug'
    TYPE_STATUS_CHANGE = 'status_change'
    TYPE_COMMENT = 'comment'
    TYPE_ASSIGNMENT = 'assignment'
    TYPE_MENTION = 'mention'
    
    NOTIFICATION_TYPES = [
        (TYPE_NEW_BUG, _('New Bug')),
        (TYPE_STATUS_CHANGE, _('Status Change')),
        (TYPE_COMMENT, _('Comment')),
        (TYPE_ASSIGNMENT, _('Assignment')),
        (TYPE_MENTION, _('Mention')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bug_notifications'
    )
    bug = models.ForeignKey(
        Bug,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        _('Notification Type'),
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(_('Title'), max_length=255)
    message = models.TextField(_('Message'))
    is_read = models.BooleanField(_('Is Read'), default=False)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    # Optional related objects
    related_comment = models.ForeignKey(
        BugComment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    class Meta:
        verbose_name = _('Bug Notification')
        verbose_name_plural = _('Bug Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"Notification for {self.user}: {self.title}"
    
    def mark_as_read(self):
        """
        Mark this notification as read.
        """
        self.is_read = True
        self.save(update_fields=['is_read'])


class NotificationPreference(models.Model):
    """
    User preferences for bug notifications.
    """
    # Frequency choices for email digests
    FREQUENCY_NEVER = 'never'
    FREQUENCY_IMMEDIATELY = 'immediately'
    FREQUENCY_DAILY = 'daily'
    FREQUENCY_WEEKLY = 'weekly'
    
    FREQUENCY_CHOICES = [
        (FREQUENCY_NEVER, _('Never')),
        (FREQUENCY_IMMEDIATELY, _('Immediately')),
        (FREQUENCY_DAILY, _('Daily Digest')),
        (FREQUENCY_WEEKLY, _('Weekly Digest')),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bug_notification_preferences'
    )
    
    # Web notification preferences
    web_notify_new_bugs = models.BooleanField(_('Web - New Bugs'), default=True)
    web_notify_status_changes = models.BooleanField(_('Web - Status Changes'), default=True)
    web_notify_comments = models.BooleanField(_('Web - Comments'), default=True)
    web_notify_assignments = models.BooleanField(_('Web - Assignments'), default=True)
    web_notify_mentions = models.BooleanField(_('Web - Mentions'), default=True)
    
    # Email notification preferences
    email_notify_new_bugs = models.BooleanField(_('Email - New Bugs'), default=False)
    email_notify_status_changes = models.BooleanField(_('Email - Status Changes'), default=False)
    email_notify_comments = models.BooleanField(_('Email - Comments'), default=False)
    email_notify_assignments = models.BooleanField(_('Email - Assignments'), default=True)
    email_notify_mentions = models.BooleanField(_('Email - Mentions'), default=True)
    
    # Email digest settings
    email_digest_frequency = models.CharField(
        _('Email Digest Frequency'),
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default=FREQUENCY_DAILY
    )
    
    # Last digest sent timestamp
    last_digest_sent = models.DateTimeField(_('Last Digest Sent'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Notification Preference')
        verbose_name_plural = _('Notification Preferences')
    
    def __str__(self):
        return f"Notification preferences for {self.user}"
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """
        Get existing preferences or create with defaults for a user.
        """
        prefs, created = cls.objects.get_or_create(user=user)
        return prefs