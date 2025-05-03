from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count, Q
from django.utils import timezone
import datetime

from .models import RequestLog, AuditLog, ErrorLog


class StaffRequiredMixin(UserPassesTestMixin):
    """Only allow staff members to access these views"""
    def test_func(self):
        return self.request.user.is_staff


class DashboardView(StaffRequiredMixin, ListView):
    """Dashboard view showing summary of logs"""
    template_name = 'logging_system/dashboard.html'
    model = RequestLog  # Placeholder, not actually used for queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get time ranges
        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - datetime.timedelta(days=1)
        last_week = today - datetime.timedelta(days=7)
        
        # Request stats
        context['total_requests'] = RequestLog.objects.count()
        context['requests_today'] = RequestLog.objects.filter(timestamp__gte=today).count()
        context['requests_yesterday'] = RequestLog.objects.filter(
            timestamp__gte=yesterday, timestamp__lt=today).count()
        
        # Error stats
        context['total_errors'] = ErrorLog.objects.count()
        context['errors_today'] = ErrorLog.objects.filter(timestamp__gte=today).count()
        context['errors_yesterday'] = ErrorLog.objects.filter(
            timestamp__gte=yesterday, timestamp__lt=today).count()
        context['critical_errors'] = ErrorLog.objects.filter(level='CRITICAL').count()
        
        # Audit stats
        context['total_audit_logs'] = AuditLog.objects.count()
        context['audit_logs_today'] = AuditLog.objects.filter(timestamp__gte=today).count()
        
        # User activity
        context['active_users_today'] = RequestLog.objects.filter(
            timestamp__gte=today, user__isnull=False
        ).values('user').distinct().count()
        
        # Recent logs
        context['recent_errors'] = ErrorLog.objects.order_by('-timestamp')[:5]
        context['recent_audit_logs'] = AuditLog.objects.order_by('-timestamp')[:5]
        context['recent_requests'] = RequestLog.objects.order_by('-timestamp')[:5]
        
        return context


class RequestLogListView(StaffRequiredMixin, ListView):
    """View for listing request logs"""
    model = RequestLog
    template_name = 'logging_system/request_log_list.html'
    context_object_name = 'logs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-timestamp')
        
        # Apply filters if provided
        path = self.request.GET.get('path')
        if path:
            queryset = queryset.filter(path__icontains=path)
            
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status_code=status)
            
        method = self.request.GET.get('method')
        if method:
            queryset = queryset.filter(method=method)
            
        user = self.request.GET.get('user')
        if user:
            queryset = queryset.filter(user__username__icontains=user)
            
        ip = self.request.GET.get('ip')
        if ip:
            queryset = queryset.filter(ip_address__icontains=ip)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['methods'] = RequestLog.objects.values('method').distinct()
        context['status_codes'] = RequestLog.objects.values('status_code').distinct()
        return context


class RequestLogDetailView(StaffRequiredMixin, DetailView):
    """Detailed view of a request log"""
    model = RequestLog
    template_name = 'logging_system/request_log_detail.html'
    context_object_name = 'log'


class AuditLogListView(StaffRequiredMixin, ListView):
    """View for listing audit logs"""
    model = AuditLog
    template_name = 'logging_system/audit_log_list.html'
    context_object_name = 'logs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-timestamp')
        
        # Apply filters if provided
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)
            
        entity_type = self.request.GET.get('entity_type')
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
            
        user = self.request.GET.get('user')
        if user:
            queryset = queryset.filter(user__username__icontains=user)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actions'] = AuditLog.objects.values('action').distinct()
        context['entity_types'] = AuditLog.objects.values('entity_type').distinct().exclude(entity_type='')
        return context


class AuditLogDetailView(StaffRequiredMixin, DetailView):
    """Detailed view of an audit log"""
    model = AuditLog
    template_name = 'logging_system/audit_log_detail.html'
    context_object_name = 'log'


class ErrorLogListView(StaffRequiredMixin, ListView):
    """View for listing error logs"""
    model = ErrorLog
    template_name = 'logging_system/error_log_list.html'
    context_object_name = 'logs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-timestamp')
        
        # Apply filters if provided
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level=level)
            
        logger = self.request.GET.get('logger')
        if logger:
            queryset = queryset.filter(logger_name__icontains=logger)
            
        error_type = self.request.GET.get('error_type')
        if error_type:
            queryset = queryset.filter(exception_type__icontains=error_type)
            
        user = self.request.GET.get('user')
        if user:
            queryset = queryset.filter(user__username__icontains=user)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['levels'] = ErrorLog.objects.values('level').distinct()
        context['loggers'] = ErrorLog.objects.values('logger_name').distinct()
        context['error_types'] = ErrorLog.objects.values('exception_type').distinct().exclude(exception_type='')
        return context


class ErrorLogDetailView(StaffRequiredMixin, DetailView):
    """Detailed view of an error log"""
    model = ErrorLog
    template_name = 'logging_system/error_log_detail.html'
    context_object_name = 'log'