"""
Tests for custom authentication backends.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from django.contrib.sites.models import Site
from django.test import RequestFactory
from dashboard.auth_backends import DiscordAuthenticationBackend

class DiscordAuthBackendTest(TestCase):
    """Test the Discord authentication backend."""
    
    def setUp(self):
        """Set up test data."""
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Set up a site
        self.site = Site.objects.get_or_create(pk=1)[0]
        self.site.domain = 'testserver'
        self.site.name = 'testserver'
        self.site.save()
        
        # Create a Discord social account for the user
        self.discord_id = '12345678901234567'
        self.social_account = SocialAccount.objects.create(
            user=self.user,
            provider='discord',
            uid=self.discord_id,
            extra_data={
                'id': self.discord_id,
                'username': 'discord_user',
                'discriminator': '1234',
            }
        )
        
        # Create a factory for request mocking
        self.factory = RequestFactory()
        
        # Create the authentication backend
        self.backend = DiscordAuthenticationBackend()
        
    def test_authenticate_with_valid_discord_id(self):
        """Test authenticating with a valid Discord ID."""
        # Create mock request
        request = self.factory.get('/')
        
        # Try to authenticate with the Discord ID
        authenticated_user = self.backend.authenticate(request, discord_id=self.discord_id)
        
        # Check that we got the right user
        self.assertEqual(authenticated_user, self.user)
        
    def test_authenticate_with_invalid_discord_id(self):
        """Test authenticating with an invalid Discord ID."""
        # Create mock request
        request = self.factory.get('/')
        
        # Try to authenticate with an invalid Discord ID
        authenticated_user = self.backend.authenticate(request, discord_id='invalid_id')
        
        # Check that authentication failed
        self.assertIsNone(authenticated_user)
        
    def test_authenticate_with_inactive_user(self):
        """Test authenticating with a Discord ID for an inactive user."""
        # Make the user inactive
        self.user.is_active = False
        self.user.save()
        
        # Create mock request
        request = self.factory.get('/')
        
        # Try to authenticate with the Discord ID
        authenticated_user = self.backend.authenticate(request, discord_id=self.discord_id)
        
        # Check that authentication failed
        self.assertIsNone(authenticated_user)
        
    def test_authenticate_with_no_discord_id(self):
        """Test authenticating without a Discord ID."""
        # Create mock request
        request = self.factory.get('/')
        
        # Try to authenticate without a Discord ID
        authenticated_user = self.backend.authenticate(request)
        
        # Check that authentication failed
        self.assertIsNone(authenticated_user)
        
    def test_get_user_with_valid_id(self):
        """Test getting a user with a valid ID."""
        # Try to get the user with the valid ID
        user = self.backend.get_user(self.user.id)
        
        # Check that we got the right user
        self.assertEqual(user, self.user)
        
    def test_get_user_with_invalid_id(self):
        """Test getting a user with an invalid ID."""
        # Try to get a user with an invalid ID
        user = self.backend.get_user(999999)
        
        # Check that we got None
        self.assertIsNone(user)
        
    def test_get_user_with_inactive_user(self):
        """Test getting an inactive user."""
        # Make the user inactive
        self.user.is_active = False
        self.user.save()
        
        # Try to get the user
        user = self.backend.get_user(self.user.id)
        
        # Check that we got None
        self.assertIsNone(user)