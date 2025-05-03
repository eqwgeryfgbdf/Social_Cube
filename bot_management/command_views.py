from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
import json

from .models import Bot, Guild, Command, CommandOption, CommandLog
from .forms import CommandForm, CommandOptionForm


@login_required
def command_list(request):
    """View to list all commands for a bot"""
    # Get the bot ID from the query parameters
    bot_id = request.GET.get('bot_id')
    
    # Get all bots owned by the current user
    user_bots = Bot.objects.filter(owner=request.user)
    
    # If a bot ID is provided and it belongs to the user, filter commands by that bot
    if bot_id and user_bots.filter(id=bot_id).exists():
        selected_bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
        commands = Command.objects.filter(bot=selected_bot)
    else:
        # If no valid bot ID is provided, use the first bot or show empty list
        selected_bot = user_bots.first()
        commands = Command.objects.filter(bot=selected_bot) if selected_bot else Command.objects.none()
        
    # Get command statistics
    total_commands = commands.count()
    active_commands = commands.filter(is_active=True).count()
    
    # Count by command type
    slash_commands = commands.filter(type=1).count()  # CHAT_INPUT
    user_commands = commands.filter(type=2).count()   # USER
    message_commands = commands.filter(type=3).count() # MESSAGE
    
    # Get usage statistics from logs (if available)
    usage_count = CommandLog.objects.filter(
        command__in=commands, 
        event_type='COMMAND_USED'
    ).count()
    
    # Handle search query
    search_query = request.GET.get('q', '')
    if search_query:
        commands = commands.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
    
    # Handle guild filter
    guild_id = request.GET.get('guild_id')
    if guild_id:
        if guild_id == 'global':
            commands = commands.filter(guild__isnull=True)
        else:
            commands = commands.filter(guild_id=guild_id)
    
    # Handle status filter
    status = request.GET.get('status')
    if status:
        if status == 'active':
            commands = commands.filter(is_active=True)
        elif status == 'inactive':
            commands = commands.filter(is_active=False)
    
    # Handle type filter
    command_type = request.GET.get('type')
    if command_type and command_type.isdigit():
        commands = commands.filter(type=int(command_type))
    
    # Paginate results
    paginator = Paginator(commands, 10)  # 10 commands per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all guilds for the selected bot (for filtering)
    bot_guilds = Guild.objects.filter(bot=selected_bot) if selected_bot else []
    
    context = {
        'page_obj': page_obj,
        'user_bots': user_bots,
        'selected_bot': selected_bot,
        'bot_guilds': bot_guilds,
        'search_query': search_query,
        'guild_id': guild_id,
        'status': status,
        'command_type': command_type,
        # Statistics
        'total_commands': total_commands,
        'active_commands': active_commands,
        'usage_count': usage_count,
        'slash_commands': slash_commands,
        'user_commands': user_commands,
        'message_commands': message_commands,
    }
    
    return render(request, 'bot_management/command_list.html', context)


@login_required
def command_detail(request, command_id):
    """View to show command details"""
    command = get_object_or_404(Command, id=command_id, bot__owner=request.user)
    
    # Get all options for this command
    options = CommandOption.objects.filter(command=command).order_by('parent', 'position')
    
    # Get top-level options (those without a parent)
    top_level_options = options.filter(parent__isnull=True)
    
    # Get recent logs for this command
    logs = CommandLog.objects.filter(command=command).order_by('-timestamp')[:10]
    
    context = {
        'command': command,
        'options': options,
        'top_level_options': top_level_options,
        'logs': logs,
    }
    
    return render(request, 'bot_management/command_detail.html', context)


@login_required
def command_create(request):
    """View to create a new command"""
    # Get the bot ID from the query parameters
    bot_id = request.GET.get('bot_id')
    initial_data = {}
    
    # If a bot ID is provided and it belongs to the user, pre-select it
    if bot_id:
        bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
        initial_data['bot'] = bot
    
    if request.method == 'POST':
        form = CommandForm(request.POST, user=request.user)
        if form.is_valid():
            command = form.save()
            
            # Log the command creation
            CommandLog.objects.create(
                command=command,
                event_type='COMMAND_CREATED',
                description=f'Command "{command.name}" created by {request.user.username}',
                details={'user_id': str(request.user.id)}
            )
            
            messages.success(request, f'Command "{command.name}" created successfully!')
            return redirect('command_detail', command_id=command.id)
    else:
        form = CommandForm(user=request.user, initial=initial_data)
    
    context = {
        'form': form,
        'is_create': True,
    }
    
    return render(request, 'bot_management/command_form.html', context)


@login_required
def command_update(request, command_id):
    """View to update an existing command"""
    command = get_object_or_404(Command, id=command_id, bot__owner=request.user)
    
    if request.method == 'POST':
        form = CommandForm(request.POST, instance=command, user=request.user)
        if form.is_valid():
            updated_command = form.save()
            
            # Log the command update
            CommandLog.objects.create(
                command=updated_command,
                event_type='COMMAND_UPDATED',
                description=f'Command "{updated_command.name}" updated by {request.user.username}',
                details={'user_id': str(request.user.id)}
            )
            
            messages.success(request, f'Command "{updated_command.name}" updated successfully!')
            return redirect('command_detail', command_id=updated_command.id)
    else:
        form = CommandForm(instance=command, user=request.user)
    
    context = {
        'form': form,
        'command': command,
        'is_create': False,
    }
    
    return render(request, 'bot_management/command_form.html', context)


@login_required
def command_delete(request, command_id):
    """View to delete a command"""
    command = get_object_or_404(Command, id=command_id, bot__owner=request.user)
    
    if request.method == 'POST':
        command_name = command.name
        bot_id = command.bot.id
        
        # Delete the command (this will cascade to options and logs)
        command.delete()
        
        messages.success(request, f'Command "{command_name}" deleted successfully!')
        return redirect(reverse('command_list') + f'?bot_id={bot_id}')
    
    context = {
        'command': command,
    }
    
    return render(request, 'bot_management/command_confirm_delete.html', context)


@login_required
def command_toggle_status(request, command_id):
    """View to toggle command active status"""
    command = get_object_or_404(Command, id=command_id, bot__owner=request.user)
    
    if request.method == 'POST':
        command.is_active = not command.is_active
        command.save()
        
        status = "activated" if command.is_active else "deactivated"
        
        # Log the status change
        CommandLog.objects.create(
            command=command,
            event_type=f'COMMAND_{status.upper()}',
            description=f'Command "{command.name}" {status} by {request.user.username}',
            details={'user_id': str(request.user.id)}
        )
        
        messages.success(request, f'Command "{command.name}" {status} successfully!')
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'command_id': command.id,
                'is_active': command.is_active,
                'status': status,
            })
        
        return redirect('command_detail', command_id=command.id)
    
    # If not a POST request, redirect to detail view
    return redirect('command_detail', command_id=command.id)


@login_required
def command_sync(request, command_id):
    """View to sync a command with Discord"""
    command = get_object_or_404(Command, id=command_id, bot__owner=request.user)
    
    if request.method == 'POST':
        success = command.sync_to_discord()
        
        if success:
            # Update last synced timestamp
            command.last_synced_at = timezone.now()
            command.save(update_fields=['last_synced_at'])
            
            messages.success(request, f'Command "{command.name}" synced successfully!')
        else:
            messages.error(request, f'Failed to sync command "{command.name}" with Discord. Please check the logs.')
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'command_id': command.id,
                'last_synced_at': command.last_synced_at.isoformat() if command.last_synced_at else None,
            })
        
        return redirect('command_detail', command_id=command.id)
    
    # If not a POST request, redirect to detail view
    return redirect('command_detail', command_id=command.id)


@login_required
def command_sync_all(request, bot_id):
    """View to sync all commands for a bot"""
    bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    
    if request.method == 'POST':
        # Get the guild ID from the query parameters (None for global commands)
        guild_id = request.POST.get('guild_id')
        
        success = Command.sync_all_commands(bot.id, guild_id)
        
        if success:
            # Update last synced timestamp for all synced commands
            synced_commands = Command.objects.filter(bot=bot)
            if guild_id:
                synced_commands = synced_commands.filter(guild_id=guild_id)
            else:
                synced_commands = synced_commands.filter(guild__isnull=True)
            
            synced_commands.update(last_synced_at=timezone.now())
            
            guild_text = f" for guild {guild_id}" if guild_id else ""
            messages.success(request, f'All commands{guild_text} synced successfully!')
        else:
            messages.error(request, 'Failed to sync commands with Discord. Please check the logs.')
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'bot_id': bot.id,
                'guild_id': guild_id,
            })
        
        return redirect(reverse('command_list') + f'?bot_id={bot.id}')
    
    # If not a POST request, redirect to command list
    return redirect(reverse('command_list') + f'?bot_id={bot.id}')


@login_required
def option_create(request, command_id):
    """View to create a new command option"""
    command = get_object_or_404(Command, id=command_id, bot__owner=request.user)
    
    if request.method == 'POST':
        form = CommandOptionForm(request.POST)
        if form.is_valid():
            option = form.save()
            
            # Log the option creation
            CommandLog.objects.create(
                command=command,
                event_type='OPTION_CREATED',
                description=f'Option "{option.name}" created for command "{command.name}" by {request.user.username}',
                details={'user_id': str(request.user.id), 'option_id': str(option.id)}
            )
            
            messages.success(request, f'Option "{option.name}" created successfully!')
            return redirect('command_detail', command_id=command.id)
    else:
        # Pre-select the command and set the position to the next available position
        next_position = CommandOption.objects.filter(command=command, parent__isnull=True).count()
        form = CommandOptionForm(initial={'command': command, 'position': next_position})
        
        # Limit parent choices to options from this command that can be parents
        form.fields['command'].queryset = Command.objects.filter(id=command.id)
        form.fields['command'].widget.attrs['disabled'] = True
        form.fields['parent'].queryset = CommandOption.objects.filter(
            command=command,
            type__in=[1, 2]  # Only SUB_COMMAND or SUB_COMMAND_GROUP can be parents
        )
    
    context = {
        'form': form,
        'command': command,
        'is_create': True,
    }
    
    return render(request, 'bot_management/option_form.html', context)


@login_required
def option_update(request, option_id):
    """View to update an existing command option"""
    option = get_object_or_404(CommandOption, id=option_id, command__bot__owner=request.user)
    command = option.command
    
    if request.method == 'POST':
        form = CommandOptionForm(request.POST, instance=option)
        if form.is_valid():
            updated_option = form.save()
            
            # Log the option update
            CommandLog.objects.create(
                command=command,
                event_type='OPTION_UPDATED',
                description=f'Option "{updated_option.name}" updated for command "{command.name}" by {request.user.username}',
                details={'user_id': str(request.user.id), 'option_id': str(updated_option.id)}
            )
            
            messages.success(request, f'Option "{updated_option.name}" updated successfully!')
            return redirect('command_detail', command_id=command.id)
    else:
        form = CommandOptionForm(instance=option)
        
        # Limit parent choices to options from this command that can be parents
        form.fields['command'].queryset = Command.objects.filter(id=command.id)
        form.fields['command'].widget.attrs['disabled'] = True
        form.fields['parent'].queryset = CommandOption.objects.filter(
            command=command,
            type__in=[1, 2]  # Only SUB_COMMAND or SUB_COMMAND_GROUP can be parents
        ).exclude(id=option.id)  # Exclude self from parent choices
    
    context = {
        'form': form,
        'option': option,
        'command': command,
        'is_create': False,
    }
    
    return render(request, 'bot_management/option_form.html', context)


@login_required
def option_delete(request, option_id):
    """View to delete a command option"""
    option = get_object_or_404(CommandOption, id=option_id, command__bot__owner=request.user)
    command = option.command
    
    if request.method == 'POST':
        option_name = option.name
        
        # Delete the option
        option.delete()
        
        # Log the option deletion
        CommandLog.objects.create(
            command=command,
            event_type='OPTION_DELETED',
            description=f'Option "{option_name}" deleted from command "{command.name}" by {request.user.username}',
            details={'user_id': str(request.user.id)}
        )
        
        messages.success(request, f'Option "{option_name}" deleted successfully!')
        return redirect('command_detail', command_id=command.id)
    
    context = {
        'option': option,
        'command': command,
    }
    
    return render(request, 'bot_management/option_confirm_delete.html', context)


@login_required
def get_guild_choices(request):
    """AJAX view to get guild choices for a bot"""
    bot_id = request.GET.get('bot_id')
    
    if not bot_id:
        return JsonResponse({'error': 'Bot ID is required'}, status=400)
    
    # Ensure the bot belongs to the current user
    try:
        bot = Bot.objects.get(id=bot_id, owner=request.user)
    except Bot.DoesNotExist:
        return JsonResponse({'error': 'Bot not found or access denied'}, status=404)
    
    # Get all guilds for this bot
    guilds = Guild.objects.filter(bot=bot, is_available=True).values('id', 'name')
    
    return JsonResponse({'guilds': list(guilds)})