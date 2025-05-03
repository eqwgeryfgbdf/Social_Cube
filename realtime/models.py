from django.db import models
from django.contrib.auth.models import User


class NotificationGroup(models.Model):
    """Model for grouping notifications by category/type"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    color = models.CharField(max_length=20, blank=True, help_text="CSS color class or hex code")
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Notification(models.Model):
    """Model for storing notifications sent to users"""
    TYPE_CHOICES = (
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('system', 'System'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    group = models.ForeignKey(NotificationGroup, on_delete=models.SET_NULL, 
                             null=True, blank=True, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user}"


class UserChannel(models.Model):
    """Model for tracking user's WebSocket connections"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='channels')
    channel_name = models.CharField(max_length=255)
    connected_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    client_info = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ('user', 'channel_name')
        ordering = ['-last_seen']
    
    def __str__(self):
        return f"{self.user.username} - {self.channel_name}"