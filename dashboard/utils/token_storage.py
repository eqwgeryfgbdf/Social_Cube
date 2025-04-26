"""
Utilities for securely storing and retrieving OAuth tokens.
Uses Fernet symmetric encryption for token storage.
"""

import logging
import json
import base64
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from allauth.socialaccount.models import SocialToken, SocialAccount

logger = logging.getLogger(__name__)

class TokenManager:
    """
    Manage Discord OAuth tokens securely using Fernet encryption.
    Handles token encryption, decryption, and refresh.
    """
    
    def __init__(self):
        """Initialize the TokenManager with the encryption key."""
        # Use the BOT_TOKEN_KEY from settings for encryption
        try:
            self.fernet = Fernet(settings.BOT_TOKEN_KEY.encode() if isinstance(settings.BOT_TOKEN_KEY, str) else settings.BOT_TOKEN_KEY)
        except Exception as e:
            logger.error(f"Error initializing TokenManager: {e}")
            self.fernet = None
    
    def encrypt_token(self, token_string):
        """
        Encrypt a token string.
        
        Args:
            token_string: The token string to encrypt
            
        Returns:
            bytes: The encrypted token
        """
        if not self.fernet:
            logger.error("Fernet not initialized, cannot encrypt token")
            return None
            
        try:
            if isinstance(token_string, str):
                token_bytes = token_string.encode()
            else:
                token_bytes = token_string
                
            return self.fernet.encrypt(token_bytes)
        except Exception as e:
            logger.exception(f"Error encrypting token: {e}")
            return None
    
    def decrypt_token(self, encrypted_token):
        """
        Decrypt an encrypted token.
        
        Args:
            encrypted_token: The encrypted token
            
        Returns:
            str: The decrypted token string or None if decryption fails
        """
        if not self.fernet:
            logger.error("Fernet not initialized, cannot decrypt token")
            return None
            
        try:
            decrypted = self.fernet.decrypt(encrypted_token)
            return decrypted.decode()
        except InvalidToken:
            logger.error("Invalid token provided for decryption")
            return None
        except Exception as e:
            logger.exception(f"Error decrypting token: {e}")
            return None
    
    def store_tokens(self, user, provider, tokens):
        """
        Store OAuth tokens securely for a user.
        
        Args:
            user: The user to store tokens for
            provider: The OAuth provider (e.g., 'discord')
            tokens: Dictionary containing 'access_token', 'refresh_token', and 'expires_in'
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the SocialAccount
            social_account = SocialAccount.objects.filter(
                user=user, 
                provider=provider
            ).first()
            
            if not social_account:
                logger.error(f"No social account found for user {user.username} with provider {provider}")
                return False
                
            # Calculate expiry time
            expires_at = None
            if 'expires_in' in tokens:
                expires_at = timezone.now() + timedelta(seconds=int(tokens['expires_in']))
                
            # Get or create SocialToken
            social_token, created = SocialToken.objects.get_or_create(
                account=social_account,
                defaults={
                    'token': tokens['access_token'],
                    'token_secret': tokens.get('refresh_token', ''),
                    'expires_at': expires_at
                }
            )
            
            # Update existing token
            if not created:
                social_token.token = tokens['access_token']
                if 'refresh_token' in tokens:
                    social_token.token_secret = tokens['refresh_token']
                social_token.expires_at = expires_at
                social_token.save()
                
            return True
            
        except Exception as e:
            logger.exception(f"Error storing tokens: {e}")
            return False
    
    def get_tokens(self, user, provider):
        """
        Get stored OAuth tokens for a user.
        
        Args:
            user: The user to get tokens for
            provider: The OAuth provider (e.g., 'discord')
            
        Returns:
            dict: Dictionary containing tokens and expiry information or None
        """
        try:
            social_token = SocialToken.objects.filter(
                account__user=user,
                account__provider=provider
            ).first()
            
            if not social_token:
                logger.warning(f"No token found for user {user.username} with provider {provider}")
                return None
                
            # Check if token is expired
            if social_token.expires_at and social_token.expires_at <= timezone.now():
                logger.warning(f"Token expired for user {user.username} with provider {provider}")
                return None
                
            # Return the tokens and expiry info
            return {
                'access_token': social_token.token,
                'refresh_token': social_token.token_secret,
                'expires_at': social_token.expires_at.isoformat() if social_token.expires_at else None
            }
            
        except Exception as e:
            logger.exception(f"Error getting tokens: {e}")
            return None
    
    def is_token_valid(self, user, provider):
        """
        Check if a user's token is valid (not expired).
        
        Args:
            user: The user to check
            provider: The OAuth provider (e.g., 'discord')
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            social_token = SocialToken.objects.filter(
                account__user=user,
                account__provider=provider
            ).first()
            
            if not social_token:
                return False
                
            # Check if token is expired
            if not social_token.expires_at:
                return True  # No expiry set, assume valid
                
            # Add a 5-minute buffer
            return social_token.expires_at > timezone.now() + timedelta(minutes=5)
            
        except Exception as e:
            logger.exception(f"Error checking token validity: {e}")
            return False