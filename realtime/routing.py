"""
WebSocket URL routing configuration for the realtime app.
"""
from django.urls import path

from realtime.consumers import (
    BotStatusConsumer, GuildActivityConsumer,
    CommandLogConsumer, DashboardActivityConsumer
)

websocket_urlpatterns = [
    # Bot status routes
    path('ws/bot-status/', BotStatusConsumer.as_asgi()),  # All bots for current user
    path('ws/bot-status/<int:bot_id>/', BotStatusConsumer.as_asgi()),  # Specific bot
    
    # Guild activity routes
    path('ws/guild-activity/bot/<int:bot_id>/', GuildActivityConsumer.as_asgi()),  # All guilds for a bot
    path('ws/guild-activity/guild/<str:guild_id>/', GuildActivityConsumer.as_asgi()),  # Specific guild
    
    # Command log routes
    path('ws/command-logs/bot/<int:bot_id>/', CommandLogConsumer.as_asgi()),  # All commands for a bot
    path('ws/command-logs/guild/<str:guild_id>/', CommandLogConsumer.as_asgi()),  # All commands for a guild
    path('ws/command-logs/command/<int:command_id>/', CommandLogConsumer.as_asgi()),  # Specific command
    
    # Dashboard activity route (staff only)
    path('ws/dashboard/', DashboardActivityConsumer.as_asgi()),
]