from django.contrib import admin
from .models import Bot, Command, CommandExecution
from .taskmaster.models import Task, TaskTag, TaskTagAssignment

# Bot models
@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    search_fields = ('name', 'owner__username')
    
@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ('name', 'bot', 'category', 'is_enabled')
    list_filter = ('category', 'is_enabled', 'bot')
    search_fields = ('name', 'description')

@admin.register(CommandExecution)
class CommandExecutionAdmin(admin.ModelAdmin):
    list_display = ('command', 'user_name', 'server_name', 'executed_at', 'is_success')
    list_filter = ('is_success', 'executed_at')
    search_fields = ('user_name', 'server_name', 'command__name')
    readonly_fields = ('command', 'user_id', 'user_name', 'server_id', 'server_name', 'channel_id', 'parameters', 'executed_at')

# Taskmaster models
class TaskTagAssignmentInline(admin.TabularInline):
    model = TaskTagAssignment
    extra = 1

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'due_date', 'user', 'created_at', 'is_overdue')
    list_filter = ('status', 'priority', 'created_at', 'user')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'
    inlines = [TaskTagAssignmentInline]

@admin.register(TaskTag)
class TaskTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)