from django.contrib import admin
from .models import RequestLog, AuditLog, ErrorLog


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'method', 'path', 'colored_status', 'duration', 'user', 'ip_address')
    list_filter = ('method', 'status_code', 'timestamp')
    search_fields = ('path', 'user__username', 'ip_address', 'user_agent')
    readonly_fields = ('timestamp', 'method', 'path', 'status_code', 'duration', 'user', 
                       'ip_address', 'user_agent', 'query_params', 'request_body', 'response_size')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        # Request logs should only be created by the middleware
        return False
    
    def has_change_permission(self, request, obj=None):
        # Request logs should not be modified
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'user', 'entity_type', 'entity_id', 'short_description')
    list_filter = ('action', 'entity_type', 'timestamp')
    search_fields = ('user__username', 'entity_type', 'entity_id', 'description')
    readonly_fields = ('timestamp', 'action', 'user', 'entity_type', 'entity_id', 
                       'entity_name', 'description', 'changes', 'additional_data', 'ip_address')
    date_hierarchy = 'timestamp'


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'colored_level', 'exception_type', 'message_brief', 'request_path')
    list_filter = ('level', 'timestamp')
    search_fields = ('exception_type', 'message', 'request_path', 'traceback')
    readonly_fields = ('timestamp', 'level', 'exception_type', 'message', 'request_path', 
                       'traceback', 'additional_data', 'user', 'ip_address', 'logger_name')
    date_hierarchy = 'timestamp'
    
    def message_brief(self, obj):
        """Display a truncated version of the message"""
        if len(obj.message) > 100:
            return f"{obj.message[:97]}..."
        return obj.message
    message_brief.short_description = "Message"