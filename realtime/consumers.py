"""
WebSocket consumers for the Social Cube project.

These consumers handle real-time communication between the server and clients
for features like bot status updates, guild activity, command logs, and
dashboard notifications.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger('realtime')


class BotStatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time bot status updates.
    
    This consumer allows clients to subscribe to status updates for one or more bots.
    """
    
    async def connect(self):
        """
        Called when the WebSocket is handshaking as part of the connection process.
        """
        user = self.scope['user']
        
        # Authenticate the connection
        if not user.is_authenticated:
            await self.close()
            return
        
        # Get parameters from the URL
        self.bot_id = self.scope['url_route']['kwargs'].get('bot_id')
        
        if self.bot_id:
            # Subscribe to a specific bot's status updates
            self.group_name = f'bot_status_{self.bot_id}'
        else:
            # Subscribe to all bot status updates for this user
            user_id = user.id
            self.group_name = f'user_{user_id}_bots'
        
        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.debug(f"WebSocket connected: {self.group_name}")
    
    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.debug(f"WebSocket disconnected: {self.group_name}, code: {close_code}")
    
    async def receive(self, text_data):
        """
        Called when we get a text frame from the client.
        
        Note: Clients are not expected to send messages to this consumer.
        This method is included for completeness and debugging.
        """
        try:
            data = json.loads(text_data)
            logger.debug(f"Received unexpected message: {data}")
        except json.JSONDecodeError:
            logger.warning(f"Received invalid JSON: {text_data}")
    
    async def bot_status_update(self, event):
        """
        Handler for bot status update events.
        
        Args:
            event: Event data including the bot status information
        """
        # Send the status update to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'bot_status_update',
            'bot_id': event['bot_id'],
            'status': event['status'],
            'timestamp': event['timestamp'],
            'details': event.get('details', {})
        }))


class GuildActivityConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time guild (server) activity updates.
    
    This consumer allows clients to subscribe to activity updates for
    guilds associated with a specific bot.
    """
    
    async def connect(self):
        """
        Called when the WebSocket is handshaking as part of the connection process.
        """
        user = self.scope['user']
        
        # Authenticate the connection
        if not user.is_authenticated:
            await self.close()
            return
        
        # Get parameters from the URL
        self.bot_id = self.scope['url_route']['kwargs'].get('bot_id')
        self.guild_id = self.scope['url_route']['kwargs'].get('guild_id')
        
        if self.guild_id:
            # Subscribe to a specific guild's activity
            self.group_name = f'guild_activity_{self.guild_id}'
        elif self.bot_id:
            # Subscribe to all guild activity for a specific bot
            self.group_name = f'bot_{self.bot_id}_guilds'
        else:
            # Invalid request
            await self.close()
            return
        
        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.debug(f"WebSocket connected: {self.group_name}")
    
    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.debug(f"WebSocket disconnected: {self.group_name}, code: {close_code}")
    
    async def receive(self, text_data):
        """
        Called when we get a text frame from the client.
        
        Note: Clients are not expected to send messages to this consumer.
        This method is included for completeness and debugging.
        """
        try:
            data = json.loads(text_data)
            logger.debug(f"Received unexpected message: {data}")
        except json.JSONDecodeError:
            logger.warning(f"Received invalid JSON: {text_data}")
    
    async def guild_activity(self, event):
        """
        Handler for guild activity events.
        
        Args:
            event: Event data including the guild activity information
        """
        # Send the activity update to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'guild_activity',
            'guild_id': event['guild_id'],
            'bot_id': event['bot_id'],
            'activity_type': event['activity_type'],
            'timestamp': event['timestamp'],
            'details': event.get('details', {})
        }))


class CommandLogConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time command execution logs.
    
    This consumer allows clients to subscribe to command logs for
    a specific bot or guild.
    """
    
    async def connect(self):
        """
        Called when the WebSocket is handshaking as part of the connection process.
        """
        user = self.scope['user']
        
        # Authenticate the connection
        if not user.is_authenticated:
            await self.close()
            return
        
        # Get parameters from the URL
        self.bot_id = self.scope['url_route']['kwargs'].get('bot_id')
        self.guild_id = self.scope['url_route']['kwargs'].get('guild_id')
        self.command_id = self.scope['url_route']['kwargs'].get('command_id')
        
        if self.command_id:
            # Subscribe to logs for a specific command
            self.group_name = f'command_log_{self.command_id}'
        elif self.guild_id:
            # Subscribe to all command logs for a specific guild
            self.group_name = f'guild_{self.guild_id}_commands'
        elif self.bot_id:
            # Subscribe to all command logs for a specific bot
            self.group_name = f'bot_{self.bot_id}_commands'
        else:
            # Invalid request
            await self.close()
            return
        
        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.debug(f"WebSocket connected: {self.group_name}")
    
    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.debug(f"WebSocket disconnected: {self.group_name}, code: {close_code}")
    
    async def receive(self, text_data):
        """
        Called when we get a text frame from the client.
        
        Note: Clients are not expected to send messages to this consumer.
        This method is included for completeness and debugging.
        """
        try:
            data = json.loads(text_data)
            logger.debug(f"Received unexpected message: {data}")
        except json.JSONDecodeError:
            logger.warning(f"Received invalid JSON: {text_data}")
    
    async def command_log(self, event):
        """
        Handler for command log events.
        
        Args:
            event: Event data including the command log information
        """
        # Send the command log to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'command_log',
            'command_id': event['command_id'],
            'guild_id': event.get('guild_id'),
            'bot_id': event['bot_id'],
            'user_id': event['user_id'],
            'status': event['status'],
            'timestamp': event['timestamp'],
            'details': event.get('details', {})
        }))


class DashboardActivityConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time dashboard activity updates.
    
    This consumer broadcasts system-wide events to authenticated admin users.
    """
    
    async def connect(self):
        """
        Called when the WebSocket is handshaking as part of the connection process.
        """
        user = self.scope['user']
        
        # Only allow staff to connect
        if not user.is_authenticated or not user.is_staff:
            await self.close()
            return
        
        # Subscribe to dashboard activity
        self.group_name = 'dashboard_activity'
        
        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.debug(f"WebSocket connected: {self.group_name}")
    
    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.debug(f"WebSocket disconnected: {self.group_name}, code: {close_code}")
    
    async def receive(self, text_data):
        """
        Called when we get a text frame from the client.
        
        Note: Clients are not expected to send messages to this consumer.
        This method is included for completeness and debugging.
        """
        try:
            data = json.loads(text_data)
            logger.debug(f"Received unexpected message: {data}")
        except json.JSONDecodeError:
            logger.warning(f"Received invalid JSON: {text_data}")
    
    async def dashboard_activity(self, event):
        """
        Handler for dashboard activity events.
        
        Args:
            event: Event data including the dashboard activity information
        """
        # Send the activity update to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'dashboard_activity',
            'activity_type': event['activity_type'],
            'timestamp': event['timestamp'],
            'details': event.get('details', {})
        }))


# Utility function to send notifications to users
async def send_notification(user_id, notification_data):
    """
    Send a notification to a specific user.
    
    Args:
        user_id: The ID of the user to notify
        notification_data: The notification data to send
    """
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    
    # Add timestamp if not present
    if 'timestamp' not in notification_data:
        from django.utils import timezone
        notification_data['timestamp'] = timezone.now().isoformat()
    
    # Send to the user's notification group
    await channel_layer.group_send(
        f'user_{user_id}_notifications',
        {
            'type': 'notification',
            **notification_data
        }
    )