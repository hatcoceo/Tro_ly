# thêm chức năng import lẫn nhau giữa các plugin
import os
import sys
import importlib.util
from typing import Dict, Any, List, Callable, TypedDict, Optional

class PluginInfo(TypedDict, total=False):
    enabled: bool
    register: Callable[[Any], None]
    command_handle: Optional[List[str]]
    
class PluginLoader:
    def __init__(self, plugins_folder: str = "plugins"):
        self.plugins_folder = plugins_folder
        os.makedirs(plugins_folder, exist_ok=True)
        init_file = os.path.join(self.plugins_folder, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8"):
                pass
                
    def load_plugins(self, assistant: Any) -> None:
        """Tải tất cả plugin từ thư mục plugins"""
        for filename in os.listdir(self.plugins_folder):
            if not filename.endswith('.py'):
                continue
            if filename.startswith('_'):
                continue
            if filename == "__init__.py":
                continue
            plugin_path = os.path.join(self.plugins_folder, filename)
            try:
                spec = importlib.util.spec_from_file_location(f"plugins.{filename[:-3]}", plugin_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                plugin_info: PluginInfo = getattr(module, 'plugin_info', {})
                if not plugin_info.get('enabled', True):
                    continue
                if 'register' in plugin_info and callable(plugin_info['register']):
                    plugin_info['register'](assistant)
            except Exception as e:
                print(f"⚠️ Lỗi khi tải plugin {filename}: {e}")
                
class VirtualAssistant:
    def __init__(self, loader=None, process_command=None):
        self.handlers: List[Any] = []
        self.loader = loader or PluginLoader()
        self.context: Dict[str, Any] = {}
        self._process_command = process_command
        
    def process_command(self, command: str):
        if self._process_command:
            return self._process_command(command)
        command = command.strip()
        if command in ['exit', 'quit', 'thoát']:
            print("👋 Tạm biệt!")
            return False
        for handler in self.handlers:
            if hasattr(handler, 'can_handle') and handler.can_handle(command):
                if hasattr(handler, 'handle'):
                    result = handler.handle(command)
                    if result is None:
                        return True
                    return result
        print("🤷 Tôi không hiểu lệnh đó")
        return True
        
    def run(self) -> None:
        """Vòng lặp chính"""
        print("🤖 Xin chào, tôi là trợ lý ảo (Asi-86)")
        print("Nhập 'exit' để thoát.\n")
        while True:
            try:
                user_input = input("Bạn: ")
                if not self.process_command(user_input):
                    break
            except KeyboardInterrupt:
                print("\n👋 Tạm biệt!")
                break
            except Exception as e:
                print(f"⚠️ Lỗi: {e}")
                
def start():
    """Tạo và khởi động trợ lý ảo"""
    assistant = VirtualAssistant()
    assistant.loader.load_plugins(assistant)
    assistant.run()
if __name__ == "__main__":
    start()