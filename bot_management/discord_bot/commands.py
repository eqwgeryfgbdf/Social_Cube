import discord
from discord import app_commands
from typing import Dict, List, Any, Callable, Optional, Union
import inspect
import logging
import functools

# Configure logging
logger = logging.getLogger(__name__)

class CommandGroup:
    """Group of commands with a common prefix"""
    
    def __init__(self, name: str, description: str = None):
        """
        Initialize a command group
        
        Args:
            name: The name of the command group
            description: Optional description for the group
        """
        self.name = name
        self.description = description or f"Commands in the {name} group"
        self.commands = {}
        
    def command(self, name: str = None, description: str = None):
        """
        Decorator to register a command in this group
        
        Args:
            name: Optional name override for the command
            description: Optional description for the command
        """
        def decorator(func):
            cmd_name = name or func.__name__
            cmd_desc = description or func.__doc__ or f"The {cmd_name} command"
            
            # Store the command in the group
            self.commands[cmd_name] = {
                'callback': func,
                'description': cmd_desc
            }
            
            # Return the original function
            return func
        return decorator
        
    def get_commands(self) -> Dict[str, Dict[str, Any]]:
        """Get all commands registered in this group"""
        return self.commands

class CommandRegistry:
    """Registry for bot commands"""
    
    def __init__(self):
        """Initialize the command registry"""
        self.groups = {}
        self.global_commands = {}
        
    def group(self, name: str, description: str = None) -> CommandGroup:
        """
        Create a new command group
        
        Args:
            name: The name of the command group
            description: Optional description for the group
            
        Returns:
            CommandGroup: The created command group
        """
        if name in self.groups:
            return self.groups[name]
            
        group = CommandGroup(name, description)
        self.groups[name] = group
        return group
        
    def command(self, name: str = None, description: str = None):
        """
        Decorator to register a global command
        
        Args:
            name: Optional name override for the command
            description: Optional description for the command
        """
        def decorator(func):
            cmd_name = name or func.__name__
            cmd_desc = description or func.__doc__ or f"The {cmd_name} command"
            
            # Store the command
            self.global_commands[cmd_name] = {
                'callback': func,
                'description': cmd_desc
            }
            
            # Return the original function
            return func
        return decorator
        
    def register_to_bot(self, bot):
        """
        Register all commands to a bot's command tree
        
        Args:
            bot: The SocialCubeBot instance to register commands with
        """
        # Register global commands
        for cmd_name, cmd_data in self.global_commands.items():
            @bot.tree.command(name=cmd_name, description=cmd_data['description'])
            async def command_wrapper(interaction: discord.Interaction, *args, **kwargs):
                # Get the original command that matches this wrapper's name
                cmd_info = self.global_commands.get(interaction.command.name)
                if cmd_info:
                    try:
                        # Call the original command
                        await cmd_info['callback'](bot, interaction, *args, **kwargs)
                        bot.command_count += 1
                    except Exception as e:
                        logger.error(f"Error executing command {interaction.command.name}: {str(e)}")
                        await interaction.response.send_message(
                            f"An error occurred while executing this command.",
                            ephemeral=True
                        )
                        
        # Register group commands
        for group_name, group in self.groups.items():
            # Create app_commands Group
            app_group = app_commands.Group(name=group_name, description=group.description)
            
            # Add commands to the group
            for cmd_name, cmd_data in group.get_commands().items():
                @app_commands.command(name=cmd_name, description=cmd_data['description'])
                async def command_wrapper(interaction: discord.Interaction, *args, **kwargs):
                    # Get the correct command from the group
                    cmd_group = self.groups.get(interaction.command.parent.name)
                    if cmd_group:
                        cmd_info = cmd_group.get_commands().get(interaction.command.name)
                        if cmd_info:
                            try:
                                # Call the original command
                                await cmd_info['callback'](bot, interaction, *args, **kwargs)
                                bot.command_count += 1
                            except Exception as e:
                                logger.error(f"Error executing command {interaction.command.parent.name} {interaction.command.name}: {str(e)}")
                                await interaction.response.send_message(
                                    f"An error occurred while executing this command.",
                                    ephemeral=True
                                )
                                
                # Add the command to the group
                app_group.add_command(command_wrapper)
                
            # Add the group to the bot's command tree
            bot.tree.add_command(app_group)
            
        logger.info(f"Registered {len(self.global_commands)} global commands and {len(self.groups)} command groups")

# Create the global registry
command_registry = CommandRegistry()

# Helper decorators for easier command registration
def command(name=None, description=None):
    """Global command decorator"""
    return command_registry.command(name, description)
    
def group(name, description=None):
    """Command group decorator factory"""
    return command_registry.group(name, description)