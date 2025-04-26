from django.db import models
from django.contrib.auth.models import User

class Bot(models.Model):
    """Discord bot model."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    token = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='bot_avatars/', blank=True, null=True)
    prefix = models.CharField(max_length=10, default='!')
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