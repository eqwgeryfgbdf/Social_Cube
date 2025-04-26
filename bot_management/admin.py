from django.contrib import admin
from .models import Bot, BotLog

@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'client_id', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'client_id', 'bot_user_id', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Bot Information', {
            'fields': ('name', 'description', 'avatar_url')
        }),
        ('Owner Information', {
            'fields': ('owner',)
        }),
        ('Discord Credentials', {
            'fields': ('token', 'client_id', 'bot_user_id'),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )

@admin.register(BotLog)
class BotLogAdmin(admin.ModelAdmin):
    list_display = ('bot', 'event_type', 'timestamp')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('bot__name', 'event_type', 'description')
    readonly_fields = ('timestamp',)
    fieldsets = (
        ('Event Information', {
            'fields': ('bot', 'event_type', 'description', 'timestamp')
        }),
    )