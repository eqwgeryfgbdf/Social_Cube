from django.apps import AppConfig


class LoggingSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logging_system'
    verbose_name = 'Logging System'

    def ready(self):
        # Import signal handlers
        try:
            import logging_system.signals
        except ImportError:
            pass