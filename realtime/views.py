from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
import json

from bot_management.models import Bot
from .utils import (
    send_bot_status_update,
    send_guild_activity,
    send_command_log,
    send_dashboard_activity
)


@login_required
def websocket_test_view(request):
    """
    View for testing WebSocket connections.
    Displays interfaces for connecting to different WebSocket channels
    and simulating events.
    """
    # Get all bots to populate select dropdowns
    bots = Bot.objects.filter(is_active=True)
    
    return render(request, 'realtime/websocket_test.html', {
        'bots': bots,
    })


@login_required
@csrf_protect
@require_POST
def simulate_bot_status(request):
    """
    API endpoint to simulate a bot status change event
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        data = json.loads(request.body)
        bot_id = data.get('bot_id')
        status = data.get('status')
        message = data.get('message', '')
        
        if not bot_id or not status:
            return JsonResponse({'success': False, 'error': 'Missing required parameters'})
        
        # Send the WebSocket update
        send_bot_status_update(
            bot_id=bot_id,
            status=status,
            message=message
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_protect
@require_POST
def simulate_guild_activity(request):
    """
    API endpoint to simulate a guild activity event
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        data = json.loads(request.body)
        bot_id = data.get('bot_id')
        guild_id = data.get('guild_id')
        event_type = data.get('event_type')
        event_data = data.get('data', {})
        
        if not bot_id or not guild_id or not event_type:
            return JsonResponse({'success': False, 'error': 'Missing required parameters'})
        
        # Send the WebSocket update
        send_guild_activity(
            bot_id=bot_id,
            guild_id=guild_id,
            event_type=event_type,
            data=event_data
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_protect
@require_POST
def simulate_command_log(request):
    """
    API endpoint to simulate a command execution log event
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        data = json.loads(request.body)
        command_id = data.get('command_id')
        command_name = data.get('command_name')
        bot_id = data.get('bot_id')
        user_id = data.get('user_id')
        status = data.get('status')
        guild_id = data.get('guild_id')
        details = data.get('details', {})
        
        if not command_id or not command_name or not bot_id or not user_id or not status:
            return JsonResponse({'success': False, 'error': 'Missing required parameters'})
        
        # Send the WebSocket update
        send_command_log(
            command_id=command_id,
            command_name=command_name,
            bot_id=bot_id,
            user_id=user_id,
            status=status,
            guild_id=guild_id,
            details=details
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_protect
@require_POST
def simulate_dashboard_activity(request):
    """
    API endpoint to simulate a dashboard activity event
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        data = json.loads(request.body)
        activity_type = data.get('activity_type')
        activity_data = data.get('data', {})
        user_id = data.get('user_id')
        
        if not activity_type:
            return JsonResponse({'success': False, 'error': 'Missing required parameters'})
        
        # Send the WebSocket update
        send_dashboard_activity(
            activity_type=activity_type,
            data=activity_data,
            user_id=user_id
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})