"""
Common utility functions used across the Social Cube project.
This module contains reusable helper functions that don't fit into a specific domain.
"""
import json
import re
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union

import pytz
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.utils import timezone


def generate_unique_id() -> str:
    """Generate a unique ID using UUID4."""
    return str(uuid.uuid4())


def format_datetime(dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime object to a string using the specified format.
    
    Args:
        dt: The datetime object to format. Defaults to current time if None.
        format_str: The format string to use.
        
    Returns:
        A formatted datetime string.
    """
    if dt is None:
        dt = timezone.now()
    elif not timezone.is_aware(dt):
        dt = timezone.make_aware(dt)
    
    return dt.strftime(format_str)


def to_dict(obj: Any) -> Dict:
    """Convert an object to a dictionary.
    
    Args:
        obj: The object to convert.
        
    Returns:
        A dictionary representation of the object.
    """
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    else:
        return obj


class ExtendedJSONEncoder(DjangoJSONEncoder):
    """Extended JSON encoder that handles additional types."""
    
    def default(self, obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def json_response(data, status=200, headers=None):
    """Create a JSON response with proper content type and encoding.
    
    Args:
        data: The data to serialize to JSON.
        status: The HTTP status code.
        headers: Additional headers to include.
        
    Returns:
        A JsonResponse object.
    """
    response = JsonResponse(
        data,
        status=status,
        json_dumps_params={'cls': ExtendedJSONEncoder},
        safe=False
    )
    
    if headers:
        for header_name, header_value in headers.items():
            response[header_name] = header_value
    
    return response


def parse_json(json_string: str, default=None) -> Any:
    """Parse a JSON string safely, returning a default value if parsing fails.
    
    Args:
        json_string: The JSON string to parse.
        default: The default value to return if parsing fails.
        
    Returns:
        The parsed JSON data or the default value.
    """
    try:
        return json.loads(json_string)
    except (ValueError, TypeError):
        return default


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate a string to a maximum length, adding a suffix if truncated.
    
    Args:
        text: The string to truncate.
        max_length: The maximum length of the string.
        suffix: The suffix to add if the string is truncated.
        
    Returns:
        The truncated string.
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing invalid characters.
    
    Args:
        filename: The filename to sanitize.
        
    Returns:
        The sanitized filename.
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
    # Remove leading/trailing whitespace
    sanitized = sanitized.strip()
    # Ensure the filename is not empty
    if not sanitized:
        sanitized = "file"
    
    return sanitized


def get_client_ip(request) -> str:
    """Get the client IP address from a request.
    
    Args:
        request: The HTTP request.
        
    Returns:
        The client IP address.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def to_local_timezone(dt: datetime, tz_name: Optional[str] = None) -> datetime:
    """Convert a datetime to the local timezone.
    
    Args:
        dt: The datetime to convert.
        tz_name: The timezone name. Defaults to settings.TIME_ZONE.
        
    Returns:
        The datetime in the local timezone.
    """
    if not timezone.is_aware(dt):
        dt = timezone.make_aware(dt, timezone=pytz.UTC)
    
    target_tz = pytz.timezone(tz_name or settings.TIME_ZONE)
    return dt.astimezone(target_tz)


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Merge two dictionaries recursively.
    
    Args:
        dict1: The first dictionary.
        dict2: The second dictionary.
        
    Returns:
        A new dictionary with dict2 values merged into dict1.
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result