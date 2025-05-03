import time
import logging
import functools
from django.conf import settings
from logging_system.utils import log_error
from bot_management.models import Bot, BotLog

logger = logging.getLogger(__name__)

# Maximum number of retry attempts for bot operations
MAX_RETRY_ATTEMPTS = getattr(settings, 'BOT_MAX_RETRY_ATTEMPTS', 3)
# Delay between retry attempts in seconds
RETRY_DELAY = getattr(settings, 'BOT_RETRY_DELAY', 5)
# List of error types that should not trigger auto-recovery
PERMANENT_ERROR_TYPES = [
    'InvalidToken',
    'Unauthorized',
    'RateLimitExceeded',
    'ForbiddenBot',
    'IntentRequired'
]

def log_bot_error(bot, error_type, error_message, context=None):
    """
    Log a bot error both to the BotLog model and the logging system.
    
    Args:
        bot (Bot): The bot instance that encountered the error
        error_type (str): Type of error that occurred
        error_message (str): Detailed error message
        context (dict): Additional context data
    
    Returns:
        BotLog: The created bot log entry
    """
    # Create a BotLog entry
    bot_log = BotLog.objects.create(
        bot=bot,
        event_type='ERROR',
        description=f"{error_type}: {error_message}"
    )
    
    # Log to the system-wide error log
    log_error(
        exception_type=error_type,
        message=error_message,
        logger_name='bot_management',
        additional_data={
            'bot_id': bot.id,
            'bot_name': bot.name,
            'context': context or {}
        }
    )
    
    return bot_log


def recoverable_error(func):
    """
    Decorator for bot operations that should attempt automatic recovery after errors.
    
    This decorator will catch exceptions, log them, and attempt to retry the operation
    up to MAX_RETRY_ATTEMPTS times with a delay between attempts.
    
    Usage:
        @recoverable_error
        def start_bot(self, bot_id):
            # Implementation
    """
    @functools.wraps(func)
    def wrapper(self, bot_id, *args, **kwargs):
        bot = None
        retry_count = 0
        
        # Get the bot instance
        try:
            bot = Bot.objects.get(id=bot_id)
        except Bot.DoesNotExist:
            log_error(
                exception_type="BotNotFound",
                message=f"Bot with ID {bot_id} does not exist",
                logger_name='bot_management'
            )
            raise
        
        # Try the operation with retries
        while retry_count <= MAX_RETRY_ATTEMPTS:
            try:
                # Execute the wrapped function
                return func(self, bot_id, *args, **kwargs)
            
            except Exception as e:
                error_type = e.__class__.__name__
                error_message = str(e)
                
                # Log the error
                log_bot_error(
                    bot=bot,
                    error_type=error_type,
                    error_message=error_message,
                    context={
                        'function': func.__name__,
                        'retry_attempt': retry_count,
                        'args': args,
                        'kwargs': kwargs
                    }
                )
                
                # If this is a permanent error type, don't retry
                if error_type in PERMANENT_ERROR_TYPES:
                    logger.error(f"Permanent error encountered for bot {bot.name} (ID: {bot_id}): {error_type}")
                    
                    # Mark the bot as inactive if it's a token or permissions issue
                    if error_type in ['InvalidToken', 'Unauthorized', 'ForbiddenBot', 'IntentRequired']:
                        bot.is_active = False
                        bot.save(update_fields=['is_active'])
                        logger.warning(f"Bot {bot.name} (ID: {bot_id}) marked as inactive due to {error_type}")
                    
                    raise  # Re-raise the exception
                
                # If we've reached the maximum retries, give up
                if retry_count >= MAX_RETRY_ATTEMPTS:
                    logger.error(f"Maximum retry attempts ({MAX_RETRY_ATTEMPTS}) reached for bot {bot.name} (ID: {bot_id})")
                    raise  # Re-raise the exception
                
                # Increment retry counter and wait before retrying
                retry_count += 1
                logger.info(f"Retrying operation ({retry_count}/{MAX_RETRY_ATTEMPTS}) for bot {bot.name} (ID: {bot_id}) after {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
    
    return wrapper


def with_bot_error_handling(bot_field='bot'):
    """
    Decorator for view functions that handle bot operations.
    
    This decorator will catch exceptions, log them to both the bot log and the error log system,
    and return appropriate error messages to the user.
    
    Args:
        bot_field (str): The name of the parameter or kwarg that contains the Bot instance
        
    Usage:
        @with_bot_error_handling(bot_field='bot')
        def start_bot_view(request, bot_id):
            # Implementation
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(*args, **kwargs):
            try:
                # Execute the view function
                return view_func(*args, **kwargs)
            
            except Exception as e:
                # Try to extract the bot instance
                bot = None
                error_type = e.__class__.__name__
                error_message = str(e)
                
                # Look for the bot in kwargs
                if bot_field in kwargs:
                    if isinstance(kwargs[bot_field], Bot):
                        bot = kwargs[bot_field]
                    elif isinstance(kwargs[bot_field], int):
                        try:
                            bot = Bot.objects.get(id=kwargs[bot_field])
                        except Bot.DoesNotExist:
                            pass
                
                # If we found a bot, log to the bot log
                if bot:
                    log_bot_error(
                        bot=bot,
                        error_type=error_type,
                        error_message=error_message,
                        context={
                            'view': view_func.__name__,
                            'args': args,
                            'kwargs': {k: v for k, v in kwargs.items() if k != bot_field}
                        }
                    )
                
                # Always log to the system error log
                log_error(
                    exception=e,
                    logger_name='bot_management.views',
                    additional_data={
                        'view': view_func.__name__,
                        'bot_id': getattr(bot, 'id', None),
                        'bot_name': getattr(bot, 'name', None)
                    }
                )
                
                # Re-raise the exception for Django to handle
                raise
        
        return wrapper
    
    return decorator


class BotErrorHandler:
    """
    Helper class for handling bot errors and recovery attempts.
    
    This class provides methods for monitoring bot health, handling errors,
    and managing recovery attempts.
    """
    
    @staticmethod
    def check_bot_health(bot):
        """
        Check if a bot is healthy and running correctly.
        
        Args:
            bot (Bot): The bot instance to check
            
        Returns:
            tuple: (is_healthy, issues) where issues is a list of detected problems
        """
        issues = []
        
        # Check for recent errors
        recent_errors = BotLog.objects.filter(
            bot=bot,
            event_type='ERROR',
            timestamp__gte=time.time() - 3600  # Last hour
        ).count()
        
        if recent_errors >= 5:
            issues.append(f"Bot has {recent_errors} errors in the last hour")
        
        # Add other health checks as needed
        
        # Return results
        return len(issues) == 0, issues
    
    @staticmethod
    def attempt_recovery(bot, error_type=None, max_attempts=3):
        """
        Attempt to recover a bot that has encountered errors.
        
        Args:
            bot (Bot): The bot instance to recover
            error_type (str): The type of error that occurred, if known
            max_attempts (int): Maximum number of recovery attempts
            
        Returns:
            bool: Whether recovery was successful
        """
        # Log the recovery attempt
        BotLog.objects.create(
            bot=bot,
            event_type='SYSTEM',
            description=f"Attempting bot recovery (Error: {error_type or 'Unknown'})"
        )
        
        from bot_management.discord_bot.service import bot_manager
        
        # Handle different error types with specific recovery strategies
        if error_type in ['ConnectionError', 'Disconnected', 'NetworkError']:
            # For connection issues, simply restart the bot
            try:
                bot_manager.restart_bot(bot.id)
                
                # Log successful recovery
                BotLog.objects.create(
                    bot=bot,
                    event_type='SYSTEM',
                    description=f"Bot successfully recovered from {error_type}"
                )
                return True
            except Exception as e:
                # Log failed recovery
                BotLog.objects.create(
                    bot=bot,
                    event_type='ERROR',
                    description=f"Recovery failed: {e}"
                )
                return False
        
        # If we don't have a specific recovery strategy, just try restarting
        try:
            bot_manager.stop_bot(bot.id)
            time.sleep(2)  # Wait a bit before restarting
            bot_manager.start_bot(bot.id)
            
            # Log successful recovery
            BotLog.objects.create(
                bot=bot,
                event_type='SYSTEM',
                description="Bot successfully restarted as recovery attempt"
            )
            return True
        except Exception as e:
            # Log failed recovery
            BotLog.objects.create(
                bot=bot,
                event_type='ERROR',
                description=f"Recovery failed: {e}"
            )
            return False