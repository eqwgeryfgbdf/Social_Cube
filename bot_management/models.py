from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
import environ
import os

# Initialize environment variables
env = environ.Env()

class Bot(models.Model):
    """Model representing a Discord bot"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bots')
    token = models.TextField(help_text='Encrypted bot token')
    client_id = models.CharField(max_length=100, unique=True)
    bot_user_id = models.CharField(max_length=100, unique=True)
    avatar_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Encrypt the token if it's not already encrypted
        if not self.id:  # New bot
            key = env('BOT_TOKEN_KEY')
            f = Fernet(key.encode() if isinstance(key, str) else key)
            self.token = f.encrypt(self.token.encode()).decode()
        super().save(*args, **kwargs)

class BotLog(models.Model):
    """Model for logging bot activity"""
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='logs')
    event_type = models.CharField(max_length=50)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.bot.name} - {self.event_type} - {self.timestamp}"
