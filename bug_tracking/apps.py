"""
Django app configuration for the bug tracking application.
"""
from django.apps import AppConfig


class BugTrackingConfig(AppConfig):
    """Configuration for the bug tracking application."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bug_tracking'
    verbose_name = 'Bug Tracking'
    
    def ready(self):
        """
        Initialize signals when the app is ready.
        
        This imports and sets up signal handlers for the bug tracking app.
        """
        # Import signals to ensure they're registered
        import bug_tracking.signals  # noqa
        
        # Connect notification signals
        from bug_tracking.decorators import connect_notification_signals
        connect_notification_signals()