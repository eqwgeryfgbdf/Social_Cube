from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.http import urlencode

from .models import Task, TaskTag, TaskTagAssignment, TaskDependency, TaskAuditLog


@login_required
def task_list(request):
    """View for displaying the task list with filtering and pagination."""
    # Get filter parameters
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    tag_id = request.GET.get('tag', '')
    search = request.GET.get('search', '')
    
    # Base queryset
    tasks = Task.objects.select_related('created_by', 'assigned_to')
    
    # Apply filters
    if status:
        tasks = tasks.filter(status=status)
    
    if priority:
        tasks = tasks.filter(priority=priority)
    
    if tag_id:
        tasks = tasks.filter(tags__tag_id=tag_id)
    
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Order by priority and created_at
    tasks = tasks.prefetch_related('tags__tag').order_by('-priority', '-created_at')
    
    # Get task stats
    task_stats = {
        'total': Task.objects.count(),
        'pending': Task.objects.filter(status='pending').count(),
        'in_progress': Task.objects.filter(status='in_progress').count(),
        'completed': Task.objects.filter(status='completed').count(),
        'other': Task.objects.exclude(status__in=['pending', 'in_progress', 'completed']).count()
    }
    
    # Paginate results
    paginator = Paginator(tasks, 10)  # 10 tasks per page
    page = request.GET.get('page')
    
    try:
        tasks = paginator.page(page)
    except PageNotAnInteger:
        tasks = paginator.page(1)
    except EmptyPage:
        tasks = paginator.page(paginator.num_pages)
    
    # Get available tags for filter dropdown
    available_tags = TaskTag.objects.all()
    
    # Build filter query for pagination links
    filter_query = {}
    if status:
        filter_query['status'] = status
    if priority:
        filter_query['priority'] = priority
    if tag_id:
        filter_query['tag'] = tag_id
    if search:
        filter_query['search'] = search
    
    filter_query_string = urlencode(filter_query)
    
    context = {
        'tasks': tasks,
        'stats': task_stats,
        'available_tags': available_tags,
        'filter_status': status,
        'filter_priority': priority,
        'filter_tag': tag_id,
        'filter_search': search,
        'filter_query': filter_query_string,
    }
    
    return render(request, 'task/list.html', context)


@login_required
def task_create(request):
    """View for creating a new task."""
    # Get data for form dropdowns
    available_tasks = Task.objects.exclude(status='completed').order_by('-created_at')[:50]
    available_tags = TaskTag.objects.all()
    available_users = User.objects.filter(is_active=True)
    
    context = {
        'available_tasks': available_tasks,
        'available_tags': available_tags,
        'available_users': available_users,
    }
    
    # If this is a POST request
    if request.method == 'POST':
        # Extract form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '')
        status = request.POST.get('status', 'pending')
        priority = request.POST.get('priority', 'medium')
        due_date = request.POST.get('due_date') or None
        details = request.POST.get('details', '')
        test_strategy = request.POST.get('test_strategy', '')
        
        # Validate required fields
        if not title:
            messages.error(request, 'Task title is required.')
            return render(request, 'task/create.html', context)
        
        # Create task
        task = Task.objects.create(
            title=title,
            description=description,
            status=status,
            priority=priority,
            due_date=due_date,
            details=details,
            test_strategy=test_strategy,
            created_by=request.user,
            source_type='web'
        )
        
        # Handle dependencies
        dependencies = request.POST.getlist('dependencies')
        for dep_id in dependencies:
            try:
                depends_on = Task.objects.get(id=dep_id)
                TaskDependency.objects.create(
                    task=task,
                    depends_on=depends_on
                )
            except Task.DoesNotExist:
                continue
        
        # Handle tags
        tags = request.POST.getlist('tags')
        for tag_id in tags:
            try:
                tag = TaskTag.objects.get(id=tag_id)
                TaskTagAssignment.objects.create(
                    task=task,
                    tag=tag
                )
            except TaskTag.DoesNotExist:
                continue
        
        # Handle assigned_to
        assigned_to_id = request.POST.get('assigned_to')
        if assigned_to_id:
            try:
                task.assigned_to = User.objects.get(id=assigned_to_id)
                task.save()
            except User.DoesNotExist:
                pass
        
        # Extract any custom metadata from form
        metadata = {}
        for key, value in request.POST.items():
            if key.startswith('meta_'):
                metadata[key[5:]] = value
        
        # Record in audit log
        audit_details = {'source': 'web'}
        if metadata:
            audit_details['metadata'] = metadata
            
        TaskAuditLog.objects.create(
            task=task,
            user=request.user,
            action='created',
            details=audit_details
        )
        
        # Set success message
        messages.success(request, f'Task "{task.title}" created successfully.')
        
        # Redirect based on save action
        save_action = request.POST.get('save_action', 'save')
        if save_action == 'save_and_new':
            return redirect('task:create')
        else:
            return redirect('task:list')
    
    return render(request, 'task/create.html', context)


@login_required
def task_detail(request, task_id):
    """View for displaying a task's details."""
    task = get_object_or_404(
        Task.objects.select_related('created_by', 'assigned_to'),
        id=task_id
    )
    
    # Get dependencies
    dependencies = TaskDependency.objects.select_related('depends_on').filter(task=task)
    dependent_tasks = TaskDependency.objects.select_related('task').filter(depends_on=task)
    
    # Get tags
    tags = TaskTagAssignment.objects.select_related('tag').filter(task=task)
    
    # Get audit logs
    audit_logs = TaskAuditLog.objects.select_related('user').filter(task=task).order_by('-timestamp')[:20]
    
    context = {
        'task': task,
        'dependencies': dependencies,
        'dependent_tasks': dependent_tasks,
        'tags': tags,
        'audit_logs': audit_logs,
    }
    
    return render(request, 'task/detail.html', context)


@login_required
def task_edit(request, task_id):
    """View for editing an existing task."""
    task = get_object_or_404(Task, id=task_id)
    
    # Get data for form dropdowns
    available_tasks = Task.objects.exclude(id=task_id).exclude(status='completed').order_by('-created_at')[:50]
    available_tags = TaskTag.objects.all()
    available_users = User.objects.filter(is_active=True)
    
    # Get current dependencies and tags
    dependencies = [dep.depends_on_id for dep in TaskDependency.objects.filter(task=task)]
    tags = [tag.tag_id for tag in TaskTagAssignment.objects.filter(task=task)]
    
    context = {
        'task': task,
        'available_tasks': available_tasks,
        'available_tags': available_tags,
        'available_users': available_users,
        'dependencies': dependencies,
        'tags': tags,
    }
    
    # If this is a POST request
    if request.method == 'POST':
        # Extract form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '')
        status = request.POST.get('status', 'pending')
        priority = request.POST.get('priority', 'medium')
        due_date = request.POST.get('due_date') or None
        details = request.POST.get('details', '')
        test_strategy = request.POST.get('test_strategy', '')
        
        # Validate required fields
        if not title:
            messages.error(request, 'Task title is required.')
            return render(request, 'task/edit.html', context)
        
        # Track changes
        changes = {}
        if task.title != title:
            changes['title'] = {'from': task.title, 'to': title}
        if task.description != description:
            changes['description'] = {'from': task.description, 'to': description}
        if task.status != status:
            changes['status'] = {'from': task.status, 'to': status}
        if task.priority != priority:
            changes['priority'] = {'from': task.priority, 'to': priority}
        if task.due_date != due_date:
            changes['due_date'] = {'from': str(task.due_date), 'to': str(due_date)}
        if task.details != details:
            changes['details'] = {'updated': True}
        if task.test_strategy != test_strategy:
            changes['test_strategy'] = {'updated': True}
        
        # Update task
        task.title = title
        task.description = description
        task.status = status
        task.priority = priority
        task.due_date = due_date
        task.details = details
        task.test_strategy = test_strategy
        
        # Handle assigned_to
        assigned_to_id = request.POST.get('assigned_to')
        if assigned_to_id:
            try:
                new_assigned_to = User.objects.get(id=assigned_to_id)
                if task.assigned_to != new_assigned_to:
                    changes['assigned_to'] = {
                        'from': str(task.assigned_to) if task.assigned_to else None,
                        'to': str(new_assigned_to)
                    }
                task.assigned_to = new_assigned_to
            except User.DoesNotExist:
                pass
        elif task.assigned_to:
            changes['assigned_to'] = {'from': str(task.assigned_to), 'to': None}
            task.assigned_to = None
        
        # Save task
        task.save()
        
        # Handle dependencies
        old_dependencies = set(dependencies)
        new_dependencies = set(map(int, request.POST.getlist('dependencies')))
        
        if old_dependencies != new_dependencies:
            changes['dependencies'] = {'updated': True}
            
            # Remove dependencies that are no longer selected
            TaskDependency.objects.filter(task=task).exclude(depends_on_id__in=new_dependencies).delete()
            
            # Add new dependencies
            for dep_id in new_dependencies - old_dependencies:
                try:
                    depends_on = Task.objects.get(id=dep_id)
                    TaskDependency.objects.create(
                        task=task,
                        depends_on=depends_on
                    )
                except Task.DoesNotExist:
                    continue
        
        # Handle tags
        old_tags = set(tags)
        new_tags = set(map(int, request.POST.getlist('tags')))
        
        if old_tags != new_tags:
            changes['tags'] = {'updated': True}
            
            # Remove tags that are no longer selected
            TaskTagAssignment.objects.filter(task=task).exclude(tag_id__in=new_tags).delete()
            
            # Add new tags
            for tag_id in new_tags - old_tags:
                try:
                    tag = TaskTag.objects.get(id=tag_id)
                    TaskTagAssignment.objects.create(
                        task=task,
                        tag=tag
                    )
                except TaskTag.DoesNotExist:
                    continue
        
        # Record in audit log if there were changes
        if changes:
            TaskAuditLog.objects.create(
                task=task,
                user=request.user,
                action='updated',
                details=changes
            )
        
        # Set success message
        messages.success(request, f'Task "{task.title}" updated successfully.')
        
        # Redirect to task detail page
        return redirect('task:detail', task_id=task.id)
    
    return render(request, 'task/edit.html', context)


@login_required
@require_POST
def task_toggle_status(request, task_id):
    """Toggle a task's status between completed and pending."""
    task = get_object_or_404(Task, id=task_id)
    
    # Toggle status
    old_status = task.status
    if task.status == 'completed':
        task.status = 'pending'
    else:
        task.status = 'completed'
    
    # Save task
    task.save()
    
    # Record in audit log
    TaskAuditLog.objects.create(
        task=task,
        user=request.user,
        action='status_changed',
        details={
            'status': {'from': old_status, 'to': task.status}
        }
    )
    
    # Handle AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'id': task.id,
            'title': task.title,
            'status': task.status,
            'status_display': task.get_status_display()
        })
    
    # Set success message
    status_msg = 'completed' if task.status == 'completed' else 'pending'
    messages.success(request, f'Task "{task.title}" marked as {status_msg}.')
    
    # Redirect back to the referring page
    return redirect(request.META.get('HTTP_REFERER', reverse('task:list')))


@login_required
@require_POST
def task_delete(request, task_id):
    """Delete a task."""
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user is allowed to delete (only creator or admin)
    if task.created_by != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to delete this task.")
        return redirect('task:detail', task_id=task.id)
    
    # Store task title for message
    task_title = task.title
    
    # Delete task (will cascade delete dependencies and tags)
    task.delete()
    
    # Set success message
    messages.success(request, f'Task "{task_title}" has been deleted.')
    
    # Redirect to task list
    return redirect('task:list')