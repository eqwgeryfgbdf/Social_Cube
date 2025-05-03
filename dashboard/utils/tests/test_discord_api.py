"""
Tests for Discord API utilities.
"""
import json
import time
from unittest.mock import patch, MagicMock

import pytest
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from allauth.socialaccount.models import SocialAccount, SocialToken
from django.contrib.sites.models import Site

from dashboard.utils.discord_api import DiscordAPI


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
    
    # Create token
    social_token = SocialToken.objects.create(
        account=social_account,
        token='mock_access_token',
        token_secret='mock_refresh_token',
    )
    
    return user


@pytest.fixture
def discord_api(user_with_discord):
    """Create a DiscordAPI instance with a mock user."""
    return DiscordAPI(user=user_with_discord)


@pytest.fixture
def mock_response():
    """Create a mock response for requests."""
    class MockResponse:
        def __init__(self, json_data, status_code, headers=None, text=None):
            self.json_data = json_data
            self.status_code = status_code
            self.headers = headers or {}
            self.text = text or json.dumps(json_data) if json_data else ""
            
        def json(self):
            return self.json_data
    
    return MockResponse


class TestDiscordAPI:
    """Tests for the DiscordAPI class."""
    
    def test_init_with_user(self, user_with_discord):
        """Test initializing with a user."""
        api = DiscordAPI(user=user_with_discord)
        
        assert api.user == user_with_discord
        assert api.social_account is not None
        assert api.social_account.provider == 'discord'
    
    def test_init_with_social_account(self, user_with_discord):
        """Test initializing with a social account."""
        social_account = SocialAccount.objects.get(user=user_with_discord)
        api = DiscordAPI(social_account=social_account)
        
        assert api.social_account == social_account
    
    def test_init_missing_discord_account(self):
        """Test initializing with a user without a Discord account."""
        user = User.objects.create_user(
            username='no_discord',
            email='no_discord@example.com',
            password='password123'
        )
        
        api = DiscordAPI(user=user)
        
        assert api.user == user
        assert api.social_account is None
    
    def test_get_headers(self, discord_api):
        """Test getting authentication headers."""
        headers = discord_api.get_headers()
        
        assert headers is not None
        assert 'Authorization' in headers
        assert headers['Authorization'] == 'Bearer mock_access_token'
        assert headers['Content-Type'] == 'application/json'
    
    def test_get_headers_no_account(self):
        """Test getting headers with no social account."""
        api = DiscordAPI()
        headers = api.get_headers()
        
        assert headers is None
    
    def test_get_headers_no_token(self, user_with_discord):
        """Test getting headers with no token."""
        # Remove the token
        SocialToken.objects.filter(account__user=user_with_discord).delete()
        
        api = DiscordAPI(user=user_with_discord)
        headers = api.get_headers()
        
        assert headers is None
    
    @patch('requests.request')
    def test_make_request_success(self, mock_request, discord_api, mock_response):
        """Test making a successful API request."""
        # Set up the mock response
        expected_data = {'id': '12345', 'username': 'test_user'}
        mock_request.return_value = mock_response(expected_data, 200)
        
        # Make the request
        result = discord_api.make_request('GET', '/test/endpoint')
        
        # Check the result
        assert result == expected_data
        
        # Check the request parameters
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs['method'] == 'GET'
        assert kwargs['url'] == f"{DiscordAPI.BASE_URL}/test/endpoint"
        assert 'Authorization' in kwargs['headers']
        assert kwargs['headers']['Authorization'] == 'Bearer mock_access_token'
    
    @patch('requests.request')
    def test_make_request_with_params(self, mock_request, discord_api, mock_response):
        """Test making a request with query parameters."""
        mock_request.return_value = mock_response({'result': 'success'}, 200)
        
        result = discord_api.make_request(
            'GET', 
            '/test/endpoint', 
            params={'param1': 'value1', 'param2': 'value2'}
        )
        
        args, kwargs = mock_request.call_args
        assert kwargs['params'] == {'param1': 'value1', 'param2': 'value2'}
    
    @patch('requests.request')
    def test_make_request_with_data(self, mock_request, discord_api, mock_response):
        """Test making a request with data."""
        mock_request.return_value = mock_response({'result': 'success'}, 200)
        
        data = {'field1': 'value1', 'field2': 'value2'}
        result = discord_api.make_request('POST', '/test/endpoint', data=data)
        
        args, kwargs = mock_request.call_args
        assert kwargs['json'] == data
    
    @patch('requests.request')
    def test_make_request_error(self, mock_request, discord_api, mock_response):
        """Test handling API errors."""
        mock_request.return_value = mock_response(
            {'code': 0, 'message': 'API Error'}, 
            400, 
            text='{"code": 0, "message": "API Error"}'
        )
        
        result = discord_api.make_request('GET', '/test/endpoint')
        
        assert result is None
    
    @patch('requests.request')
    @patch('time.sleep')
    def test_make_request_rate_limit(self, mock_sleep, mock_request, discord_api, mock_response):
        """Test handling rate limits."""
        # First response is rate limited, second is successful
        mock_request.side_effect = [
            mock_response(None, 429, headers={'Retry-After': '2'}),
            mock_response({'result': 'success'}, 200)
        ]
        
        result = discord_api.make_request('GET', '/test/endpoint')
        
        # Check that sleep was called with the retry-after value
        mock_sleep.assert_called_once_with(2)
        
        # Check that request was called twice
        assert mock_request.call_count == 2
        
        # Check the result is from the second request
        assert result == {'result': 'success'}
    
    @patch('requests.request')
    def test_make_request_no_retry(self, mock_request, discord_api, mock_response):
        """Test making a request with retry disabled."""
        mock_request.return_value = mock_response(
            None, 
            429, 
            headers={'Retry-After': '2'}
        )
        
        result = discord_api.make_request('GET', '/test/endpoint', retry=False)
        
        # Should not retry
        assert mock_request.call_count == 1
        assert result is None
    
    @patch('requests.request')
    def test_make_request_exception(self, mock_request, discord_api):
        """Test handling exceptions during requests."""
        mock_request.side_effect = requests.exceptions.RequestException("Connection error")
        
        result = discord_api.make_request('GET', '/test/endpoint')
        
        assert result is None
    
    @patch.object(DiscordAPI, 'make_request')
    def test_get_user_profile(self, mock_make_request, discord_api):
        """Test getting the user profile."""
        expected_data = {'id': '12345', 'username': 'test_user'}
        mock_make_request.return_value = expected_data
        
        result = discord_api.get_user_profile()
        
        mock_make_request.assert_called_once_with('GET', '/users/@me')
        assert result == expected_data
    
    @patch.object(DiscordAPI, 'make_request')
    def test_get_user_guilds(self, mock_make_request, discord_api):
        """Test getting user guilds."""
        expected_data = [{'id': '1', 'name': 'Server 1'}, {'id': '2', 'name': 'Server 2'}]
        mock_make_request.return_value = expected_data
        
        result = discord_api.get_user_guilds()
        
        mock_make_request.assert_called_once_with('GET', '/users/@me/guilds')
        assert result == expected_data
    
    @patch.object(DiscordAPI, 'make_request')
    def test_get_guild(self, mock_make_request, discord_api):
        """Test getting guild details."""
        guild_id = '12345'
        expected_data = {'id': guild_id, 'name': 'Test Server'}
        mock_make_request.return_value = expected_data
        
        result = discord_api.get_guild(guild_id)
        
        mock_make_request.assert_called_once_with('GET', f'/guilds/{guild_id}')
        assert result == expected_data
    
    @patch.object(DiscordAPI, 'make_request')
    def test_get_guild_channels(self, mock_make_request, discord_api):
        """Test getting guild channels."""
        guild_id = '12345'
        expected_data = [
            {'id': '1', 'name': 'general', 'type': 0},
            {'id': '2', 'name': 'voice', 'type': 2}
        ]
        mock_make_request.return_value = expected_data
        
        result = discord_api.get_guild_channels(guild_id)
        
        mock_make_request.assert_called_once_with('GET', f'/guilds/{guild_id}/channels')
        assert result == expected_data
    
    @patch('requests.get')
    def test_get_bot_guilds(self, mock_get, mock_response):
        """Test getting bot guilds."""
        expected_data = [{'id': '1', 'name': 'Server 1'}, {'id': '2', 'name': 'Server 2'}]
        mock_get.return_value = mock_response(expected_data, 200)
        
        # Mock settings
        with patch('django.conf.settings.DISCORD_BOT_TOKEN', 'bot_token'):
            result = DiscordAPI.get_bot_guilds()
        
        # Check the request parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == f"{DiscordAPI.BASE_URL}/users/@me/guilds"
        assert kwargs['headers']['Authorization'] == 'Bot bot_token'
        
        # Check the result
        assert result == expected_data
    
    @patch('requests.get')
    def test_get_bot_guilds_error(self, mock_get, mock_response):
        """Test handling errors when getting bot guilds."""
        mock_get.return_value = mock_response({'code': 0, 'message': 'API Error'}, 400)
        
        with patch('django.conf.settings.DISCORD_BOT_TOKEN', 'bot_token'):
            result = DiscordAPI.get_bot_guilds()
        
        assert result is None
    
    @patch('requests.get')
    def test_get_bot_guilds_exception(self, mock_get):
        """Test handling exceptions when getting bot guilds."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        with patch('django.conf.settings.DISCORD_BOT_TOKEN', 'bot_token'):
            result = DiscordAPI.get_bot_guilds()
        
        assert result is None