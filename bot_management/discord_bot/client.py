import discord
from discord import app_commands
import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from cryptography.fernet import Fernet
import environ
import os
import time
import random
import string
from functools import wraps

# Initialize environment variables
env = environ.Env()

# Configure logging
logger = logging.getLogger(__name__)

class SocialCubeBot(discord.Client):
    """Custom Discord client for Social Cube application"""
    
    def __init__(self, *, bot_id: int, token: str, owner_id: int, **options):
        """
        Initialize the bot client
        
        Args:
            bot_id: The database ID of the bot
            token: The encrypted Discord bot token
            owner_id: The user ID of the bot owner
            **options: Additional options for the discord.Client
        """
        # Set default intents for the bot
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        # Merge with any provided intents
        if 'intents' in options:
            provided_intents = options.pop('intents')
            for name, value in provided_intents.__dict__.items():
                if name.startswith('_'):
                    continue
                setattr(intents, name, value)
        
        # Pass the intents to the parent class
        super().__init__(intents=intents, **options)
        
        # Store bot configuration
        self.bot_id = bot_id
        self.encrypted_token = token
        self.owner_id = owner_id
        self.ready_event = asyncio.Event()
        
        # Bot status tracking
        self.startup_time = None
        self.last_heartbeat = None
        self.heartbeat_interval = 60  # seconds
        self.command_count = 0
        
        # Create the app_commands tree
        self.tree = app_commands.CommandTree(self)
        
        # Store for custom commands
        self.custom_commands = {}
        
    async def setup_hook(self) -> None:
        """Setup hook called before the bot connects to Discord"""
        await super().setup_hook()
        
        # Register default commands
        self.register_default_commands()
        
        # Start the heartbeat task
        self.heartbeat_task = self.loop.create_task(self._heartbeat_task())
        
    def register_default_commands(self) -> None:
        """Register default slash commands for the bot"""
        
        # Info command
        @self.tree.command(name="info", description="Get information about the bot")
        async def info(interaction: discord.Interaction):
            """Display information about the bot"""
            uptime = time.time() - self.startup_time if self.startup_time else 0
            days, remainder = divmod(uptime, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
            
            embed = discord.Embed(
                title=f"{self.user.name} Info",
                description="A bot managed by Social Cube",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Bot ID", value=str(self.user.id), inline=True)
            embed.add_field(name="Commands Used", value=str(self.command_count), inline=True)
            embed.add_field(name="Uptime", value=uptime_str, inline=True)
            
            embed.add_field(name="Guilds", value=str(len(self.guilds)), inline=True)
            embed.add_field(name="Users", value=str(sum(g.member_count for g in self.guilds)), inline=True)
            
            if self.user.avatar:
                embed.set_thumbnail(url=self.user.avatar.url)
                
            embed.set_footer(text="Powered by Social Cube")
            
            await interaction.response.send_message(embed=embed)
            self.command_count += 1
            
        # Help command
        @self.tree.command(name="help", description="Get help with bot commands")
        async def help_command(interaction: discord.Interaction):
            """Display help information for the bot"""
            embed = discord.Embed(
                title=f"{self.user.name} Help",
                description="Here are the available commands:",
                color=discord.Color.green()
            )
            
            # Get all registered commands
            commands = await self.tree.fetch_commands()
            
            for command in commands:
                embed.add_field(
                    name=f"/{command.name}",
                    value=command.description or "No description available",
                    inline=False
                )
                
            if self.user.avatar:
                embed.set_thumbnail(url=self.user.avatar.url)
                
            embed.set_footer(text="Powered by Social Cube")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            self.command_count += 1
            
    def decrypt_token(self) -> str:
        """Decrypt the bot token using the environment key"""
        key = env('BOT_TOKEN_KEY')
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.decrypt(self.encrypted_token.encode()).decode()
        
    async def start_bot(self) -> None:
        """Start the bot with the decrypted token"""
        try:
            decrypted_token = self.decrypt_token()
            await self.start(decrypted_token)
        except Exception as e:
            logger.error(f"Failed to start bot ID {self.bot_id}: {str(e)}")
            raise
            
    async def _heartbeat_task(self) -> None:
        """Task to periodically send heartbeat signals and monitor bot health"""
        try:
            while not self.is_closed():
                self.last_heartbeat = time.time()
                
                # Log connection status and basic metrics
                if self.is_ready():
                    logger.info(
                        f"Bot {self.bot_id} heartbeat: Connected to {len(self.guilds)} "
                        f"guilds with {sum(g.member_count for g in self.guilds)} users"
                    )
                
                await asyncio.sleep(self.heartbeat_interval)
        except asyncio.CancelledError:
            # Task was cancelled, clean shutdown
            pass
        except Exception as e:
            logger.error(f"Heartbeat task error for bot {self.bot_id}: {str(e)}")
            
    async def on_ready(self):
        """Event handler for when the bot is ready and connected to Discord"""
        logger.info(f"Bot {self.user.name} (ID: {self.user.id}) is connected to Discord")
        
        # Set startup time and mark as ready
        self.startup_time = time.time()
        self.ready_event.set()
        
        # Sync guilds to database
        try:
            logger.info(f"Syncing guilds for bot {self.user.name}")
            await self._sync_all_guilds()
        except Exception as e:
            logger.error(f"Failed to sync guilds for bot {self.user.name}: {str(e)}")
        
        # Sync application commands with Discord
        try:
            # Sync commands globally
            await self.tree.sync()
            logger.info(f"Synced application commands for bot {self.user.name}")
        except Exception as e:
            logger.error(f"Failed to sync commands for bot {self.user.name}: {str(e)}")
            
    async def _sync_all_guilds(self):
        """Sync all guilds to the database"""
        for guild in self.guilds:
            await self._sync_guild_to_db(guild)
            await self._sync_guild_channels(guild)
            
    async def _sync_guild_channels(self, guild):
        """Sync all channels for a guild to the database"""
        try:
            from bot_management.models import Guild, GuildChannel
            
            # Get the guild from the database
            try:
                guild_obj = await asyncio.to_thread(
                    Guild.objects.get,
                    bot_id=self.bot_id,
                    guild_id=str(guild.id)
                )
            except Guild.DoesNotExist:
                logger.error(f"Guild {guild.id} not found in database, cannot sync channels")
                return
                
            # Track existing channel IDs for cleanup
            existing_channels = set(await asyncio.to_thread(
                lambda: list(GuildChannel.objects.filter(
                    guild=guild_obj
                ).values_list('channel_id', flat=True))
            ))
            processed_channels = set()
            
            # Sync all channels
            for channel in guild.channels:
                # Prepare channel data
                channel_data = {
                    'name': channel.name,
                    'type': channel.type.value,
                    'position': getattr(channel, 'position', 0),
                    'category_id': str(channel.category_id) if getattr(channel, 'category_id', None) else None,
                    'is_nsfw': getattr(channel, 'nsfw', False),
                    'topic': getattr(channel, 'topic', None)
                }
                
                # Add to processed channels
                processed_channels.add(str(channel.id))
                
                # Update or create the channel
                try:
                    channel_obj, created = await asyncio.to_thread(
                        GuildChannel.objects.update_or_create,
                        guild=guild_obj,
                        channel_id=str(channel.id),
                        defaults=channel_data
                    )
                    
                    action = "created" if created else "updated"
                    logger.debug(f"Channel {channel.name} (ID: {channel.id}) {action} in database")
                except Exception as e:
                    logger.error(f"Failed to sync channel {channel.id}: {str(e)}")
            
            # Remove channels that no longer exist
            channels_to_remove = existing_channels - processed_channels
            if channels_to_remove:
                await asyncio.to_thread(
                    GuildChannel.objects.filter(
                        guild=guild_obj, 
                        channel_id__in=channels_to_remove
                    ).delete
                )
                logger.info(f"Removed {len(channels_to_remove)} deleted channels from database for guild {guild.id}")
                
            logger.info(f"Synced {len(processed_channels)} channels for guild {guild.id}")
            
        except Exception as e:
            logger.error(f"Failed to sync channels for guild {guild.id}: {str(e)}")
            
    async def on_guild_channel_create(self, channel):
        """Event handler for when a channel is created"""
        logger.info(f"Channel created: {channel.name} (ID: {channel.id}) in guild {channel.guild.id}")
        
        # Get the guild from database and sync the new channel
        try:
            # Only process guild channels
            if not hasattr(channel, 'guild'):
                return
                
            from bot_management.models import Guild, GuildChannel
            
            # Get guild object
            guild_obj = await asyncio.to_thread(
                Guild.objects.get,
                bot_id=self.bot_id,
                guild_id=str(channel.guild.id)
            )
            
            # Create channel data
            channel_data = {
                'name': channel.name,
                'type': channel.type.value,
                'position': getattr(channel, 'position', 0),
                'category_id': str(channel.category_id) if getattr(channel, 'category_id', None) else None,
                'is_nsfw': getattr(channel, 'nsfw', False),
                'topic': getattr(channel, 'topic', None)
            }
            
            # Create the channel
            await asyncio.to_thread(
                GuildChannel.objects.create,
                guild=guild_obj,
                channel_id=str(channel.id),
                **channel_data
            )
            
            logger.info(f"Channel {channel.name} (ID: {channel.id}) added to database")
            
        except Exception as e:
            logger.error(f"Failed to add channel {channel.id} to database: {str(e)}")
            
    async def on_guild_channel_delete(self, channel):
        """Event handler for when a channel is deleted"""
        logger.info(f"Channel deleted: {channel.name} (ID: {channel.id}) in guild {channel.guild.id}")
        
        # Remove the channel from database
        try:
            # Only process guild channels
            if not hasattr(channel, 'guild'):
                return
                
            from bot_management.models import GuildChannel
            
            # Delete the channel
            deleted = await asyncio.to_thread(
                GuildChannel.objects.filter(
                    channel_id=str(channel.id)
                ).delete
            )
            
            if deleted[0] > 0:
                logger.info(f"Channel {channel.id} removed from database")
            else:
                logger.warning(f"Channel {channel.id} not found in database")
                
        except Exception as e:
            logger.error(f"Failed to remove channel {channel.id} from database: {str(e)}")
            
    async def on_guild_channel_update(self, before, after):
        """Event handler for when a channel is updated"""
        logger.info(f"Channel updated: {after.name} (ID: {after.id}) in guild {after.guild.id}")
        
        # Update the channel in database
        try:
            # Only process guild channels
            if not hasattr(after, 'guild'):
                return
                
            from bot_management.models import Guild, GuildChannel
            
            # Get guild object
            guild_obj = await asyncio.to_thread(
                Guild.objects.get,
                bot_id=self.bot_id,
                guild_id=str(after.guild.id)
            )
            
            # Update channel data
            channel_data = {
                'name': after.name,
                'type': after.type.value,
                'position': getattr(after, 'position', 0),
                'category_id': str(after.category_id) if getattr(after, 'category_id', None) else None,
                'is_nsfw': getattr(after, 'nsfw', False),
                'topic': getattr(after, 'topic', None)
            }
            
            # Update the channel
            updated = await asyncio.to_thread(
                GuildChannel.objects.filter(
                    guild=guild_obj,
                    channel_id=str(after.id)
                ).update,
                **channel_data
            )
            
            if updated > 0:
                logger.info(f"Channel {after.name} (ID: {after.id}) updated in database")
            else:
                logger.warning(f"Channel {after.id} not found in database")
                
        except Exception as e:
            logger.error(f"Failed to update channel {after.id} in database: {str(e)}")
            
    async def on_guild_join(self, guild):
        """Event handler for when the bot joins a new guild"""
        logger.info(f"Bot {self.user.name} joined guild: {guild.name} (ID: {guild.id})")
        
        # Save guild information to database
        await self._sync_guild_to_db(guild)
        
        # If the guild has a system channel, send a welcome message
        if guild.system_channel:
            try:
                embed = discord.Embed(
                    title=f"Thanks for adding {self.user.name}!",
                    description="Use `/help` to see the list of available commands.",
                    color=discord.Color.blue()
                )
                
                if self.user.avatar:
                    embed.set_thumbnail(url=self.user.avatar.url)
                    
                embed.set_footer(text="Powered by Social Cube")
                
                await guild.system_channel.send(embed=embed)
            except Exception as e:
                logger.warning(f"Could not send welcome message to {guild.name}: {str(e)}")
                
    async def on_guild_remove(self, guild):
        """Event handler for when the bot is removed from a guild"""
        logger.info(f"Bot {self.user.name} removed from guild: {guild.name} (ID: {guild.id})")
        
        # Mark guild as unavailable in database
        try:
            from bot_management.models import Guild
            
            # Update in a separate thread to avoid blocking the bot
            await asyncio.to_thread(
                Guild.objects.filter(
                    bot_id=self.bot_id,
                    guild_id=str(guild.id)
                ).update,
                is_available=False
            )
            
            logger.info(f"Marked guild {guild.id} as unavailable in database")
        except Exception as e:
            logger.error(f"Failed to mark guild {guild.id} as unavailable: {str(e)}")
            
    async def on_guild_update(self, before, after):
        """Event handler for when a guild is updated"""
        logger.info(f"Guild updated: {after.name} (ID: {after.id})")
        
        # Update guild information in database
        await self._sync_guild_to_db(after)
        
    async def _sync_guild_to_db(self, guild):
        """Sync a guild's information to the database"""
        try:
            from bot_management.models import Guild, BotLog
            
            # Prepare guild data
            guild_data = {
                'name': guild.name,
                'guild_id': str(guild.id),
                'owner_id': str(guild.owner_id) if guild.owner_id else None,
                'icon_url': str(guild.icon.url) if guild.icon else None,
                'member_count': guild.member_count,
                'description': guild.description,
                'features': list(guild.features),
                'is_available': True
            }
            
            # Use asyncio.to_thread to run database operations in a separate thread
            guild_obj, created = await asyncio.to_thread(
                Guild.objects.update_or_create,
                bot_id=self.bot_id,
                guild_id=str(guild.id),
                defaults=guild_data
            )
            
            # Log the action
            action = "created" if created else "updated"
            await asyncio.to_thread(
                BotLog.objects.create,
                bot_id=self.bot_id,
                event_type="GUILD_SYNCED",
                description=f"Guild {guild.name} (ID: {guild.id}) {action} in database"
            )
            
            logger.info(f"Guild {guild.name} (ID: {guild.id}) {action} in database")
            return guild_obj
            
        except Exception as e:
            logger.error(f"Failed to sync guild {guild.id} to database: {str(e)}")
            return None
                
    async def wait_until_ready(self, timeout=None):
        """Wait until the bot is connected and ready"""
        await asyncio.wait_for(self.ready_event.wait(), timeout=timeout)
        
    def is_healthy(self) -> bool:
        """Check if the bot is healthy based on heartbeat and connection status"""
        # Bot must be connected
        if not self.is_ready():
            return False
            
        # Check last heartbeat time
        if self.last_heartbeat is None:
            return False
            
        # Ensure heartbeat is recent
        time_since_heartbeat = time.time() - self.last_heartbeat
        return time_since_heartbeat <= (self.heartbeat_interval * 2)
        
    async def _sync_global_command(self, command_id: int, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync a single global command with Discord
        
        Args:
            command_id: Database ID of the command
            command_data: Discord-compatible command data
            
        Returns:
            Dict: Discord API response or None if failed
        """
        try:
            # Ensure the bot is ready
            await self.wait_until_ready()
            
            # Log the action
            logger.info(f"Bot {self.bot_id} syncing global command: {command_data.get('name', 'Unknown')}") 
            
            # Create command using Discord API
            result = await self.http.upsert_global_command(self.user.id, command_data)
            
            # Log the result
            logger.info(f"Command {command_data.get('name')} synced with Discord ID: {result.get('id')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error syncing global command {command_data.get('name', 'Unknown')}: {str(e)}")
            return None
            
    async def _sync_guild_command(self, guild_id: int, command_id: int, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync a single guild command with Discord
        
        Args:
            guild_id: Discord ID of the guild
            command_id: Database ID of the command
            command_data: Discord-compatible command data
            
        Returns:
            Dict: Discord API response or None if failed
        """
        try:
            # Ensure the bot is ready
            await self.wait_until_ready()
            
            # Log the action
            logger.info(f"Bot {self.bot_id} syncing guild command: {command_data.get('name', 'Unknown')} for guild {guild_id}")
            
            # Create command using Discord API
            result = await self.http.upsert_guild_command(self.user.id, guild_id, command_data)
            
            # Log the result
            logger.info(f"Command {command_data.get('name')} synced for guild {guild_id} with Discord ID: {result.get('id')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error syncing guild command {command_data.get('name', 'Unknown')} for guild {guild_id}: {str(e)}")
            return None
            
    async def _delete_global_command(self, command_id: str) -> bool:
        """Delete a global command from Discord
        
        Args:
            command_id: Discord ID of the command to delete
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure the bot is ready
            await self.wait_until_ready()
            
            # Log the action
            logger.info(f"Bot {self.bot_id} deleting global command with Discord ID: {command_id}")
            
            # Delete command using Discord API
            await self.http.delete_global_command(self.user.id, command_id)
            
            # Log success
            logger.info(f"Global command with Discord ID {command_id} deleted successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting global command with Discord ID {command_id}: {str(e)}")
            return False
            
    async def _delete_guild_command(self, guild_id: int, command_id: str) -> bool:
        """Delete a guild command from Discord
        
        Args:
            guild_id: Discord ID of the guild
            command_id: Discord ID of the command to delete
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure the bot is ready
            await self.wait_until_ready()
            
            # Log the action
            logger.info(f"Bot {self.bot_id} deleting guild command with Discord ID: {command_id} from guild {guild_id}")
            
            # Delete command using Discord API
            await self.http.delete_guild_command(self.user.id, guild_id, command_id)
            
            # Log success
            logger.info(f"Guild command with Discord ID {command_id} deleted successfully from guild {guild_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting guild command with Discord ID {command_id} from guild {guild_id}: {str(e)}")
            return False
            
    async def _bulk_sync_global_commands(self, commands_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk sync global commands with Discord
        
        Args:
            commands_data: List of Discord-compatible command data
            
        Returns:
            List[Dict]: List of Discord API responses or None if failed
        """
        try:
            # Ensure the bot is ready
            await self.wait_until_ready()
            
            # Log the action
            logger.info(f"Bot {self.bot_id} bulk syncing {len(commands_data)} global commands")
            
            # Bulk update commands using Discord API
            result = await self.http.bulk_upsert_global_commands(self.user.id, commands_data)
            
            # Log success
            logger.info(f"Successfully bulk synced {len(result)} global commands")
            
            return result
            
        except Exception as e:
            logger.error(f"Error bulk syncing global commands: {str(e)}")
            return None
            
    async def _bulk_sync_guild_commands(self, guild_id: int, commands_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk sync guild commands with Discord
        
        Args:
            guild_id: Discord ID of the guild
            commands_data: List of Discord-compatible command data
            
        Returns:
            List[Dict]: List of Discord API responses or None if failed
        """
        try:
            # Ensure the bot is ready
            await self.wait_until_ready()
            
            # Log the action
            logger.info(f"Bot {self.bot_id} bulk syncing {len(commands_data)} commands for guild {guild_id}")
            
            # Bulk update commands using Discord API
            result = await self.http.bulk_upsert_guild_commands(self.user.id, guild_id, commands_data)
            
            # Log success
            logger.info(f"Successfully bulk synced {len(result)} commands for guild {guild_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error bulk syncing commands for guild {guild_id}: {str(e)}")
            return None