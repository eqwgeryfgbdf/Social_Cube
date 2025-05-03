from django.urls import path
from . import views
from . import command_views
from . import guild_views

app_name = 'bot_management'

urlpatterns = [
    # Bot listing and management
    path('', views.index, name='index'),
    path('bot/new/', views.bot_create, name='bot_create'),
    path('bot/<int:bot_id>/', views.bot_detail, name='bot_detail'),
    path('bot/<int:bot_id>/edit/', views.bot_update, name='bot_update'),
    path('bot/<int:bot_id>/delete/', views.bot_delete, name='bot_delete'),
    path('bot/<int:bot_id>/toggle-status/', views.toggle_bot_status, name='toggle_bot_status'),
    path('bot/<int:bot_id>/logs/', views.bot_logs, name='bot_logs'),
    
    # Bot operation
    path('bot/<int:bot_id>/start/', views.start_bot, name='start_bot'),
    path('bot/<int:bot_id>/stop/', views.stop_bot, name='stop_bot'),
    path('bot/<int:bot_id>/restart/', views.restart_bot, name='restart_bot'),
    
    # Command management
    path('commands/', command_views.command_list, name='command_list'),
    path('commands/new/', command_views.command_create, name='command_create'),
    path('commands/<int:command_id>/', command_views.command_detail, name='command_detail'),
    path('commands/<int:command_id>/edit/', command_views.command_update, name='command_update'),
    path('commands/<int:command_id>/delete/', command_views.command_delete, name='command_delete'),
    path('commands/<int:command_id>/toggle-status/', command_views.command_toggle_status, name='command_toggle_status'),
    path('commands/<int:command_id>/sync/', command_views.command_sync, name='command_sync'),
    path('commands/sync-all/<int:bot_id>/', command_views.command_sync_all, name='command_sync_all'),
    
    # Command option management
    path('commands/<int:command_id>/option/new/', command_views.option_create, name='option_create'),
    path('options/<int:option_id>/edit/', command_views.option_update, name='option_update'),
    path('options/<int:option_id>/delete/', command_views.option_delete, name='option_delete'),
    
    # AJAX endpoints
    path('api/guilds-by-bot/', command_views.get_guild_choices, name='get_guild_choices'),
    
    # Guild management
    path('guilds/', guild_views.guild_list, name='guild_list'),
    path('guilds/<int:guild_id>/', guild_views.guild_detail, name='guild_detail'),
    path('guilds/<int:guild_id>/settings/', guild_views.guild_settings, name='guild_settings'),
    path('guilds/<int:guild_id>/sync/', guild_views.sync_guild, name='sync_guild'),
    path('guilds/sync-all/<int:bot_id>/', guild_views.sync_all_guilds, name='sync_all_guilds'),
    path('guilds/<int:guild_id>/channels/', guild_views.guild_channels, name='guild_channels'),
    path('guilds/<int:guild_id>/commands/', guild_views.guild_commands, name='guild_commands'),
]