from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from dashboard.decorators import discord_login_required
from .models import Bot, BotLog
from .forms import BotForm, BotLogForm
from .error_handling import with_bot_error_handling
from logging_system.utils import log_error
import time
import functools

@discord_login_required
def index(request):
    """Bot management index view showing a list of user's bots"""
    bots = Bot.objects.filter(owner=request.user).order_by('-created_at')
    
    # Get status for each bot
    bots_with_status = []
    for bot in bots:
        status = bot.get_status()
        bots_with_status.append({
            'bot': bot,
            'status': status
        })
    
    return render(request, 'bot_management/index.html', {
        'title': 'Bot Management',
        'bots': bots_with_status,
    })

@discord_login_required
def bot_detail(request, bot_id):
    """View to show details of a specific bot"""
    bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    logs = bot.logs.all().order_by('-timestamp')[:10]  # Get the 10 most recent logs
    
    # Get bot status
    status = bot.get_status()
    
    # Format uptime if available
    uptime_str = ""
    if status["running"] and status["connected"] and status["uptime"] > 0:
        uptime = status["uptime"]
        days, remainder = divmod(uptime, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
    
    return render(request, 'bot_management/bot_detail.html', {
        'title': f'Bot: {bot.name}',
        'bot': bot,
        'logs': logs,
        'status': status,
        'uptime': uptime_str,
    })

@discord_login_required
def bot_create(request):
    """View to create a new bot"""
    if request.method == 'POST':
        form = BotForm(request.POST)
        if form.is_valid():
            bot = form.save(commit=False)
            bot.owner = request.user
            bot.save()
            
            # Create a log entry for bot creation
            BotLog.objects.create(
                bot=bot,
                event_type='BOT_CREATED',
                description=f'Bot created by {request.user.username}'
            )
            
            messages.success(request, f'Bot "{bot.name}" has been created successfully!')
            return redirect('bot_management:bot_detail', bot_id=bot.id)
    else:
        form = BotForm()
    
    return render(request, 'bot_management/bot_form.html', {
        'title': 'Create Bot',
        'form': form,
        'is_create': True,
    })

@discord_login_required
def bot_update(request, bot_id):
    """View to update an existing bot"""
    bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    
    if request.method == 'POST':
        form = BotForm(request.POST, instance=bot)
        if form.is_valid():
            # Check if token was changed
            token_changed = form.cleaned_data.get('token') != ''
            
            # If token wasn't provided, don't update it
            if not token_changed:
                form.cleaned_data.pop('token')
                bot = form.save(commit=False)
                bot.token = Bot.objects.get(id=bot_id).token  # Keep original token
                bot.save()
            else:
                form.save()
            
            # Create a log entry for bot update
            BotLog.objects.create(
                bot=bot,
                event_type='BOT_UPDATED',
                description=f'Bot updated by {request.user.username}'
            )
            
            # If the bot is running and the token was changed, restart it
            status = bot.get_status()
            if status["running"] and token_changed:
                bot.restart()
                messages.info(request, f'Bot "{bot.name}" is being restarted with the new token.')
            
            messages.success(request, f'Bot "{bot.name}" has been updated successfully!')
            return redirect('bot_management:bot_detail', bot_id=bot.id)
    else:
        # Don't display the actual token in the form for security
        form = BotForm(instance=bot)
        # Clear the token field to avoid exposing it
        form.initial['token'] = ''
    
    return render(request, 'bot_management/bot_form.html', {
        'title': f'Edit Bot: {bot.name}',
        'form': form,
        'bot': bot,
        'is_create': False,
    })

@discord_login_required
@require_POST
@with_bot_error_handling(bot_field='bot_id')
def bot_delete(request, bot_id):
    """View to delete a bot"""
    bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    
    # Stop the bot if it's running
    status = bot.get_status()
    if status["running"]:
        bot.stop()
    
    bot_name = bot.name
    
    # Delete the bot
    bot.delete()
    
    messages.success(request, f'Bot "{bot_name}" has been deleted successfully!')
    return redirect('bot_management:index')

@discord_login_required
@require_POST
@with_bot_error_handling(bot_field='bot_id')
def toggle_bot_status(request, bot_id):
    """AJAX view to toggle a bot's active status"""
    bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    
    # Toggle the status
    bot.is_active = not bot.is_active
    bot.save()
    
    # Create a log entry for status change
    status = "activated" if bot.is_active else "deactivated"
    BotLog.objects.create(
        bot=bot,
        event_type=f'BOT_{status.upper()}',
        description=f'Bot {status} by {request.user.username}'
    )
    
    # If the bot is now inactive, stop it if it's running
    if not bot.is_active:
        bot_status = bot.get_status()
        if bot_status["running"]:
            bot.stop()
    
    return JsonResponse({
        'success': True,
        'is_active': bot.is_active,
        'message': f'Bot "{bot.name}" has been {status} successfully!'
    })

@discord_login_required
def bot_logs(request, bot_id):
    """View to show all logs for a specific bot"""
    bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    logs = bot.logs.all().order_by('-timestamp')
    
    return render(request, 'bot_management/bot_logs.html', {
        'title': f'Logs: {bot.name}',
        'bot': bot,
        'logs': logs,
    })

@discord_login_required
@require_POST
@with_bot_error_handling(bot_field='bot_id')
def start_bot(request, bot_id):
    """View to start a bot"""
    bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    
    # Check if the bot is already running
    status = bot.get_status()
    if status["running"]:
        messages.warning(request, f'Bot "{bot.name}" is already running.')
    else:
        # Ensure the bot is active
        if not bot.is_active:
            bot.is_active = True
            bot.save()
            messages.info(request, f'Bot "{bot.name}" has been activated.')
        
        # Start the bot
        success = bot.start()
        
        if success:
            messages.success(request, f'Bot "{bot.name}" has been started successfully!')
        else:
            messages.error(request, f'Failed to start bot "{bot.name}". Check the logs for details.')
    
    return redirect('bot_management:bot_detail', bot_id=bot.id)

@discord_login_required
@require_POST
@with_bot_error_handling(bot_field='bot_id')
def stop_bot(request, bot_id):
    """View to stop a bot"""
    bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    
    # Check if the bot is running
    status = bot.get_status()
    if not status["running"]:
        messages.warning(request, f'Bot "{bot.name}" is not running.')
    else:
        # Stop the bot
        success = bot.stop()
        
        if success:
            messages.success(request, f'Bot "{bot.name}" has been stopped successfully!')
        else:
            messages.error(request, f'Failed to stop bot "{bot.name}". Check the logs for details.')
    
    return redirect('bot_management:bot_detail', bot_id=bot.id)

@discord_login_required
@require_POST
@with_bot_error_handling(bot_field='bot_id')
def restart_bot(request, bot_id):
    """View to restart a bot"""
    bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    
    # Restart the bot
    success = bot.restart()
    
    if success:
        messages.success(request, f'Bot "{bot.name}" is being restarted!')
    else:
        messages.error(request, f'Failed to restart bot "{bot.name}". Check the logs for details.')
    
    return redirect('bot_management:bot_detail', bot_id=bot.id)