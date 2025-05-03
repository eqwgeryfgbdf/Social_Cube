"""
Tests for token storage utilities.
"""
from datetime import timedelta
from unittest.mock import patch, MagicMock

import pytest
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils import timezone
from allauth.socialaccount.models import SocialAccount, SocialToken

from dashboard.utils.token_storage import TokenManager


@pytest.fixture
def user_with_discord():
    """Create a user with a Discord social account."""
    user = User.objects.create_user(
        username='discord_user',
        email='discord@example.com',
        password='password123'
    )
    
    # Create a site
    site = Site.objects.get_or_create(pk=1)[0]
    site.domain = 'testserver'
    site.name = 'testserver'
    site.save()
    
    # Create Discord social account
    social_account = SocialAccount.objects.create(
        user=user,
        provider='discord',
        uid='12345678901234',
        extra_data={
            'id': '12345678901234',
            'username': 'discord_user',
            'discriminator': '1234',
        }
    )
    
    return user


@pytest.fixture
def token_manager():
    """Create a TokenManager with a test key."""
    test_key = Fernet.generate_key()
    
    # Override settings for testing
    with patch('django.conf.settings.BOT_TOKEN_KEY', test_key):
        yield TokenManager()


@pytest.fixture
def tokens():
    """Sample tokens for testing."""
    return {
        'access_token': 'test_access_token',
        'refresh_token': 'test_refresh_token',
        'expires_in': 3600
    }


class TestTokenManager:
    """Tests for the TokenManager class."""
    
    def test_encrypt_decrypt_token(self, token_manager):
        """Test token encryption and decryption."""
        original_token = 'test_secret_token'
        
        # Encrypt the token
        encrypted = token_manager.encrypt_token(original_token)
        
        # Should be different from original
        assert encrypted != original_token
        
        # Decrypt the token
        decrypted = token_manager.decrypt_token(encrypted)
        
        # Should match original
        assert decrypted == original_token
    
    def test_encrypt_decrypt_empty_token(self, token_manager):
        """Test encrypting and decrypting an empty token."""
        original_token = ''
        encrypted = token_manager.encrypt_token(original_token)
        decrypted = token_manager.decrypt_token(encrypted)
        
        assert decrypted == original_token
    
    def test_encrypt_decrypt_none_token(self, token_manager):
        """Test handling None values."""
        # Should handle None without error
        encrypted = token_manager.encrypt_token(None)
        assert encrypted is None
        
        # Should handle None without error
        decrypted = token_manager.decrypt_token(None)
        assert decrypted is None
    
    def test_decrypt_invalid_token(self, token_manager):
        """Test decrypting an invalid token."""
        invalid_token = 'not_an_encrypted_token'
        
        # Should return None for invalid tokens
        decrypted = token_manager.decrypt_token(invalid_token)
        assert decrypted is None
    
    def test_store_tokens(self, token_manager, user_with_discord, tokens):
        """Test storing tokens for a user."""
        # Store tokens
        result = token_manager.store_tokens(user_with_discord, 'discord', tokens)
        
        # Should succeed
        assert result is True
        
        # Check database
        social_token = SocialToken.objects.get(
            account__user=user_with_discord,
            account__provider='discord'
        )
        
        # Access token should be stored as provided
        assert social_token.token == tokens['access_token']
        
        # Refresh token should be encrypted
        decrypted_refresh = token_manager.decrypt_token(social_token.token_secret)
        assert decrypted_refresh == tokens['refresh_token']
        
        # Expiry should be set
        assert social_token.expires_at is not None
    
    def test_store_tokens_with_expires_at(self, token_manager, user_with_discord):
        """Test storing tokens with explicit expires_at."""
        expires_at = timezone.now() + timedelta(hours=2)
        tokens_with_expiry = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_at': expires_at
        }
        
        result = token_manager.store_tokens(user_with_discord, 'discord', tokens_with_expiry)
        
        # Check database
        social_token = SocialToken.objects.get(
            account__user=user_with_discord,
            account__provider='discord'
        )
        
        # Expiry should match provided value
        assert social_token.expires_at == expires_at
    
    def test_store_tokens_missing_user_account(self, token_manager, tokens):
        """Test storing tokens for a nonexistent account."""
        # Create a user without a social account
        user = User.objects.create_user(
            username='no_social',
            email='no_social@example.com',
            password='password123'
        )
        
        # Should fail gracefully
        result = token_manager.store_tokens(user, 'discord', tokens)
        
        assert result is False
    
    def test_get_tokens(self, token_manager, user_with_discord, tokens):
        """Test retrieving tokens for a user."""
        # Store tokens first
        token_manager.store_tokens(user_with_discord, 'discord', tokens)
        
        # Get tokens
        stored_tokens = token_manager.get_tokens(user_with_discord, 'discord')
        
        # Check retrieved tokens
        assert stored_tokens is not None
        assert stored_tokens['access_token'] == tokens['access_token']
        assert stored_tokens['refresh_token'] == tokens['refresh_token']
        assert 'expires_at' in stored_tokens
    
    def test_get_tokens_missing_account(self, token_manager):
        """Test getting tokens for a nonexistent account."""
        # Create a user without a social account
        user = User.objects.create_user(
            username='no_tokens',
            email='no_tokens@example.com',
            password='password123'
        )
        
        # Should return None
        tokens = token_manager.get_tokens(user, 'discord')
        
        assert tokens is None
    
    def test_get_tokens_missing_token(self, token_manager, user_with_discord):
        """Test getting tokens when none are stored."""
        # No tokens stored yet
        
        # Should return None
        tokens = token_manager.get_tokens(user_with_discord, 'discord')
        
        assert tokens is None
    
    def test_is_token_valid_fresh_token(self, token_manager, user_with_discord, tokens):
        """Test checking if a fresh token is valid."""
        # Store tokens with future expiry
        tokens_with_expiry = tokens.copy()
        tokens_with_expiry['expires_at'] = timezone.now() + timedelta(hours=1)
        token_manager.store_tokens(user_with_discord, 'discord', tokens_with_expiry)
        
        # Should be valid
        is_valid = token_manager.is_token_valid(user_with_discord, 'discord')
        
        assert is_valid is True
    
    def test_is_token_valid_expired_token(self, token_manager, user_with_discord, tokens):
        """Test checking if an expired token is valid."""
        # Store tokens with past expiry
        tokens_with_expiry = tokens.copy()
        tokens_with_expiry['expires_at'] = timezone.now() - timedelta(hours=1)
        token_manager.store_tokens(user_with_discord, 'discord', tokens_with_expiry)
        
        # Should be invalid
        is_valid = token_manager.is_token_valid(user_with_discord, 'discord')
        
        assert is_valid is False
    
    def test_is_token_valid_missing_account(self, token_manager):
        """Test checking validity for a nonexistent account."""
        # Create a user without a social account
        user = User.objects.create_user(
            username='no_account',
            email='no_account@example.com',
            password='password123'
        )
        
        # Should return False
        is_valid = token_manager.is_token_valid(user, 'discord')
        
        assert is_valid is False
    
    def test_is_token_valid_missing_token(self, token_manager, user_with_discord):
        """Test checking validity when no token exists."""
        # No token stored yet
        
        # Should return False
        is_valid = token_manager.is_token_valid(user_with_discord, 'discord')
        
        assert is_valid is False
    
    def test_refresh_token(self, token_manager, user_with_discord, tokens):
        """Test refreshing a token."""
        # Store initial tokens
        token_manager.store_tokens(user_with_discord, 'discord', tokens)
        
        # New tokens after refresh
        new_tokens = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3600
        }
        
        # Mock the API refresh call
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = new_tokens
            mock_post.return_value = mock_response
            
            # Call refresh_token
            success = token_manager.refresh_token(user_with_discord, 'discord')
            
            # Should succeed
            assert success is True
            
            # Check the API call
            mock_post.assert_called_once()
            
        # Get the updated token
        updated_tokens = token_manager.get_tokens(user_with_discord, 'discord')
        
        # Should have new values
        assert updated_tokens['access_token'] == new_tokens['access_token']
        assert updated_tokens['refresh_token'] == new_tokens['refresh_token']
    
    def test_refresh_token_api_error(self, token_manager, user_with_discord, tokens):
        """Test handling API errors during token refresh."""
        # Store initial tokens
        token_manager.store_tokens(user_with_discord, 'discord', tokens)
        
        # Mock a failed API refresh call
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = 'Invalid request'
            mock_post.return_value = mock_response
            
            # Call refresh_token
            success = token_manager.refresh_token(user_with_discord, 'discord')
            
            # Should fail
            assert success is False