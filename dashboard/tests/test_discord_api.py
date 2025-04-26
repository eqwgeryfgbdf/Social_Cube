"""
Tests for Discord API utilities.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialToken
from django.contrib.sites.models import Site
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from dashboard.utils.discord_api import DiscordAPI

class DiscordAPITest(TestCase):
    """Test the DiscordAPI helper class."""
    
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
        
        # Create token
        self.social_token = SocialToken.objects.create(
            account=self.social_account,
            token='test_access_token',
            token_secret='test_refresh_token',
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        # Create Discord API instance
        self.discord_api = DiscordAPI(user=self.user)
        
    def test_get_headers(self):
        """Test getting authentication headers."""
        # Get headers
        headers = self.discord_api.get_headers()
        
        # Check that the headers contain the token
        self.assertIn('Authorization', headers)
        self.assertEqual(headers['Authorization'], f'Bearer {self.social_token.token}')
        
        # Check that the content type is set
        self.assertIn('Content-Type', headers)
        self.assertEqual(headers['Content-Type'], 'application/json')
    
    @patch('requests.request')
    def test_make_request(self, mock_request):
        """Test making API requests."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': '12345', 'username': 'discord_user'}
        mock_response.text = '{"id": "12345", "username": "discord_user"}'
        mock_request.return_value = mock_response
        
        # Make a request
        result = self.discord_api.make_request('GET', '/users/@me')
        
        # Check that the request was made correctly
        mock_request.assert_called_once_with(
            method='GET',
            url='https://discord.com/api/v10/users/@me',
            headers=self.discord_api.get_headers(),
            json=None,
            params=None
        )
        
        # Check the result
        self.assertEqual(result, {'id': '12345', 'username': 'discord_user'})
    
    @patch('requests.request')
    def test_rate_limit_handling(self, mock_request):
        """Test handling rate limits."""
        # Set up first response (rate limited)
        rate_limited_response = MagicMock()
        rate_limited_response.status_code = 429
        rate_limited_response.headers = {'Retry-After': '1'}
        
        # Set up second response (success after retry)
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {'id': '12345', 'username': 'discord_user'}
        success_response.text = '{"id": "12345", "username": "discord_user"}'
        
        # Mock the request to return rate limited first, then success
        mock_request.side_effect = [rate_limited_response, success_response]
        
        # Make a request with time.sleep patched to avoid waiting
        with patch('time.sleep') as mock_sleep:
            result = self.discord_api.make_request('GET', '/users/@me')
            
            # Check that sleep was called with the retry after value
            mock_sleep.assert_called_once_with(1)
        
        # Check that request was called twice
        self.assertEqual(mock_request.call_count, 2)
        
        # Check the result from the second request
        self.assertEqual(result, {'id': '12345', 'username': 'discord_user'})
    
    @patch('requests.request')
    def test_error_handling(self, mock_request):
        """Test handling API errors."""
        # Set up error response
        error_response = MagicMock()
        error_response.status_code = 401
        error_response.text = 'Unauthorized'
        mock_request.return_value = error_response
        
        # Make a request
        result = self.discord_api.make_request('GET', '/users/@me')
        
        # Check that the result is None
        self.assertIsNone(result)
    
    @patch.object(DiscordAPI, 'make_request')
    def test_get_user_profile(self, mock_make_request):
        """Test getting the user profile."""
        # Set up mock return value
        mock_make_request.return_value = {'id': '12345', 'username': 'discord_user'}
        
        # Get the user profile
        result = self.discord_api.get_user_profile()
        
        # Check that make_request was called correctly
        mock_make_request.assert_called_once_with('GET', '/users/@me')
        
        # Check the result
        self.assertEqual(result, {'id': '12345', 'username': 'discord_user'})
    
    @patch.object(DiscordAPI, 'make_request')
    def test_get_user_guilds(self, mock_make_request):
        """Test getting the user's guilds."""
        # Set up mock return value
        mock_make_request.return_value = [
            {'id': '111111', 'name': 'Server 1', 'owner': True},
            {'id': '222222', 'name': 'Server 2', 'owner': False}
        ]
        
        # Get the user's guilds
        result = self.discord_api.get_user_guilds()
        
        # Check that make_request was called correctly
        mock_make_request.assert_called_once_with('GET', '/users/@me/guilds')
        
        # Check the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'Server 1')
        self.assertEqual(result[1]['name'], 'Server 2')