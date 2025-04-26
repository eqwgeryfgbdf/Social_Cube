"""
Tests for custom decorators.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialAccount, SocialToken
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from dashboard.decorators import discord_login_required, bot_owner_required
from dashboard.models import Bot

class DecoratorTest(TestCase):
    """Test the custom decorators."""
    
    def setUp(self):
        """Set up test data."""
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create another user
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
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
        
        # Create a bot owned by the test user
        self.bot = Bot.objects.create(
            name='Test Bot',
            token='test_bot_token',
            owner=self.user
        )
        
        # Create a request factory
        self.factory = RequestFactory()
    
    def _get_request_with_session_and_messages(self, url, user=None):
        """Helper method to create a request with session and messages."""
        request = self.factory.get(url)
        request.user = user
        
        # Add session
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        
        # Add messages
        middleware = MessageMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        
        return request
    
    def test_discord_login_required_authenticated_with_discord(self):
        """Test the discord_login_required decorator with an authenticated user with Discord."""
        # Define a simple view
        @discord_login_required
        def test_view(request):
            return HttpResponse("Success")
            
        # Create a request
        request = self._get_request_with_session_and_messages('/', self.user)
        
        # Test the view
        with patch('dashboard.decorators.TokenManager.is_token_valid') as mock_is_valid:
            mock_is_valid.return_value = True
            response = test_view(request)
            
        # Check that the view was accessed
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Success")
    
    def test_discord_login_required_not_authenticated(self):
        """Test the discord_login_required decorator with a non-authenticated user."""
        # Define a simple view
        @discord_login_required
        def test_view(request):
            return HttpResponse("Success")
            
        # Create a request from an anonymous user
        request = self._get_request_with_session_and_messages('/')
        
        # Test the view
        response = test_view(request)
        
        # Check that we were redirected to login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('account_login')))
    
    def test_discord_login_required_no_discord_account(self):
        """Test the discord_login_required decorator with a user without a Discord account."""
        # Define a simple view
        @discord_login_required
        def test_view(request):
            return HttpResponse("Success")
            
        # Create a request from a user without Discord
        request = self._get_request_with_session_and_messages('/', self.other_user)
        
        # Test the view
        response = test_view(request)
        
        # Check that we were redirected to login
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('account_login'))
    
    def test_discord_login_required_invalid_token(self):
        """Test the discord_login_required decorator with an expired token."""
        # Define a simple view
        @discord_login_required
        def test_view(request):
            return HttpResponse("Success")
            
        # Create a request
        request = self._get_request_with_session_and_messages('/', self.user)
        
        # Test the view
        with patch('dashboard.decorators.TokenManager.is_token_valid') as mock_is_valid:
            mock_is_valid.return_value = False
            response = test_view(request)
            
        # Check that we were redirected to login
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('account_login'))
    
    def test_bot_owner_required_owner(self):
        """Test the bot_owner_required decorator with the bot owner."""
        # Define a simple view
        @bot_owner_required
        def test_view(request, bot_id):
            return HttpResponse("Success")
            
        # Create a request from the bot owner
        request = self._get_request_with_session_and_messages('/', self.user)
        
        # Test the view with the correct bot ID
        response = test_view(request, bot_id=self.bot.id)
        
        # Check that the view was accessed
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Success")
    
    def test_bot_owner_required_not_owner(self):
        """Test the bot_owner_required decorator with a user who is not the owner."""
        # Define a simple view
        @bot_owner_required
        def test_view(request, bot_id):
            return HttpResponse("Success")
            
        # Create a request from another user
        request = self._get_request_with_session_and_messages('/', self.other_user)
        
        # Test the view with the correct bot ID
        response = test_view(request, bot_id=self.bot.id)
        
        # Check that access was denied
        self.assertEqual(response.status_code, 403)
    
    def test_bot_owner_required_not_authenticated(self):
        """Test the bot_owner_required decorator with a non-authenticated user."""
        # Define a simple view
        @bot_owner_required
        def test_view(request, bot_id):
            return HttpResponse("Success")
            
        # Create a request from an anonymous user
        request = self._get_request_with_session_and_messages('/')
        
        # Test the view with the correct bot ID
        response = test_view(request, bot_id=self.bot.id)
        
        # Check that we were redirected to login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('account_login')))