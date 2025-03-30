# announcement.py
import discord
from discord.ext import commands
import logging

from utils.config import ANNOUNCEMENT_CHANNEL_ID

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Announcement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Support multiple announcement channels
        self.announcement_channels = [ANNOUNCEMENT_CHANNEL_ID]  # Keep the original channel
        logging.info(f"Announcement channels initialized: {self.announcement_channels}")
    
    async def broadcast_announcement(self, announcement_message: str):
        """
        Core announcement function that handles role/mention replacements and broadcasts to all announcement channels.
        """
        if not self.bot.guilds:
            logging.warning("Bot is not in any guilds, cannot send announcement.")
            return False

        guild = self.bot.guilds[0]  # Use the first guild for role/member lookups

        # Handle role and member mentions
        if '@' in announcement_message:
            parts = announcement_message.split(' ')
            new_parts = []
            for part in parts:
                # Handle role mentions (@&role_name)
                if part.startswith('@&'):
                    role_name = part[2:]
                    role = discord.utils.get(guild.roles, name=role_name)
                    if role:
                        new_parts.append(f'<@&{role.id}>')
                    else:
                        new_parts.append(part)
                        logging.warning(f'Role "{role_name}" not found in guild.')
                # Handle member mentions (@member_name)
                elif part.startswith('@'):
                    member_name = part[1:]
                    member = discord.utils.get(guild.members, name=member_name)
                    if member:
                        new_parts.append(f'<@{member.id}>')
                    else:
                        new_parts.append(part)
                        logging.warning(f'Member "{member_name}" not found in guild.')
                else:
                    new_parts.append(part)

            announcement_message = ' '.join(new_parts)

        # Broadcast to all announcement channels
        success = False
        for ch_id in self.announcement_channels:
            channel = self.bot.get_channel(ch_id)
            if channel:
                try:
                    await channel.send(f"**Announcement:** {announcement_message}")
                    logging.info(f'Announcement sent to channel: {channel.name} (ID: {ch_id})')
                    success = True
                except Exception as e:
                    logging.error(f'Failed to send message to channel ID {ch_id}: {e}')
            else:
                logging.warning(f'Channel not found: {ch_id}')

        return success

    @commands.dm_only()
    @commands.command(name="announce")
    async def announce(self, ctx, *, message: str):
        """
        Allows authorized users to post an announcement to the public channel.
        Usage (in DM): !announce Your announcement message here
        """
        success = await self.broadcast_announcement(message)
        if success:
            await ctx.send("Announcement posted successfully!")
        else:
            await ctx.send("Failed to post announcement to any channels.")

    def add_announcement_channel(self, channel_id: int):
        """Add a new channel to the announcement channels list."""
        if channel_id not in self.announcement_channels:
            self.announcement_channels.append(channel_id)
            logging.info(f"Added new announcement channel: {channel_id}")

    def remove_announcement_channel(self, channel_id: int):
        """Remove a channel from the announcement channels list."""
        if channel_id in self.announcement_channels:
            self.announcement_channels.remove(channel_id)
            logging.info(f"Removed announcement channel: {channel_id}")

async def setup(bot):
    """這裡提供給 bot.load_extension() 時候呼叫"""
    await bot.add_cog(Announcement(bot)) 