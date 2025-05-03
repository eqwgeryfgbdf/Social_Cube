"""
Tests for error handling utilities.
"""
import json
from unittest.mock import patch, MagicMock

import pytest
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory

from utils.error_handling import (
    SocialCubeError,
    AuthenticationError,
    PermissionDeniedError,
    ResourceNotFoundError,
    ValidationError,
    ExternalServiceError,
    DiscordAPIError,
    handle_exception,
    log_exception,
    create_error_report,
    get_exception_handler,
    ErrorHandlingMiddleware,
    APIErrorMiddleware,
)


class TestExceptions:
    """Tests for custom exceptions."""
    
    def test_base_exception(self):
        """Test SocialCubeError base exception."""
        error = SocialCubeError("Test message")
        
        # Basic attributes
        assert str(error) == "Test message"
        assert error.message == "Test message"
        assert error.code == "SOCIAL_CUBE_ERROR"
        assert error.status_code == 500  # Default status code
        
        # Test dictionary representation
        error_dict = error.to_dict()
        assert error_dict["message"] == "Test message"
        assert error_dict["code"] == "SOCIAL_CUBE_ERROR"
        assert "details" in error_dict
    
    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        error = AuthenticationError("Authentication failed")
        
        assert error.code == "AUTHENTICATION_ERROR"
        assert error.status_code == 401
        assert str(error) == "Authentication failed"
    
    def test_permission_denied_error(self):
        """Test PermissionDeniedError exception."""
        error = PermissionDeniedError("Access denied", resource="test_resource")
        
        assert error.code == "PERMISSION_DENIED"
        assert error.status_code == 403
        assert error.details["resource"] == "test_resource"
    
    def test_resource_not_found_error(self):
        """Test ResourceNotFoundError exception."""
        error = ResourceNotFoundError("Resource not found", resource_id="123")
        
        assert error.code == "RESOURCE_NOT_FOUND"
        assert error.status_code == 404
        assert error.details["resource_id"] == "123"
    
    def test_validation_error(self):
        """Test ValidationError exception."""
        fields = {"name": ["This field is required"], "age": ["Must be positive"]}
        error = ValidationError("Validation error", fields=fields)
        
        assert error.code == "VALIDATION_ERROR"
        assert error.status_code == 400
        assert error.details["fields"] == fields
    
    def test_external_service_error(self):
        """Test ExternalServiceError exception."""
        error = ExternalServiceError(
            "API error", 
            service="test_api",
            status_code=503,
            details={"response": "Service Unavailable"}
        )
        
        assert error.code == "EXTERNAL_SERVICE_ERROR"
        assert error.status_code == 503
        assert error.details["service"] == "test_api"
    
    def test_discord_api_error(self):
        """Test DiscordAPIError exception."""
        response = {"code": 0, "message": "General error"}
        error = DiscordAPIError("Discord API error", response=response)
        
        assert error.code == "DISCORD_API_ERROR"
        assert error.details["response"] == response


class TestExceptionHandlers:
    """Tests for exception handlers."""
    
    def test_handle_exception_social_cube_error(self):
        """Test handling a SocialCubeError."""
        error = ValidationError("Invalid data", fields={"name": ["Required"]})
        result = handle_exception(error)
        
        # Should return a dictionary with error details
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert result["error"]["message"] == "Invalid data"
    
    def test_handle_exception_standard_error(self):
        """Test handling a standard Python exception."""
        error = ValueError("Invalid value")
        result = handle_exception(error)
        
        # Should return a dictionary with error details
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"]["code"] == "SERVER_ERROR"
        assert "Invalid value" in result["error"]["message"]
    
    @patch("utils.error_handling.handlers.logging")
    def test_log_exception(self, mock_logging):
        """Test logging an exception."""
        error = ResourceNotFoundError("User not found", resource_id="123")
        log_exception(error, level="error")
        
        # Should log the error with correct level
        mock_logging.error.assert_called_once()
        
        # Log message should contain error details
        log_args = mock_logging.error.call_args[0]
        assert "User not found" in log_args[0]
    
    @patch("utils.error_handling.handlers.uuid.uuid4")
    @patch("utils.error_handling.handlers.logging")
    def test_create_error_report(self, mock_logging, mock_uuid):
        """Test creating an error report."""
        mock_uuid.return_value = "test-uuid"
        
        # Create a request mock
        factory = RequestFactory()
        request = factory.get("/test/path")
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.username = "test_user"
        
        # Create an error
        try:
            raise ValueError("Test error")
        except ValueError as e:
            error = e
            report = create_error_report(error, request)
        
        # Check report contents
        assert report["error_id"] == "test-uuid"
        assert report["path"] == "/test/path"
        assert report["user"] == "test_user"
        assert report["ip_address"] == "127.0.0.1"
        assert "traceback" in report
        assert "Test error" in report["message"]
        
        # Should log the report
        mock_logging.error.assert_called_once()
    
    def test_get_exception_handler(self):
        """Test getting the appropriate exception handler."""
        # For SocialCubeError
        error = AuthenticationError("Not authenticated")
        handler = get_exception_handler(error)
        
        # Should return handle_exception
        from utils.error_handling.handlers import handle_exception as expected_handler
        assert handler == expected_handler
        
        # For standard error
        error = TypeError("Type error")
        handler = get_exception_handler(error)
        
        # Should return handle_exception
        assert handler == expected_handler


class TestMiddleware:
    """Tests for error handling middleware."""
    
    def test_error_handling_middleware(self):
        """Test the ErrorHandlingMiddleware."""
        # Create a mock response
        def get_response(request):
            raise ValueError("Test error")
        
        # Create the middleware
        middleware = ErrorHandlingMiddleware(get_response)
        
        # Create a request
        factory = RequestFactory()
        request = factory.get("/test/path")
        
        # Process the request
        with patch("utils.error_handling.middleware.handle_exception") as mock_handler:
            mock_handler.return_value = {"error": "Handled error"}
            
            # This should catch the error
            response = middleware(request)
            
            # Check that handle_exception was called
            mock_handler.assert_called_once()
            
            # Check response
            assert isinstance(response, HttpResponse)
            assert response.status_code == 500
    
    def test_api_error_middleware(self):
        """Test the APIErrorMiddleware."""
        # Create a mock response
        def get_response(request):
            raise ValidationError("Invalid data", fields={"name": ["Required"]})
        
        # Create the middleware
        middleware = APIErrorMiddleware(get_response)
        
        # Create a request
        factory = RequestFactory()
        request = factory.get("/api/test")
        
        # Process the request
        response = middleware(request)
        
        # Check response
        assert isinstance(response, JsonResponse)
        assert response.status_code == 400
        
        # Check response content
        content = json.loads(response.content.decode())
        assert content["error"]["code"] == "VALIDATION_ERROR"
        assert content["error"]["message"] == "Invalid data"
    
    def test_api_error_middleware_non_api_path(self):
        """Test the APIErrorMiddleware with a non-API path."""
        # Create a mock response that works normally
        def get_response(request):
            return HttpResponse("OK")
        
        # Create the middleware
        middleware = APIErrorMiddleware(get_response)
        
        # Create a request to a non-API path
        factory = RequestFactory()
        request = factory.get("/not-api/test")
        
        # Process the request
        response = middleware(request)
        
        # Should pass through to the view
        assert isinstance(response, HttpResponse)
        assert response.content == b"OK"