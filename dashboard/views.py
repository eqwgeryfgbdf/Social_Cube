from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count
from .models import Bot, Command, CommandExecution
import json
import requests
from datetime import datetime, timedelta
from django.contrib.auth import logout, login
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
import secrets

@login_required
def index(request):
    """Dashboard home view."""
    user_bots = Bot.objects.filter(owner=request.user)
    
    # Stats for dashboard overview
    total_bots = user_bots.count()
    total_commands = Command.objects.filter(bot__in=user_bots).count()
    total_executions = CommandExecution.objects.filter(command__bot__in=user_bots).count()
    
    # Recent executions for activity feed
    recent_executions = CommandExecution.objects.filter(
        command__bot__in=user_bots
    ).order_by('-executed_at')[:10]
    
    # Top commands by usage
    top_commands = Command.objects.filter(
        bot__in=user_bots
    ).annotate(
        execution_count=Count('commandexecution')
    ).order_by('-execution_count')[:5]
    
    context = {
        'total_bots': total_bots,
        'total_commands': total_commands,
        'total_executions': total_executions,
        'recent_executions': recent_executions,
        'top_commands': top_commands,
        'user_bots': user_bots,
    }
    
    return render(request, 'dashboard/index.html', context)

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
    """Server list view."""
    user_bots = Bot.objects.filter(owner=request.user)
    
    context = {
        'bots': user_bots,
    }
    
    return render(request, 'dashboard/servers.html', context)

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