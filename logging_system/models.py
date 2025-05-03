import json
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

User = get_user_model()


class RequestLog(models.Model):
    """
    Logs HTTP requests to the application.
    """
    # Request metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    status_code = models.IntegerField()
    duration = models.FloatField(help_text="Request duration in seconds")
    
    # User information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Request data
    query_params = models.JSONField(default=dict, blank=True)
    request_body = models.JSONField(default=dict, blank=True)
    response_size = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = _("Request Log")
        verbose_name_plural = _("Request Logs")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['path']),
            models.Index(fields=['status_code']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code} at {self.timestamp}"
    
    def colored_status(self):
        """Return a colored status code representation"""
        if self.status_code < 300:
            color = 'green'
        elif self.status_code < 400:
            color = 'blue'
        elif self.status_code < 500:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color: {};">{}</span>', color, self.status_code)


class AuditLog(models.Model):
    """
    Logs user actions and system changes for audit purposes.
    """
    ACTION_TYPES = (
        ('create', _('Create')),
        ('update', _('Update')),
        ('delete', _('Delete')),
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('auth_success', _('Authentication Success')),
        ('auth_failure', _('Authentication Failure')),
        ('permission', _('Permission Change')),
        ('admin', _('Admin Action')),
        ('other', _('Other')),
    )
    
    # Audit metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Entity information
    entity_type = models.CharField(max_length=100, blank=True)
    entity_id = models.CharField(max_length=100, blank=True)
    entity_name = models.CharField(max_length=255, blank=True)
    
    # Context information
    description = models.TextField()
    changes = models.JSONField(default=dict, blank=True)
    additional_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['entity_type']),
        ]

    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"
    
    @property
    def short_description(self):
        """Return a truncated description for display purposes"""
        if len(self.description) > 100:
            return f"{self.description[:97]}..."
        return self.description


class ErrorLog(models.Model):
    """
    Logs application errors and exceptions.
    """
    LOG_LEVELS = (
        ('DEBUG', _('Debug')),
        ('INFO', _('Info')),
        ('WARNING', _('Warning')),
        ('ERROR', _('Error')),
        ('CRITICAL', _('Critical')),
    )
    
    # Error metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=10, choices=LOG_LEVELS, default='ERROR')
    logger_name = models.CharField(max_length=100)
    
    # Error details
    message = models.TextField()
    exception_type = models.CharField(max_length=255, blank=True)
    traceback = models.TextField(blank=True)
    
    # Context information
    request_path = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    additional_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = _("Error Log")
        verbose_name_plural = _("Error Logs")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['level']),
            models.Index(fields=['logger_name']),
            models.Index(fields=['exception_type']),
        ]

    def __str__(self):
        return f"{self.level} at {self.timestamp}: {self.message[:50]}"
    
    def colored_level(self):
        """Return a colored log level representation"""
        colors = {
            'DEBUG': 'grey',
            'INFO': 'blue',
            'WARNING': 'orange',
            'ERROR': 'red',
            'CRITICAL': 'purple'
        }
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                           colors.get(self.level, 'black'), self.level)