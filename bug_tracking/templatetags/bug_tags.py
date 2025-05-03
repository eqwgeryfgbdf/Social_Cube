"""
Template tags and filters for the bug tracking application.
"""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Template filter to get a value from a dictionary using the key.
    
    Usage:
        {{ my_dict|get_item:key }}
    """
    return dictionary.get(key, 0)


@register.filter
def status_badge(status):
    """
    Template filter to render a status badge with the appropriate color.
    
    Usage:
        {{ bug.status|status_badge }}
    """
    status_classes = {
        'new': 'bg-blue-100 text-blue-800',
        'triaged': 'bg-yellow-100 text-yellow-800',
        'in_progress': 'bg-purple-100 text-purple-800',
        'resolved': 'bg-green-100 text-green-800',
        'closed': 'bg-gray-100 text-gray-800',
        'reopened': 'bg-red-100 text-red-800',
    }
    
    classes = status_classes.get(status, 'bg-gray-100 text-gray-800')
    
    return format_html(
        '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">{}</span>',
        classes,
        status.replace('_', ' ').title()
    )


@register.filter
def severity_badge(severity):
    """
    Template filter to render a severity badge with the appropriate color.
    
    Usage:
        {{ bug.severity|severity_badge }}
    """
    severity_classes = {
        'critical': 'bg-red-100 text-red-800',
        'high': 'bg-orange-100 text-orange-800',
        'medium': 'bg-yellow-100 text-yellow-800',
        'low': 'bg-green-100 text-green-800',
    }
    
    classes = severity_classes.get(severity, 'bg-blue-100 text-blue-800')
    
    return format_html(
        '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">{}</span>',
        classes,
        severity.title()
    )


@register.filter
def tag_badge(tag):
    """
    Template filter to render a tag badge with its color.
    
    Usage:
        {{ tag|tag_badge }}
    """
    # Use the tag's color if available, otherwise default to blue
    color = getattr(tag, 'color', '#3B82F6').lstrip('#')
    
    # Determine if we need dark or light text based on the background color
    r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    text_color = 'black' if luminance > 0.5 else 'white'
    
    return format_html(
        '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" '
        'style="background-color: #{0}; color: {1};">{2}</span>',
        color,
        text_color,
        tag.name
    )


@register.filter
def notification_icon(notification_type):
    """
    Template filter to render the appropriate icon for a notification type.
    
    Usage:
        {{ notification.notification_type|notification_icon }}
    """
    icons = {
        'new_bug': '<i class="fas fa-bug"></i>',
        'status_change': '<i class="fas fa-exchange-alt"></i>',
        'comment': '<i class="fas fa-comment"></i>',
        'assignment': '<i class="fas fa-user-check"></i>',
        'mention': '<i class="fas fa-at"></i>',
    }
    
    return mark_safe(icons.get(notification_type, '<i class="fas fa-bell"></i>'))


@register.inclusion_tag('bug_tracking/tags/notification_counter.html')
def notification_counter(user):
    """
    Template tag to render the unread notification counter.
    
    Usage:
        {% notification_counter user %}
    """
    if user.is_authenticated:
        count = user.bug_notifications.filter(is_read=False).count()
    else:
        count = 0
        
    return {'count': count}


@register.inclusion_tag('bug_tracking/tags/bug_status_label.html')
def bug_status_label(bug):
    """
    Template tag to render a status label with icon for a bug.
    
    Usage:
        {% bug_status_label bug %}
    """
    status_data = {
        'new': {
            'icon': 'fas fa-exclamation-circle',
            'color': 'text-blue-500',
            'label': 'New'
        },
        'triaged': {
            'icon': 'fas fa-clipboard-check',
            'color': 'text-yellow-500',
            'label': 'Triaged'
        },
        'in_progress': {
            'icon': 'fas fa-sync-alt fa-spin',
            'color': 'text-purple-500',
            'label': 'In Progress'
        },
        'resolved': {
            'icon': 'fas fa-check-circle',
            'color': 'text-green-500',
            'label': 'Resolved'
        },
        'closed': {
            'icon': 'fas fa-times-circle',
            'color': 'text-gray-500',
            'label': 'Closed'
        },
        'reopened': {
            'icon': 'fas fa-redo-alt',
            'color': 'text-red-500',
            'label': 'Reopened'
        },
    }
    
    return {
        'bug': bug,
        'status_data': status_data.get(bug.status, {
            'icon': 'fas fa-question-circle',
            'color': 'text-gray-500',
            'label': bug.get_status_display()
        })
    }