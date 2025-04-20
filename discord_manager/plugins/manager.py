import os
import importlib
import inspect
from typing import Dict, Type, Optional, List
import yaml
from pathlib import Path

from .base import BasePlugin

class PluginManager:
    """Manages the loading, unloading, and configuration of plugins."""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_classes: Dict[str, Type[BasePlugin]] = {}
        self._load_plugin_classes()
        
    def _load_plugin_classes(self) -> None:
        """Discover and load all plugin classes from the plugins directory."""
        plugins_path = Path(self.plugins_dir)
        if not plugins_path.exists():
            return
            
        for file in plugins_path.glob("*.py"):
            if file.name.startswith("_"):
                continue
                
            module_name = file.stem
            try:
                module = importlib.import_module(f"{self.plugins_dir}.{module_name}")
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BasePlugin) and 
                        obj != BasePlugin):
                        self.plugin_classes[obj.__name__] = obj
            except Exception as e:
                print(f"Failed to load plugin {module_name}: {e}")
                
    async def load_plugin(self, plugin_name: str, config: Optional[Dict] = None) -> Optional[BasePlugin]:
        """Load and initialize a plugin by name."""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]
            
        if plugin_name not in self.plugin_classes:
            print(f"Plugin {plugin_name} not found")
            return None
            
        try:
            plugin = self.plugin_classes[plugin_name]()
            if config:
                plugin.configure(config)
            self.plugins[plugin_name] = plugin
            return plugin
        except Exception as e:
            print(f"Failed to initialize plugin {plugin_name}: {e}")
            return None
            
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin by name."""
        if plugin_name not in self.plugins:
            return False
            
        plugin = self.plugins[plugin_name]
        if plugin.is_enabled:
            await plugin.disable()
        
        del self.plugins[plugin_name]
        return True
        
    async def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a loaded plugin."""
        if plugin_name not in self.plugins:
            return False
            
        await self.plugins[plugin_name].enable()
        return True
        
    async def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a loaded plugin."""
        if plugin_name not in self.plugins:
            return False
            
        await self.plugins[plugin_name].disable()
        return True
        
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get a plugin instance by name."""
        return self.plugins.get(plugin_name)
        
    def list_available_plugins(self) -> List[str]:
        """List all available plugin classes."""
        return list(self.plugin_classes.keys())
        
    def list_loaded_plugins(self) -> List[str]:
        """List all loaded plugin instances."""
        return list(self.plugins.keys())
        
    def save_config(self, config_file: str = "plugin_config.yml") -> None:
        """Save the current plugin configuration to a file."""
        config = {
            name: {
                "enabled": plugin.is_enabled,
                "config": plugin.config
            }
            for name, plugin in self.plugins.items()
        }
        
        with open(config_file, "w") as f:
            yaml.dump(config, f)
            
    def load_config(self, config_file: str = "plugin_config.yml") -> None:
        """Load plugin configuration from a file."""
        if not os.path.exists(config_file):
            return
            
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
            
        for plugin_name, plugin_config in config.items():
            plugin = self.get_plugin(plugin_name)
            if plugin:
                plugin.configure(plugin_config.get("config", {}))
                if plugin_config.get("enabled", False):
                    plugin.enable() 