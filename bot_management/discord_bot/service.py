import asyncio
import logging
import threading
from typing import Dict, Optional, List, Tuple
import time
from concurrent.futures import ThreadPoolExecutor
from django.db import transaction
from functools import wraps

from bot_management.models import Bot, BotLog
from .client import SocialCubeBot
from bot_management.error_handling import recoverable_error, log_error

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
        
    @recoverable_error
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
            
            # Give the bot some time to connect
            time.sleep(5)  # Wait for 5 seconds
            
            # Sync commands after startup
            try:
                # Get all active commands for this bot
                from bot_management.models import Command
                
                # Check if bot has any commands to sync
                has_commands = Command.objects.filter(bot_id=bot_id, is_active=True).exists()
                
                if has_commands:
                    # Sync global commands
                    self.sync_all_commands(bot_id)
                    
                    # Get guilds with guild-specific commands
                    guild_ids = Command.objects.filter(
                        bot_id=bot_id,
                        guild__isnull=False,
                        is_active=True
                    ).values_list('guild__guild_id', flat=True).distinct()
                    
                    # Sync commands for each guild
                    for guild_id in guild_ids:
                        self.sync_all_commands(bot_id, guild_id)
                        
                    logger.info(f"Synced all commands for bot {bot_id}")
            except Exception as e:
                logger.error(f"Failed to sync commands for bot {bot_id}: {str(e)}")
                # Continue anyway since the bot is running
            
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
            
    @recoverable_error
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
            
    @recoverable_error
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
            
    @recoverable_error
    def sync_command(self, command_id: int) -> bool:
        """
        Sync a specific command to Discord
        
        Args:
            command_id: The database ID of the command to sync
            
        Returns:
            bool: True if successfully synced, False otherwise
        """
        from bot_management.models import Command
        
        try:
            # Get command from database
            command = Command.objects.get(id=command_id, is_active=True)
            
            # Get the bot client
            bot_id = command.bot.id
            if bot_id not in self.running_bots:
                logger.warning(f"Bot {bot_id} is not running, cannot sync command {command_id}")
                return False
                
            client, _, _ = self.running_bots[bot_id]
            
            # Wait until the bot is ready
            try:
                asyncio.run_coroutine_threadsafe(client.wait_until_ready(timeout=10), client.loop).result(timeout=15)
            except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
                logger.error(f"Timed out waiting for bot {bot_id} to be ready")
                return False
                
            # Convert command to Discord format
            command_data = command.to_discord_json()
            
            # Create or update the command on Discord
            if command.guild:
                # Guild-specific command
                guild_id = int(command.guild.guild_id)
                
                result = asyncio.run_coroutine_threadsafe(
                    client._sync_guild_command(guild_id, command.id, command_data),
                    client.loop
                ).result(timeout=15)
            else:
                # Global command
                result = asyncio.run_coroutine_threadsafe(
                    client._sync_global_command(command.id, command_data),
                    client.loop
                ).result(timeout=15)
                
            if result and 'id' in result:
                # Update the command_id
                command.command_id = result['id']
                command.save(update_fields=['command_id'])
                
                logger.info(f"Synced command {command.name} (ID: {command_id}) to Discord")
                return True
            else:
                logger.error(f"Failed to sync command {command.name} (ID: {command_id})")
                return False
                
        except Command.DoesNotExist:
            logger.error(f"Command {command_id} not found or not active")
            return False
        except Exception as e:
            logger.error(f"Failed to sync command {command_id}: {str(e)}")
            return False
            
    @recoverable_error
    def delete_command(self, command_id: int) -> bool:
        """
        Delete a specific command from Discord
        
        Args:
            command_id: The database ID of the command to delete
            
        Returns:
            bool: True if successfully deleted, False otherwise
        """
        from bot_management.models import Command
        
        try:
            # Get command from database
            command = Command.objects.get(id=command_id)
            
            # If no command_id, it was never synced to Discord
            if not command.command_id:
                logger.warning(f"Command {command_id} was never synced to Discord, nothing to delete")
                return True
                
            # Get the bot client
            bot_id = command.bot.id
            if bot_id not in self.running_bots:
                logger.warning(f"Bot {bot_id} is not running, cannot delete command {command_id}")
                return False
                
            client, _, _ = self.running_bots[bot_id]
            
            # Wait until the bot is ready
            try:
                asyncio.run_coroutine_threadsafe(client.wait_until_ready(timeout=10), client.loop).result(timeout=15)
            except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
                logger.error(f"Timed out waiting for bot {bot_id} to be ready")
                return False
                
            # Delete the command from Discord
            if command.guild:
                # Guild-specific command
                guild_id = int(command.guild.guild_id)
                discord_command_id = command.command_id
                
                success = asyncio.run_coroutine_threadsafe(
                    client._delete_guild_command(guild_id, discord_command_id),
                    client.loop
                ).result(timeout=15)
            else:
                # Global command
                discord_command_id = command.command_id
                
                success = asyncio.run_coroutine_threadsafe(
                    client._delete_global_command(discord_command_id),
                    client.loop
                ).result(timeout=15)
                
            if success:
                # Clear the command_id
                command.command_id = None
                command.save(update_fields=['command_id'])
                
                logger.info(f"Deleted command {command.name} (ID: {command_id}) from Discord")
                return True
            else:
                logger.error(f"Failed to delete command {command.name} (ID: {command_id})")
                return False
                
        except Command.DoesNotExist:
            logger.error(f"Command {command_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to delete command {command_id}: {str(e)}")
            return False
            
    @recoverable_error
    def sync_all_commands(self, bot_id: int, guild_id: str = None) -> bool:
        """
        Sync all commands for a bot, optionally filtered by guild
        
        Args:
            bot_id: The database ID of the bot
            guild_id: The Discord ID of the guild, or None for global commands
            
        Returns:
            bool: True if successfully synced, False otherwise
        """
        from bot_management.models import Command, Guild
        
        try:
            # Get the bot client
            if bot_id not in self.running_bots:
                logger.warning(f"Bot {bot_id} is not running, cannot sync commands")
                return False
                
            client, _, _ = self.running_bots[bot_id]
            
            # Wait until the bot is ready
            try:
                asyncio.run_coroutine_threadsafe(client.wait_until_ready(timeout=10), client.loop).result(timeout=15)
            except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
                logger.error(f"Timed out waiting for bot {bot_id} to be ready")
                return False
                
            # Get active commands for this bot
            commands_query = Command.objects.filter(bot_id=bot_id, is_active=True)
            
            if guild_id:
                # Guild-specific commands
                try:
                    guild = Guild.objects.get(bot_id=bot_id, guild_id=guild_id)
                    commands_query = commands_query.filter(guild=guild)
                except Guild.DoesNotExist:
                    logger.error(f"Guild {guild_id} not found for bot {bot_id}")
                    return False
                    
                # Prepare command data
                commands_data = [cmd.to_discord_json() for cmd in commands_query]
                
                # Sync all commands at once
                result = asyncio.run_coroutine_threadsafe(
                    client._bulk_sync_guild_commands(int(guild_id), commands_data),
                    client.loop
                ).result(timeout=30)  # Longer timeout for bulk operations
                
                # Update command IDs in the database
                if result:
                    self._update_command_ids(commands_query, result)
                    logger.info(f"Synced {len(commands_data)} commands for bot {bot_id} in guild {guild_id}")
                    return True
                else:
                    logger.error(f"Failed to sync commands for bot {bot_id} in guild {guild_id}")
                    return False
            else:
                # Global commands
                commands_query = commands_query.filter(guild__isnull=True)
                
                # Prepare command data
                commands_data = [cmd.to_discord_json() for cmd in commands_query]
                
                # Sync all commands at once
                result = asyncio.run_coroutine_threadsafe(
                    client._bulk_sync_global_commands(commands_data),
                    client.loop
                ).result(timeout=30)  # Longer timeout for bulk operations
                
                # Update command IDs in the database
                if result:
                    self._update_command_ids(commands_query, result)
                    logger.info(f"Synced {len(commands_data)} global commands for bot {bot_id}")
                    return True
                else:
                    logger.error(f"Failed to sync global commands for bot {bot_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to sync all commands for bot {bot_id}: {str(e)}")
            return False
            
    def _update_command_ids(self, commands_query, result_commands):
        """
        Update command IDs in the database based on the response from Discord
        
        Args:
            commands_query: QuerySet of Command objects
            result_commands: List of command data from Discord API
        """
        name_to_id = {cmd['name']: cmd['id'] for cmd in result_commands if 'name' in cmd and 'id' in cmd}
        
        for command in commands_query:
            if command.name in name_to_id:
                command.command_id = name_to_id[command.name]
        
        # Bulk update to improve performance
        Command.objects.bulk_update(commands_query, ['command_id'])
        
    @recoverable_error
    def sync_guild(self, bot_id: int, guild_id: str) -> bool:
        """
        Sync a specific guild with Discord API
        
        Args:
            bot_id: The database ID of the bot
            guild_id: The Discord ID of the guild to sync
            
        Returns:
            bool: True if successfully synced, False otherwise
        """
        # Check if bot is running
        if bot_id not in self.running_bots:
            logger.warning(f"Bot {bot_id} is not running, cannot sync guild {guild_id}")
            return False
            
        client, _, _ = self.running_bots[bot_id]
        
        try:
            # Find the guild in the bot's guilds
            discord_guild = None
            
            # Wait until the bot is ready
            try:
                asyncio.run_coroutine_threadsafe(client.wait_until_ready(timeout=10), client.loop).result(timeout=15)
                
                # Get the guild by ID
                discord_guild = asyncio.run_coroutine_threadsafe(
                    client.fetch_guild(int(guild_id)),
                    client.loop
                ).result(timeout=15)
                
            except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
                logger.error(f"Timed out waiting for bot {bot_id} to be ready")
                return False
            except Exception as e:
                logger.error(f"Failed to fetch guild {guild_id}: {str(e)}")
                return False
                
            if not discord_guild:
                logger.error(f"Guild {guild_id} not found for bot {bot_id}")
                return False
                
            # Sync the guild to the database
            asyncio.run_coroutine_threadsafe(
                client._sync_guild_to_db(discord_guild),
                client.loop
            ).result(timeout=15)
            
            # Sync the guild's channels
            asyncio.run_coroutine_threadsafe(
                client._sync_guild_channels(discord_guild),
                client.loop
            ).result(timeout=30)  # Longer timeout for channels
            
            logger.info(f"Successfully synced guild {guild_id} for bot {bot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync guild {guild_id} for bot {bot_id}: {str(e)}")
            return False
            
    @recoverable_error
    def sync_all_guilds(self, bot_id: int) -> bool:
        """
        Sync all guilds for a bot with Discord API
        
        Args:
            bot_id: The database ID of the bot
            
        Returns:
            bool: True if successfully synced, False otherwise
        """
        # Check if bot is running
        if bot_id not in self.running_bots:
            logger.warning(f"Bot {bot_id} is not running, cannot sync guilds")
            return False
            
        client, _, _ = self.running_bots[bot_id]
        
        try:
            # Wait until the bot is ready
            try:
                asyncio.run_coroutine_threadsafe(client.wait_until_ready(timeout=10), client.loop).result(timeout=15)
            except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
                logger.error(f"Timed out waiting for bot {bot_id} to be ready")
                return False
                
            # Sync all guilds
            asyncio.run_coroutine_threadsafe(
                client._sync_all_guilds(),
                client.loop
            ).result(timeout=60)  # Longer timeout for bulk operation
            
            # Log success
            from bot_management.models import BotLog
            BotLog.objects.create(
                bot_id=bot_id,
                event_type="ALL_GUILDS_SYNCED",
                description=f"All guilds synced for bot {bot_id}"
            )
            
            logger.info(f"Successfully synced all guilds for bot {bot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync all guilds for bot {bot_id}: {str(e)}")
            return False

# Create the singleton instance
bot_manager = BotManager()