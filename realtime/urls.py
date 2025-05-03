from django.urls import path
from . import views, fallback_views

app_name = 'realtime'

urlpatterns = [
    # WebSocket test page
    path('websocket-test/', views.websocket_test_view, name='websocket_test'),
    
    # Simulation API endpoints
    path('api/simulate/bot-status/', views.simulate_bot_status, name='simulate_bot_status'),
    path('api/simulate/guild-activity/', views.simulate_guild_activity, name='simulate_guild_activity'),
    path('api/simulate/command-log/', views.simulate_command_log, name='simulate_command_log'),
    path('api/simulate/dashboard-activity/', views.simulate_dashboard_activity, name='simulate_dashboard_activity'),
    
    # Fallback polling endpoints
    path('api/fallback/bot-status/', fallback_views.fallback_bot_status, name='fallback_bot_status'),
    path('api/fallback/guild-activity/', fallback_views.fallback_guild_activity, name='fallback_guild_activity'),
    path('api/fallback/command-logs/', fallback_views.fallback_command_logs, name='fallback_command_logs'),
    path('api/fallback/dashboard-activity/', fallback_views.fallback_dashboard_activity, name='fallback_dashboard_activity'),
]