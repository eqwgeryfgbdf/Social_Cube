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
        
        # Sync application commands with Discord
        try:
            # Sync commands globally
            await self.tree.sync()
            logger.info(f"Synced application commands for bot {self.user.name}")
        except Exception as e:
            logger.error(f"Failed to sync commands for bot {self.user.name}: {str(e)}")
            
    async def on_guild_join(self, guild):
        """Event handler for when the bot joins a new guild"""
        logger.info(f"Bot {self.user.name} joined guild: {guild.name} (ID: {guild.id})")
        
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