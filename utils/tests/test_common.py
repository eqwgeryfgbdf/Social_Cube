"""
Tests for common utility functions.
"""
import json
import re
from datetime import datetime, date
from unittest.mock import patch, MagicMock

import pytest
import pytz
from django.conf import settings
from django.http import JsonResponse
from django.test import RequestFactory
from django.utils import timezone

from utils.common import (
    generate_unique_id,
    format_datetime,
    to_dict,
    ExtendedJSONEncoder,
    json_response,
    parse_json,
    truncate_string,
    sanitize_filename,
    get_client_ip,
    to_local_timezone,
    merge_dicts,
)


class TestGenerateUniqueId:
    """Tests for generate_unique_id function."""
    
    def test_unique_id_format(self):
        """Test that generated ID is a valid UUID string."""
        unique_id = generate_unique_id()
        
        # Check that it's a string
        assert isinstance(unique_id, str)
        
        # Check that it matches UUID format
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        assert re.match(uuid_pattern, unique_id)
    
    def test_unique_id_is_unique(self):
        """Test that generated IDs are unique."""
        ids = [generate_unique_id() for _ in range(100)]
        unique_ids = set(ids)
        
        # All IDs should be unique
        assert len(ids) == len(unique_ids)


class TestFormatDatetime:
    """Tests for format_datetime function."""
    
    def test_format_datetime_default(self):
        """Test formatting datetime with default parameters."""
        # Mock timezone.now() to return a fixed datetime
        fixed_now = datetime(2023, 1, 15, 14, 30, 45, tzinfo=pytz.UTC)
        
        with patch('django.utils.timezone.now', return_value=fixed_now):
            formatted = format_datetime()
            
            # Check the format matches expected
            assert formatted == "2023-01-15 14:30:45"
    
    def test_format_datetime_custom_format(self):
        """Test formatting datetime with custom format string."""
        dt = datetime(2023, 5, 20, 9, 15, 30, tzinfo=pytz.UTC)
        formatted = format_datetime(dt, "%d/%m/%Y %H:%M")
        
        # Check the format matches expected
        assert formatted == "20/05/2023 09:15"
    
    def test_format_datetime_naive(self):
        """Test formatting naive datetime (without timezone)."""
        naive_dt = datetime(2023, 3, 10, 12, 0, 0)
        formatted = format_datetime(naive_dt)
        
        # Should be timezone-aware now
        assert formatted == "2023-03-10 12:00:00"


class TestToDict:
    """Tests for to_dict function."""
    
    def test_to_dict_with_dict_object(self):
        """Test converting a dictionary to dictionary."""
        original = {'key': 'value', 'number': 123}
        result = to_dict(original)
        
        # Should return the same object
        assert result is original
    
    def test_to_dict_with_object(self):
        """Test converting an object with __dict__ to dictionary."""
        class TestObject:
            def __init__(self):
                self.public = 'value'
                self._private = 'hidden'
        
        obj = TestObject()
        result = to_dict(obj)
        
        # Should include public attributes but not private ones
        assert 'public' in result
        assert result['public'] == 'value'
        assert '_private' not in result
    
    def test_to_dict_with_to_dict_method(self):
        """Test converting an object with to_dict method."""
        class DictableObject:
            def to_dict(self):
                return {'custom': 'dict', 'from': 'method'}
        
        obj = DictableObject()
        result = to_dict(obj)
        
        # Should use the to_dict method
        assert result == {'custom': 'dict', 'from': 'method'}


class TestExtendedJSONEncoder:
    """Tests for ExtendedJSONEncoder class."""
    
    def test_json_encoder_with_datetime(self):
        """Test encoding datetime objects."""
        data = {'date': datetime(2023, 6, 15, 10, 30, 0, tzinfo=pytz.UTC)}
        encoded = json.dumps(data, cls=ExtendedJSONEncoder)
        
        # Should encode datetime as ISO format string
        expected = '{"date": "2023-06-15T10:30:00+00:00"}'
        assert encoded == expected
    
    def test_json_encoder_with_date(self):
        """Test encoding date objects."""
        data = {'date': date(2023, 6, 15)}
        encoded = json.dumps(data, cls=ExtendedJSONEncoder)
        
        # Should encode date as ISO format string
        expected = '{"date": "2023-06-15"}'
        assert encoded == expected
    
    def test_json_encoder_with_to_dict_method(self):
        """Test encoding objects with to_dict method."""
        class DictableObject:
            def to_dict(self):
                return {'converted': True}
        
        data = {'obj': DictableObject()}
        encoded = json.dumps(data, cls=ExtendedJSONEncoder)
        
        # Should use the to_dict method
        expected = '{"obj": {"converted": true}}'
        assert encoded == expected


class TestJsonResponse:
    """Tests for json_response function."""
    
    def test_json_response_basic(self):
        """Test creating a basic JSON response."""
        data = {'key': 'value', 'number': 123}
        response = json_response(data)
        
        # Check response type
        assert isinstance(response, JsonResponse)
        
        # Check status code
        assert response.status_code == 200
        
        # Check content
        content = json.loads(response.content.decode())
        assert content == data
    
    def test_json_response_with_status(self):
        """Test creating a JSON response with custom status code."""
        data = {'error': 'Not found'}
        response = json_response(data, status=404)
        
        # Check status code
        assert response.status_code == 404
    
    def test_json_response_with_headers(self):
        """Test creating a JSON response with custom headers."""
        data = {'result': 'success'}
        headers = {'X-Custom-Header': 'Test Value'}
        response = json_response(data, headers=headers)
        
        # Check custom header
        assert response['X-Custom-Header'] == 'Test Value'


class TestParseJson:
    """Tests for parse_json function."""
    
    def test_parse_json_valid(self):
        """Test parsing valid JSON string."""
        json_string = '{"key": "value", "numbers": [1, 2, 3]}'
        result = parse_json(json_string)
        
        # Check parsed data
        assert result == {'key': 'value', 'numbers': [1, 2, 3]}
    
    def test_parse_json_invalid(self):
        """Test parsing invalid JSON string."""
        invalid_json = '{not valid json}'
        default_value = {'default': True}
        result = parse_json(invalid_json, default=default_value)
        
        # Should return the default value
        assert result == default_value
    
    def test_parse_json_none(self):
        """Test parsing None value."""
        result = parse_json(None, default=[])
        
        # Should return the default value
        assert result == []


class TestTruncateString:
    """Tests for truncate_string function."""
    
    def test_truncate_string_short(self):
        """Test truncating a string shorter than max length."""
        text = "Short text"
        max_length = 20
        result = truncate_string(text, max_length)
        
        # Should return the original string
        assert result == text
    
    def test_truncate_string_long(self):
        """Test truncating a string longer than max length."""
        text = "This is a very long text that needs to be truncated"
        max_length = 20
        result = truncate_string(text, max_length)
        
        # Should truncate and add suffix
        assert len(result) <= max_length
        assert result.endswith("...")
        assert result == "This is a very lon..."
    
    def test_truncate_string_custom_suffix(self):
        """Test truncating a string with custom suffix."""
        text = "Another long text to truncate"
        max_length = 15
        suffix = " [more]"
        result = truncate_string(text, max_length, suffix)
        
        # Should truncate and add custom suffix
        assert len(result) <= max_length
        assert result.endswith(suffix)
        assert result == "Another [more]"
    
    def test_truncate_string_empty(self):
        """Test truncating an empty string."""
        text = ""
        result = truncate_string(text)
        
        # Should return empty string
        assert result == ""


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""
    
    def test_sanitize_filename_clean(self):
        """Test sanitizing an already clean filename."""
        filename = "clean_filename.txt"
        result = sanitize_filename(filename)
        
        # Should return the original filename
        assert result == filename
    
    def test_sanitize_filename_invalid_chars(self):
        """Test sanitizing a filename with invalid characters."""
        filename = "file*with?invalid:chars.txt"
        result = sanitize_filename(filename)
        
        # Should replace invalid chars with underscores
        assert result == "file_with_invalid_chars.txt"
    
    def test_sanitize_filename_whitespace(self):
        """Test sanitizing a filename with leading/trailing whitespace."""
        filename = "  filename_with_spaces.txt  "
        result = sanitize_filename(filename)
        
        # Should trim whitespace
        assert result == "filename_with_spaces.txt"
    
    def test_sanitize_filename_empty(self):
        """Test sanitizing an empty filename."""
        filename = ""
        result = sanitize_filename(filename)
        
        # Should return default filename
        assert result == "file"


class TestGetClientIp:
    """Tests for get_client_ip function."""
    
    def test_get_client_ip_direct(self):
        """Test getting client IP from direct connection."""
        factory = RequestFactory()
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        ip = get_client_ip(request)
        
        # Should return the REMOTE_ADDR
        assert ip == '192.168.1.1'
    
    def test_get_client_ip_forwarded(self):
        """Test getting client IP from X-Forwarded-For header."""
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 10.0.0.2, 10.0.0.3'
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        ip = get_client_ip(request)
        
        # Should return the first IP in X-Forwarded-For
        assert ip == '10.0.0.1'
    
    def test_get_client_ip_missing(self):
        """Test getting client IP when both headers are missing."""
        factory = RequestFactory()
        request = factory.get('/')
        
        # Remove relevant META keys
        request.META = {}
        
        ip = get_client_ip(request)
        
        # Should return empty string
        assert ip == ''


class TestToLocalTimezone:
    """Tests for to_local_timezone function."""
    
    def test_to_local_timezone_aware(self):
        """Test converting an aware datetime to local timezone."""
        utc_dt = datetime(2023, 7, 15, 10, 0, 0, tzinfo=pytz.UTC)
        local_tz = pytz.timezone('America/New_York')
        
        with patch('django.conf.settings.TIME_ZONE', 'America/New_York'):
            local_dt = to_local_timezone(utc_dt)
            
            # Should convert to the correct timezone
            assert local_dt.tzinfo.zone == 'America/New_York'
            
            # Time should be adjusted (UTC-4 or UTC-5 depending on DST)
            # July is during DST, so it should be UTC-4
            assert local_dt.hour == 6
    
    def test_to_local_timezone_naive(self):
        """Test converting a naive datetime to local timezone."""
        naive_dt = datetime(2023, 7, 15, 10, 0, 0)
        
        with patch('django.conf.settings.TIME_ZONE', 'America/New_York'):
            local_dt = to_local_timezone(naive_dt)
            
            # Should be made aware and converted to local timezone
            assert local_dt.tzinfo.zone == 'America/New_York'
    
    def test_to_local_timezone_custom_timezone(self):
        """Test converting a datetime to a specific timezone."""
        utc_dt = datetime(2023, 7, 15, 10, 0, 0, tzinfo=pytz.UTC)
        tokyo_dt = to_local_timezone(utc_dt, 'Asia/Tokyo')
        
        # Should convert to Tokyo timezone
        assert tokyo_dt.tzinfo.zone == 'Asia/Tokyo'
        
        # Tokyo is UTC+9
        assert tokyo_dt.hour == 19


class TestMergeDicts:
    """Tests for merge_dicts function."""
    
    def test_merge_dicts_simple(self):
        """Test merging two simple dictionaries."""
        dict1 = {'a': 1, 'b': 2}
        dict2 = {'c': 3, 'd': 4}
        result = merge_dicts(dict1, dict2)
        
        # Should include all keys from both dictionaries
        assert result == {'a': 1, 'b': 2, 'c': 3, 'd': 4}
    
    def test_merge_dicts_overlap(self):
        """Test merging dictionaries with overlapping keys."""
        dict1 = {'a': 1, 'b': 2, 'c': 3}
        dict2 = {'b': 20, 'c': 30, 'd': 40}
        result = merge_dicts(dict1, dict2)
        
        # Should override values from dict1 with values from dict2
        assert result == {'a': 1, 'b': 20, 'c': 30, 'd': 40}
    
    def test_merge_dicts_nested(self):
        """Test merging dictionaries with nested dictionaries."""
        dict1 = {'a': 1, 'nested': {'x': 10, 'y': 20}}
        dict2 = {'b': 2, 'nested': {'y': 30, 'z': 40}}
        result = merge_dicts(dict1, dict2)
        
        # Should recursively merge nested dictionaries
        assert result == {'a': 1, 'b': 2, 'nested': {'x': 10, 'y': 30, 'z': 40}}
    
    def test_merge_dicts_nested_non_dict(self):
        """Test merging where a non-dict value overrides a dict value."""
        dict1 = {'a': {'nested': 'dict'}}
        dict2 = {'a': 'string'}
        result = merge_dicts(dict1, dict2)
        
        # Non-dict values should override dict values
        assert result == {'a': 'string'}