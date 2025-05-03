from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
import environ
import os
from unittest.mock import patch

from bot_management.models import Bot, BotLog, Guild, GuildSettings, GuildChannel

class BotBaseTestCase(TestCase):
    """Base test case that sets up the Fernet encryption key for all bot tests"""
    
    @classmethod
    def setUpClass(cls):
        # Generate a valid Fernet key for testing
        cls.valid_key = Fernet.generate_key()
        # Set up environment patch
        cls.env_patcher = patch.dict('os.environ', {'BOT_TOKEN_KEY': cls.valid_key.decode()})
        cls.env_patcher.start()
        super().setUpClass()
    
    @classmethod
    def tearDownClass(cls):
        # Stop the environment patch
        cls.env_patcher.stop()
        super().tearDownClass()

class BotModelTest(BotBaseTestCase):
    """Tests for the Bot model"""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a test bot
        self.bot = Bot.objects.create(
            name='Test Bot',
            description='A test bot for unit tests',
            owner=self.user,
            token='mock_token',
            client_id='123456789',
            bot_user_id='987654321',
            avatar_url='https://example.com/avatar.png',
            is_active=True
        )
    
    def test_bot_string_representation(self):
        """Test the string representation of a Bot"""
        self.assertEqual(str(self.bot), 'Test Bot')
    
    def test_bot_fields(self):
        """Test that bot fields are saved correctly"""
        self.assertEqual(self.bot.name, 'Test Bot')
        self.assertEqual(self.bot.description, 'A test bot for unit tests')
        self.assertEqual(self.bot.owner, self.user)
        self.assertEqual(self.bot.client_id, '123456789')
        self.assertEqual(self.bot.bot_user_id, '987654321')
        self.assertEqual(self.bot.avatar_url, 'https://example.com/avatar.png')
        self.assertTrue(self.bot.is_active)
        
    def test_token_encryption(self):
        """Test that the token is encrypted when saved"""
        # Token should be encrypted and not equal to the plaintext
        self.assertNotEqual(self.bot.token, 'mock_token')
        # Token should be a string
        self.assertIsInstance(self.bot.token, str)
        # Token should be longer after encryption
        self.assertGreater(len(self.bot.token), len('mock_token'))


class BotLogModelTest(BotBaseTestCase):
    """Tests for the BotLog model"""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a test bot
        self.bot = Bot.objects.create(
            name='Test Bot',
            description='A test bot for unit tests',
            owner=self.user,
            token='mock_token',
            client_id='123456789',
            bot_user_id='987654321',
            is_active=True
        )
        
        # Create a test log entry
        self.log = BotLog.objects.create(
            bot=self.bot,
            event_type='TEST_EVENT',
            description='This is a test log entry'
        )
    
    def test_log_string_representation(self):
        """Test the string representation of a BotLog"""
        expected = f"{self.bot.name} - TEST_EVENT - {self.log.timestamp}"
        self.assertEqual(str(self.log), expected)
    
    def test_log_fields(self):
        """Test that log fields are saved correctly"""
        self.assertEqual(self.log.bot, self.bot)
        self.assertEqual(self.log.event_type, 'TEST_EVENT')
        self.assertEqual(self.log.description, 'This is a test log entry')
        self.assertIsNotNone(self.log.timestamp)


class GuildModelTest(BotBaseTestCase):
    """Tests for the Guild model"""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a test bot
        self.bot = Bot.objects.create(
            name='Test Bot',
            description='A test bot for unit tests',
            owner=self.user,
            token='mock_token',
            client_id='123456789',
            bot_user_id='987654321',
            is_active=True
        )
        
        # Create a test guild
        self.guild = Guild.objects.create(
            bot=self.bot,
            guild_id='123456789',
            name='Test Guild',
            icon_url='https://example.com/icon.png',
            owner_id='987654321',
            member_count=100,
            is_available=True
        )
    
    def test_guild_string_representation(self):
        """Test the string representation of a Guild"""
        self.assertEqual(str(self.guild), 'Test Guild (123456789)')
    
    def test_guild_fields(self):
        """Test that guild fields are saved correctly"""
        self.assertEqual(self.guild.bot, self.bot)
        self.assertEqual(self.guild.guild_id, '123456789')
        self.assertEqual(self.guild.name, 'Test Guild')
        self.assertEqual(self.guild.icon_url, 'https://example.com/icon.png')
        self.assertEqual(self.guild.owner_id, '987654321')
        self.assertEqual(self.guild.member_count, 100)
        self.assertTrue(self.guild.is_available)
        self.assertIsNotNone(self.guild.joined_at)


class GuildSettingsModelTest(BotBaseTestCase):
    """Tests for the GuildSettings model"""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a test bot
        self.bot = Bot.objects.create(
            name='Test Bot',
            description='A test bot for unit tests',
            owner=self.user,
            token='mock_token',
            client_id='123456789',
            bot_user_id='987654321',
            is_active=True
        )
        
        # Create a test guild
        self.guild = Guild.objects.create(
            bot=self.bot,
            guild_id='123456789',
            name='Test Guild',
            owner_id='987654321',
            member_count=100,
            is_available=True
        )
        
        # Create test guild settings
        self.settings = GuildSettings.objects.create(
            guild=self.guild,
            prefix='!',
            custom_settings={
                'welcome_channel': '12345',
                'welcome_message': 'Hello {user}!'
            }
        )
    
    def test_settings_string_representation(self):
        """Test the string representation of GuildSettings"""
        self.assertEqual(str(self.settings), 'Settings for Test Guild')
    
    def test_settings_fields(self):
        """Test that settings fields are saved correctly"""
        self.assertEqual(self.settings.guild, self.guild)
        self.assertEqual(self.settings.prefix, '!')
        self.assertEqual(self.settings.custom_settings['welcome_channel'], '12345')
        self.assertEqual(self.settings.custom_settings['welcome_message'], 'Hello {user}!')
        
    def test_get_custom_setting(self):
        """Test the get_setting method"""
        self.assertEqual(self.settings.get_custom_setting('welcome_channel'), '12345')
        self.assertEqual(self.settings.get_custom_setting('welcome_message'), 'Hello {user}!')
        self.assertEqual(self.settings.get_custom_setting('nonexistent', 'default'), 'default')

    def test_set_custom_setting(self):
        """Test the set_setting method"""
        self.settings.set_custom_setting('new_setting', 'value')
        self.assertEqual(self.settings.custom_settings['new_setting'], 'value')
        # Change existing setting
        self.settings.set_custom_setting('welcome_channel', '67890')
        self.assertEqual(self.settings.custom_settings['welcome_channel'], '67890')


class GuildChannelModelTest(BotBaseTestCase):
    """Tests for the GuildChannel model"""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a test bot
        self.bot = Bot.objects.create(
            name='Test Bot',
            description='A test bot for unit tests',
            owner=self.user,
            token='mock_token',
            client_id='123456789',
            bot_user_id='987654321',
            is_active=True
        )
        
        # Create a test guild
        self.guild = Guild.objects.create(
            bot=self.bot,
            guild_id='123456789',
            name='Test Guild',
            owner_id='987654321',
            member_count=100,
            is_available=True
        )
        
        # Create a test channel
        self.channel = GuildChannel.objects.create(
            guild=self.guild,
            channel_id='987654321',
            name='test-channel',
            type=0,  # Text channel
            position=1,
            category_id='111222333',
            is_nsfw=False
        )
    
    def test_channel_string_representation(self):
        """Test the string representation of a GuildChannel"""
        self.assertEqual(str(self.channel), f"#{self.channel.name} ({self.channel.get_type_display()})")
    
    def test_channel_fields(self):
        """Test that channel fields are saved correctly"""
        self.assertEqual(self.channel.guild, self.guild)
        self.assertEqual(self.channel.channel_id, '987654321')
        self.assertEqual(self.channel.name, 'test-channel')
        self.assertEqual(self.channel.type, 0)
        self.assertEqual(self.channel.position, 1)
        self.assertEqual(self.channel.category_id, '111222333')
        self.assertFalse(self.channel.is_nsfw)
    
    def test_get_type_display(self):
        """Test the get_type_display method"""
        self.assertEqual(self.channel.get_type_display(), 'Text')
        
        # Test other channel types
        self.channel.type = 2
        self.channel.save()
        self.assertEqual(self.channel.get_type_display(), 'Voice')
        
        self.channel.type = 4
        self.channel.save()
        self.assertEqual(self.channel.get_type_display(), 'Category')
        
        # For an invalid type, Django returns the raw value
        # instead of None, so we just check that it's the right value
        self.channel.type = 999  # Unknown type
        self.channel.save()
        self.assertEqual(self.channel.get_type_display(), 999)