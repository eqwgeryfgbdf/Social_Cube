import discord
from discord.ext import commands
import asyncio
import threading
import logging

# 設置詳細的日誌記錄
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class DiscordBot:
    _instances = {}
    
    @classmethod
    def get_instance(cls, bot_config):
        if bot_config.id in cls._instances:
            return cls._instances[bot_config.id]
        instance = cls(bot_config)
        cls._instances[bot_config.id] = instance
        return instance

    def __init__(self, bot_config):
        self.bot_config = bot_config
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        self.client = commands.Bot(command_prefix='!', intents=intents)
        self._thread = None
        self.is_running = False
        self._bot_ready = threading.Event()
        
        # 添加事件處理器
        @self.client.event
        async def on_ready():
            logger.info(f'Bot {self.client.user} (ID: {self.client.user.id}) has connected to Discord!')
            logger.info(f'Connected to {len(self.client.guilds)} guilds:')
            for guild in self.client.guilds:
                logger.info(f'- {guild.name} (ID: {guild.id})')
                for channel in guild.text_channels:
                    logger.info(f'  - Channel: {channel.name} (ID: {channel.id})')
            self._bot_ready.set()

        @self.client.event
        async def on_guild_join(guild):
            logger.info(f'Bot joined guild: {guild.name} (ID: {guild.id})')

        @self.client.event
        async def on_error(event, *args, **kwargs):
            logger.error(f'Discord event error in {event}:', exc_info=True)

    def start(self):
        if self.is_running:
            logger.info(f'Bot {self.bot_config.name} is already running')
            return
        
        logger.info(f'Starting bot {self.bot_config.name}...')
        self._bot_ready.clear()
        self._thread = threading.Thread(target=self._run_bot)
        self._thread.daemon = True
        self._thread.start()
        self.is_running = True

    def stop(self):
        if not self.is_running:
            logger.info(f'Bot {self.bot_config.name} is not running')
            return
        
        logger.info(f'Stopping bot {self.bot_config.name}...')
        async def stop_bot():
            await self.client.close()
        
        future = asyncio.run_coroutine_threadsafe(stop_bot(), self.client.loop)
        try:
            future.result(timeout=5.0)
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
        self._thread.join()
        self.is_running = False
        self._bot_ready.clear()
        if self.bot_config.id in self._instances:
            del self._instances[self.bot_config.id]

    def send_test_message(self, channel_id, message="Test message from bot"):
        if not self.is_running:
            logger.error("Attempted to send message while bot is not running")
            raise RuntimeError("Bot is not running")

        logger.info(f'Waiting for bot {self.bot_config.name} to be ready...')
        if not self._bot_ready.wait(timeout=10.0):
            logger.error("Bot ready timeout")
            raise RuntimeError("Bot is not ready yet")
        
        async def send_message():
            try:
                logger.debug(f'Attempting to get channel {channel_id}...')
                channel = self.client.get_channel(int(channel_id))
                
                if channel is None:
                    logger.debug(f'Channel not found via get_channel, trying fetch_channel...')
                    try:
                        channel = await self.client.fetch_channel(int(channel_id))
                    except discord.NotFound:
                        logger.error(f"Channel {channel_id} not found")
                        raise ValueError(f"Channel with ID {channel_id} not found")
                    except discord.Forbidden:
                        logger.error(f"No access to channel {channel_id}")
                        raise ValueError(f"Bot doesn't have permission to access channel {channel_id}")
                
                logger.info(f'Found channel: {channel.name} (ID: {channel.id}) in guild: {channel.guild.name}')
                
                if not isinstance(channel, discord.TextChannel):
                    logger.error(f"Channel {channel_id} is not a text channel")
                    raise ValueError(f"Channel {channel_id} is not a text channel")
                
                permissions = channel.permissions_for(channel.guild.me)
                logger.debug(f'Bot permissions in channel {channel.name}: {permissions.value}')
                if not permissions.send_messages:
                    logger.error(f"No permission to send messages in channel {channel_id}")
                    raise ValueError(f"Bot doesn't have permission to send messages in channel {channel_id}")
                
                logger.info(f'Sending message to channel {channel.name}: {message}')
                await channel.send(message)
                logger.info('Message sent successfully')
                return True
            except Exception as e:
                logger.error(f"Error sending message: {str(e)}", exc_info=True)
                raise RuntimeError(f"Failed to send message: {str(e)}")

        try:
            future = asyncio.run_coroutine_threadsafe(send_message(), self.client.loop)
            return future.result(timeout=5.0)
        except asyncio.TimeoutError:
            logger.error("Sending message timed out")
            raise RuntimeError("Sending message timed out")
        except Exception as e:
            logger.error(f"Error in send_test_message: {str(e)}", exc_info=True)
            raise

    def _run_bot(self):
        try:
            logger.info(f'Running bot {self.bot_config.name} with token: {self.bot_config.token[:10]}...')
            self.client.run(self.bot_config.token)
        except Exception as e:
            logger.error(f"Error running bot: {e}", exc_info=True)
            self.is_running = False
            self._bot_ready.set()  # 設置事件以避免死鎖 