"""
Test fixtures for utility function tests.
"""
import json
import pytest
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.utils import timezone
from unittest.mock import MagicMock, patch

from utils.error_handling.exceptions import SocialCubeError, ExternalServiceError


@pytest.fixture
def request_factory():
    """Return a RequestFactory instance."""
    return RequestFactory()


@pytest.fixture
def mock_request(request_factory):
    """Return a mock request with session and messages attributes."""
    request = request_factory.get('/')
    middleware = SessionMiddleware(lambda x: x)
    middleware.process_request(request)
    request.session.save()
    
    # Add messages storage
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    return request


@pytest.fixture
def auth_user():
    """Create and return a standard authenticated user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='password123'
    )


@pytest.fixture
def admin_user():
    """Create and return an admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def future_timestamp():
    """Return a future timestamp (1 hour from now)."""
    return (timezone.now() + timedelta(hours=1)).isoformat()


@pytest.fixture
def past_timestamp():
    """Return a past timestamp (1 hour ago)."""
    return (timezone.now() - timedelta(hours=1)).isoformat()


@pytest.fixture
def mock_time():
    """Patch timezone.now to return a fixed time."""
    fixed_now = timezone.now()
    with patch('django.utils.timezone.now', return_value=fixed_now):
        yield fixed_now


@pytest.fixture
def sample_error_response():
    """Return a sample error response as would be returned by an API."""
    return {
        'error': True,
        'code': 'VALIDATION_ERROR',
        'message': 'Invalid input data',
        'details': {
            'field1': ['This field is required'],
            'field2': ['Value must be a positive number']
        }
    }


@pytest.fixture
def discord_mock_response():
    """Return a sample Discord API response."""
    return {
        'id': '12345678901234567',
        'username': 'TestUser',
        'discriminator': '1234',
        'avatar': 'abcdef123456789',
        'verified': True,
        'email': 'discord@example.com',
        'flags': 0,
        'banner': None,
        'accent_color': None,
        'premium_type': 0,
        'public_flags': 0
    }


@pytest.fixture
def mock_exception_handler():
    """Return a mock exception handler that logs exceptions."""
    mock_handler = MagicMock()
    
    def side_effect(exc, context=None):
        mock_handler.called_with = (exc, context)
        if isinstance(exc, SocialCubeError):
            return {'error': exc.to_dict()}
        return {'error': str(exc)}
    
    mock_handler.side_effect = side_effect
    return mock_handler


@pytest.fixture
def mock_external_service_error():
    """Return a mocked external service error."""
    return ExternalServiceError(
        message="External API failed",
        service="test_service",
        status_code=500,
        details={"reason": "Server error"}
    )


@pytest.fixture
def json_encoder_test_data():
    """Return test data for JSON encoding tests."""
    data = {
        'string': 'test',
        'number': 123,
        'date': datetime(2023, 1, 1, 12, 0, 0),
        'list': [1, 2, 3],
        'nested': {
            'key': 'value'
        }
    }
    return data