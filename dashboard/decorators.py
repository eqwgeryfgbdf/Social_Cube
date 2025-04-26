"""
Custom decorators for the Social Cube dashboard.
Includes decorators for route protection and permission checking.
"""

import logging
from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.contrib import messages
from allauth.socialaccount.models import SocialAccount
from .utils.token_storage import TokenManager

logger = logging.getLogger(__name__)

def discord_login_required(view_func):
    """
    Decorator for views that require Discord OAuth login.
    Redirects to the login page if the user is not authenticated
    or doesn't have a Discord account linked.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Store the requested URL for post-login redirect
            next_url = request.get_full_path()
            login_url = f"{reverse('account_login')}?next={next_url}"
            return redirect(login_url)
            
        # Check if user has a Discord account
        try:
            social_account = SocialAccount.objects.get(
                user=request.user,
                provider='discord'
            )
        except SocialAccount.DoesNotExist:
            # User is authenticated but doesn't have a Discord account
            messages.warning(
                request, 
                "This page requires a Discord account. Please link your Discord account."
            )
            return redirect('account_login')
            
        # Check if Discord token is valid
        token_manager = TokenManager()
        if not token_manager.is_token_valid(request.user, 'discord'):
            # Token is expired or invalid
            messages.warning(
                request, 
                "Your Discord authorization has expired. Please log in again."
            )
            # Log the user out to force re-authentication
            from django.contrib.auth import logout
            logout(request)
            return redirect('account_login')
            
        # All checks passed, continue to the view
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def bot_owner_required(view_func):
    """
    Decorator for views that require bot ownership.
    Checks if the user is the owner of the bot specified in the URL.
    Requires 'bot_id' to be in the URL or passed as a keyword argument.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Must be authenticated first
        if not request.user.is_authenticated:
            next_url = request.get_full_path()
            login_url = f"{reverse('account_login')}?next={next_url}"
            return redirect(login_url)
            
        # Get the bot ID from kwargs or URL parameters
        bot_id = kwargs.get('bot_id') or request.GET.get('bot_id')
        if not bot_id:
            logger.error("bot_owner_required: No bot_id found in URL or kwargs")
            return HttpResponseForbidden("Bot ID not provided")
            
        # Import here to avoid circular imports
        from .models import Bot
        
        # Check if the user is the owner of the bot
        try:
            bot = Bot.objects.get(id=bot_id)
            if bot.owner != request.user:
                logger.warning(f"User {request.user} attempted to access bot {bot_id} owned by {bot.owner}")
                return HttpResponseForbidden("You don't have permission to access this bot")
        except Bot.DoesNotExist:
            logger.error(f"bot_owner_required: Bot with ID {bot_id} not found")
            return HttpResponseForbidden("Bot not found")
            
        # All checks passed, continue to the view
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def guild_access_required(view_func):
    """
    Decorator for views that require access to a specific Discord guild.
    Checks if the user is a member of the guild specified in the URL.
    Requires 'guild_id' to be in the URL or passed as a keyword argument.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Must have Discord login first
        if not hasattr(request.user, 'socialaccount_set'):
            next_url = request.get_full_path()
            login_url = f"{reverse('account_login')}?next={next_url}"
            return redirect(login_url)
            
        # Get the guild ID from kwargs or URL parameters
        guild_id = kwargs.get('guild_id') or request.GET.get('guild_id')
        if not guild_id:
            logger.error("guild_access_required: No guild_id found in URL or kwargs")
            return HttpResponseForbidden("Guild ID not provided")
            
        # Check if the user is a member of the guild
        try:
            # Import here to avoid circular imports
            from .utils.discord_api import DiscordAPI
            
            # Get the user's guilds
            discord_api = DiscordAPI(user=request.user)
            guilds = discord_api.get_user_guilds()
            
            if not guilds:
                logger.error(f"guild_access_required: Failed to get guilds for user {request.user}")
                messages.error(request, "Failed to retrieve your Discord servers. Please try again later.")
                return redirect('dashboard:index')
                
            # Check if the guild ID is in the user's guilds
            guild_ids = [str(guild['id']) for guild in guilds]
            if str(guild_id) not in guild_ids:
                logger.warning(f"User {request.user} attempted to access guild {guild_id} but is not a member")
                return HttpResponseForbidden("You don't have access to this Discord server")
                
        except Exception as e:
            logger.exception(f"guild_access_required: Error checking guild access - {e}")
            messages.error(request, "An error occurred while checking your Discord server access.")
            return redirect('dashboard:index')
            
        # All checks passed, continue to the view
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view