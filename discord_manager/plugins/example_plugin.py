from .base import BasePlugin

class ExamplePlugin(BasePlugin):
    """An example plugin to demonstrate the plugin system."""
    
    def __init__(self):
        super().__init__()
        self.description = "An example plugin that demonstrates the plugin system"
        self.version = "1.0.0"
        
    async def setup(self) -> None:
        """Setup the plugin."""
        print(f"Setting up {self.name}")
        # Add your initialization code here
        # For example:
        # - Register commands
        # - Initialize resources
        # - Setup event listeners
        
    async def cleanup(self) -> None:
        """Cleanup the plugin."""
        print(f"Cleaning up {self.name}")
        # Add your cleanup code here
        # For example:
        # - Unregister commands
        # - Release resources
        # - Remove event listeners 