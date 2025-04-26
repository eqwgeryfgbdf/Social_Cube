from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Task, TaskTag, TaskTagAssignment, TaskStatus
from .forms import TaskForm, TaskTagForm


@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter options
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    search_query = request.GET.get('search', '')
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    pending_tasks = tasks.filter(status=TaskStatus.PENDING)
    in_progress_tasks = tasks.filter(status=TaskStatus.IN_PROGRESS)
    completed_tasks = tasks.filter(status=TaskStatus.COMPLETED)
    
    context = {
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
    }
    
    return render(request, 'dashboard/taskmaster/task_list.html', context)


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    return render(request, 'dashboard/taskmaster/task_detail.html', {'task': task})


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            
            # Handle tags
            tags = form.cleaned_data.get('tags')
            if tags:
                for tag in tags:
                    TaskTagAssignment.objects.create(task=task, tag=tag)
            
            messages.success(request, 'Task created successfully.')
            return redirect('dashboard:taskmaster:task_detail', pk=task.pk)
    else:
        form = TaskForm()
    
    return render(request, 'dashboard/taskmaster/task_form.html', {'form': form})


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            
            # Handle tags - first remove existing
            TaskTagAssignment.objects.filter(task=task).delete()
            
            # Add new tags
            tags = form.cleaned_data.get('tags')
            if tags:
                for tag in tags:
                    TaskTagAssignment.objects.create(task=task, tag=tag)
            
            messages.success(request, 'Task updated successfully.')
            return redirect('dashboard:taskmaster:task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'dashboard/taskmaster/task_form.html', {'form': form, 'task': task})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully.')
        return redirect('dashboard:taskmaster:task_list')
    
    return render(request, 'dashboard/taskmaster/task_confirm_delete.html', {'task': task})


@login_required
def task_toggle_status(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    if task.status == TaskStatus.COMPLETED:
        task.status = TaskStatus.PENDING
        messages.success(request, 'Task marked as pending.')
    else:
        task.status = TaskStatus.COMPLETED
        messages.success(request, 'Task marked as completed.')
    
    task.save()
    return redirect('dashboard:taskmaster:task_list')


@login_required
def tag_list(request):
    tags = TaskTag.objects.all().order_by('name')
    return render(request, 'dashboard/taskmaster/tag_list.html', {'tags': tags})


@login_required
def tag_create(request):
    if request.method == 'POST':
        form = TaskTagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag created successfully.')
            return redirect('dashboard:taskmaster:tag_list')
    else:
        form = TaskTagForm()
    
    return render(request, 'dashboard/taskmaster/tag_form.html', {'form': form})


@login_required
def tag_update(request, pk):
    tag = get_object_or_404(TaskTag, pk=pk)
    
    if request.method == 'POST':
        form = TaskTagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag updated successfully.')
            return redirect('dashboard:taskmaster:tag_list')
    else:
        form = TaskTagForm(instance=tag)
    
    return render(request, 'dashboard/taskmaster/tag_form.html', {'form': form, 'tag': tag})


@login_required
def tag_delete(request, pk):
    tag = get_object_or_404(TaskTag, pk=pk)
    
    if request.method == 'POST':
        tag.delete()
        messages.success(request, 'Tag deleted successfully.')
        return redirect('dashboard:taskmaster:tag_list')
    
    return render(request, 'dashboard/taskmaster/tag_confirm_delete.html', {'tag': tag})


@login_required
def dashboard(request):
    # Task statistics
    total_tasks = Task.objects.filter(user=request.user).count()
    completed_tasks = Task.objects.filter(user=request.user, status=TaskStatus.COMPLETED).count()
    pending_tasks = Task.objects.filter(user=request.user, status=TaskStatus.PENDING).count()
    in_progress_tasks = Task.objects.filter(user=request.user, status=TaskStatus.IN_PROGRESS).count()
    
    # Overdue tasks
    overdue_tasks = Task.objects.filter(
        user=request.user,
        due_date__lt=timezone.now(),
        status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
    )
    
    # Due soon tasks (within the next 24 hours)
    due_soon_tasks = Task.objects.filter(
        user=request.user,
        due_date__range=[timezone.now(), timezone.now() + timezone.timedelta(days=1)],
        status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
    )
    
    # Recent tasks
    recent_tasks = Task.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'overdue_tasks': overdue_tasks,
        'due_soon_tasks': due_soon_tasks,
        'recent_tasks': recent_tasks,
    }
    
    return render(request, 'dashboard/taskmaster/dashboard.html', context)