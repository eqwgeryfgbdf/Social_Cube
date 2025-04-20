from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BasePlugin(ABC):
    """Base class for all plugins."""
    
    def __init__(self):
        self.name: str = self.__class__.__name__
        self.description: str = "No description provided"
        self.version: str = "0.1.0"
        self.enabled: bool = False
        self.config: Dict[str, Any] = {}
        
    @abstractmethod
    async def setup(self) -> None:
        """Setup the plugin. Called when the plugin is loaded."""
        pass
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup the plugin. Called when the plugin is unloaded."""
        pass
    
    async def enable(self) -> None:
        """Enable the plugin."""
        if not self.enabled:
            await self.setup()
            self.enabled = True
    
    async def disable(self) -> None:
        """Disable the plugin."""
        if self.enabled:
            await self.cleanup()
            self.enabled = False
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the plugin with the given configuration."""
        self.config.update(config)
    
    @property
    def is_enabled(self) -> bool:
        """Check if the plugin is enabled."""
        return self.enabled 