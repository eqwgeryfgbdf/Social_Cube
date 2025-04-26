from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class BotManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bot_management"
    verbose_name = "Bot Management"
    
    def ready(self):
        """Initialize bot manager when the app is ready"""
        # Import bot_manager here to avoid circular imports
        from bot_management.discord_bot.service import bot_manager
        
        # Only start in main Django process, not in runserver reloader or other processes
        import sys
        if 'runserver' in sys.argv:
            # Don't auto-start bots in development server
            # Use the management command instead
            logger.info("Bot manager initialized. Use the botmanager command to start bots.")
        elif 'test' not in sys.argv:
            # In production, start the manager but not individual bots
            # Bots should be started via management command or admin interface
            try:
                bot_manager.start()
                logger.info("Bot manager service started.")
            except Exception as e:
                logger.error(f"Failed to start bot manager: {str(e)}")