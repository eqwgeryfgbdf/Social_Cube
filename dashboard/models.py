from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.serializers.json import DjangoJSONEncoder

class Bot(models.Model):
    """Discord bot model."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    token = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='bot_avatars/', blank=True, null=True)
    prefix = models.CharField(max_length=10, default='!')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Command(models.Model):
    """Discord bot command model."""
    CATEGORY_CHOICES = [
        ('moderation', 'Moderation'),
        ('utility', 'Utility'),
        ('fun', 'Fun'),
        ('music', 'Music'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=50)
    description = models.TextField()
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='commands')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='utility')
    is_enabled = models.BooleanField(default=True)
    syntax = models.CharField(max_length=255, blank=True)
    options = models.TextField(blank=True)  # JSON field to store command options
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('name', 'bot')
    
    def __str__(self):
        return f"{self.bot.name} - {self.name}"

class CommandExecution(models.Model):
    """Record of command execution."""
    command = models.ForeignKey(Command, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=20)
    user_name = models.CharField(max_length=100)
    server_id = models.CharField(max_length=20)
    server_name = models.CharField(max_length=100)
    channel_id = models.CharField(max_length=20)
    parameters = models.TextField(blank=True)  # JSON field to store parameters
    is_success = models.BooleanField(default=True)
    executed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.command.name} by {self.user_name} in {self.server_name}"


class UserSettings(models.Model):
    """Model for storing user-specific settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # UI preferences
    enable_dark_mode = models.BooleanField(default=False)
    dashboard_layout = models.CharField(
        max_length=20, 
        choices=[
            ('default', 'Default'),
            ('compact', 'Compact'),
            ('expanded', 'Expanded')
        ],
        default='default'
    )
    
    # Notification settings
    email_notifications = models.BooleanField(default=True)
    discord_notifications = models.BooleanField(default=True)
    
    # Notification types
    notify_on_bot_status_change = models.BooleanField(default=True)
    notify_on_server_join = models.BooleanField(default=True)
    notify_on_command_usage = models.BooleanField(default=False)
    notify_on_error = models.BooleanField(default=True)
    
    # Custom preferences stored as JSON
    preferences = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Settings for {self.user.username}"
    
    def get_preference(self, key, default=None):
        """Get a custom preference by key"""
        return self.preferences.get(key, default)
    
    def set_preference(self, key, value):
        """Set a custom preference"""
        if not self.preferences:
            self.preferences = {}
        
        self.preferences[key] = value
        self.save(update_fields=['preferences', 'updated_at'])
        
        return True
    
    def delete_preference(self, key):
        """Delete a custom preference"""
        if not self.preferences or key not in self.preferences:
            return False
        
        del self.preferences[key]
        self.save(update_fields=['preferences', 'updated_at'])
        
        return True

@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """Create UserSettings when a new User is created"""
    if created:
        UserSettings.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_settings(sender, instance, **kwargs):
    """Ensure UserSettings is saved when User is saved"""
    try:
        instance.settings.save()
    except UserSettings.DoesNotExist:
        UserSettings.objects.create(user=instance)