"""
Utilities for interacting with the Discord API.
Includes functions for making authenticated API requests and handling rate limits.
"""

import logging
import time
import requests
from django.conf import settings
from allauth.socialaccount.models import SocialToken, SocialAccount
from .token_storage import TokenManager

logger = logging.getLogger(__name__)

class DiscordAPI:
    """
    Helper class for making Discord API requests.
    Handles authentication, rate limits, and error handling.
    """
    
    # Discord API base URL
    BASE_URL = 'https://discord.com/api/v10'
    
    def __init__(self, user=None, social_account=None):
        """
        Initialize the Discord API helper.
        
        Args:
            user: The Django user (optional if social_account is provided)
            social_account: The SocialAccount instance (optional if user is provided)
        """
        self.token_manager = TokenManager()
        self.user = user
        
        # Get the social account if not provided
        if not social_account and user:
            try:
                self.social_account = SocialAccount.objects.get(
                    user=user, 
                    provider='discord'
                )
            except SocialAccount.DoesNotExist:
                logger.error(f"No Discord account found for user {user}")
                self.social_account = None
        else:
            self.social_account = social_account
    
    def get_headers(self):
        """
        Get authentication headers for Discord API requests.
        
        Returns:
            dict: Headers dictionary or None if no valid token
        """
        if not self.social_account:
            return None
            
        try:
            # Get the token
            social_token = SocialToken.objects.get(
                account=self.social_account
            )
            
            return {
                'Authorization': f'Bearer {social_token.token}',
                'Content-Type': 'application/json',
            }
        except SocialToken.DoesNotExist:
            logger.error(f"No token found for Discord account {self.social_account.id}")
            return None
        except Exception as e:
            logger.exception(f"Error getting headers: {e}")
            return None
    
    def make_request(self, method, endpoint, data=None, params=None, retry=True):
        """
        Make an authenticated request to the Discord API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request data for POST/PUT requests
            params: Query parameters
            retry: Whether to retry on rate limits
            
        Returns:
            dict: Response data or None if request failed
        """
        if not self.social_account:
            logger.error("No Discord account available for API request")
            return None
            
        headers = self.get_headers()
        if not headers:
            logger.error("Could not get authentication headers for Discord API request")
            return None
            
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            # Make the request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params
            )
            
            # Handle rate limits
            if response.status_code == 429 and retry:
                retry_after = int(response.headers.get('Retry-After', 1))
                logger.warning(f"Rate limited by Discord API, retrying after {retry_after} seconds")
                time.sleep(retry_after)
                return self.make_request(method, endpoint, data, params, retry=False)
                
            # Handle successful responses
            if response.status_code >= 200 and response.status_code < 300:
                return response.json() if response.text else None
                
            # Handle errors
            logger.error(f"Discord API error: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logger.exception(f"Error making Discord API request: {e}")
            return None
    
    def get_user_profile(self):
        """
        Get the current user's Discord profile.
        
        Returns:
            dict: User profile data or None
        """
        return self.make_request('GET', '/users/@me')
    
    def get_user_guilds(self):
        """
        Get the current user's Discord guilds (servers).
        
        Returns:
            list: List of guild data or None
        """
        return self.make_request('GET', '/users/@me/guilds')
    
    def get_guild(self, guild_id):
        """
        Get detailed information about a specific guild.
        
        Args:
            guild_id: The Discord guild ID
            
        Returns:
            dict: Guild data or None
        """
        return self.make_request('GET', f'/guilds/{guild_id}')
    
    def get_guild_channels(self, guild_id):
        """
        Get channels in a specific guild.
        
        Args:
            guild_id: The Discord guild ID
            
        Returns:
            list: List of channel data or None
        """
        return self.make_request('GET', f'/guilds/{guild_id}/channels')
    
    @classmethod
    def get_bot_guilds(cls):
        """
        Get guilds for the bot using the bot token.
        
        Returns:
            list: List of guild data or None
        """
        headers = {
            'Authorization': f'Bot {settings.DISCORD_BOT_TOKEN}',
            'Content-Type': 'application/json',
        }
        
        try:
            response = requests.get(
                f"{cls.BASE_URL}/users/@me/guilds",
                headers=headers
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                return response.json()
            else:
                logger.error(f"Error getting bot guilds: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.exception(f"Error getting bot guilds: {e}")
            return None