"""
Discord OAuth2 adapter for Django-allauth.
Handles Discord-specific authentication logic.
"""

import requests
import logging
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.conf import settings

logger = logging.getLogger(__name__)

class DiscordSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for Discord OAuth2 authentication.
    Extends the functionality of allauth's DefaultSocialAccountAdapter.
    """
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save the user and retrieve additional Discord profile information.
        
        Args:
            request: The HTTP request
            sociallogin: The social login being processed
            form: Form with user input
            
        Returns:
            User: The user instance that was created or connected
        """
        # First, save the user with the default adapter behavior
        user = super().save_user(request, sociallogin, form)
        
        # Get the Discord account data
        discord_account = SocialAccount.objects.get(user=user, provider='discord')
        discord_data = discord_account.extra_data
        
        # Additional user profile setup could go here
        # For example, setting a profile image from Discord avatar
        
        # Log successful authentication
        logger.info(f"Discord user {discord_data.get('username')} authenticated successfully")
        
        return user
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user fields based on Discord profile data.
        
        Args:
            request: The HTTP request
            sociallogin: The social login being processed
            data: The data from the social provider
            
        Returns:
            User: The populated user instance
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Set username to Discord username if empty
        if 'username' in data and not user.username:
            user.username = data['username']
        
        # Set email from Discord profile if available
        if 'email' in data and data['email'] and not user.email:
            user.email = data['email']
        
        return user
    
    def get_discord_guilds(self, discord_account):
        """
        Retrieve the Discord servers (guilds) for a user.
        
        Args:
            discord_account: SocialAccount instance for a Discord user
            
        Returns:
            list: List of guild data or empty list if error
        """
        if not discord_account or discord_account.provider != 'discord':
            return []
        
        access_token = discord_account.socialtoken_set.first().token
        
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get('https://discord.com/api/v10/users/@me/guilds', headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch Discord guilds: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.exception(f"Error fetching Discord guilds: {e}")
            return []