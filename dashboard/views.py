from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.contrib import messages
from .models import Bot, Command, CommandExecution, UserSettings
from .forms import UserSettingsForm, UserProfileForm
import json
import requests
from datetime import datetime, timedelta
from django.contrib.auth import logout, login
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
import secrets

@login_required
def index(request):
    """Dashboard home view with bot overview."""
    user_bots = Bot.objects.filter(owner=request.user)
    
    # Stats for dashboard overview
    bots_count = user_bots.count()
    active_bots = user_bots.filter(is_active=True).count()
    
    # Get server statistics
    servers_count = 0
    total_members = 0
    
    # Get command statistics
    total_commands = 0
    commands_today = 0
    
    # Get bot status and metrics
    bot_statuses = []
    for bot in user_bots:
        # Get bot status
        status = bot.get_status() if hasattr(bot, 'get_status') else 'unknown'
        
        # Count commands for this bot
        bot_commands = Command.objects.filter(bot=bot).count() if hasattr(bot, 'commands') else 0
        total_commands += bot_commands
        
        # Count servers for this bot
        bot_servers = 0
        if hasattr(bot, 'guilds'):
            bot_servers = bot.guilds.count()
            servers_count += bot_servers
            
            # Sum up members
            total_members += bot.guilds.aggregate(total=Sum('member_count')).get('total', 0) or 0
        
        # Get recent activity
        recent_logs = []
        if hasattr(bot, 'logs'):
            recent_logs = bot.logs.all().order_by('-timestamp')[:5]
        
        # Add to bot statuses
        bot_statuses.append({
            'bot': bot,
            'status': status,
            'commands': bot_commands,
            'servers': bot_servers,
            'recent_logs': recent_logs
        })
    
    # Get system-wide recent logs
    recent_logs = []
    for bot in user_bots:
        if hasattr(bot, 'logs'):
            bot_logs = bot.logs.all().order_by('-timestamp')[:5]
            recent_logs.extend(list(bot_logs))
    
    # Sort and limit logs
    if recent_logs:
        recent_logs.sort(key=lambda x: x.timestamp, reverse=True)
        recent_logs = recent_logs[:10]
    
    # Calculate the last updated time
    last_updated = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    context = {
        'user_bots': user_bots,
        'bots_count': bots_count,
        'active_bots': active_bots,
        'servers_count': servers_count,
        'total_members': total_members,
        'total_commands': total_commands,
        'commands_today': commands_today,
        'bot_statuses': bot_statuses,
        'recent_logs': recent_logs,
        'last_updated': last_updated
    }
    
    return render(request, 'dashboard/new_index.html', context)

@login_required
def bot_list(request):
    """Bot list view."""
    user_bots = Bot.objects.filter(owner=request.user)
    
    # Set up pagination
    paginator = Paginator(user_bots, 12)  # Show 12 bots per page
    page = request.GET.get('page')
    bots = paginator.get_page(page)
    
    context = {
        'bots': bots,
    }
    
    return render(request, 'dashboard/new_bots.html', context)

@login_required
def bot_overview(request):
    """Bot overview dashboard with status indicators and statistics."""
    user_bots = Bot.objects.filter(owner=request.user)
    
    # Stats for dashboard overview
    bots_count = user_bots.count()
    active_bots = user_bots.filter(is_active=True).count()
    
    # Get server statistics
    servers_count = 0
    total_members = 0
    
    # Get command statistics
    total_commands = 0
    commands_today = 0
    
    # Get today's date for command stats
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    # Get bot status and metrics
    bot_statuses = []
    for bot in user_bots:
        # Get bot status
        status = bot.get_status() if hasattr(bot, 'get_status') else ('online' if bot.is_active else 'offline')
        
        # Count commands for this bot
        bot_commands = 0
        if hasattr(bot, 'commands'):
            bot_commands = bot.commands.count()
            total_commands += bot_commands
        
        # Count today's commands
        bot_commands_today = 0
        if hasattr(bot, 'commandexecution_set'):
            bot_commands_today = bot.commandexecution_set.filter(executed_at__gte=today_start).count()
            commands_today += bot_commands_today
        
        # Count servers for this bot
        bot_servers = 0
        if hasattr(bot, 'guilds'):
            bot_servers = bot.guilds.count()
            servers_count += bot_servers
            
            # Sum up members
            total_members += bot.guilds.aggregate(total=Sum('member_count')).get('total', 0) or 0
        
        # Get recent activity logs
        recent_logs = []
        if hasattr(bot, 'logs'):
            recent_logs = bot.logs.all().order_by('-timestamp')[:5]
        
        # Add to bot statuses
        bot_statuses.append({
            'bot': bot,
            'status': status,
            'commands': bot_commands,
            'servers': bot_servers,
            'recent_logs': recent_logs
        })
    
    # Calculate the last updated time
    last_updated = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    context = {
        'user_bots': user_bots,
        'bots_count': bots_count,
        'active_bots': active_bots,
        'servers_count': servers_count,
        'total_members': total_members,
        'total_commands': total_commands,
        'commands_today': commands_today,
        'bot_statuses': bot_statuses,
        'last_updated': last_updated
    }
    
    return render(request, 'dashboard/bot_overview.html', context)

@login_required
def bot_add(request):
    """Add new bot view."""
    if request.method == 'POST':
        token = request.POST.get('token')
        prefix = request.POST.get('prefix', '!')
        
        # Create new bot
        bot = Bot.objects.create(
            token=token,
            prefix=prefix,
            owner=request.user
        )
        
        return JsonResponse({
            'status': 'success',
            'bot': {
                'id': bot.id,
                'name': bot.name
            }
        })
    
    return render(request, 'dashboard/bot_add.html')

@login_required
def bot_detail(request, bot_id):
    """Bot detail view."""
    bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    
    # Get bot statistics
    total_commands = bot.commands.count()
    total_executions = CommandExecution.objects.filter(command__bot=bot).count()
    
    # Get recent executions
    recent_executions = CommandExecution.objects.filter(
        command__bot=bot
    ).order_by('-executed_at')[:10]
    
    # Get top commands
    top_commands = bot.commands.annotate(
        execution_count=Count('commandexecution')
    ).order_by('-execution_count')[:5]
    
    context = {
        'bot': bot,
        'total_commands': total_commands,
        'total_executions': total_executions,
        'recent_executions': recent_executions,
        'top_commands': top_commands,
    }
    
    return render(request, 'dashboard/bot_detail.html', context)

@login_required
def bot_toggle(request, bot_id):
    """Toggle bot active status."""
    bot = get_object_or_404(Bot, id=bot_id, owner=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'activate':
            bot.is_active = True
        elif action == 'deactivate':
            bot.is_active = False
        bot.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=405)

@login_required
def server_list(request):
    """Server list view with filtering and sorting."""
    user_bots = Bot.objects.filter(owner=request.user)
    
    # Get all servers from all user's bots
    servers = []
    for bot in user_bots:
        if hasattr(bot, 'guilds'):
            # Get guild data for this bot
            bot_servers = bot.guilds.all()
            
            for server in bot_servers:
                # Check if this server is already in our list (from another bot)
                existing_server = next((s for s in servers if s.guild_id == server.guild_id), None)
                
                if existing_server:
                    # Add this bot to the existing server's bots list
                    if not hasattr(existing_server, 'bots'):
                        existing_server.bots = []
                    existing_server.bots.append(bot)
                else:
                    # Add bot to this server
                    if not hasattr(server, 'bots'):
                        server.bots = []
                    server.bots.append(bot)
                    
                    # Add popular commands (if available)
                    if hasattr(server, 'get_popular_commands'):
                        server.popular_commands = server.get_popular_commands()
                    else:
                        server.popular_commands = []
                        
                    servers.append(server)
    
    # Apply filters
    bot_filter = request.GET.get('bot_id')
    search_query = request.GET.get('q')
    sort_by = request.GET.get('sort', 'name')
    
    filtered_servers = servers
    
    # Filter by bot
    if bot_filter and bot_filter != 'all':
        filtered_servers = [s for s in filtered_servers if any(b.id == int(bot_filter) for b in s.bots)]
    
    # Search by name
    if search_query:
        filtered_servers = [s for s in filtered_servers if search_query.lower() in s.name.lower()]
    
    # Sort servers
    if sort_by == 'member_count':
        filtered_servers.sort(key=lambda s: s.member_count if hasattr(s, 'member_count') else 0, reverse=True)
    elif sort_by == 'name':
        filtered_servers.sort(key=lambda s: s.name.lower())
    elif sort_by == 'recent_activity':
        # Sort by last activity if available, otherwise by name
        filtered_servers.sort(
            key=lambda s: getattr(s, 'last_activity', datetime.min) if hasattr(s, 'last_activity') else datetime.min,
            reverse=True
        )
    
    # Set up pagination
    paginator = Paginator(filtered_servers, 12)  # Show 12 servers per page
    page = request.GET.get('page', 1)
    servers_page = paginator.get_page(page)
    
    context = {
        'user_bots': user_bots,
        'servers': servers_page,
        'active_bot_filter': bot_filter,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    
    return render(request, 'dashboard/new_servers.html', context)

@login_required
def server_detail(request, server_id):
    """Server detail view showing connected bots and configuration."""
    # Get the server and check that it belongs to one of the user's bots
    user_bots = Bot.objects.filter(owner=request.user)
    server = None
    
    # Find the server by ID across all user's bots
    for bot in user_bots:
        if hasattr(bot, 'guilds'):
            try:
                found_server = bot.guilds.get(id=server_id)
                if server is None:
                    server = found_server
                    server.bots = [bot]
                else:
                    # This server is connected to multiple bots
                    if not hasattr(server, 'bots'):
                        server.bots = []
                    server.bots.append(bot)
            except Exception:
                continue
    
    if server is None:
        return redirect('dashboard:servers')
    
    # Get server channels if available
    channels = []
    if hasattr(server, 'channels'):
        channels = server.channels.all().order_by('type', 'position', 'name')
        
        # Group channels by category
        categories = {}
        uncategorized = []
        
        # First, collect categories
        for channel in channels:
            if channel.type == 4:  # Category
                categories[channel.channel_id] = {
                    'name': channel.name,
                    'channels': []
                }
        
        # Then, assign channels to categories
        for channel in channels:
            if channel.type != 4:  # Not a category
                if channel.category_id and channel.category_id in categories:
                    categories[channel.category_id]['channels'].append(channel)
                else:
                    uncategorized.append(channel)
    else:
        categories = {}
        uncategorized = []
    
    # Get commands available in this server
    commands = []
    for bot in server.bots if hasattr(server, 'bots') else []:
        if hasattr(bot, 'commands'):
            # Get guild-specific commands
            guild_commands = bot.commands.filter(guild=server)
            commands.extend(list(guild_commands))
            
            # Get global commands
            global_commands = bot.commands.filter(guild__isnull=True)
            commands.extend(list(global_commands))
    
    # Get server settings if available
    settings = None
    if hasattr(server, 'get_settings'):
        settings = server.get_settings()
    
    # Get recent logs for this server
    logs = []
    for bot in server.bots if hasattr(server, 'bots') else []:
        if hasattr(bot, 'logs'):
            # Filter logs containing the server ID
            server_logs = bot.logs.filter(description__icontains=server.guild_id).order_by('-timestamp')[:10]
            logs.extend(list(server_logs))
    
    # Sort logs by timestamp (most recent first)
    logs.sort(key=lambda x: x.timestamp, reverse=True)
    logs = logs[:10]  # Limit to 10 most recent logs
    
    context = {
        'server': server,
        'channels': channels,
        'categories': categories,
        'uncategorized': uncategorized,
        'commands': commands,
        'settings': settings,
        'logs': logs
    }
    
    return render(request, 'dashboard/server_detail.html', context)

@login_required
def server_edit(request, server_id):
    """Edit server settings."""
    # Get the server and check that it belongs to one of the user's bots
    user_bots = Bot.objects.filter(owner=request.user)
    server = None
    
    # Find the server by ID across all user's bots
    for bot in user_bots:
        if hasattr(bot, 'guilds'):
            try:
                found_server = bot.guilds.get(id=server_id)
                if server is None:
                    server = found_server
                    server.bots = [bot]
                else:
                    # This server is connected to multiple bots
                    if not hasattr(server, 'bots'):
                        server.bots = []
                    server.bots.append(bot)
            except Exception:
                continue
    
    if server is None:
        return redirect('dashboard:servers')
    
    # Get or create settings
    settings = None
    if hasattr(server, 'get_settings'):
        settings = server.get_settings()
    
    # Get available channels for the notification dropdown
    text_channels = []
    if hasattr(server, 'channels'):
        text_channels = server.channels.filter(type=0).order_by('position', 'name')
    
    if request.method == 'POST':
        # Process form submission
        if settings is not None and hasattr(settings, 'save'):
            # Update settings based on form data
            if 'prefix' in request.POST:
                settings.prefix = request.POST.get('prefix')
            if 'notification_channel_id' in request.POST:
                settings.notification_channel_id = request.POST.get('notification_channel_id')
            if 'welcome_message' in request.POST:
                settings.welcome_message = request.POST.get('welcome_message')
            if 'goodbye_message' in request.POST:
                settings.goodbye_message = request.POST.get('goodbye_message')
                
            # Boolean settings
            settings.enable_welcome_messages = 'enable_welcome_messages' in request.POST
            settings.enable_goodbye_messages = 'enable_goodbye_messages' in request.POST
            settings.enable_member_tracking = 'enable_member_tracking' in request.POST
            settings.enable_moderation = 'enable_moderation' in request.POST
            
            # Role IDs
            if 'admin_role_id' in request.POST:
                settings.admin_role_id = request.POST.get('admin_role_id')
            if 'moderator_role_id' in request.POST:
                settings.moderator_role_id = request.POST.get('moderator_role_id')
                
            # Save settings
            settings.save()
            
            # Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
                
            return redirect('dashboard:server_detail', server_id=server.id)
    
    context = {
        'server': server,
        'settings': settings,
        'text_channels': text_channels
    }
    
    return render(request, 'dashboard/server_edit.html', context)

@login_required
def stats(request):
    """Statistics view."""
    user_bots = Bot.objects.filter(owner=request.user)
    
    # Get date range (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Commands executed over time
    executions_by_day = CommandExecution.objects.filter(
        command__bot__in=user_bots,
        executed_at__gte=start_date,
        executed_at__lte=end_date
    ).values('executed_at__date').annotate(count=Count('id')).order_by('executed_at__date')
    
    # Format the data for the frontend
    days = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(31)]
    usage_counts = [0] * 31
    
    for execution in executions_by_day:
        day = execution['executed_at__date'].strftime('%Y-%m-%d')
        if day in days:
            day_index = days.index(day)
            usage_counts[day_index] = execution['count']
    
    context = {
        'bots': user_bots,
        'usage_data': {
            'labels': days,
            'counts': usage_counts
        }
    }
    
    return render(request, 'dashboard/stats.html', context)

def oauth2_login(request):
    """Discord OAuth2 login."""
    # Save the 'next' parameter if it exists
    next_url = request.GET.get('next')
    if next_url:
        request.session['next'] = next_url
        
    client_id = settings.DISCORD_CLIENT_ID
    redirect_uri = request.build_absolute_uri(reverse('dashboard:oauth2_callback'))
    scope = 'identify guilds email'  # Added email scope
    
    # Add state parameter for security
    state = secrets.token_urlsafe(32)
    request.session['oauth_state'] = state
    
    oauth2_url = (
        f'https://discord.com/api/oauth2/authorize'
        f'?client_id={client_id}'
        f'&redirect_uri={redirect_uri}'
        f'&response_type=code'
        f'&scope={scope}'
        f'&state={state}'
    )
    return redirect(oauth2_url)

def oauth2_callback(request):
    """Discord OAuth2 callback."""
    code = request.GET.get('code')
    if not code:
        return redirect('dashboard:index')
        
    # Exchange the code for an access token
    data = {
        'client_id': settings.DISCORD_CLIENT_ID,
        'client_secret': settings.DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': request.build_absolute_uri(reverse('dashboard:oauth2_callback')),
        'scope': 'identify guilds'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Make the token exchange request
    response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
    
    if response.status_code == 200:
        # Store the tokens in session
        tokens = response.json()
        request.session['discord_access_token'] = tokens['access_token']
        if 'refresh_token' in tokens:
            request.session['discord_refresh_token'] = tokens['refresh_token']
            
        # Get user info from Discord
        user_response = requests.get(
            'https://discord.com/api/users/@me',
            headers={'Authorization': f"Bearer {tokens['access_token']}"}
        )
        
        if user_response.status_code == 200:
            discord_user = user_response.json()
            
            # Try to find existing user or create new one
            try:
                user = User.objects.get(username=f"discord_{discord_user['id']}")
            except User.DoesNotExist:
                # Create new user
                user = User.objects.create_user(
                    username=f"discord_{discord_user['id']}",
                    email=discord_user.get('email', ''),
                    first_name=discord_user.get('username', '')
                )
                
            # Store Discord info in session
            request.session['discord_user'] = {
                'id': discord_user['id'],
                'username': discord_user['username'],
                'discriminator': discord_user.get('discriminator', ''),
                'avatar': discord_user.get('avatar', '')
            }
            
            # Log the user in
            login(request, user)
            
            # Redirect to the next URL if it exists, otherwise to dashboard
            next_url = request.session.get('next', 'dashboard:index')
            if 'next' in request.session:
                del request.session['next']
            return redirect(next_url)
            
    # If something went wrong, redirect to login
    return redirect('dashboard:oauth2_login')

def oauth2_debug(request):
    """Debug OAuth2 data."""
    return render(request, 'dashboard/oauth2_debug.html')

def logout_view(request):
    """Logout view."""
    logout(request)
    return redirect('login')

@login_required
def user_settings(request):
    """User settings view allowing customization of dashboard preferences."""
    # Get or create user settings
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=user_settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your settings have been updated successfully!')
            
            # Handle AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
                
            return redirect('dashboard:user_settings')
    else:
        form = UserSettingsForm(instance=user_settings)
    
    context = {
        'form': form,
        'settings': user_settings,
    }
    
    return render(request, 'dashboard/user_settings.html', context)

@login_required
def profile(request):
    """User profile view showing Discord account information."""
    # Get the user's Discord account if it exists
    try:
        discord_account = SocialAccount.objects.get(user=request.user, provider='discord')
        
        # Use our adapter to get the user's Discord guilds
        from .adapters.discord import DiscordSocialAccountAdapter
        adapter = DiscordSocialAccountAdapter()
        discord_guilds = adapter.get_discord_guilds(discord_account)
    except SocialAccount.DoesNotExist:
        discord_account = None
        discord_guilds = []
        
    # Handle profile form submission
    if request.method == 'POST' and 'update_profile' in request.POST:
        profile_form = UserProfileForm(request.POST, instance=request.user)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('dashboard:profile')
    else:
        profile_form = UserProfileForm(instance=request.user)
    
    context = {
        'discord_account': discord_account,
        'discord_guilds': discord_guilds,
        'profile_form': profile_form,
    }
    
    return render(request, 'dashboard/profile.html', context)