from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum

from .models import Bot, Guild, GuildSettings, GuildChannel, BotLog
from .forms import GuildSettingsForm

@login_required
def guild_list(request):
    """View to list all guilds for a bot"""
    # Get the bot ID from the query parameters
    bot_id = request.GET.get('bot_id')
    
    # Get all bots owned by the current user
    user_bots = Bot.objects.filter(owner=request.user)
    
    # If a bot ID is provided and it belongs to the user, filter guilds by that bot
    if bot_id and user_bots.filter(id=bot_id).exists():
        selected_bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
        guilds = Guild.objects.filter(bot=selected_bot)
    else:
        # If no valid bot ID is provided, use the first bot or show empty list
        selected_bot = user_bots.first()
        guilds = Guild.objects.filter(bot=selected_bot) if selected_bot else Guild.objects.none()
    
    # Handle search query
    search_query = request.GET.get('q', '')
    if search_query:
        guilds = guilds.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
    
    # Handle status filter
    status = request.GET.get('status')
    if status:
        if status == 'available':
            guilds = guilds.filter(is_available=True)
        elif status == 'unavailable':
            guilds = guilds.filter(is_available=False)
    
    # Handle sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'member_count':
        guilds = guilds.order_by('-member_count')
    elif sort_by == 'joined':
        guilds = guilds.order_by('-joined_at')
    else:  # Default to sorting by name
        guilds = guilds.order_by('name')
    
    # Annotate with channel counts for display
    guilds = guilds.annotate(
        channel_count=Count('channels'),
        text_channel_count=Count('channels', filter=Q(channels__type=0)),
        voice_channel_count=Count('channels', filter=Q(channels__type=2))
    )
    
    # Paginate results
    paginator = Paginator(guilds, 12)  # 12 guilds per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    total_guilds = guilds.count()
    active_guilds = guilds.filter(is_available=True).count()
    total_members = guilds.filter(is_available=True).aggregate(total=Sum('member_count'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'user_bots': user_bots,
        'selected_bot': selected_bot,
        'search_query': search_query,
        'status': status,
        'sort_by': sort_by,
        'total_guilds': total_guilds,
        'active_guilds': active_guilds,
        'total_members': total_members
    }
    
    return render(request, 'bot_management/guild_list.html', context)


@login_required
def guild_detail(request, guild_id):
    """View to show guild details"""
    guild = get_object_or_404(Guild, id=guild_id, bot__owner=request.user)
    
    # Get settings
    guild_settings = guild.get_settings()
    
    # Get channels grouped by category
    text_channels = guild.channels.filter(type=0).order_by('position', 'name')
    voice_channels = guild.channels.filter(type=2).order_by('position', 'name')
    categories = guild.channels.filter(type=4).order_by('position', 'name')
    other_channels = guild.channels.exclude(type__in=[0, 2, 4]).order_by('position', 'name')
    
    # Get commands for this guild
    guild_commands = guild.commands.all().order_by('name')
    
    # Get recent bot logs related to this guild
    bot_logs = BotLog.objects.filter(
        bot=guild.bot,
        description__icontains=guild.guild_id
    ).order_by('-timestamp')[:10]
    
    context = {
        'guild': guild,
        'settings': guild_settings,
        'text_channels': text_channels,
        'voice_channels': voice_channels,
        'categories': categories,
        'other_channels': other_channels,
        'commands': guild_commands,
        'logs': bot_logs
    }
    
    return render(request, 'bot_management/guild_detail.html', context)


@login_required
def guild_settings(request, guild_id):
    """View to manage guild settings"""
    guild = get_object_or_404(Guild, id=guild_id, bot__owner=request.user)
    
    # Get or create settings
    settings, created = GuildSettings.objects.get_or_create(guild=guild)
    
    if request.method == 'POST':
        form = GuildSettingsForm(request.POST, instance=settings, guild=guild)
        if form.is_valid():
            form.save()
            messages.success(request, f'Settings for "{guild.name}" updated successfully!')
            
            # Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            return redirect('bot_management:guild_detail', guild_id=guild.id)
    else:
        form = GuildSettingsForm(instance=settings, guild=guild)
    
    context = {
        'guild': guild,
        'form': form,
        'settings': settings
    }
    
    return render(request, 'bot_management/guild_settings.html', context)


@login_required
def sync_guild(request, guild_id):
    """View to sync guild information with Discord"""
    guild = get_object_or_404(Guild, id=guild_id, bot__owner=request.user)
    
    if request.method == 'POST':
        success = guild.sync_with_discord()
        
        if success:
            messages.success(request, f'Guild "{guild.name}" synced successfully!')
        else:
            messages.error(request, f'Failed to sync guild "{guild.name}" with Discord. Please check the logs.')
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'guild_id': guild.id,
                'last_sync': guild.last_sync.isoformat()
            })
        
        return redirect('bot_management:guild_detail', guild_id=guild.id)
    
    # If not a POST request, redirect to detail view
    return redirect('bot_management:guild_detail', guild_id=guild.id)


@login_required
def sync_all_guilds(request, bot_id):
    """View to sync all guilds for a bot"""
    bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    
    if request.method == 'POST':
        success = bot.sync_guilds()
        
        if success:
            messages.success(request, f'All guilds for "{bot.name}" synced successfully!')
        else:
            messages.error(request, 'Failed to sync guilds with Discord. Please check the logs.')
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'bot_id': bot.id
            })
        
        return redirect('bot_management:guild_list')
    
    # If not a POST request, redirect to guild list
    return redirect('bot_management:guild_list')


@login_required
def guild_channels(request, guild_id):
    """View to show all channels for a guild"""
    guild = get_object_or_404(Guild, id=guild_id, bot__owner=request.user)
    
    # Get channels grouped by category
    categories = {}
    uncategorized = []
    
    for channel in guild.channels.all().order_by('position', 'name'):
        if channel.type == 4:  # Category
            categories[channel.channel_id] = {
                'name': channel.name,
                'channels': []
            }
    
    for channel in guild.channels.exclude(type=4).order_by('position', 'name'):
        if channel.category_id and channel.category_id in categories:
            categories[channel.category_id]['channels'].append(channel)
        else:
            uncategorized.append(channel)
    
    context = {
        'guild': guild,
        'categories': categories,
        'uncategorized': uncategorized
    }
    
    return render(request, 'bot_management/guild_channels.html', context)


@login_required
def guild_commands(request, guild_id):
    """View to show all commands for a guild"""
    guild = get_object_or_404(Guild, id=guild_id, bot__owner=request.user)
    
    # Get all commands for this guild
    commands = guild.commands.all().order_by('name')
    
    # Get global commands for this bot
    global_commands = guild.bot.commands.filter(guild__isnull=True).order_by('name')
    
    context = {
        'guild': guild,
        'guild_commands': commands,
        'global_commands': global_commands
    }
    
    return render(request, 'bot_management/guild_commands.html', context)