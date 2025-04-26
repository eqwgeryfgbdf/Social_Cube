from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
import environ
import os
import logging

# Initialize environment variables
env = environ.Env()

# Get logger
logger = logging.getLogger(__name__)

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
        if not self.id or kwargs.get('update_fields') and 'token' in kwargs.get('update_fields'):
            # Only update token if it's not empty and doesn't look encrypted
            if self.token and len(self.token) < 100:  # Simple check for likely unencrypted tokens
                key = env('BOT_TOKEN_KEY')
                f = Fernet(key.encode() if isinstance(key, str) else key)
                self.token = f.encrypt(self.token.encode()).decode()
        
        super().save(*args, **kwargs)
    
    def start(self):
        """Start the bot instance"""
        from bot_management.discord_bot.service import bot_manager
        
        success = bot_manager.start_bot(self.id)
        
        if success:
            BotLog.objects.create(
                bot=self,
                event_type='BOT_START_REQUESTED',
                description=f'Bot start requested via model method'
            )
            
        return success
    
    def stop(self):
        """Stop the bot instance"""
        from bot_management.discord_bot.service import bot_manager
        
        success = bot_manager.stop_bot(self.id)
        
        if success:
            BotLog.objects.create(
                bot=self,
                event_type='BOT_STOP_REQUESTED',
                description=f'Bot stop requested via model method'
            )
            
        return success
    
    def restart(self):
        """Restart the bot instance"""
        from bot_management.discord_bot.service import bot_manager
        
        success = bot_manager.restart_bot(self.id)
        
        if success:
            BotLog.objects.create(
                bot=self,
                event_type='BOT_RESTART_REQUESTED',
                description=f'Bot restart requested via model method'
            )
            
        return success
    
    def get_status(self):
        """Get the bot's current status"""
        from bot_management.discord_bot.service import bot_manager
        
        return bot_manager.get_bot_status(self.id)

class BotLog(models.Model):
    """Model for logging bot activity"""
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='logs')
    event_type = models.CharField(max_length=50)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.bot.name} - {self.event_type} - {self.timestamp}"