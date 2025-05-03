from django.contrib import admin
from .models import Bot, BotLog, Guild, GuildSettings, GuildChannel

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

@admin.register(Guild)
class GuildAdmin(admin.ModelAdmin):
    list_display = ('name', 'guild_id', 'bot', 'member_count', 'is_available', 'last_sync')
    list_filter = ('is_available', 'bot', 'joined_at')
    search_fields = ('name', 'guild_id', 'owner_id')
    readonly_fields = ('joined_at', 'last_sync')
    fieldsets = (
        ('Guild Information', {
            'fields': ('bot', 'guild_id', 'name', 'owner_id', 'description')
        }),
        ('Server Details', {
            'fields': ('icon_url', 'region', 'member_count', 'features')
        }),
        ('Status', {
            'fields': ('is_available', 'joined_at', 'last_sync')
        }),
    )

@admin.register(GuildSettings)
class GuildSettingsAdmin(admin.ModelAdmin):
    list_display = ('guild', 'prefix', 'enable_welcome_messages', 'enable_moderation', 'updated_at')
    list_filter = ('enable_welcome_messages', 'enable_goodbye_messages', 'enable_moderation', 'enable_member_tracking')
    search_fields = ('guild__name', 'prefix', 'notification_channel_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Guild', {
            'fields': ('guild',)
        }),
        ('Command Settings', {
            'fields': ('prefix',)
        }),
        ('Notification Settings', {
            'fields': ('notification_channel_id', 'welcome_message', 'goodbye_message')
        }),
        ('Feature Toggles', {
            'fields': ('enable_welcome_messages', 'enable_goodbye_messages', 'enable_member_tracking', 'enable_moderation')
        }),
        ('Role Configuration', {
            'fields': ('admin_role_id', 'moderator_role_id')
        }),
        ('Custom Settings', {
            'fields': ('custom_settings',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(GuildChannel)
class GuildChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'guild', 'type', 'position', 'is_nsfw', 'last_sync')
    list_filter = ('type', 'is_nsfw', 'guild')
    search_fields = ('name', 'channel_id', 'topic', 'guild__name')
    readonly_fields = ('last_sync',)
    fieldsets = (
        ('Channel Information', {
            'fields': ('guild', 'channel_id', 'name', 'type')
        }),
        ('Details', {
            'fields': ('position', 'category_id', 'is_nsfw', 'topic')
        }),
        ('Timestamps', {
            'fields': ('last_sync',)
        }),
    )