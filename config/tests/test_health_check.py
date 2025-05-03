from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
from django.db.utils import OperationalError
import redis
import socket


class HealthCheckTestCase(TestCase):
    """Test the health check endpoint to ensure it correctly reports system health."""

    def setUp(self):
        """Set up the test client."""
        self.client = Client()

    def test_health_check_success(self):
        """Test that the health check returns 200 OK when all systems are healthy."""
        response = self.client.get('/health/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        self.assertTrue(response.json()['components']['database'])
        self.assertTrue(response.json()['components']['redis'])
        self.assertTrue(response.json()['components']['application'])
        self.assertEqual(len(response.json()['errors']), 0)

    @patch('config.health_views.connections')
    def test_database_failure(self, mock_connections):
        """Test that the health check reports database failures correctly."""
        # Configure the mock to raise an OperationalError when cursor() is called
        mock_db_conn = MagicMock()
        mock_db_conn.cursor.side_effect = OperationalError("Database connection error")
        mock_connections.__getitem__.return_value = mock_db_conn
        
        response = self.client.get('/health/')
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['status'], 'error')
        self.assertFalse(response.json()['components']['database'])
        self.assertTrue(response.json()['components']['redis'])
        self.assertTrue(response.json()['components']['application'])
        self.assertEqual(len(response.json()['errors']), 1)
        self.assertIn("Database error", response.json()['errors'][0])

    @patch('config.health_views.redis.Redis')
    def test_redis_failure(self, mock_redis_client):
        """Test that the health check reports Redis failures correctly."""
        # Configure the mock to raise a RedisError when ping() is called
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.side_effect = redis.exceptions.RedisError("Redis connection error")
        mock_redis_client.return_value = mock_redis_instance
        
        # Mock the settings to indicate Redis is required
        with patch('config.health_views.settings') as mock_settings:
            mock_settings.CHANNEL_LAYERS = {
                'default': {'BACKEND': 'channels_redis.core.RedisChannelLayer'}
            }
            
            response = self.client.get('/health/')
            
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json()['status'], 'error')
            self.assertTrue(response.json()['components']['database'])
            self.assertFalse(response.json()['components']['redis'])
            self.assertTrue(response.json()['components']['application'])
            self.assertEqual(len(response.json()['errors']), 1)
            self.assertIn("Redis error", response.json()['errors'][0])

    @patch('config.health_views.redis.Redis')
    def test_redis_failure_not_required(self, mock_redis_client):
        """Test that the health check doesn't mark the system as unhealthy when Redis fails but isn't required."""
        # Configure the mock to raise a RedisError when ping() is called
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.side_effect = redis.exceptions.RedisError("Redis connection error")
        mock_redis_client.return_value = mock_redis_instance
        
        # Mock the settings to indicate Redis is NOT required
        with patch('config.health_views.settings') as mock_settings:
            mock_settings.CHANNEL_LAYERS = {
                'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}
            }
            
            response = self.client.get('/health/')
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['status'], 'ok')
            self.assertTrue(response.json()['components']['database'])
            self.assertFalse(response.json()['components']['redis'])
            self.assertTrue(response.json()['components']['application'])
            self.assertEqual(len(response.json()['errors']), 0)

    @patch('config.health_views.redis.Redis')
    def test_socket_timeout(self, mock_redis_client):
        """Test that the health check handles socket timeouts correctly."""
        # Configure the mock to raise a socket.error when ping() is called
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.side_effect = socket.error("Socket timeout")
        mock_redis_client.return_value = mock_redis_instance
        
        # Mock the settings to indicate Redis is required
        with patch('config.health_views.settings') as mock_settings:
            mock_settings.CHANNEL_LAYERS = {
                'default': {'BACKEND': 'channels_redis.core.RedisChannelLayer'}
            }
            
            response = self.client.get('/health/')
            
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json()['status'], 'error')
            self.assertTrue(response.json()['components']['database'])
            self.assertFalse(response.json()['components']['redis'])
            self.assertTrue(response.json()['components']['application'])
            self.assertEqual(len(response.json()['errors']), 1)
            self.assertIn("Redis error", response.json()['errors'][0])