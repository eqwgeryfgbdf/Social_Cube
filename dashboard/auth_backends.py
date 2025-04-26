"""
Custom authentication backends for Social Cube.
Includes a Discord-specific authentication backend.
"""

import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount

logger = logging.getLogger(__name__)
User = get_user_model()

class DiscordAuthenticationBackend(ModelBackend):
    """
    Authentication backend that allows users to authenticate with their Discord account.
    This is used in addition to the default ModelBackend.
    """
    
    def authenticate(self, request, discord_id=None, **kwargs):
        """
        Authenticate a user based on their Discord ID.
        
        Args:
            request: The HTTP request
            discord_id: The Discord user ID
            
        Returns:
            User: The authenticated user or None
        """
        if discord_id is None:
            return None
            
        try:
            # Find the social account with this Discord ID
            social_account = SocialAccount.objects.get(
                provider='discord',
                uid=discord_id
            )
            
            # Get the user associated with this social account
            user = social_account.user
            
            # Check if the user is active
            if not self.user_can_authenticate(user):
                logger.warning(f"Discord user {discord_id} is not active")
                return None
                
            logger.info(f"Successfully authenticated user via Discord: {user.username}")
            return user
            
        except SocialAccount.DoesNotExist:
            logger.warning(f"No Discord account found with ID: {discord_id}")
            return None
        except Exception as e:
            logger.exception(f"Error authenticating via Discord: {e}")
            return None
            
    def get_user(self, user_id):
        """
        Get a user by their ID.
        
        Args:
            user_id: The user's primary key
            
        Returns:
            User: The user object or None
        """
        try:
            user = User.objects.get(pk=user_id)
            if self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            return None