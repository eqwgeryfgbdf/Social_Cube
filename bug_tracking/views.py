"""
Views for the bug tracking application.

These views provide the web interface for interacting with the bug tracking system.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.utils import timezone

from bug_tracking.models import (
    Bug, BugComment, BugAttachment, BugTag, 
    BugHistory, BugSubscription
)
from bug_tracking.forms import (
    BugForm, BugCommentForm, BugAttachmentForm, 
    BugTagForm, BugStatusForm, BugAssignForm
)

logger = logging.getLogger('bug_tracking')


@login_required
def bug_dashboard(request):
    """View for the bug tracking dashboard with statistics and summaries."""
    # Get counts by status
    status_counts = Bug.objects.values('status').annotate(count=Count('id'))
    status_data = {item['status']: item['count'] for item in status_counts}
    
    # Get counts by severity
    severity_counts = Bug.objects.values('severity').annotate(count=Count('id'))
    severity_data = {item['severity']: item['count'] for item in severity_counts}
    
    # Get recent bugs
    recent_bugs = Bug.objects.order_by('-created_at')[:5]
    
    # Get assigned bugs for current user
    assigned_bugs = Bug.objects.filter(
        assignee=request.user,
        status__in=[Bug.STATUS_NEW, Bug.STATUS_TRIAGED, Bug.STATUS_IN_PROGRESS]
    ).order_by('-created_at')[:5]
    
    # Get bugs by tags
    tag_counts = BugTag.objects.annotate(bug_count=Count('bugs')).filter(bug_count__gt=0)
    
    # Get open bug age distribution
    open_bugs = Bug.objects.filter(
        status__in=[Bug.STATUS_NEW, Bug.STATUS_TRIAGED, Bug.STATUS_IN_PROGRESS]
    )
    
    now = timezone.now()
    age_data = {
        'today': open_bugs.filter(created_at__gte=now.replace(hour=0, minute=0, second=0, microsecond=0)).count(),
        'this_week': open_bugs.filter(created_at__gte=now - timezone.timedelta(days=7)).count(),
        'this_month': open_bugs.filter(created_at__gte=now - timezone.timedelta(days=30)).count(),
        'older': open_bugs.filter(created_at__lt=now - timezone.timedelta(days=30)).count(),
    }
    
    context = {
        'status_data': status_data,
        'severity_data': severity_data,
        'recent_bugs': recent_bugs,
        'assigned_bugs': assigned_bugs,
        'tag_counts': tag_counts,
        'age_data': age_data,
        'total_bugs': Bug.objects.count(),
        'open_bugs': open_bugs.count(),
    }
    
    return render(request, 'bug_tracking/dashboard.html', context)


@login_required
def bug_list(request):
    """View for listing bugs with filtering options."""
    # Start with all bugs
    bugs = Bug.objects.all()
    
    # Apply filters
    status = request.GET.get('status')
    if status:
        bugs = bugs.filter(status=status)
    
    severity = request.GET.get('severity')
    if severity:
        bugs = bugs.filter(severity=severity)
    
    tag = request.GET.get('tag')
    if tag:
        bugs = bugs.filter(tags__id=tag)
    
    assigned_to = request.GET.get('assigned_to')
    if assigned_to:
        if assigned_to == 'me':
            bugs = bugs.filter(assignee=request.user)
        elif assigned_to == 'unassigned':
            bugs = bugs.filter(assignee__isnull=True)
        else:
            bugs = bugs.filter(assignee__id=assigned_to)
    
    reported_by = request.GET.get('reported_by')
    if reported_by:
        if reported_by == 'me':
            bugs = bugs.filter(reporter=request.user)
        else:
            bugs = bugs.filter(reporter__id=reported_by)
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        bugs = bugs.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Sorting
    sort = request.GET.get('sort', '-created_at')
    bugs = bugs.order_by(sort)
    
    # Pagination
    paginator = Paginator(bugs, 20)  # 20 bugs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get tags for filtering
    tags = BugTag.objects.all()
    
    context = {
        'page_obj': page_obj,
        'tags': tags,
        'status_choices': Bug.STATUS_CHOICES,
        'severity_choices': Bug.SEVERITY_CHOICES,
        'current_filters': {
            'status': status,
            'severity': severity,
            'tag': tag,
            'assigned_to': assigned_to,
            'reported_by': reported_by,
            'search': search,
            'sort': sort,
        }
    }
    
    return render(request, 'bug_tracking/bug_list.html', context)


@login_required
def bug_detail(request, pk):
    """View for displaying detailed bug information."""
    bug = get_object_or_404(Bug, pk=pk)
    
    # Get related data
    comments = bug.comments.all().order_by('created_at')
    attachments = bug.attachments.all().order_by('-created_at')
    history = bug.history.all().order_by('-timestamp')
    
    # Check if user is subscribed
    is_subscribed = BugSubscription.objects.filter(bug=bug, user=request.user).exists()
    
    # Forms for adding comments and attachments
    comment_form = BugCommentForm()
    attachment_form = BugAttachmentForm()
    
    # Forms for changing status and assignment
    status_form = BugStatusForm(instance=bug)
    assign_form = BugAssignForm(instance=bug)
    
    context = {
        'bug': bug,
        'comments': comments,
        'attachments': attachments,
        'history': history,
        'is_subscribed': is_subscribed,
        'comment_form': comment_form,
        'attachment_form': attachment_form,
        'status_form': status_form,
        'assign_form': assign_form,
    }
    
    return render(request, 'bug_tracking/bug_detail.html', context)


@login_required
def bug_create(request):
    """View for creating a new bug."""
    if request.method == 'POST':
        form = BugForm(request.POST)
        if form.is_valid():
            bug = form.save(commit=False)
            bug.reporter = request.user
            bug.save()
            
            # Handle tags
            if form.cleaned_data.get('tags'):
                bug.tags.set(form.cleaned_data['tags'])
            
            # Record in history
            BugHistory.objects.create(
                bug=bug,
                user=request.user,
                action=BugHistory.ACTION_CREATE
            )
            
            # Subscribe the reporter
            BugSubscription.objects.create(
                bug=bug,
                user=request.user
            )
            
            messages.success(request, 'Bug report created successfully!')
            return redirect('bug_tracking:bug_detail', pk=bug.pk)
    else:
        form = BugForm()
    
    context = {'form': form}
    return render(request, 'bug_tracking/bug_form.html', context)


@login_required
def bug_update(request, pk):
    """View for updating an existing bug."""
    bug = get_object_or_404(Bug, pk=pk)
    
    if request.method == 'POST':
        form = BugForm(request.POST, instance=bug)
        if form.is_valid():
            updated_bug = form.save()
            
            # Handle tags
            if 'tags' in form.cleaned_data:
                updated_bug.tags.set(form.cleaned_data['tags'])
            
            # Record in history
            BugHistory.objects.create(
                bug=updated_bug,
                user=request.user,
                action=BugHistory.ACTION_UPDATE
            )
            
            messages.success(request, 'Bug updated successfully!')
            return redirect('bug_tracking:bug_detail', pk=updated_bug.pk)
    else:
        form = BugForm(instance=bug)
    
    context = {'form': form, 'bug': bug}
    return render(request, 'bug_tracking/bug_form.html', context)


@login_required
@require_POST
def bug_delete(request, pk):
    """View for deleting a bug."""
    bug = get_object_or_404(Bug, pk=pk)
    
    # Only allow staff or the reporter to delete bugs
    if not (request.user.is_staff or request.user == bug.reporter):
        messages.error(request, 'You do not have permission to delete this bug.')
        return redirect('bug_tracking:bug_detail', pk=bug.pk)
    
    title = bug.title
    bug.delete()
    
    messages.success(request, f'Bug "{title}" has been deleted.')
    return redirect('bug_tracking:bug_list')


@login_required
@require_POST
def bug_assign(request, pk):
    """View for assigning a bug to a user."""
    bug = get_object_or_404(Bug, pk=pk)
    
    form = BugAssignForm(request.POST, instance=bug)
    if form.is_valid():
        old_assignee = bug.assignee
        updated_bug = form.save()
        
        # Record in history
        BugHistory.objects.create(
            bug=updated_bug,
            user=request.user,
            action=BugHistory.ACTION_ASSIGN,
            changes={
                'old_assignee': old_assignee.username if old_assignee else None,
                'new_assignee': updated_bug.assignee.username if updated_bug.assignee else None
            }
        )
        
        messages.success(request, 'Bug assignment updated successfully!')
    else:
        messages.error(request, 'Error updating bug assignment.')
    
    # Handle AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': form.is_valid(),
            'assignee': bug.assignee.username if bug.assignee else None
        })
    
    return redirect('bug_tracking:bug_detail', pk=bug.pk)


@login_required
@require_POST
def bug_change_status(request, pk):
    """View for changing the status of a bug."""
    bug = get_object_or_404(Bug, pk=pk)
    
    form = BugStatusForm(request.POST, instance=bug)
    if form.is_valid():
        old_status = bug.status
        updated_bug = form.save()
        
        # Record in history
        BugHistory.objects.create(
            bug=updated_bug,
            user=request.user,
            action=BugHistory.ACTION_STATUS_CHANGE,
            changes={
                'old_status': old_status,
                'new_status': updated_bug.status
            }
        )
        
        messages.success(request, 'Bug status updated successfully!')
    else:
        messages.error(request, 'Error updating bug status.')
    
    # Handle AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': form.is_valid(),
            'status': bug.get_status_display()
        })
    
    return redirect('bug_tracking:bug_detail', pk=bug.pk)


@login_required
@require_POST
def add_comment(request, pk):
    """View for adding a comment to a bug."""
    bug = get_object_or_404(Bug, pk=pk)
    
    form = BugCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.bug = bug
        comment.author = request.user
        comment.save()
        
        # Record in history
        BugHistory.objects.create(
            bug=bug,
            user=request.user,
            action=BugHistory.ACTION_COMMENT,
            comment=comment
        )
        
        messages.success(request, 'Comment added successfully!')
    else:
        messages.error(request, 'Error adding comment.')
    
    return redirect('bug_tracking:bug_detail', pk=bug.pk)


@login_required
@require_POST
def add_attachment(request, pk):
    """View for adding an attachment to a bug."""
    bug = get_object_or_404(Bug, pk=pk)
    
    form = BugAttachmentForm(request.POST, request.FILES)
    if form.is_valid():
        attachment = form.save(commit=False)
        attachment.bug = bug
        attachment.uploader = request.user
        attachment.save()
        
        # Record in history
        BugHistory.objects.create(
            bug=bug,
            user=request.user,
            action=BugHistory.ACTION_ATTACH,
            attachment=attachment
        )
        
        messages.success(request, 'Attachment added successfully!')
    else:
        messages.error(request, 'Error adding attachment.')
    
    return redirect('bug_tracking:bug_detail', pk=bug.pk)


@login_required
@require_POST
def bug_subscribe(request, pk):
    """View for subscribing to a bug."""
    bug = get_object_or_404(Bug, pk=pk)
    
    # Check if already subscribed
    subscription, created = BugSubscription.objects.get_or_create(
        bug=bug,
        user=request.user
    )
    
    if created:
        messages.success(request, 'You are now subscribed to this bug.')
    else:
        messages.info(request, 'You were already subscribed to this bug.')
    
    # Handle AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'subscribed': True})
    
    return redirect('bug_tracking:bug_detail', pk=bug.pk)


@login_required
@require_POST
def bug_unsubscribe(request, pk):
    """View for unsubscribing from a bug."""
    bug = get_object_or_404(Bug, pk=pk)
    
    # Try to find and delete subscription
    try:
        subscription = BugSubscription.objects.get(bug=bug, user=request.user)
        subscription.delete()
        messages.success(request, 'You have unsubscribed from this bug.')
        subscribed = False
    except BugSubscription.DoesNotExist:
        messages.info(request, 'You were not subscribed to this bug.')
        subscribed = False
    
    # Handle AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'subscribed': subscribed})
    
    return redirect('bug_tracking:bug_detail', pk=bug.pk)


@login_required
def tag_list(request):
    """View for listing and managing bug tags."""
    # Handle tag creation
    if request.method == 'POST':
        form = BugTagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag created successfully!')
            return redirect('bug_tracking:tag_list')
    else:
        form = BugTagForm()
    
    # Get all tags with bug counts
    tags = BugTag.objects.annotate(bug_count=Count('bugs'))
    
    context = {'tags': tags, 'form': form}
    return render(request, 'bug_tracking/tag_list.html', context)


@login_required
def tag_detail(request, pk):
    """View for displaying and editing a specific tag."""
    tag = get_object_or_404(BugTag, pk=pk)
    
    # Handle tag update
    if request.method == 'POST':
        form = BugTagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag updated successfully!')
            return redirect('bug_tracking:tag_list')
    else:
        form = BugTagForm(instance=tag)
    
    # Get bugs with this tag
    bugs = Bug.objects.filter(tags=tag)
    
    context = {'tag': tag, 'form': form, 'bugs': bugs}
    return render(request, 'bug_tracking/tag_detail.html', context)