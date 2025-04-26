from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from dashboard.decorators import discord_login_required
from .models import Bot, BotLog
from .forms import BotForm, BotLogForm

@discord_login_required
def index(request):
    """Bot management index view showing a list of user's bots"""
    bots = Bot.objects.filter(owner=request.user).order_by('-created_at')
    
    return render(request, 'bot_management/index.html', {
        'title': 'Bot Management',
        'bots': bots,
    })

@discord_login_required
def bot_detail(request, bot_id):
    """View to show details of a specific bot"""
    bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    logs = bot.logs.all().order_by('-timestamp')[:10]  # Get the 10 most recent logs
    
    return render(request, 'bot_management/bot_detail.html', {
        'title': f'Bot: {bot.name}',
        'bot': bot,
        'logs': logs,
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
            form.save()
            
            # Create a log entry for bot update
            BotLog.objects.create(
                bot=bot,
                event_type='BOT_UPDATED',
                description=f'Bot updated by {request.user.username}'
            )
            
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
def bot_delete(request, bot_id):
    """View to delete a bot"""
    bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    bot_name = bot.name
    
    # Delete the bot
    bot.delete()
    
    messages.success(request, f'Bot "{bot_name}" has been deleted successfully!')
    return redirect('bot_management:index')

@discord_login_required
@require_POST
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