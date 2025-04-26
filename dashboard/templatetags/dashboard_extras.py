from django import template
import pprint

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get a specific key from a dictionary."""
    if not dictionary:
        return None
    return dictionary.get(key)

@register.filter
def pprint(obj):
    """Pretty print an object."""
    return pprint.pformat(obj, indent=2) 