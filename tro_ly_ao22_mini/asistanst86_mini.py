import os
import importlib.util
from typing import Dict, Any, List, Callable, TypedDict, Optional

# Định nghĩa cấu trúc plugin_info
class PluginInfo(TypedDict, total=False):
    enabled: bool
    register: Callable[[Any], None]
    command_handle: Optional[List[str]]

class PluginLoader:
    def __init__(self, plugins_folder: str = "plugins"):
        self.plugins_folder = plugins_folder
        os.makedirs(plugins_folder, exist_ok=True)

    def load_plugins(self, assistant: Any) -> None:
        """Tải tất cả plugin từ thư mục plugins"""
        for filename in os.listdir(self.plugins_folder):
            if not filename.endswith('.py') or filename.startswith('_'):
                continue
                
            plugin_path = os.path.join(self.plugins_folder, filename)
            try:
                # Load plugin module
                spec = importlib.util.spec_from_file_location(f"plugin_{filename[:-3]}", plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Lấy thông tin plugin
                plugin_info: PluginInfo = getattr(module, 'plugin_info', {})
                if not plugin_info.get('enabled', True):
                    continue
                    
                # Gọi hàm register của plugin
                if 'register' in plugin_info and callable(plugin_info['register']):
                    plugin_info['register'](assistant)
            except Exception as e:
                print(f"⚠️ Lỗi khi tải plugin {filename}: {e}")

class VirtualAssistant:
    def __init__(self):
        self.handlers: List[Any] = []
        self.loader = PluginLoader()
        self.context: Dict[str, Any] = {}

    def process_command(self, command: str) -> bool:
        """Xử lý lệnh từ người dùng"""
        command = command.strip().lower()
        
        if command in ['exit', 'quit', 'thoát']:
            print("👋 Tạm biệt!")
            return False
            
        for handler in self.handlers:
            if hasattr(handler, 'can_handle') and handler.can_handle(command):
                if hasattr(handler, 'handle'):
                    handler.handle(command)
                    return True
                
        print("🤷 Tôi không hiểu lệnh đó")
        return True
        
    def run(self) -> None:
        """Vòng lặp chính"""
        print("🤖 Xin chào, tôi là trợ lý ảo (Asi-1)")
        print("Nhập 'exit' để thoát. \n")
        
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