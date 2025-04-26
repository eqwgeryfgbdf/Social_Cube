"""
Example commands for Discord bots
These can be imported and registered with any bot instance.
"""

import discord
from discord import app_commands
import random
import time
import platform
from typing import Optional
from .commands import command, group

# Create a utility group
util_group = group("util", "Utility commands for the bot")

@util_group.command(description="Ping the bot to check latency")
async def ping(bot, interaction: discord.Interaction):
    """Check the bot's latency"""
    latency = bot.latency * 1000  # Convert to ms
    start_time = time.time()
    
    # Initial response
    await interaction.response.send_message("Pinging...")
    
    # Edit with the results
    message = await interaction.original_response()
    end_time = time.time()
    
    api_latency = (end_time - start_time) * 1000  # Convert to ms
    
    embed = discord.Embed(
        title="🏓 Pong!",
        color=discord.Color.green()
    )
    
    embed.add_field(name="Bot Latency", value=f"{latency:.2f} ms", inline=True)
    embed.add_field(name="API Latency", value=f"{api_latency:.2f} ms", inline=True)
    
    await message.edit(content=None, embed=embed)

@util_group.command(description="Get basic server information")
async def serverinfo(bot, interaction: discord.Interaction):
    """Display information about the current server"""
    guild = interaction.guild
    
    if not guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    
    # Create embed with server info
    embed = discord.Embed(
        title=f"{guild.name} Info",
        description=guild.description or "No description set",
        color=discord.Color.blue()
    )
    
    # Add fields with server information
    created_at = int(guild.created_at.timestamp())
    
    # General information
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
    embed.add_field(name="Created On", value=f"<t:{created_at}:D> (<t:{created_at}:R>)", inline=True)
    
    # Member stats
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    bot_count = sum(1 for member in guild.members if member.bot)
    embed.add_field(name="Humans", value=guild.member_count - bot_count, inline=True)
    embed.add_field(name="Bots", value=bot_count, inline=True)
    
    # Channel stats
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    categories = len(guild.categories)
    embed.add_field(name="Text Channels", value=text_channels, inline=True)
    embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
    embed.add_field(name="Categories", value=categories, inline=True)
    
    # Other counts
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
    embed.add_field(name="Boost Level", value=f"Level {guild.premium_tier}", inline=True)
    
    # Add server icon as thumbnail if available
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    await interaction.response.send_message(embed=embed)

# Create a fun commands group
fun_group = group("fun", "Fun and miscellaneous commands")

@fun_group.command(description="Get a random 8-ball response to a question")
async def eightball(bot, interaction: discord.Interaction, question: str):
    """Ask the Magic 8-Ball a question"""
    responses = [
        # Positive responses
        "It is certain.",
        "It is decidedly so.",
        "Without a doubt.",
        "Yes - definitely.",
        "You may rely on it.",
        "As I see it, yes.",
        "Most likely.",
        "Outlook good.",
        "Yes.",
        "Signs point to yes.",
        
        # Neutral responses
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        
        # Negative responses
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Very doubtful."
    ]
    
    # Select a random response
    response = random.choice(responses)
    
    # Create and send an embed with the question and response
    embed = discord.Embed(
        title="🎱 The Magic 8-Ball",
        color=discord.Color.purple()
    )
    
    embed.add_field(name="Question", value=question, inline=False)
    embed.add_field(name="Answer", value=response, inline=False)
    
    await interaction.response.send_message(embed=embed)

@fun_group.command(description="Roll one or more dice")
async def roll(bot, interaction: discord.Interaction, dice: str = "1d20"):
    """
    Roll dice in the format XdY where X is the number of dice and Y is the sides
    Examples: 1d20, 3d6, 2d10
    """
    try:
        # Parse the dice string
        parts = dice.lower().split('d')
        if len(parts) != 2:
            raise ValueError("Invalid dice format")
            
        num_dice = int(parts[0])
        sides = int(parts[1])
        
        # Validate input
        if num_dice < 1 or num_dice > 100:
            await interaction.response.send_message("Please use between 1 and 100 dice.", ephemeral=True)
            return
            
        if sides < 2 or sides > 1000:
            await interaction.response.send_message("Dice must have between 2 and 1000 sides.", ephemeral=True)
            return
            
        # Roll the dice
        results = [random.randint(1, sides) for _ in range(num_dice)]
        total = sum(results)
        
        # Format the response
        if num_dice == 1:
            description = f"You rolled a {total}"
        else:
            description = f"You rolled: {', '.join(str(r) for r in results)}\nTotal: {total}"
            
        # Create and send an embed with the roll results
        embed = discord.Embed(
            title=f"🎲 Dice Roll: {dice}",
            description=description,
            color=discord.Color.gold()
        )
        
        await interaction.response.send_message(embed=embed)
        
    except ValueError as e:
        await interaction.response.send_message(
            f"Error: {str(e)}. Please use the format XdY (e.g., 1d20, 3d6).",
            ephemeral=True
        )

# System commands
@command(description="Show system information about the bot")
async def system(bot, interaction: discord.Interaction):
    """Show system information about the bot"""
    
    # Get system info
    py_version = platform.python_version()
    discord_version = discord.__version__
    os_name = platform.system()
    os_version = platform.version()
    processor = platform.processor() or "Unknown"
    
    # Bot stats
    uptime = time.time() - bot.startup_time if bot.startup_time else 0
    days, remainder = divmod(uptime, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
    
    # Create embed
    embed = discord.Embed(
        title="System Information",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Bot User", value=f"{bot.user.name} ({bot.user.id})", inline=False)
    
    # System information
    embed.add_field(name="Python Version", value=py_version, inline=True)
    embed.add_field(name="Discord.py Version", value=discord_version, inline=True)
    embed.add_field(name="Operating System", value=f"{os_name} {os_version}", inline=True)
    
    # Bot statistics
    embed.add_field(name="Uptime", value=uptime_str, inline=True)
    embed.add_field(name="Guilds", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="Users", value=str(sum(g.member_count for g in bot.guilds)), inline=True)
    
    # Set bot avatar as thumbnail
    if bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
        
    embed.set_footer(text="Powered by Social Cube")
    
    await interaction.response.send_message(embed=embed)