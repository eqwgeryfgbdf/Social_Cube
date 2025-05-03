from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta

from bot_management.models import Bot, BotLog, CommandLog


@login_required
def fallback_bot_status(request):
    """
    Fallback API endpoint for polling bot status when WebSockets aren't available
    """
    # Get since parameter, default to 10 minutes ago if not provided
    since_str = request.GET.get('since')
    if since_str:
        try:
            since = datetime.fromisoformat(since_str)
        except ValueError:
            # If invalid format, default to 10 minutes ago
            since = timezone.now() - timedelta(minutes=10)
    else:
        since = timezone.now() - timedelta(minutes=10)
    
    # Get bot ID filter if provided
    bot_id = request.GET.get('bot_id')
    
    # Build the query
    query = Q(timestamp__gte=since)
    
    if bot_id:
        query &= Q(bot_id=bot_id)
    
    # Get connection status events for bots
    connection_events = BotLog.objects.filter(
        query & Q(event_type__in=['connected', 'disconnected', 'error'])
    ).order_by('timestamp')
    
    # Format the results
    results = []
    for event in connection_events:
        status = 'online' if event.event_type == 'connected' else 'offline' if event.event_type == 'disconnected' else 'error'
        results.append({
            'bot_id': event.bot.id,
            'status': status,
            'message': event.description,
            'timestamp': event.timestamp.isoformat()
        })
    
    # Get the latest timestamp for next poll
    latest_timestamp = timezone.now().isoformat()
    
    return JsonResponse({
        'results': results,
        'timestamp': latest_timestamp
    })


@login_required
def fallback_guild_activity(request):
    """
    Fallback API endpoint for polling guild activity when WebSockets aren't available
    """
    # Get since parameter, default to 10 minutes ago if not provided
    since_str = request.GET.get('since')
    if since_str:
        try:
            since = datetime.fromisoformat(since_str)
        except ValueError:
            # If invalid format, default to 10 minutes ago
            since = timezone.now() - timedelta(minutes=10)
    else:
        since = timezone.now() - timedelta(minutes=10)
    
    # Get bot ID and guild ID filters if provided
    bot_id = request.GET.get('bot_id')
    guild_id = request.GET.get('guild_id')
    
    # Build the query
    query = Q(timestamp__gte=since)
    
    if bot_id:
        query &= Q(bot_id=bot_id)
    
    if guild_id:
        query &= Q(guild_id=guild_id)
    else:
        # Only include guild-specific events when no guild ID is specified
        query &= ~Q(guild_id='')
    
    # Get guild-related events
    guild_events = BotLog.objects.filter(query).order_by('timestamp')
    
    # Format the results
    results = []
    for event in guild_events:
        results.append({
            'bot_id': event.bot.id,
            'guild_id': event.guild_id,
            'event_type': event.event_type,
            'data': {
                'description': event.description
            },
            'timestamp': event.timestamp.isoformat()
        })
    
    # Get the latest timestamp for next poll
    latest_timestamp = timezone.now().isoformat()
    
    return JsonResponse({
        'results': results,
        'timestamp': latest_timestamp
    })


@login_required
def fallback_command_logs(request):
    """
    Fallback API endpoint for polling command logs when WebSockets aren't available
    """
    # Get since parameter, default to 10 minutes ago if not provided
    since_str = request.GET.get('since')
    if since_str:
        try:
            since = datetime.fromisoformat(since_str)
        except ValueError:
            # If invalid format, default to 10 minutes ago
            since = timezone.now() - timedelta(minutes=10)
    else:
        since = timezone.now() - timedelta(minutes=10)
    
    # Get bot ID and guild ID filters if provided
    bot_id = request.GET.get('bot_id')
    guild_id = request.GET.get('guild_id')
    
    # Build the query
    query = Q(timestamp__gte=since)
    
    if bot_id:
        query &= Q(command__bot_id=bot_id)
    
    if guild_id:
        query &= Q(guild_id=guild_id)
    
    # Get command logs
    command_logs = CommandLog.objects.filter(query).order_by('timestamp')
    
    # Format the results
    results = []
    for log in command_logs:
        results.append({
            'command_id': log.command.id,
            'command_name': log.command.name,
            'bot_id': log.command.bot.id,
            'user_id': log.user_id,
            'status': log.status,
            'guild_id': log.guild_id,
            'details': {
                'options': log.options,
                'error': log.error if log.status == 'error' else None
            },
            'timestamp': log.timestamp.isoformat()
        })
    
    # Get the latest timestamp for next poll
    latest_timestamp = timezone.now().isoformat()
    
    return JsonResponse({
        'results': results,
        'timestamp': latest_timestamp
    })


@login_required
def fallback_dashboard_activity(request):
    """
    Fallback API endpoint for polling dashboard activity when WebSockets aren't available
    """
    # Only staff members can access this endpoint
    if not request.user.is_staff:
        return JsonResponse({
            'error': 'Permission denied'
        }, status=403)
    
    # Get since parameter, default to 10 minutes ago if not provided
    since_str = request.GET.get('since')
    if since_str:
        try:
            since = datetime.fromisoformat(since_str)
        except ValueError:
            # If invalid format, default to 10 minutes ago
            since = timezone.now() - timedelta(minutes=10)
    else:
        since = timezone.now() - timedelta(minutes=10)
    
    # For dashboard activity, combine various logs to create a feed
    # Start with bot logs for important events
    important_bot_events = BotLog.objects.filter(
        Q(timestamp__gte=since) & 
        Q(event_type__in=['error', 'warning', 'disconnected', 'connected'])
    ).order_by('timestamp')
    
    # Format the results
    results = []
    
    # Add bot events
    for event in important_bot_events:
        results.append({
            'activity_type': f'bot_{event.event_type}',
            'data': {
                'bot_id': event.bot.id,
                'name': event.bot.name,
                'description': event.description,
                'guild_id': event.guild_id if event.guild_id else None
            },
            'timestamp': event.timestamp.isoformat()
        })
    
    # Sort results by timestamp
    results.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Get the latest timestamp for next poll
    latest_timestamp = timezone.now().isoformat()
    
    return JsonResponse({
        'results': results,
        'timestamp': latest_timestamp
    })