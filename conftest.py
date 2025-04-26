import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()

@pytest.fixture
def client():
    """A Django test client instance."""
    return Client()

@pytest.fixture
def authenticated_client(client, django_user_model):
    """A Django test client instance with an authenticated user."""
    user = django_user_model.objects.create_user(username='testuser', password='testpass123')
    client.login(username='testuser', password='testpass123')
    return client

@pytest.fixture
def test_user(django_user_model):
    """Create a test user."""
    return django_user_model.objects.create_user(username='testuser', password='testpass123')

@pytest.fixture
def test_superuser(django_user_model):
    """Create a test superuser."""
    return django_user_model.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    ) 