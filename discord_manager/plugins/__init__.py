"""
Plugin system initialization.
This package contains the core plugin system and plugin base classes.
"""

from .base import BasePlugin
from .manager import PluginManager

__all__ = ['BasePlugin', 'PluginManager'] 