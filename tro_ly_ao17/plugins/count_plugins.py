# plugins/count_plugins.py

import os
import importlib.util
from typing import Any

def register(assistant: Any):
    handler = CountPluginsHandler()
    assistant.handlers.insert(2, handler)
    print("✅ Đã đăng ký CountPluginsHandler")

class CountPluginsHandler:
    def can_handle(self, command: str) -> bool:
        return command.strip().lower() in ["số plugin", "count plugins"]

    def handle(self, command: str) -> bool:
        folder = "plugins"
        plugins = []
        
        for file in os.listdir(folder):
            if file.endswith(".py") and file != "__init__.py":
                plugin_name = file[:-3]
                description = self._load_plugin_description(folder, plugin_name)
                plugins.append((plugin_name, description))
        
        print(f"📦 Hệ thống hiện có {len(plugins)} plugin:\n")
        for name, desc in plugins:
            if desc:
                print(f"🔹 {name} - {desc}")
            else:
                print(f"🔹 {name}")
        return True

    def _load_plugin_description(self, folder: str, plugin_name: str) -> str:
        """
        Nạp plugin và lấy plugin_info["description"] nếu có
        """
        try:
            path = os.path.join(folder, plugin_name + ".py")
            spec = importlib.util.spec_from_file_location(plugin_name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            plugin_info = getattr(module, "plugin_info", None)
            if plugin_info and "description" in plugin_info:
                return plugin_info["description"]
        except Exception as e:
            # Bỏ qua lỗi load plugin
            pass
        return ""

plugin_info = {
    "enabled": True,
    "register": register,
    "methods": [],
    "classes": [],
    "description": "Hiển thị số lượng và danh sách plugin hiện có trong hệ thống.",
}