from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages

from bot_management.models import Bot, BotLog
from bot_management.tests.test_models import BotBaseTestCase

class BotViewsTest(BotBaseTestCase):
    """Tests for the bot_management views"""
    
    def setUp(self):
        # Create a test client
        self.client = Client()
        
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
        
        # Login the test user
        self.client.login(username='testuser', password='password123')
    
    def test_bot_list_view(self):
        """Test the bot list view"""
        # Assuming there's a url named 'bot_list'
        url = reverse('bot_management:bot_list')
        response = self.client.get(url)
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the bot is in the context
        self.assertIn('bots', response.context)
        self.assertIn(self.bot, response.context['bots'])
    
    def test_bot_detail_view(self):
        """Test the bot detail view"""
        # Assuming there's a url named 'bot_detail' that takes a bot_id
        url = reverse('bot_management:bot_detail', args=[self.bot.id])
        response = self.client.get(url)
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the bot is in the context
        self.assertEqual(response.context['bot'], self.bot)
    
    def test_create_bot_view_get(self):
        """Test the GET request to the create bot view"""
        # Assuming there's a url named 'bot_create'
        url = reverse('bot_management:bot_create')
        response = self.client.get(url)
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the form is in the context
        self.assertIn('form', response.context)
    
    def test_create_bot_view_post(self):
        """Test the POST request to the create bot view"""
        # Assuming there's a url named 'bot_create'
        url = reverse('bot_management:bot_create')
        
        # Bot data to submit
        bot_data = {
            'name': 'New Test Bot',
            'description': 'A new test bot for unit tests',
            'token': 'new_mock_token',
            'client_id': '987654321',
            'bot_user_id': '123456789',
            'is_active': True
        }
        
        # Submit the form
        response = self.client.post(url, bot_data, follow=True)
        
        # Check that the bot was created
        self.assertTrue(Bot.objects.filter(name='New Test Bot').exists())
        
        # Check for a success message
        messages = list(get_messages(response.wsgi_request))
        self.assertGreater(len(messages), 0)
        
        # Check redirection to bot list
        # Assuming successful submission redirects to bot_list
        self.assertRedirects(response, reverse('bot_management:bot_list'))
    
    def test_update_bot_view(self):
        """Test the update bot view"""
        # Assuming there's a url named 'bot_update' that takes a bot_id
        url = reverse('bot_management:bot_update', args=[self.bot.id])
        
        # Updated bot data
        updated_data = {
            'name': 'Updated Test Bot',
            'description': 'An updated test bot for unit tests',
            'token': 'updated_mock_token',
            'client_id': '111222333',
            'bot_user_id': '444555666',
            'is_active': True
        }
        
        # Submit the form
        response = self.client.post(url, updated_data, follow=True)
        
        # Refresh the bot from the database
        self.bot.refresh_from_db()
        
        # Check that the bot was updated
        self.assertEqual(self.bot.name, 'Updated Test Bot')
        self.assertEqual(self.bot.description, 'An updated test bot for unit tests')
        self.assertEqual(self.bot.client_id, '111222333')
        self.assertEqual(self.bot.bot_user_id, '444555666')
        
        # Check redirection to bot detail
        # Assuming successful submission redirects to bot_detail
        self.assertRedirects(response, reverse('bot_management:bot_detail', args=[self.bot.id]))
    
    def test_delete_bot_view(self):
        """Test the delete bot view"""
        # Assuming there's a url named 'bot_delete' that takes a bot_id
        url = reverse('bot_management:bot_delete', args=[self.bot.id])
        
        # Submit the form
        response = self.client.post(url, follow=True)
        
        # Check that the bot was deleted
        self.assertFalse(Bot.objects.filter(id=self.bot.id).exists())
        
        # Check redirection to bot list
        # Assuming successful deletion redirects to bot_list
        self.assertRedirects(response, reverse('bot_management:bot_list'))