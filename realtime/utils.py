import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone


def send_bot_status_update(bot_id, status, message=None):
    """
    Send a bot status update to all connected WebSocket clients.
    
    Args:
        bot_id (int): The ID of the bot
        status (str): Status of the bot (online, offline, error, etc.)
        message (str, optional): Additional status message
    """
    channel_layer = get_channel_layer()
    
    # Format timestamp as ISO string for consistent serialization
    timestamp = timezone.now().isoformat()
    
    # Send to the group
    async_to_sync(channel_layer.group_send)(
        "bot_status_updates",
        {
            "type": "bot_status_update",
            "bot_id": bot_id,
            "status": status,
            "timestamp": timestamp,
            "message": message or ""
        }
    )


def send_guild_activity(bot_id, guild_id, event_type, data):
    """
    Send a guild activity update to WebSocket clients monitoring the guild.
    
    Args:
        bot_id (int): The ID of the bot
        guild_id (str): The Discord guild ID
        event_type (str): Type of event (member_join, message, etc.)
        data (dict): Event-specific data
    """
    channel_layer = get_channel_layer()
    
    # Format timestamp as ISO string for consistent serialization
    timestamp = timezone.now().isoformat()
    
    # Send to specific guild group
    async_to_sync(channel_layer.group_send)(
        f"guild_activity_{bot_id}_{guild_id}",
        {
            "type": "guild_activity",
            "bot_id": bot_id,
            "guild_id": guild_id,
            "event_type": event_type,
            "data": data,
            "timestamp": timestamp
        }
    )
    
    # Also send to bot-wide group
    async_to_sync(channel_layer.group_send)(
        f"guild_activity_{bot_id}",
        {
            "type": "guild_activity",
            "bot_id": bot_id,
            "guild_id": guild_id,
            "event_type": event_type,
            "data": data,
            "timestamp": timestamp
        }
    )
    
    # Also send to all-guilds group
    async_to_sync(channel_layer.group_send)(
        "guild_activity_all",
        {
            "type": "guild_activity",
            "bot_id": bot_id,
            "guild_id": guild_id,
            "event_type": event_type,
            "data": data,
            "timestamp": timestamp
        }
    )


def send_command_log(command_id, command_name, bot_id, user_id, status, guild_id=None, details=None):
    """
    Send a command execution log to WebSocket clients.
    
    Args:
        command_id (int): The ID of the command
        command_name (str): Name of the command
        bot_id (int): The ID of the bot
        user_id (str): Discord user ID who executed the command
        status (str): Status of execution (success, error, etc.)
        guild_id (str, optional): The Discord guild ID where command was executed
        details (dict, optional): Additional execution details
    """
    channel_layer = get_channel_layer()
    
    # Format timestamp as ISO string for consistent serialization
    timestamp = timezone.now().isoformat()
    
    # Prepare the event data
    event_data = {
        "type": "command_log",
        "command_id": command_id,
        "command_name": command_name,
        "bot_id": bot_id,
        "user_id": user_id,
        "status": status,
        "timestamp": timestamp
    }
    
    if guild_id:
        event_data["guild_id"] = guild_id
    
    if details:
        event_data["details"] = details
    
    # Send to specific groups based on available info
    if guild_id:
        # Send to specific guild group
        async_to_sync(channel_layer.group_send)(
            f"command_logs_{bot_id}_{guild_id}",
            event_data
        )
    
    # Always send to bot-wide group
    async_to_sync(channel_layer.group_send)(
        f"command_logs_{bot_id}",
        event_data
    )
    
    # Always send to all-logs group
    async_to_sync(channel_layer.group_send)(
        "command_logs_all",
        event_data
    )


def send_dashboard_activity(activity_type, data, user_id=None):
    """
    Send a dashboard activity update to admin WebSocket clients.
    
    Args:
        activity_type (str): Type of activity (user_login, settings_change, etc.)
        data (dict): Activity-specific data
        user_id (int, optional): User ID who performed the action
    """
    channel_layer = get_channel_layer()
    
    # Format timestamp as ISO string for consistent serialization
    timestamp = timezone.now().isoformat()
    
    # Prepare the event data
    event_data = {
        "type": "dashboard_activity",
        "activity_type": activity_type,
        "data": data,
        "timestamp": timestamp
    }
    
    if user_id:
        event_data["user_id"] = user_id
    
    # Send to the dashboard_activity group
    async_to_sync(channel_layer.group_send)(
        "dashboard_activity",
        event_data
    )