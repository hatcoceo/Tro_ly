import os
import importlib.util
from typing import Dict, Any, List, Callable, TypedDict, Optional
from flask import Flask, request, jsonify, render_template

# ------------------------
# Plugin Loader
# ------------------------
class PluginInfo(TypedDict, total=False):
    enabled: bool
    register: Callable[[Any], None]
    command_handle: Optional[List[str]]

class PluginLoader:
    def __init__(self, plugins_folder: str = "plugins"):
        self.plugins_folder = plugins_folder
        os.makedirs(plugins_folder, exist_ok=True)

    def load_plugins(self, assistant: Any) -> None:
        for filename in os.listdir(self.plugins_folder):
            if not filename.endswith('.py') or filename.startswith('_'):
                continue
                
            plugin_path = os.path.join(self.plugins_folder, filename)
            try:
                spec = importlib.util.spec_from_file_location(f"plugin_{filename[:-3]}", plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                plugin_info: PluginInfo = getattr(module, 'plugin_info', {})
                if not plugin_info.get('enabled', True):
                    continue
                    
                if 'register' in plugin_info and callable(plugin_info['register']):
                    plugin_info['register'](assistant)
            except Exception as e:
                print(f"⚠️ Lỗi khi tải plugin {filename}: {e}")

# ------------------------
# Virtual Assistant
# ------------------------
class VirtualAssistant:
    def __init__(self):
        self.handlers: List[Any] = []
        self.loader = PluginLoader()
        self.context: Dict[str, Any] = {}

    def process_command(self, command: str) -> str:
        command = command.strip().lower()
        
        if command in ['exit', 'quit', 'thoát']:
            return "👋 Tạm biệt!"
            
        for handler in self.handlers:
            if hasattr(handler, 'can_handle') and handler.can_handle(command):
                if hasattr(handler, 'handle'):
                    return handler.handle(command)
                
        return "🤷 Tôi không hiểu lệnh đó"

# ------------------------
# Flask App
# ------------------------
app = Flask(__name__)
assistant = VirtualAssistant()
assistant.loader.load_plugins(assistant)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")  # Lấy từ templates/index.html

@app.route("/command", methods=["POST"])
def command():
    data = request.get_json()
    if not data or "command" not in data:
        return jsonify({"error": "Thiếu 'command'"}), 400
    
    cmd = data["command"]
    response = assistant.process_command(cmd)
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)