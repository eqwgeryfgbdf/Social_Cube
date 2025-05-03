from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
import environ
import os
import logging
import json
from django.core.serializers.json import DjangoJSONEncoder

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
    
    def get_guilds(self):
        """Get all guilds for this bot"""
        return self.guilds.all()
        
    def sync_guilds(self):
        """Sync all guilds for this bot with Discord API"""
        from bot_management.discord_bot.service import bot_manager
        
        success = bot_manager.sync_all_guilds(self.id)
        
        if success:
            BotLog.objects.create(
                bot=self,
                event_type='ALL_GUILDS_SYNCED',
                description=f'All guilds synced for bot {self.name}'
            )
            
        return success
        
    def sync_guild(self, guild_id):
        """Sync a specific guild for this bot with Discord API"""
        from bot_management.discord_bot.service import bot_manager
        
        success = bot_manager.sync_guild(self.id, guild_id)
        
        if success:
            guild_name = self.guilds.filter(guild_id=guild_id).first().name if self.guilds.filter(guild_id=guild_id).exists() else 'Unknown'
            BotLog.objects.create(
                bot=self,
                event_type='GUILD_SYNCED',
                description=f'Guild {guild_name} (ID: {guild_id}) synced for bot {self.name}'
            )
            
        return success
        
    def record_error(self, error_type, error_message, context=None):
        """Record an error for this bot and attempt recovery if appropriate"""
        from bot_management.error_handling import log_bot_error, BotErrorHandler
        
        # Log the error
        log_bot_error(
            bot=self,
            error_type=error_type,
            error_message=error_message,
            context=context
        )
        
        # Check if we should attempt recovery
        permanent_errors = [
            'InvalidToken',
            'Unauthorized',
            'RateLimitExceeded',
            'ForbiddenBot',
            'IntentRequired'
        ]
        
        if error_type not in permanent_errors:
            # Attempt recovery for non-permanent errors
            return BotErrorHandler.attempt_recovery(self, error_type)
        else:
            # For permanent errors, mark the bot as inactive if needed
            if error_type in ['InvalidToken', 'Unauthorized', 'ForbiddenBot', 'IntentRequired']:
                self.is_active = False
                self.save(update_fields=['is_active'])
                
                BotLog.objects.create(
                    bot=self,
                    event_type='BOT_DEACTIVATED',
                    description=f'Bot automatically deactivated due to {error_type} error'
                )
            
            return False

class BotLog(models.Model):
    """Model for logging bot activity"""
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='logs')
    event_type = models.CharField(max_length=50)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.bot.name} - {self.event_type} - {self.timestamp}"

class Guild(models.Model):
    """Model representing a Discord server (guild)"""
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='guilds')
    guild_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    icon_url = models.URLField(blank=True, null=True)
    owner_id = models.CharField(max_length=100, null=True)
    member_count = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    region = models.CharField(max_length=50, blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_sync = models.DateTimeField(auto_now=True)
    is_available = models.BooleanField(default=True)
    features = models.JSONField(default=list, encoder=DjangoJSONEncoder)
    
    class Meta:
        unique_together = ('bot', 'guild_id')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.guild_id})"
    
    def get_settings(self):
        """Get guild-specific settings or create default ones if they don't exist"""
        settings, created = GuildSettings.objects.get_or_create(guild=self)
        return settings
    
    def sync_from_discord(self, guild_data):
        """Update guild information from Discord guild data"""
        self.name = guild_data.get('name', self.name)
        self.icon_url = guild_data.get('icon_url', self.icon_url)
        self.owner_id = guild_data.get('owner_id', self.owner_id)
        self.member_count = guild_data.get('member_count', self.member_count)
        self.description = guild_data.get('description', self.description)
        self.region = guild_data.get('region', self.region)
        self.features = guild_data.get('features', self.features)
        self.is_available = True
        self.save()
        
        # Log the sync
        BotLog.objects.create(
            bot=self.bot,
            event_type='GUILD_SYNCED',
            description=f'Guild {self.name} ({self.guild_id}) synchronized with Discord'
        )
        
        return self

    def mark_unavailable(self):
        """Mark the guild as unavailable (bot left or was kicked)"""
        self.is_available = False
        self.save()
        
        # Log the status change
        BotLog.objects.create(
            bot=self.bot,
            event_type='GUILD_UNAVAILABLE',
            description=f'Guild {self.name} ({self.guild_id}) marked as unavailable'
        )
        
    def sync_with_discord(self):
        """Sync this guild with Discord API"""
        from bot_management.discord_bot.service import bot_manager
        
        success = bot_manager.sync_guild(self.bot.id, self.guild_id)
        
        if success:
            BotLog.objects.create(
                bot=self.bot,
                event_type='GUILD_SYNCED',
                description=f'Guild {self.name} ({self.guild_id}) synced with Discord'
            )
            
        return success
        
    def get_channels(self):
        """Get all channels for this guild"""
        return self.channels.all().order_by('position', 'name')

class GuildSettings(models.Model):
    """Model for guild-specific settings"""
    guild = models.OneToOneField(Guild, on_delete=models.CASCADE, related_name='settings')
    
    # Command prefix (for classic commands, if used)
    prefix = models.CharField(max_length=10, default='!')
    
    # Notification settings
    notification_channel_id = models.CharField(max_length=100, blank=True, null=True)
    welcome_message = models.TextField(blank=True, null=True)
    goodbye_message = models.TextField(blank=True, null=True)
    
    # Feature toggles
    enable_welcome_messages = models.BooleanField(default=False)
    enable_goodbye_messages = models.BooleanField(default=False)
    enable_member_tracking = models.BooleanField(default=False)
    enable_moderation = models.BooleanField(default=False)
    
    # Role settings
    admin_role_id = models.CharField(max_length=100, blank=True, null=True)
    moderator_role_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Custom settings (stored as JSON)
    custom_settings = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Settings for {self.guild.name}"
    
    def get_custom_setting(self, key, default=None):
        """Get a custom setting by key"""
        return self.custom_settings.get(key, default)
    
    def set_custom_setting(self, key, value):
        """Set a custom setting"""
        if not self.custom_settings:
            self.custom_settings = {}
        
        self.custom_settings[key] = value
        self.save(update_fields=['custom_settings', 'updated_at'])
        
        return True
    
    def delete_custom_setting(self, key):
        """Delete a custom setting"""
        if not self.custom_settings or key not in self.custom_settings:
            return False
        
        del self.custom_settings[key]
        self.save(update_fields=['custom_settings', 'updated_at'])
        
        return True

class GuildChannel(models.Model):
    """Model representing a Discord channel within a guild"""
    guild = models.ForeignKey(Guild, on_delete=models.CASCADE, related_name='channels')
    channel_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    
    # Channel types (using Discord's channel type IDs)
    TYPES = (
        (0, 'Text'),
        (1, 'DM'),
        (2, 'Voice'),
        (3, 'Group DM'),
        (4, 'Category'),
        (5, 'Announcement'),
        (10, 'Announcement Thread'),
        (11, 'Public Thread'),
        (12, 'Private Thread'),
        (13, 'Stage Voice'),
        (14, 'Directory'),
        (15, 'Forum'),
    )
    
    type = models.IntegerField(choices=TYPES, default=0)
    position = models.IntegerField(default=0)
    category_id = models.CharField(max_length=100, blank=True, null=True)
    is_nsfw = models.BooleanField(default=False)
    topic = models.CharField(max_length=1024, blank=True, null=True)
    last_sync = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('guild', 'channel_id')
        ordering = ['position', 'name']
    
    def __str__(self):
        return f"#{self.name} ({self.get_type_display()})"
    
    def sync_from_discord(self, channel_data):
        """Update channel information from Discord channel data"""
        self.name = channel_data.get('name', self.name)
        self.type = channel_data.get('type', self.type)
        self.position = channel_data.get('position', self.position)
        self.category_id = channel_data.get('parent_id', self.category_id)
        self.is_nsfw = channel_data.get('nsfw', self.is_nsfw)
        self.topic = channel_data.get('topic', self.topic)
        self.save()


class CommandOption(models.Model):
    """Model representing a Discord slash command option"""
    # Option types (using Discord's application command option types)
    TYPES = (
        (1, 'SUB_COMMAND'),
        (2, 'SUB_COMMAND_GROUP'),
        (3, 'STRING'),
        (4, 'INTEGER'),
        (5, 'BOOLEAN'),
        (6, 'USER'),
        (7, 'CHANNEL'),
        (8, 'ROLE'),
        (9, 'MENTIONABLE'),
        (10, 'NUMBER'),
        (11, 'ATTACHMENT'),
    )
    
    name = models.CharField(max_length=32)  # Discord limit for option names is 32 characters
    description = models.CharField(max_length=100)  # Discord limit for option descriptions is 100 characters
    type = models.IntegerField(choices=TYPES)
    required = models.BooleanField(default=False)
    # For storing choices and other option-specific configurations
    option_data = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    # Self-referential relationship for sub-command and sub-command group options
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    command = models.ForeignKey('Command', on_delete=models.CASCADE, related_name='options')
    position = models.IntegerField(default=0)  # For ordering options
    
    class Meta:
        ordering = ['position']
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    def to_discord_json(self):
        """Convert the option to a Discord API compatible JSON format"""
        data = {
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'required': self.required,
            **self.option_data  # Include any additional option data
        }
        
        # Add choices if present in option_data
        if 'choices' in self.option_data:
            data['choices'] = self.option_data['choices']
        
        # Include channel_types if specified for CHANNEL type options
        if self.type == 7 and 'channel_types' in self.option_data:
            data['channel_types'] = self.option_data['channel_types']
        
        # Include min_value and max_value for INTEGER and NUMBER types
        if self.type in [4, 10]:
            if 'min_value' in self.option_data:
                data['min_value'] = self.option_data['min_value']
            if 'max_value' in self.option_data:
                data['max_value'] = self.option_data['max_value']
        
        # Add options for SUB_COMMAND and SUB_COMMAND_GROUP types
        if self.type in [1, 2] and self.children.exists():
            data['options'] = [child.to_discord_json() for child in self.children.all()]
        
        return data


class Command(models.Model):
    """Model representing a Discord slash command"""
    # Command types (using Discord's application command types)
    TYPES = (
        (1, 'CHAT_INPUT'),  # Slash command
        (2, 'USER'),         # User context menu command
        (3, 'MESSAGE'),      # Message context menu command
    )
    
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='commands')
    guild = models.ForeignKey(Guild, on_delete=models.CASCADE, related_name='commands', null=True, blank=True)  # Null for global commands
    name = models.CharField(max_length=32)  # Discord limit for command names is 32 characters
    description = models.CharField(max_length=100, blank=True)  # Discord limit for command descriptions is 100 characters
    type = models.IntegerField(choices=TYPES, default=1)  # Default to slash command (CHAT_INPUT)
    default_member_permissions = models.CharField(max_length=100, blank=True, null=True)  # Permission flags as string
    is_dm_enabled = models.BooleanField(default=True)  # Whether the command is enabled in DMs
    is_nsfw = models.BooleanField(default=False)  # Whether the command is age-restricted
    command_id = models.CharField(max_length=100, blank=True, null=True)  # Discord's ID for the command once registered
    is_active = models.BooleanField(default=True)  # Whether the command is active and should be synced
    # For additional custom configurations and metadata
    command_data = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)  # Last time the command was synced with Discord
    
    class Meta:
        unique_together = ('bot', 'guild', 'name')  # Command names must be unique per bot and guild
        ordering = ['name']
    
    def __str__(self):
        guild_name = f" - {self.guild.name}" if self.guild else " (Global)"
        return f"{self.name}{guild_name}"
    
    def to_discord_json(self):
        """Convert the command to a Discord API compatible JSON format"""
        data = {
            'name': self.name,
            'type': self.type,
        }
        
        # Only CHAT_INPUT commands have descriptions
        if self.type == 1:  # CHAT_INPUT
            data['description'] = self.description
        
        # Add options if they exist
        if self.options.exists():
            data['options'] = [option.to_discord_json() for option in self.options.filter(parent=None)]  # Only top-level options
        
        # Add additional fields if they exist
        if self.default_member_permissions:
            data['default_member_permissions'] = self.default_member_permissions
        
        data['dm_permission'] = self.is_dm_enabled
        
        if self.is_nsfw:
            data['nsfw'] = True
        
        # Include any additional command data
        for key, value in self.command_data.items():
            if key not in data:  # Don't override existing fields
                data[key] = value
        
        return data
    
    def sync_to_discord(self):
        """Sync this command to Discord API"""
        from bot_management.discord_bot.service import bot_manager
        
        success = bot_manager.sync_command(self.id)
        
        if success:
            BotLog.objects.create(
                bot=self.bot,
                event_type='COMMAND_SYNCED',
                description=f'Command {self.name} synced with Discord'
            )
            
        return success
    
    def delete_from_discord(self):
        """Delete this command from Discord API"""
        from bot_management.discord_bot.service import bot_manager
        
        success = bot_manager.delete_command(self.id)
        
        if success:
            BotLog.objects.create(
                bot=self.bot,
                event_type='COMMAND_DELETED',
                description=f'Command {self.name} deleted from Discord'
            )
            
        return success
    
    @staticmethod
    def sync_all_commands(bot_id, guild_id=None):
        """Sync all commands for a bot, optionally filtered by guild"""
        from bot_management.discord_bot.service import bot_manager
        
        success = bot_manager.sync_all_commands(bot_id, guild_id)
        
        if success:
            guild_text = f" for guild {guild_id}" if guild_id else ""
            BotLog.objects.create(
                bot_id=bot_id,
                event_type='ALL_COMMANDS_SYNCED',
                description=f'All commands synced with Discord{guild_text}'
            )
            
        return success


class CommandLog(models.Model):
    """Model for logging command-related activity"""
    command = models.ForeignKey(Command, on_delete=models.CASCADE, related_name='logs')
    event_type = models.CharField(max_length=50)
    description = models.TextField()
    details = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True, null=True)  # For storing additional details
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.command.name} - {self.event_type} - {self.timestamp}"