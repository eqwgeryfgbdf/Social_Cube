"""
Views for bug tracking notifications.

These views handle notification listing, marking as read, and notification preferences.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone

from bug_tracking.models import BugNotification, NotificationPreference
from bug_tracking.forms import NotificationPreferenceForm


@login_required
def notifications_list(request):
    """View for listing a user's bug notifications."""
    # Get filter parameter
    filter_type = request.GET.get('filter')
    
    # Start with all user's notifications
    notifications = BugNotification.objects.filter(user=request.user)
    
    # Apply filters
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'assigned':
        notifications = notifications.filter(notification_type=BugNotification.TYPE_ASSIGNMENT)
    elif filter_type == 'created':
        notifications = notifications.filter(notification_type=BugNotification.TYPE_NEW_BUG)
    elif filter_type == 'status':
        notifications = notifications.filter(notification_type=BugNotification.TYPE_STATUS_CHANGE)
    elif filter_type == 'comments':
        notifications = notifications.filter(notification_type=BugNotification.TYPE_COMMENT)
    
    # Paginate results
    paginator = Paginator(notifications, 20)  # 20 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Count unread notifications
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': page_obj,
        'unread_count': unread_count,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'filter': filter_type,
    }
    
    return render(request, 'bug_tracking/notifications.html', context)


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read."""
    notification = get_object_or_404(BugNotification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    # If AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
        
    # Otherwise redirect back to notifications page
    return redirect('bug_tracking:notifications')


@login_required
@require_POST
def mark_all_read(request):
    """Mark all notifications for the current user as read."""
    BugNotification.objects.filter(user=request.user, is_read=False).update(
        is_read=True
    )
    
    # If AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
        
    messages.success(request, 'All notifications marked as read.')
    return redirect('bug_tracking:notifications')


@login_required
def notification_settings(request):
    """View for managing notification preferences."""
    # Get or create user preferences
    preferences = NotificationPreference.get_or_create_for_user(request.user)
    
    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notification settings updated successfully.')
            return redirect('bug_tracking:notification_settings')
    else:
        form = NotificationPreferenceForm(instance=preferences)
    
    context = {
        'form': form,
    }
    
    return render(request, 'bug_tracking/notification_settings.html', context)


@login_required
def notification_count(request):
    """AJAX view to get current user's unread notification count."""
    count = BugNotification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})