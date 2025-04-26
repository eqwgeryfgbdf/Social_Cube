import discord
import logging
import json
import os
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional, Union
import time
from bot_management.models import BotLog

# Configure logging
logger = logging.getLogger(__name__)

async def send_paginated_message(
    interaction: discord.Interaction,
    pages: List[Union[discord.Embed, str]],
    ephemeral: bool = False,
    timeout: int = 300
) -> None:
    """
    Send a paginated message with navigation buttons
    
    Args:
        interaction: The original Discord interaction
        pages: List of embeds or strings to paginate
        ephemeral: Whether the response should be ephemeral
        timeout: Button timeout in seconds
    """
    if not pages:
        return
    
    # Initialize page counter
    current_page = 0
    
    # Create buttons for navigation
    first_button = discord.ui.Button(emoji="⏮️", style=discord.ButtonStyle.secondary)
    prev_button = discord.ui.Button(emoji="◀️", style=discord.ButtonStyle.secondary)
    next_button = discord.ui.Button(emoji="▶️", style=discord.ButtonStyle.secondary)
    last_button = discord.ui.Button(emoji="⏭️", style=discord.ButtonStyle.secondary)
    
    # Create view with buttons
    view = discord.ui.View(timeout=timeout)
    view.add_item(first_button)
    view.add_item(prev_button)
    view.add_item(next_button)
    view.add_item(last_button)
    
    # Define button callbacks
    async def update_page(button_interaction: discord.Interaction, new_page: int):
        nonlocal current_page
        current_page = max(0, min(new_page, len(pages) - 1))
        
        content = None
        embed = None
        
        if isinstance(pages[current_page], discord.Embed):
            embed = pages[current_page]
            # Add page counter to footer
            embed.set_footer(text=f"Page {current_page + 1}/{len(pages)}")
        else:
            content = f"{pages[current_page]}\n\nPage {current_page + 1}/{len(pages)}"
            
        await button_interaction.response.edit_message(content=content, embed=embed, view=view)
    
    # Set button callbacks
    first_button.callback = lambda i: update_page(i, 0)
    prev_button.callback = lambda i: update_page(i, current_page - 1)
    next_button.callback = lambda i: update_page(i, current_page + 1)
    last_button.callback = lambda i: update_page(i, len(pages) - 1)
    
    # Handle initial response
    content = None
    embed = None
    
    if isinstance(pages[0], discord.Embed):
        embed = pages[0]
        # Add page counter to footer
        embed.set_footer(text=f"Page 1/{len(pages)}")
    else:
        content = f"{pages[0]}\n\nPage 1/{len(pages)}"
        
    await interaction.response.send_message(content=content, embed=embed, view=view, ephemeral=ephemeral)

async def fetch_json(url: str, headers: Dict = None) -> Dict:
    """
    Fetch JSON data from a URL
    
    Args:
        url: The URL to fetch from
        headers: Optional headers for the request
        
    Returns:
        Dict: The JSON response data
        
    Raises:
        Exception: If the request fails or returns invalid JSON
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"Request failed with status {response.status}")
            
            try:
                return await response.json()
            except Exception as e:
                raise Exception(f"Failed to parse JSON: {str(e)}")

def log_bot_event(bot_id: int, event_type: str, description: str) -> None:
    """
    Log a bot event to the database
    
    Args:
        bot_id: The database ID of the bot
        event_type: The type of event
        description: Description of the event
    """
    try:
        from bot_management.models import Bot
        
        bot = Bot.objects.get(id=bot_id)
        BotLog.objects.create(
            bot=bot,
            event_type=event_type,
            description=description
        )
    except Exception as e:
        logger.error(f"Failed to log bot event: {str(e)}")

class RateLimiter:
    """A utility for rate limiting operations"""
    
    def __init__(self, limit: int, interval: float):
        """
        Initialize a rate limiter
        
        Args:
            limit: Maximum number of operations in the interval
            interval: Time interval in seconds
        """
        self.limit = limit
        self.interval = interval
        self.operations = []
        
    async def acquire(self) -> bool:
        """
        Attempt to acquire permission to perform an operation
        
        Returns:
            bool: True if operation is allowed, False otherwise
        """
        now = time.time()
        
        # Remove timestamps older than the interval
        self.operations = [t for t in self.operations if now - t <= self.interval]
        
        # Check if under the limit
        if len(self.operations) < self.limit:
            self.operations.append(now)
            return True
            
        # Calculate time to wait if over limit
        if self.operations:
            oldest = min(self.operations)
            wait_time = self.interval - (now - oldest)
            
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                return await self.acquire()
                
        return False