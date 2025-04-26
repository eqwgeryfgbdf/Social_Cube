"""
Custom middleware for the Social Cube dashboard.
"""

import logging
import time
import requests
import json
from django.conf import settings
from allauth.socialaccount.models import SocialToken, SocialAccount
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class DiscordTokenRefreshMiddleware:
    """
    Middleware to refresh Discord access tokens when needed.
    This ensures API requests to Discord don't fail due to expired tokens.
    """
    
    def __init__(self, get_response):
        """Initialize the middleware."""
        self.get_response = get_response
        
    def __call__(self, request):
        """
        Process the request.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: The HTTP response
        """
        # Only process if user is authenticated
        if request.user.is_authenticated:
            try:
                # Find Discord social account for the current user
                social_account = SocialAccount.objects.filter(
                    user=request.user, 
                    provider='discord'
                ).first()
                
                if social_account:
                    # Get the token for this account
                    social_token = SocialToken.objects.filter(
                        account=social_account
                    ).first()
                    
                    if social_token:
                        # Check if token is about to expire (within 5 minutes)
                        if social_token.expires_at and social_token.expires_at - timezone.now() < timedelta(minutes=5):
                            self._refresh_token(social_token)
            
            except Exception as e:
                logger.exception(f"Error refreshing Discord token: {e}")
                
        # Continue processing the request
        response = self.get_response(request)
        return response
    
    def _refresh_token(self, social_token):
        """
        Refresh a Discord access token.
        
        Args:
            social_token: The SocialToken to refresh
        """
        try:
            # Prepare the request
            refresh_token = social_token.token_secret
            client_id = settings.DISCORD_CLIENT_ID
            client_secret = settings.DISCORD_CLIENT_SECRET
            
            data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Make the request to Discord
            response = requests.post(
                'https://discord.com/api/oauth2/token', 
                data=data, 
                headers=headers
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Update the token
                social_token.token = token_data['access_token']
                social_token.token_secret = token_data['refresh_token']
                social_token.expires_at = timezone.now() + timedelta(seconds=token_data['expires_in'])
                social_token.save()
                
                logger.info(f"Successfully refreshed Discord token for user {social_token.account.user.username}")
            else:
                logger.error(f"Failed to refresh Discord token: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.exception(f"Error in token refresh: {e}")
            
            
class RequestLogMiddleware:
    """
    Middleware to log request information for debugging.
    Only enabled when DEBUG=True.
    """
    
    def __init__(self, get_response):
        """Initialize the middleware."""
        self.get_response = get_response
        
    def __call__(self, request):
        """
        Process the request.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: The HTTP response
        """
        if settings.DEBUG:
            # Log request details
            start_time = time.time()
            
            # Process the request
            response = self.get_response(request)
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Log the request
            logger.debug(f"{request.method} {request.path} - {response.status_code} ({duration:.2f}s)")
            
            return response
        else:
            # Skip logging if not in debug mode
            return self.get_response(request)