from django.db import models
from django.contrib.auth.models import User
from bot_management.models import Bot

class ApiKey(models.Model):
    """Model for API authentication"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    key = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"

class ApiLog(models.Model):
    """Model for logging API requests"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_logs', null=True, blank=True)
    api_key = models.ForeignKey(ApiKey, on_delete=models.SET_NULL, related_name='logs', null=True, blank=True)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)  # GET, POST, PUT, DELETE, etc.
    status_code = models.IntegerField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.endpoint} - {self.method} - {self.status_code}"
