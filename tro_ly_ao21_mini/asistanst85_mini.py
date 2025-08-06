import os
import importlib.util
from typing import Dict, Any, List, Callable, TypedDict, Optional

# Define the expected plugin_info structure
class PluginInfo(TypedDict, total=False):
    enabled: bool
    register: Callable[[Any], None]
    command_handle: List[str]

class PluginLoader:
    def __init__(self, plugins_folder: str = "plugins"):
        self.plugins_folder = plugins_folder
        os.makedirs(plugins_folder, exist_ok=True)

    def load_plugins(self, assistant: Any) -> None:
        """Dynamically load all plugins from the plugins folder"""
        for filename in os.listdir(self.plugins_folder):
            if not filename.endswith('.py') or filename.startswith('_'):
                continue
                
            plugin_path = os.path.join(self.plugins_folder, filename)
            try:
                # Load plugin module
                spec = importlib.util.spec_from_file_location(f"plugin_{filename[:-3]}", plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Get plugin info
                plugin_info: PluginInfo = getattr(module, 'plugin_info', {})
                if not plugin_info.get('enabled', True):
                    continue
                    
                # Register plugin using the register function
                if 'register' in plugin_info and callable(plugin_info['register']):
                    plugin_info['register'](assistant)
            except Exception as e:
                print(f"⚠️ Error loading plugin {filename}: {e}")

class VirtualAssistant:
    def __init__(self):
        self.handlers: List[Any] = []
        self.loader = PluginLoader()
        self.context: Dict[str, Any] = {}

    def process_command(self, command: str) -> bool:
        """Process user command"""
        command = command.strip().lower()
        
        if command in ['exit', 'quit', 'thoát']:
            print("👋 Goodbye!")
            return False
            
        for handler in self.handlers:
            if hasattr(handler, 'can_handle') and handler.can_handle(command):
                if hasattr(handler, 'handle'):
                    handler.handle(command)
                    return True
                
        print("🤷 I don't understand that command")
        return True
        
    def run(self) -> None:
        """Main execution loop"""
        print("🤖 Xin chào, tôi là trợ lý ảo (Asi-1)")
        print("Nhập 'exit' để thoát. \n")
        self.loader.load_plugins(self)
        
        while True:
            try:
                user_input = input("Bạn: ")
                if not self.process_command(user_input):
                    break
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    assistant = VirtualAssistant()
    assistant.run()