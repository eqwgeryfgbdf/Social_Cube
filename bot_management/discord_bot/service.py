import asyncio
import logging
import threading
from typing import Dict, Optional, List, Tuple
import time
from concurrent.futures import ThreadPoolExecutor
from django.db import transaction

from bot_management.models import Bot, BotLog
from .client import SocialCubeBot

# Configure logging
logger = logging.getLogger(__name__)

class BotManager:
    """
    Service for managing multiple Discord bot instances
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one bot manager exists"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BotManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize the bot manager"""
        # Only initialize once
        if self._initialized:
            return
            
        self.running_bots: Dict[int, Tuple[SocialCubeBot, asyncio.Task, threading.Thread]] = {}
        self.loop = None
        self.health_check_interval = 300  # 5 minutes
        self.health_check_task = None
        self._initialized = True
        logger.info("Bot Manager initialized")
        
    def start(self):
        """Start the bot manager service"""
        if not self.loop:
            # Create a new event loop for the manager
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Start health check task
            self.health_check_task = self.loop.create_task(self._health_check_loop())
            
            logger.info("Bot Manager service started")
            
    def stop(self):
        """Stop the bot manager and all running bots"""
        # Cancel the health check task
        if self.health_check_task:
            self.health_check_task.cancel()
            
        # Stop all running bots
        for bot_id in list(self.running_bots.keys()):
            self.stop_bot(bot_id)
            
        # Close the event loop
        if self.loop:
            self.loop.stop()
            
        logger.info("Bot Manager service stopped")
        
    def start_bot(self, bot_id: int) -> bool:
        """
        Start a specific bot by its ID
        
        Args:
            bot_id: The database ID of the bot to start
            
        Returns:
            bool: True if successfully started, False otherwise
        """
        # Check if bot is already running
        if bot_id in self.running_bots:
            logger.warning(f"Bot {bot_id} is already running")
            return False
            
        try:
            # Get bot from database
            bot_model = Bot.objects.get(id=bot_id, is_active=True)
            
            # Create the bot client
            client = SocialCubeBot(
                bot_id=bot_id,
                token=bot_model.token,
                owner_id=bot_model.owner.id
            )
            
            # Create and start the bot thread
            def run_bot_thread():
                # Each bot gets its own event loop in its own thread
                bot_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(bot_loop)
                
                # Start the bot
                bot_task = None
                try:
                    bot_task = bot_loop.create_task(client.start_bot())
                    bot_loop.run_forever()
                except Exception as e:
                    logger.error(f"Error in bot {bot_id} thread: {str(e)}")
                finally:
                    # Clean up
                    if bot_task and not bot_task.done():
                        bot_task.cancel()
                    bot_loop.close()
                    
            # Create and start thread
            bot_thread = threading.Thread(
                target=run_bot_thread,
                name=f"Bot-{bot_id}",
                daemon=True
            )
            bot_thread.start()
            
            # Store references
            self.running_bots[bot_id] = (client, None, bot_thread)
            
            # Log the start
            BotLog.objects.create(
                bot=bot_model,
                event_type="BOT_STARTED",
                description=f"Bot started by Bot Manager"
            )
            
            logger.info(f"Started bot {bot_id} ({bot_model.name})")
            return True
            
        except Bot.DoesNotExist:
            logger.error(f"Bot {bot_id} not found or not active")
            return False
        except Exception as e:
            logger.error(f"Failed to start bot {bot_id}: {str(e)}")
            return False
            
    def stop_bot(self, bot_id: int) -> bool:
        """
        Stop a specific bot by its ID
        
        Args:
            bot_id: The database ID of the bot to stop
            
        Returns:
            bool: True if successfully stopped, False otherwise
        """
        # Check if bot is running
        if bot_id not in self.running_bots:
            logger.warning(f"Bot {bot_id} is not running")
            return False
            
        try:
            client, _, thread = self.running_bots[bot_id]
            
            # Close the client connection
            asyncio.run_coroutine_threadsafe(client.close(), client.loop)
            
            # Remove from running bots
            del self.running_bots[bot_id]
            
            # Log the stop
            try:
                bot_model = Bot.objects.get(id=bot_id)
                BotLog.objects.create(
                    bot=bot_model,
                    event_type="BOT_STOPPED",
                    description=f"Bot stopped by Bot Manager"
                )
            except Bot.DoesNotExist:
                # Bot might have been deleted from the database
                pass
                
            logger.info(f"Stopped bot {bot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop bot {bot_id}: {str(e)}")
            return False
            
    def restart_bot(self, bot_id: int) -> bool:
        """
        Restart a specific bot by its ID
        
        Args:
            bot_id: The database ID of the bot to restart
            
        Returns:
            bool: True if successfully restarted, False otherwise
        """
        if self.stop_bot(bot_id):
            # Wait briefly for the bot to fully stop
            time.sleep(2)
            return self.start_bot(bot_id)
        return False
        
    def get_bot_status(self, bot_id: int) -> Dict:
        """
        Get the status of a specific bot
        
        Args:
            bot_id: The database ID of the bot
            
        Returns:
            Dict: Status information about the bot
        """
        status = {
            "running": False,
            "connected": False,
            "healthy": False,
            "guilds": 0,
            "users": 0,
            "uptime": 0,
            "commands_used": 0
        }
        
        # Check if bot is running
        if bot_id in self.running_bots:
            client, _, _ = self.running_bots[bot_id]
            status["running"] = True
            
            # Get additional status if client is connected
            if client.is_ready():
                status["connected"] = True
                status["healthy"] = client.is_healthy()
                status["guilds"] = len(client.guilds)
                status["users"] = sum(g.member_count for g in client.guilds)
                
                if client.startup_time:
                    status["uptime"] = time.time() - client.startup_time
                    
                status["commands_used"] = client.command_count
                
        return status
        
    def get_all_bots_status(self) -> Dict[int, Dict]:
        """
        Get status for all running bots
        
        Returns:
            Dict[int, Dict]: Dictionary mapping bot IDs to their status
        """
        result = {}
        for bot_id in self.running_bots:
            result[bot_id] = self.get_bot_status(bot_id)
        return result
        
    async def _health_check_loop(self):
        """Background task to perform regular health checks on all bots"""
        try:
            while True:
                await self._perform_health_check()
                await asyncio.sleep(self.health_check_interval)
        except asyncio.CancelledError:
            # Task was cancelled, clean shutdown
            pass
        except Exception as e:
            logger.error(f"Health check task error: {str(e)}")
            
    async def _perform_health_check(self):
        """Perform health checks on all running bots"""
        logger.info("Performing health check on all bots")
        
        for bot_id in list(self.running_bots.keys()):
            try:
                status = self.get_bot_status(bot_id)
                
                # Check if bot is running but not healthy
                if status["running"] and not status["healthy"]:
                    logger.warning(f"Bot {bot_id} is not healthy, attempting to restart")
                    
                    # Log the unhealthy state
                    try:
                        bot_model = Bot.objects.get(id=bot_id)
                        BotLog.objects.create(
                            bot=bot_model,
                            event_type="BOT_UNHEALTHY",
                            description="Bot detected as unhealthy during health check"
                        )
                    except Bot.DoesNotExist:
                        pass
                        
                    # Restart the bot in a separate thread to avoid blocking
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        executor.submit(self.restart_bot, bot_id)
                        
            except Exception as e:
                logger.error(f"Health check failed for bot {bot_id}: {str(e)}")
                
    def start_active_bots(self):
        """Start all active bots from the database"""
        try:
            # Get all active bots from the database
            active_bots = Bot.objects.filter(is_active=True)
            
            for bot in active_bots:
                # Don't start already running bots
                if bot.id not in self.running_bots:
                    self.start_bot(bot.id)
                    
            logger.info(f"Started {len(active_bots)} active bots")
            
        except Exception as e:
            logger.error(f"Failed to start active bots: {str(e)}")
            
# Create the singleton instance
bot_manager = BotManager()