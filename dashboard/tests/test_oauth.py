"""
Tests for Discord OAuth2 authentication.
"""
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialApp, SocialAccount
from django.contrib.sites.models import Site
from unittest.mock import patch, MagicMock
from dashboard.adapters.discord import DiscordSocialAccountAdapter

class DiscordOAuthTest(TestCase):
    """Test Discord OAuth2 authentication functionality."""
    
    def setUp(self):
        """Set up test data."""
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
        
        # Create Discord SocialApp
        self.app = SocialApp.objects.create(
            provider='discord',
            name='Discord',
            client_id='test-client-id',
            secret='test-secret',
        )
        self.app.sites.add(self.site)
        
        # Create factory for request mocking
        self.factory = RequestFactory()
        
    def test_discord_adapter_save_user(self):
        """Test the Discord adapter's save_user method."""
        # Create a mock sociallogin object
        mock_sociallogin = MagicMock()
        mock_sociallogin.user = self.user
        mock_sociallogin.account.provider = 'discord'
        mock_sociallogin.account.extra_data = {
            'id': '123456789',
            'username': 'discord_user',
            'discriminator': '1234',
            'avatar': 'avatar_hash',
            'email': 'discord@example.com',
        }
        
        # Mock SocialAccount.objects.get to return the mock account
        with patch('allauth.socialaccount.models.SocialAccount.objects.get') as mock_get:
            mock_get.return_value = mock_sociallogin.account
            
            # Create adapter and call save_user
            adapter = DiscordSocialAccountAdapter()
            request = self.factory.get('/')
            result = adapter.save_user(request, mock_sociallogin)
            
            # Check the user was returned
            self.assertEqual(result, self.user)
            
    def test_discord_adapter_populate_user(self):
        """Test the Discord adapter's populate_user method."""
        # Create a new user without username
        user = User(email='new@example.com')
        
        # Create the adapter
        adapter = DiscordSocialAccountAdapter()
        
        # Create a mock request
        request = self.factory.get('/')
        
        # Mock sociallogin
        mock_sociallogin = MagicMock()
        
        # Call populate_user with Discord data
        discord_data = {
            'username': 'discord_username',
            'email': 'discord@example.com'
        }
        
        # Mock the parent class method to return the user
        with patch('allauth.socialaccount.adapter.DefaultSocialAccountAdapter.populate_user') as mock_populate:
            mock_populate.return_value = user
            
            result = adapter.populate_user(request, mock_sociallogin, discord_data)
            
            # Check the username and email were set correctly
            self.assertEqual(result.username, 'discord_username')
            self.assertEqual(result.email, 'discord@example.com')
    
    @patch('requests.get')
    def test_get_discord_guilds(self, mock_get):
        """Test the get_discord_guilds method."""
        # Create a mock response with sample guild data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'id': '111111',
                'name': 'Test Server 1',
                'icon': 'icon_hash_1',
                'owner': True
            },
            {
                'id': '222222',
                'name': 'Test Server 2',
                'icon': 'icon_hash_2',
                'owner': False
            }
        ]
        mock_get.return_value = mock_response
        
        # Create a mock Discord account
        mock_account = MagicMock()
        mock_account.provider = 'discord'
        mock_token = MagicMock()
        mock_token.token = 'fake_access_token'
        mock_account.socialtoken_set.first.return_value = mock_token
        
        # Create adapter and call get_discord_guilds
        adapter = DiscordSocialAccountAdapter()
        guilds = adapter.get_discord_guilds(mock_account)
        
        # Check that the mock was called with correct parameters
        mock_get.assert_called_once_with(
            'https://discord.com/api/v10/users/@me/guilds', 
            headers={'Authorization': 'Bearer fake_access_token'}
        )
        
        # Check that the guilds were returned correctly
        self.assertEqual(len(guilds), 2)
        self.assertEqual(guilds[0]['name'], 'Test Server 1')
        self.assertEqual(guilds[1]['name'], 'Test Server 2')