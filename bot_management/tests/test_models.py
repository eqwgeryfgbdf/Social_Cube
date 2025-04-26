from django.test import TestCase
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
import environ
import os

from bot_management.models import Bot, BotLog

class BotModelTest(TestCase):
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


class BotLogModelTest(TestCase):
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