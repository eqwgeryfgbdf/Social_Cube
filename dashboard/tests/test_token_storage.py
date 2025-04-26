"""
Tests for token storage utilities.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.test.utils import override_settings
from datetime import timedelta
from allauth.socialaccount.models import SocialAccount, SocialToken
from django.contrib.sites.models import Site
from dashboard.utils.token_storage import TokenManager
from cryptography.fernet import Fernet
import base64

class TokenManagerTest(TestCase):
    """Test the TokenManager class."""
    
    def setUp(self):
        """Set up test data."""
        # Create a test key
        self.test_key = Fernet.generate_key()
        
        # Override settings for testing
        self._original_bot_token_key = settings.BOT_TOKEN_KEY
        settings.BOT_TOKEN_KEY = self.test_key
        
        # Create token manager
        self.token_manager = TokenManager()
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Set up site
        self.site = Site.objects.get_or_create(pk=1)[0]
        self.site.domain = 'testserver'
        self.site.name = 'testserver'
        self.site.save()
        
        # Create Discord social account
        self.social_account = SocialAccount.objects.create(
            user=self.user,
            provider='discord',
            uid='12345678901234',
            extra_data={
                'id': '12345678901234',
                'username': 'discord_user',
                'discriminator': '1234',
            }
        )
        
        # Sample tokens
        self.tokens = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 3600
        }
        
    def tearDown(self):
        """Restore original settings."""
        settings.BOT_TOKEN_KEY = self._original_bot_token_key
    
    def test_encrypt_decrypt_token(self):
        """Test token encryption and decryption."""
        # Test encrypting a token
        original_token = 'test_secret_token'
        encrypted = self.token_manager.encrypt_token(original_token)
        
        # Check that the result is not the original token
        self.assertNotEqual(encrypted, original_token)
        
        # Test decrypting the token
        decrypted = self.token_manager.decrypt_token(encrypted)
        
        # Check that the decrypted token matches the original
        self.assertEqual(decrypted, original_token)
    
    def test_store_and_get_tokens(self):
        """Test storing and retrieving tokens."""
        # Store tokens for the user
        result = self.token_manager.store_tokens(
            self.user, 
            'discord', 
            self.tokens
        )
        
        # Check that the store operation was successful
        self.assertTrue(result)
        
        # Get tokens for the user
        stored_tokens = self.token_manager.get_tokens(
            self.user, 
            'discord'
        )
        
        # Check that we got tokens back
        self.assertIsNotNone(stored_tokens)
        
        # Check that the access token matches
        self.assertEqual(stored_tokens['access_token'], self.tokens['access_token'])
        
        # Check that the refresh token matches
        self.assertEqual(stored_tokens['refresh_token'], self.tokens['refresh_token'])
        
        # Check that expires_at is set
        self.assertIsNotNone(stored_tokens['expires_at'])
    
    def test_token_validity_check(self):
        """Test checking if a token is valid (not expired)."""
        # Store tokens with expiry in the future
        self.token_manager.store_tokens(
            self.user, 
            'discord', 
            self.tokens
        )
        
        # Check that the token is valid
        self.assertTrue(self.token_manager.is_token_valid(self.user, 'discord'))
        
        # Update the token to be expired
        social_token = SocialToken.objects.get(account=self.social_account)
        social_token.expires_at = timezone.now() - timedelta(hours=1)
        social_token.save()
        
        # Check that the token is now invalid
        self.assertFalse(self.token_manager.is_token_valid(self.user, 'discord'))
    
    def test_nonexistent_user_provider(self):
        """Test behavior with nonexistent user/provider combinations."""
        # Test getting tokens for a nonexistent provider
        tokens = self.token_manager.get_tokens(self.user, 'nonexistent')
        self.assertIsNone(tokens)
        
        # Test checking token validity for a nonexistent provider
        valid = self.token_manager.is_token_valid(self.user, 'nonexistent')
        self.assertFalse(valid)
        
        # Create another user without a social account
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpassword'
        )
        
        # Test getting tokens for a user without a social account
        tokens = self.token_manager.get_tokens(user2, 'discord')
        self.assertIsNone(tokens)
        
        # Test checking token validity for a user without a social account
        valid = self.token_manager.is_token_valid(user2, 'discord')
        self.assertFalse(valid)